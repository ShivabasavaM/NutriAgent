import json
import os
from datetime import datetime

LOG_FILE = "daily_log.json"

def get_today_log():
    """Loads today's food log. Resets if the date has changed."""
    today_str = datetime.now().strftime("%Y-%m-%d")
    
    # 1. Load existing data
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r") as f:
            data = json.load(f)
    else:
        data = {"date": today_str, "foods": [], "total_calories": 0}

    # 2. Check if it's a new day
    if data.get("date") != today_str:
        data = {"date": today_str, "foods": [], "total_calories": 0}
        save_log(data)

    return data

def save_log(data):
    with open(LOG_FILE, "w") as f:
        json.dump(data, f, indent=4)

def add_food(food_name, calories):
    """Adds a meal to the stomach."""
    data = get_today_log()
    
    entry = {
        "time": datetime.now().strftime("%H:%M"),
        "food": food_name,
        "calories": int(calories)
    }
    
    data["foods"].append(entry)
    data["total_calories"] += int(calories)
    
    save_log(data)
    return data["total_calories"]

def get_net_calories():
    """Returns total eaten today."""
    data = get_today_log()
    return data["total_calories"]