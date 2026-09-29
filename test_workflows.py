"""Local regression checks; cloud writes are mocked and use temporary storage."""
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import MagicMock, patch

from streamlit.testing.v1 import AppTest

import services
import telemetry
import seed_data


class TelemetryTests(unittest.TestCase):
    def test_real_snapshot_bounds(self):
        readings = telemetry.snapshot(.05)
        for key in ("cpu_percent", "memory_percent", "disk_percent"):
            self.assertGreaterEqual(readings[key], 0)
            self.assertLessEqual(readings[key], 100)
        self.assertGreater(readings["memory_total_gb"], 0)
        self.assertGreaterEqual(readings["network"]["sent_bps"], 0)

    def test_network_rate_and_counter_reset(self):
        before = SimpleNamespace(bytes_sent=100, bytes_recv=200)
        after = SimpleNamespace(bytes_sent=300, bytes_recv=600)
        self.assertEqual(telemetry.network_rates(before, after, 2), {"sent_bps": 100, "received_bps": 200})
        self.assertEqual(telemetry.network_rates(after, before, 2), {"sent_bps": 0, "received_bps": 0})


class ResolutionTests(unittest.TestCase):
    def test_failed_sync_preserves_ticket_and_retry_is_idempotent(self):
        with tempfile.TemporaryDirectory() as directory:
            db = Path(directory) / "test.sqlite3"
            doc = services.save_resolution("Test device", "Test issue", "Verified test fix", db)
            self.assertEqual(doc, services.save_resolution("Test device", "Test issue", "Verified test fix", db))
            client = MagicMock()
            client.retain.side_effect = TimeoutError()
            with patch("services.memory_client", return_value=client):
                with self.assertRaises(TimeoutError):
                    services.sync_resolution(doc, db)
                self.assertFalse(services.list_resolutions(db)[0]["synced"])
                client.retain.side_effect = None
                services.sync_resolution(doc, db)
                services.sync_resolution(doc, db)
                self.assertEqual(client.retain.call_count, 2)
                self.assertTrue(services.list_resolutions(db)[0]["synced"])
                self.assertEqual(len(services.list_resolutions(db)), 1)
                self.assertEqual(client.retain.call_args.kwargs["tags"], [services.VERIFIED_TAG])

    def test_recall_requires_verified_tag(self):
        client = MagicMock()
        client.recall.return_value = SimpleNamespace(results=[])
        with patch("services.memory_client", return_value=client):
            self.assertEqual(services.recall("test"), "")
        self.assertEqual(client.recall.call_args.kwargs["tags_match"], "all_strict")
        client.close.assert_called_once()

    def test_import_rejects_unverified_before_writes(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "tickets.json"
            path.write_text('[{"verified":false}]')
            with patch("seed_data.save_resolution") as save:
                with self.assertRaises(ValueError):
                    seed_data.import_tickets(path)
                save.assert_not_called()


class AppTests(unittest.TestCase):
    def test_ui_rerun_recovers_partial_stream_and_unlocks_controls(self):
        def interrupted(*_):
            import streamlit as st
            yield "Partial reply before rerun"
            st.rerun()
        with patch("services.recall", return_value=""), patch("services.stream_answer", side_effect=interrupted) as stream:
            app = AppTest.from_file("app.py", default_timeout=20).run()
            app.chat_input[0].set_value("Test interrupted UI").run()
            self.assertFalse(app.exception)
            self.assertEqual(stream.call_count, 1)
            self.assertFalse(app.session_state["generating"])
            self.assertFalse(app.chat_input[0].disabled)
            self.assertIn("Partial reply before rerun", app.session_state["messages"][-1]["content"])
            self.assertIn("Response interrupted", app.session_state["messages"][-1]["content"])

    def test_chat_transition_followup_and_reset(self):
        with patch("services.recall", return_value=""), patch("services.stream_answer", side_effect=lambda *_: iter(["Hello", " there."])) as stream:
            app = AppTest.from_file("app.py", default_timeout=20).run()
            app.chat_input[0].set_value("First question").run()
            self.assertFalse(app.exception)
            self.assertTrue(app.session_state["chat_active"])
            self.assertEqual([m["role"] for m in app.session_state["messages"]], ["user", "assistant"])
            app.chat_input[0].set_value("Follow-up question").run()
            self.assertFalse(app.exception)
            self.assertFalse(app.chat_input[0].disabled)
            self.assertFalse(app.button(key="nav_dashboard").disabled)
            self.assertEqual(len(app.session_state["messages"]), 4)
            app.run()  # Rerenders never resubmit a request or replay the stream.
            self.assertEqual(stream.call_count, 2)
            app.button(key="reset").click().run()
            self.assertFalse(app.session_state["chat_active"])
            self.assertEqual(app.session_state["messages"], [])

    def test_interrupted_stream_keeps_partial_answer(self):
        def interrupted(*_):
            yield "Partial answer"
            raise TimeoutError()
        with patch("services.recall", return_value=""), patch("services.stream_answer", side_effect=interrupted):
            app = AppTest.from_file("app.py", default_timeout=20).run()
            app.chat_input[0].set_value("Test interruption").run()
            self.assertFalse(app.exception)
            message = app.session_state["messages"][-1]
            self.assertTrue(message["error"])
            self.assertIn("Partial answer", message["content"])
            self.assertIn("Response interrupted", message["content"])

    def test_local_diagnostics_and_navigation_without_cloud(self):
        with patch("services.stream_answer") as answer, patch("services.recall") as recall:
            app = AppTest.from_file("app.py", default_timeout=20).run()
            self.assertFalse(app.exception)
            for key in ("diag_monitor_heart", "diag_memory", "diag_wifi", "diag_speed"):
                app.button(key=key).click().run()
                self.assertFalse(app.exception)
                self.assertTrue(app.session_state["messages"][-1]["local"])
            answer.assert_not_called()
            recall.assert_not_called()
            app.button(key="nav_history").click().run()
            self.assertFalse(app.exception)
            app.button(key="reset").click().run()
            self.assertEqual(app.session_state["messages"], [])
            app.button(key="nav_settings").click().run()
            self.assertFalse(app.exception)

    def test_chat_memory_failure_still_answers(self):
        with patch("services.recall", side_effect=TimeoutError()), patch("services.stream_answer", return_value=iter(["General ", "guidance"])):
            app = AppTest.from_file("app.py", default_timeout=20).run()
            app.chat_input[0].set_value("Test support request").run()
            self.assertFalse(app.exception)
            self.assertEqual(app.session_state["messages"][-1]["content"], "General guidance")
            self.assertIn("unavailable", app.session_state["messages"][-1]["notice"])
            self.assertEqual(app.session_state["session_queries_count"], 1)

    def test_resolution_form_validation(self):
        with tempfile.TemporaryDirectory() as directory, patch("services.DB_PATH", Path(directory) / "test.sqlite3"):
            app = AppTest.from_file("app.py", default_timeout=20).run()
            app.button(key="nav_library").click().run()
            app.button(key="FormSubmitter:retain_resolution-Save verified resolution").click().run()
            self.assertFalse(app.exception)
            self.assertTrue(app.error)


if __name__ == "__main__":
    unittest.main()
