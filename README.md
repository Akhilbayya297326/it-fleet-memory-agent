<<<<<<< HEAD
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
=======
# 🛡️ Fleet Command: Autonomous IT Memory Agent

**Fleet Command** is an autonomous enterprise IT support agent that leverages **Hindsight Memory** to store, recall, and apply hardware-specific historical resolutions. By bridging persistent vector memory with the speed of Groq LLMs, Fleet Command eliminates generic troubleshooting and reduces repetitive L1 support tickets.

---

## 🎯 The Problem & Solution

### The Enterprise Pain Point

Traditional enterprise IT helpdesks rely on stateless LLM chatbots or static runbooks. When an employee experiences a complex hardware collision (e.g., VPN drops on specific laptop models after security patches), stateless chatbots offer generic, multi-step advice that fails to account for corporate infrastructure history. This leads to prolonged employee downtime and redundant support escalation.

### The Fleet Command Solution
Fleet Command maintains a centralized **Fleet Memory Bank** powered by Hindsight. When senior IT administrators solve an edge-case bug, the resolution is injected directly into Hindsight's memory layer. When an employee asks for help, the agent dynamically recalls that exact historical context, transforming a generic language model into a context-aware internal technician capable of generating executable remediation scripts.

---

## 🏗️ Architecture & Tech Stack

Memory Layer: Hindsight Cloud SDK (hindsight_client) for persistent semantic memory.

LLM Engine: Groq API (openai/gpt-oss-120b) for ultra-fast, low-latency inference.

Frontend UI: Streamlit (Python) for an interactive enterprise command center dashboard.

Resilience: Built-in automatic retry logic with exponential backoff to handle upstream network timeouts gracefully during data seeding and memory calls.

---

## 🧠 Deep Dive: How Hindsight Memory is Utilized

Hindsight memory accounts for the core engine of this agent. The integration is broken down into three lifecycle phases:

### 1. Ingestion & Retention (The Admin Loop)
* **Mechanism:** Using the `hindsight_client` SDK, historical IT tickets and admin-injected fixes are structured and pushed to a persistent cloud memory bank (`fleet-memory-bank`) via the `client.retain()` API.
* **Data Structure:** Each memory block explicitly tags the device target, operating system, reported issue, and verified resolution:
  ```python
  memory_text = f"Device Target: {ticket['device_target']} | Issue: {ticket['issue']} | Resolution: {ticket['resolution']}"
  client.retain(bank_id=BANK_ID, content=memory_text)

### 2. Contextual Recall (The Retrieval Loop)
Mechanism: When an employee submits an IT query through the Streamlit UI, the application queries the Hindsight cloud database using the client.recall() method.

Execution:
search_results = hindsight_client.recall(bank_id=BANK_ID, query=prompt)
memory_context = str(search_results)

Transparency:
The Streamlit sidebar features a live "Raw Memory Data" expander, allowing judges and administrators to inspect the exact vector facts retrieved in real time.

### 3. Dynamic Prompt Augmentation & Agentic Action
Stateless vs. Stateful Toggle: A UI toggle allows users to switch Hindsight memory ON or OFF, demonstrating a clear before-and-after comparison.

Prompt Injection: When memory is active, the retrieved historical context is appended directly to the Groq system prompt (openai/gpt-oss-120b), forcing the model to bypass generic advice and output the exact verified script (e.g., PowerShell commands to disable IPv6 adapters).

---

## ⚡ Quick Start
1. Clone the repository: `git clone https://github.com/Akhilbayya297326/it-fleet-memory-agent.git`
2. Install dependencies: `pip install -r requirements.txt`
3. Add your API keys to a `.env` file (`HINDSIGHT_API_KEY` and `GROQ_API_KEY`).
4. Inject the historical enterprise memory: `python seed_data.py`
5. Launch the Command Center: `streamlit run app.py`

---
>>>>>>> 695b9861fc6a7f52a988d91f8ea0f9e8fa01c651
