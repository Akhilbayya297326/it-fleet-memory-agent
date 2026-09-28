# 🛡️ Fleet Command: Autonomous IT Memory Agent

**Fleet Command** is an autonomous enterprise IT support agent that leverages **Hindsight Memory** to store, recall, and apply hardware-specific historical resolutions. By bridging persistent vector memory with the speed of Groq LLMs, Fleet Command eliminates generic troubleshooting and reduces repetitive L1 support tickets.

---

## 🎯 The Problem & Solution

### The Enterprise Pain Point

Traditional enterprise IT helpdesks rely on stateless LLM chatbots or static runbooks. When an employee experiences a complex hardware collision (e.g., VPN drops on specific laptop models after security patches), stateless chatbots offer generic, multi-step advice that fails to account for corporate infrastructure history. This leads to prolonged employee downtime and redundant support escalation.

### The Fleet Command Solution
Fleet Command maintains a centralized **Fleet Memory Bank** powered by Hindsight. When senior IT administrators solve an edge-case bug, the resolution is injected directly into Hindsight's memory layer. When an employee asks for help, the agent dynamically recalls that exact historical context, transforming a generic language model into a context-aware internal technician capable of generating executable remediation scripts.

---

### 🛠️ Architecture & Tech Stack
* **Memory Layer:** Hindsight Cloud API (Persistent Vector Storage)
* **LLM Engine:** Groq API (`openai/gpt-oss-120b`)
* **Frontend UI:** Streamlit (Python)
* **Agentic Framework:** Custom function-parsing for local script execution simulation

---

### ⚡ Quick Start
1. Clone the repository: `git clone https://github.com/Akhilbayya297326/it-fleet-memory-agent.git`
2. Install dependencies: `pip install -r requirements.txt`
3. Add your API keys to a `.env` file (`HINDSIGHT_API_KEY` and `GROQ_API_KEY`).
4. Inject the historical enterprise memory: `python seed_data.py`
5. Launch the Command Center: `streamlit run app.py`

---

## 🧠 Deep Dive: How Hindsight Memory is Utilized

Hindsight memory accounts for the core engine of this agent. The integration is broken down into three lifecycle phases:

### 1. Ingestion & Retention (The Admin Loop)
* **Mechanism:** Using the `hindsight_client` SDK, historical IT tickets and admin-injected fixes are structured and pushed to a persistent cloud memory bank (`fleet-memory-bank`) via the `client.retain()` API.
* **Data Structure:** Each memory block explicitly tags the device target, operating system, reported issue, and verified resolution:
  ```python
  memory_text = f"Device Target: {ticket['device_target']} | Issue: {ticket['issue']} | Resolution: {ticket['resolution']}"
  client.retain(bank_id=BANK_ID, content=memory_text)
