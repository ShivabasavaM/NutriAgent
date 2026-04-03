from fastapi import FastAPI, Request, BackgroundTasks
from fastapi.responses import PlainTextResponse
from langchain_core.messages import HumanMessage
import logging
from app.brain import agent_app

app = FastAPI()

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
    
    user_message = form_data.get("Body", "").strip()
    sender = form_data.get("From", "Unknown")
    
    image_url = form_data.get("MediaUrl0")
    
    logger.info(f"[*] Incoming: '{user_message}' | Media: {1 if image_url else 0}")

    if image_url:
        print(f"[*] Vision Detected: {image_url}")
        message_content = [
            {"type": "text", "text": user_message or "Analyze this food."},
            {"type": "image_url", "image_url": image_url}
        ]
    else:
        message_content = user_message
    
    config = {"configurable": {"thread_id": sender}}
    
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

    user_id = "whatsapp:+919999999999" 
    
    config = {"configurable": {"thread_id": user_id}}
    
    agent_app.invoke(
        {"messages": [HumanMessage(content="SCHEDULER_TRIGGER: Check status.")]}, 
        config=config
    )
    
    return {"status": "Agent Triggered"}