import json
import os
from datetime import datetime

PROFILE_FILE = "user_profile.json"

def load_profile():
    """Loads the profile and calculates 'Day X'."""
    if not os.path.exists(PROFILE_FILE): return None
    try:
        with open(PROFILE_FILE, "r") as f: 
            data = json.load(f)
            
        # CALCULATE CURRENT DAY
        if "start_date" in data:
            start = datetime.strptime(data["start_date"], "%Y-%m-%d")
            # Calculate difference in days (adding 1 so the first day is Day 1)
            day_count = (datetime.now() - start).days + 1
            data["current_day"] = day_count
        else:
            data["current_day"] = 1
            
        return data
    except: return None

def save_profile(data):
    """Saves the strategy with a timestamp."""
    # If this is a new profile, stamp the start date
    if "start_date" not in data:
        data["start_date"] = datetime.now().strftime("%Y-%m-%d")
        
    # Ensure status is set
    if "status" not in data:
        data["status"] = "ACTIVE"
        
    with open(PROFILE_FILE, "w") as f:
        json.dump(data, f, indent=4)
        
    return "✅ Profile & Strategy Updated."

def reset_profile():
    if os.path.exists(PROFILE_FILE): os.remove(PROFILE_FILE)