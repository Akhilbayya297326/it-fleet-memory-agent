# 🛡️ Fleet Command: Autonomous IT Memory Agent

**Fleet Command** is an autonomous enterprise IT support agent that utilizes **Hindsight Memory** to store and recall hardware-specific resolutions, eliminating generic troubleshooting and duplicate L1 support tickets.

### 🚀 The Problem & Solution
Standard LLMs are stateless and generic. When enterprise hardware breaks, employees receive textbook advice rather than company-specific resolutions, leading to prolonged downtime. 

Fleet Command solves this by maintaining a persistent "Fleet Memory Bank." The agent learns from senior IT admins and applies those precise fixes to employees experiencing identical hardware collisions. It goes beyond chat by generating autonomous execution scripts to resolve issues instantly.

### 🛠️ Architecture & Tech Stack
* **Memory Layer:** Hindsight Cloud API (Persistent Vector Storage)
* **LLM Engine:** Groq API (`openai/gpt-oss-120b`)
* **Frontend UI:** Streamlit (Python)
* **Agentic Framework:** Custom function-parsing for local script execution simulation

### ⚡ Quick Start
1. Clone the repository: `git clone https://github.com/Akhilbayya297326/it-fleet-memory-agent.git`
2. Install dependencies: `pip install -r requirements.txt`
3. Add your API keys to a `.env` file (`HINDSIGHT_API_KEY` and `GROQ_API_KEY`).
4. Inject the historical enterprise memory: `python seed_data.py`
5. Launch the Command Center: `streamlit run app.py`
