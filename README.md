# Fleet Command Center

Streamlit IT support dashboard with live local telemetry, Groq chat, and verified-resolution memory in Hindsight.

## Run

```powershell
venv/Scripts/python.exe -m pip install -r requirements.txt
venv/Scripts/python.exe -m streamlit run app.py --server.address 127.0.0.1 --server.port 8502
```

Set `GROQ_API_KEY` and `HINDSIGHT_API_KEY` in `.env`. Optional configuration: `GROQ_MODEL`, `HINDSIGHT_BANK_ID`, and `HINDSIGHT_BASE_URL`. Restart after changing configuration. Settings → Test service connections verifies the configured model and memory bank.

## Real data sources

- The only connected device is the **machine running Streamlit**, not a browser visitor's computer or a remote fleet. Inventory comes from the OS; Windows uses registry/CIM hardware information.
- CPU and aggregate network throughput are sampled over 250 ms. Memory and system-volume usage come from psutil. The health panel refreshes every five seconds while the session is active. Network is KiB/s, not a fabricated utilization percentage.
- Diagnostic shortcuts collect host inventory, adapter status, memory-heavy processes, and Windows System warnings/errors from the last 24 hours. Diagnostics remain local and work without cloud services. Missing permissions produce an explicit error.
- Chat uses the configured Groq model. Hindsight recalls only records tagged `fleet-verified-resolution-v1`; old untagged sample memories are excluded without deleting them. If recall fails or finds no fix, the answer is labeled general guidance.
- Sending a message transitions the dashboard into a focused conversation. User bubbles align right, assistant bubbles align left, loading dots indicate pending work, and Groq text streams with a typing cursor. Follow-ups scroll to the latest user turn. Controls are temporarily disabled during generation; interrupted responses retain their partial text. Dashboard navigation preserves the conversation, while Reset starts a new one. Reduced-motion preferences disable the transition animations.
- Optional sharing beside the composer sends only current CPU/memory/disk readings to Groq. Local log and process reports are excluded from AI conversation history.
- Resolution library saves operator-verified fixes to `data/resolutions.sqlite3`, then syncs to Hindsight. Failed syncs remain retryable. Stable document IDs make repeated saves of the same content reuse a record.
- Chat/activity history is browser-session scoped. Export the conversation before ending the session. Resolution records survive restarts.

This is a local operator application. It does not execute remediation scripts or authenticate remote administrators. Keep it bound to localhost; remote fleet collection requires separately installed endpoint agents and authenticated ingestion.

## Import actual tickets

```powershell
venv/Scripts/python.exe seed_data.py path/to/verified-tickets.json
```

Input must be a JSON array. Each object must contain nonempty `device_target`, `issue`, and `resolution` strings, plus `verified: true`. The entire file is validated before any writes. Failed uploads are retained locally and the command exits nonzero. No sample tickets are shipped or automatically uploaded.

## Verify

```powershell
venv/Scripts/python.exe -m unittest test_workflows -v
```

Tests use actual local telemetry and mocked cloud calls. They never upload test resolutions to Hindsight.
