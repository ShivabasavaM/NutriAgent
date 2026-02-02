import time
import requests
from datetime import datetime

# The "Trigger" URL
AGENT_URL = "http://127.0.0.1:8000/trigger-agent"

# Run every 30 minutes (1800 seconds)
# FOR TESTING: We will set this to 10 seconds so you can see it work NOW.
# scheduler.py
CHECK_INTERVAL = 1800  # 30 Minutes 

print(f"[*] Coach Scheduler Started. Poking agent every {CHECK_INTERVAL} seconds...")

while True:
    try:
        current_time = datetime.now().strftime('%H:%M')
        print(f"[*] ({current_time}) Poking Agent...")
        
        # This sends a "Wake Up" signal to the brain
        # The Brain will check Fitbit, check your Goal, and decide if it needs to text you.
        response = requests.post(AGENT_URL)
        
        print(f"    Agent Decision: {response.json().get('final_decision')}")
    except Exception as e:
        print(f"    Error: {e}")
        
    time.sleep(CHECK_INTERVAL)