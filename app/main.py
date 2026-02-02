from fastapi import FastAPI, Request, BackgroundTasks
from fastapi.responses import PlainTextResponse
from langchain_core.messages import HumanMessage
import logging

# Import the Brain
from app.brain import agent_app

app = FastAPI()

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("uvicorn")

@app.get("/")
def home():
    return {"status": "NutriAgent is Awake 🟢"}

@app.post("/whatsapp-webhook")
async def whatsapp_reply(request: Request):
    """
    The Ear & Eye: Listens for Text AND Images from WhatsApp.
    """
    form_data = await request.form()
    
    # 1. Get the User's Message
    user_message = form_data.get("Body", "").strip()
    sender = form_data.get("From", "Unknown")
    
    # 2. Get the Image (if any)
    # WhatsApp sends images as 'MediaUrl0'
    image_url = form_data.get("MediaUrl0")
    
    logger.info(f"[*] Incoming: '{user_message}' | Media: {1 if image_url else 0}")

    # 3. Construct the Message for the Brain
    # If there is an image, we bundle it with the text.
    if image_url:
        print(f"[*] Vision Detected: {image_url}")
        message_content = [
            {"type": "text", "text": user_message or "Analyze this food."},
            {"type": "image_url", "image_url": image_url}
        ]
    else:
        message_content = user_message

    # 4. Invoke the Agent (Background Task to avoid timeouts)
    # We use a background task so Twilio gets a 200 OK immediately
    # while the Brain thinks (Vision takes 2-3 seconds).
    
    config = {"configurable": {"thread_id": sender}}
    
    # We run the invoke synchronously in the background (FastAPI handles the thread)
    # Note: For production, we'd use a true async queue, but this works for a demo.
    try:
        agent_app.invoke(
            {"messages": [HumanMessage(content=message_content)]}, 
            config=config
        )
    except Exception as e:
        logger.error(f"Brain Error: {e}")

    return PlainTextResponse("OK")

@app.post("/trigger-agent")
def trigger_agent():
    """
    The Alarm Clock: Wakes up the agent every 30 mins.
    """
    # Hardcoded ID for now (Simulating single user)
    # In production, you'd loop through all active users in a database.
    user_id = "whatsapp:+919999999999"  # Replace with env var if needed
    
    config = {"configurable": {"thread_id": user_id}}
    
    # Send a "Heartbeat" message (Hidden from user, seen by Brain)
    # The Brain's 'monitor_node' will detect this and run logic.
    agent_app.invoke(
        {"messages": [HumanMessage(content="SCHEDULER_TRIGGER: Check status.")]}, 
        config=config
    )
    
    return {"status": "Agent Triggered"}