import streamlit as st
from langchain_core.messages import HumanMessage
from app.brain import agent_app
import base64

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="NutriAgent Command Center",
    page_icon="🥗",
    layout="wide"  # Uses more screen space
)

# --- CUSTOM CSS FOR POLISH ---
# This hides the default 'Deploy' button and makes the chat look cleaner
st.markdown("""
<style>
    .stDeployButton {display:none;}
    .stChatMessage {padding: 1rem; border-radius: 10px; margin-bottom: 0.5rem;}
</style>
""", unsafe_allow_html=True)

# --- HEADER ---
col_logo, col_title = st.columns([0.1, 0.9])
with col_logo:
    st.markdown("## 🥗")
with col_title:
    st.title("NutriAgent Command Center")
    st.caption("🟢 Status: **Online** | 🧠 Mode: **Autonomous Agent**")

st.divider()

# --- SESSION STATE ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- SIDEBAR: THE TOOLKIT ---
with st.sidebar:
    st.header("🛠️ Agent Toolkit")
    
    # 1. Vision Module
    st.subheader("📷 Vision Input")
    uploaded_file = st.file_uploader(
        "Upload Food Photo", 
        type=["jpg", "png", "jpeg"], 
        help="The Agent will analyze calories automatically."
    )
    
    if uploaded_file:
        st.success("Image Loaded! Type a message to send it.")
        # Display preview in sidebar
        st.image(uploaded_file, caption="Ready to Analyze", use_container_width=True)

    st.divider()

    # 2. Scheduler Simulation
    st.subheader("⚙️ Simulation")
    if st.button("⏰ Fast Forward 30 Mins", type="primary"):
        with st.spinner("Waking up Agent..."):
            # Trigger the hidden scheduler message
            response = agent_app.invoke(
                {"messages": [HumanMessage(content="SCHEDULER_TRIGGER: Check status.")]}, 
                config={"configurable": {"thread_id": "streamlit_user"}}
            )
            ai_msg = response["messages"][-1].content
            
            if ai_msg:
                st.session_state.messages.append({"role": "assistant", "content": f"**[Scheduler Trigger]**\n{ai_msg}"})
                st.rerun()
            else:
                st.toast("Agent checked status: All clear (Silent).")

# --- CHAT HISTORY ---
# Create a container for chat history so it doesn't get covered by the input
chat_container = st.container()

with chat_container:
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"], avatar="🤖" if msg["role"] == "assistant" else "👤"):
            # Render Image if present
            if "image_data" in msg:
                st.image(msg["image_data"], width=300)
            
            # Render Text
            st.markdown(msg["content"])

# --- MAIN INPUT (Bottom) ---
user_input = st.chat_input("Type your message here...")

# --- LOGIC HANDLER ---
if user_input:
    # 1. Handle User Input
    content_payload = []
    
    # Add text
    content_payload.append({"type": "text", "text": user_input})
    
    # Add Image (if currently in sidebar)
    if uploaded_file:
        st.toast("Attaching Image to Vision Module...")
        # Note: In a real app, you'd upload this to S3/Cloudinary to get a URL.
        # For this local demo, we pass a context marker.
        content_payload.append({"type": "text", "text": "\n[IMAGE CONTEXT: User uploaded a food photo]"})
        
        # Add to UI history with the actual image file for display
        st.session_state.messages.append({
            "role": "user", 
            "content": user_input, 
            "image_data": uploaded_file
        })
    else:
        # Text only history
        st.session_state.messages.append({"role": "user", "content": user_input})

    # 2. Run the Brain
    with st.chat_message("assistant", avatar="🤖"):
        with st.spinner("Thinking..."):
            # Invoke Agent
            response = agent_app.invoke(
                {"messages": [HumanMessage(content=content_payload)]}, 
                config={"configurable": {"thread_id": "streamlit_user"}}
            )
            ai_response = response["messages"][-1].content
            
            st.markdown(ai_response)
    
    # 3. Save Assistant Response to History
    st.session_state.messages.append({"role": "assistant", "content": ai_response})
    
    # Rerun to update the state properly
    st.rerun()