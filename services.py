"""Bounded service calls and verified-resolution persistence."""
import hashlib
from contextlib import contextmanager
import json
import os
from pathlib import Path
import sqlite3
from datetime import datetime, timezone

from dotenv import load_dotenv
from groq import Groq
from hindsight_client import Hindsight

ROOT = Path(__file__).parent
load_dotenv(ROOT / ".env")
BANK_ID = os.getenv("HINDSIGHT_BANK_ID", "fleet-memory-bank")
MODEL_ID = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")
VERIFIED_TAG = "fleet-verified-resolution-v1"
DB_PATH = ROOT / "data" / "resolutions.sqlite3"


def groq_client():
    key = os.getenv("GROQ_API_KEY")
    if not key:
        raise ValueError("GROQ_API_KEY is missing")
    return Groq(api_key=key, timeout=30, max_retries=1)


def memory_client():
    key = os.getenv("HINDSIGHT_API_KEY")
    if not key:
        raise ValueError("HINDSIGHT_API_KEY is missing")
    return Hindsight(base_url=os.getenv("HINDSIGHT_BASE_URL", "https://api.hindsight.vectorize.io"),
                     api_key=key, timeout=30, max_attempts=2)


def error_message(exc):
    status = getattr(exc, "status_code", None) or getattr(exc, "status", None)
    if isinstance(exc, ValueError):
        return "Credentials are missing. Configure the service in .env and restart the app."
    if isinstance(exc, LookupError):
        return "The configured inference model is not available to this account."
    if status in (401, 403):
        return "The service rejected the credentials or account permissions."
    if status == 429:
        return "The service rate limit or account quota was reached. Try again later."
    if status == 404:
        return "The configured model or memory bank was not found."
    return "The service could not complete the request. Check connectivity and service availability."


def check_services():
    result = {}
    for name, check in [("Groq", check_model), ("Hindsight", check_bank)]:
        try:
            check()
            result[name] = {"ok": True, "message": "Connected", "checked_at": datetime.now().astimezone().strftime("%H:%M:%S")}
        except Exception as exc:
            result[name] = {"ok": False, "message": error_message(exc), "checked_at": datetime.now().astimezone().strftime("%H:%M:%S")}
    return result


def check_model():
    with groq_client() as client:
        models = client.models.list()
        if not any(model.id == MODEL_ID for model in models.data):
            raise LookupError("Configured model is not available")


@contextmanager
def memory_connection():
    client = memory_client()
    try:
        yield client
    finally:
        client.close()


def check_bank():
    with memory_connection() as client:
        return client.get_bank_config(BANK_ID)


def recall(query):
    with memory_connection() as client:
        result = client.recall(bank_id=BANK_ID, query=query,
                              tags=[VERIFIED_TAG], tags_match="all_strict", max_tokens=2048)
    # Empty results must not masquerade as a remembered resolution.
    return "\n\n".join(item.text for item in result.results if item.text)


def answer(messages, system_prompt):
    with groq_client() as client:
        result = client.chat.completions.create(
            model=MODEL_ID, messages=[{"role": "system", "content": system_prompt}] + messages,
            temperature=0.2,
        )
    return result.choices[0].message.content or "The service returned an empty answer. Please retry."


def stream_answer(messages, system_prompt):
    """Yield only text deltas; release the HTTP stream on completion or failure."""
    with groq_client() as client:
        with client.chat.completions.create(
            model=MODEL_ID,
            messages=[{"role": "system", "content": system_prompt}] + messages,
            temperature=0.2, stream=True,
        ) as stream:
            for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content


@contextmanager
def connection(db_path=None):
    path = Path(db_path or DB_PATH)
    path.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(path, timeout=10)
    db.execute("CREATE TABLE IF NOT EXISTS resolutions (id TEXT PRIMARY KEY, device TEXT, issue TEXT, resolution TEXT, created_at TEXT, synced INTEGER DEFAULT 0)")
    db.commit()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def save_resolution(device, issue, resolution, db_path=None):
    fields = [device.strip(), issue.strip(), resolution.strip()]
    if not all(fields):
        raise ValueError("Device, issue, and verified resolution are required.")
    doc_id = hashlib.sha256(json.dumps(fields).encode()).hexdigest()
    with connection(db_path) as db:
        db.execute("INSERT OR IGNORE INTO resolutions VALUES (?, ?, ?, ?, ?, 0)",
                   (doc_id, *fields, datetime.now(timezone.utc).isoformat()))
    return doc_id


def list_resolutions(db_path=None):
    with connection(db_path) as db:
        db.row_factory = sqlite3.Row
        return [dict(row) for row in db.execute("SELECT * FROM resolutions ORDER BY created_at DESC")]


def sync_resolution(doc_id, db_path=None):
    with connection(db_path) as db:
        db.row_factory = sqlite3.Row
        row = db.execute("SELECT * FROM resolutions WHERE id=?", (doc_id,)).fetchone()
        if row is None:
            raise ValueError("Resolution does not exist")
        if row["synced"]:
            return
        with memory_connection() as client:
            client.retain(
                bank_id=BANK_ID, content=f"Device: {row['device']} | Issue: {row['issue']} | Resolution: {row['resolution']}",
                document_id=doc_id, tags=[VERIFIED_TAG],
            )
        db.execute("UPDATE resolutions SET synced=1 WHERE id=?", (doc_id,))
