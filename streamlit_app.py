import streamlit as st
import sqlite3
from app.brain import app_graph
from app import database

# Configure the page
st.set_page_config(page_title="NutriAgent MVP", page_icon="🤖", layout="centered")
st.title("🤖 NutriAgent")
st.caption("Your Autonomous Health Coach (Powered by LangGraph & Fitbit)")
st.markdown("---")

config = {"configurable": {"thread_id": "1"}}

# --- NEW: Dynamic Initial Greeting ---
def get_initial_greeting():
    """Checks the database to see if the user needs onboarding."""
    try:
        conn = sqlite3.connect(database.DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT daily_calorie_target FROM users WHERE id = 1")
        row = cursor.fetchone()
        conn.close()
        
        # If a goal exists
        if row and row[0]:
            return f"Welcome back! Your daily goal is {row[0]} kcal. What did you eat today, or would you like a status update?"
        # If no goal exists (Onboarding mode)
        else:
            return "Welcome to NutriAgent! I see we haven't set up your profile yet. Please tell me your current weight and your daily calorie goal to get started."
    except Exception:
        return "Welcome! Let's set up your profile. What is your weight and calorie goal?"

# Initialize the Streamlit UI chat history dynamically
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": get_initial_greeting()}
    ]

# Render previous messages in the UI
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Handle user input
if user_input := st.chat_input("Type your message here..."):
    
    # 1. Display user input
    st.chat_message("user").markdown(user_input)
    st.session_state.messages.append({"role": "user", "content": user_input})

    # 2. Call the LangGraph Agent
    with st.chat_message("assistant"):
        with st.spinner("Processing..."):
            final_response = ""
            
            # Stream the execution from our compiled LangGraph
            for event in app_graph.stream({"messages": [("user", user_input)]}, config):
                for value in event.values():
                    if "messages" in value:
                        last_message = value["messages"][-1]
                        
                        # Handle text extraction robustly
                        if last_message.type == "ai" and last_message.content:
                            if isinstance(last_message.content, str):
                                final_response = last_message.content
                            elif isinstance(last_message.content, list):
                                text_blocks = [
                                    block["text"] for block in last_message.content 
                                    if isinstance(block, dict) and "text" in block
                                ]
                                final_response = "\n".join(text_blocks)
            
            # Render the final AI answer
            st.markdown(final_response)
            
    # 3. Save the response to Streamlit's UI state
    st.session_state.messages.append({"role": "assistant", "content": final_response})