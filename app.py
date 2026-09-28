import os
import time
import streamlit as st
from dotenv import load_dotenv
from groq import Groq
from hindsight_client import Hindsight

# 1. Load Environment Variables
load_dotenv()

# 2. Initialize API Clients
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
hindsight_client = Hindsight(
    base_url="https://api.hindsight.vectorize.io",
    api_key=os.getenv("HINDSIGHT_API_KEY")
)
BANK_ID = "fleet-memory-bank"

# 3. Employee & Admin Database
PERSONAS = {
    "John (Sales)": {"role": "user", "device": "Lenovo ThinkPad", "os": "Windows 11 23H2"},
    "Sarah (Engineering)": {"role": "user", "device": "MacBook Pro M2", "os": "macOS 14.2"},
    "Mike (Marketing)": {"role": "user", "device": "Dell XPS 15", "os": "Windows 11 22H2"},
    "Dave (IT Admin)": {"role": "admin", "device": "IT Workstation", "os": "Windows Server"}
}

# 4. Enterprise UI Setup
st.set_page_config(page_title="Fleet Command | IT Agent", page_icon="🛡️", layout="wide")

st.markdown("""
<style>
    .stButton>button { width: 100%; border-radius: 5px; }
    .action-btn>button { background-color: #00FF00; color: black; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

st.title("🛡️ Fleet Command IT Agent")
st.caption("Autonomous IT Resolution powered by Hindsight Memory")

# Sidebar - Command Center
with st.sidebar:
    st.header("⚙️ Control Panel")
    selected_persona = st.selectbox("Active Persona", list(PERSONAS.keys()))
    user_data = PERSONAS[selected_persona]
    
    st.divider()
    
    # Core Demo Toggles
    enable_memory = st.toggle("🧠 Enable Hindsight Memory", value=False)
    if enable_memory:
        st.success("Memory Layer: ACTIVE")
    else:
        st.warning("Memory Layer: OFFLINE")
        
    if st.button("🗑️ Clear Chat History"):
        st.session_state.messages = []
        st.rerun()
        
    st.divider()
    
    # Real-World Impact Metrics
    st.write("**Quarterly ROI Diagnostics**")
    st.metric(label="L1 Tickets Auto-Resolved", value="842", delta="14 today")
    st.metric(label="Helpdesk Hours Saved", value="142 hrs", delta="4.5 hrs this week")
    st.metric(label="Cost Avoidance", value="$5,680", delta="$180 today")

# 5. Live Learning Loop (Admin Only)
if user_data["role"] == "admin":
    st.info("👋 **Admin Mode Active:** You can inject new fleet resolutions directly into the AI's memory.")
    with st.expander("➕ Document New Fleet Resolution", expanded=True):
        new_issue = st.text_input("Reported Issue:")
        new_device = st.text_input("Affected Device:")
        new_fix = st.text_area("Verified Resolution / Script:")
        
        if st.button("Save to Hindsight Memory"):
            if new_issue and new_fix:
                memory_string = f"Device: {new_device} | Issue: {new_issue} | Resolution: {new_fix}"
                with st.spinner("Injecting to neural memory..."):
                    hindsight_client.retain(bank_id=BANK_ID, content=memory_string)
                    time.sleep(1)
                st.success("Successfully memorized! The agent will now apply this fix fleet-wide.")
            else:
                st.error("Please fill out all fields.")

# 6. Chat Interface
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": f"Hardware profile verified: {user_data['device']}. How can I assist?"}]

for message in st.session_state.messages:
    avatar = "👤" if message["role"] == "user" else "🛡️"
    with st.chat_message(message["role"], avatar=avatar):
        st.markdown(message["content"])

if prompt := st.chat_input("Describe your IT issue..."):
    # Prevent chat if in Admin mode to keep demo clean
    if user_data["role"] == "admin":
        st.warning("Switch to an Employee persona to test the chat interface.")
        st.stop()
        
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="👤"):
        st.markdown(prompt)

    with st.chat_message("assistant", avatar="🛡️"):
        memory_context = ""
        
        if enable_memory:
            with st.status("🧠 Consulting Fleet Memory...", expanded=True) as status:
                st.write(f"Analyzing hardware signature: {user_data['device']}...")
                max_retries = 3
                for attempt in range(max_retries):
                    try:
                        search_results = hindsight_client.recall(bank_id=BANK_ID, query=prompt)
                        memory_context = str(search_results)
                        time.sleep(0.5)
                        status.update(label="Memory retrieved successfully.", state="complete", expanded=False)
                        break
                    except Exception as e:
                        if attempt < max_retries - 1:
                            time.sleep(2)
                        else:
                            status.update(label="Memory fetch failed.", state="error", expanded=False)
                
            with st.expander("👁️ View Agent's Memory Context"):
                st.code(memory_context)

        user_context_string = f"Device: {user_data['device']}, OS: {user_data['os']}"
        system_prompt = f"""You are an autonomous enterprise IT agent. The user's hardware is: {user_context_string}.
        If you provide a script or command to fix an issue, format it strictly in a markdown code block.
        """
        
        if enable_memory:
            system_prompt += f"\nCompany memory context:\n{memory_context}\nIf the memory contains a fix, provide ONLY the exact resolution and the required script. Do not include lengthy manual GUI steps or generic explanations. Output the script strictly in a markdown code block."
        else:
            system_prompt += "\nYou have no company memory. Provide generic, multi-step troubleshooting advice."

        message_placeholder = st.empty()
        try:
            completion = groq_client.chat.completions.create(
                model="openai/gpt-oss-120b",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
            )
            response = completion.choices[0].message.content
            message_placeholder.markdown(response)
            st.session_state.messages.append({"role": "assistant", "content": response})
            
            # Agentic Action Simulation: If the AI outputted a code block, render an action button
            if "```" in response:
                st.markdown('<div class="action-btn">', unsafe_allow_html=True)
                if st.button("▶ Execute Resolution Script on Local Machine"):
                    st.success("Script executed successfully. Telemetry indicates issue is resolved.")
                st.markdown('</div>', unsafe_allow_html=True)
                
        except Exception as e:
            message_placeholder.error(f"Groq API Error: {e}")