import os
import operator
import sqlite3
import json
import re
from typing import TypedDict, Annotated, List

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.sqlite import SqliteSaver
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage, BaseMessage
from dotenv import load_dotenv

from app.fitbit_client import fitbit
from app.gps_manager import gps
from app.profile_manager import load_profile, save_profile, reset_profile
# ✅ IMPORT THE NEW STOMACH MANAGER
from app.food_manager import add_food, get_net_calories
from app.tools import send_whatsapp

load_dotenv()

class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], operator.add]
    calories_burned: int
    calories_eaten: int  # ✅ NEW: Tracks food intake
    active_minutes: int
    sleep_hours: float
    location: str

# --- HELPER FUNCTION (Vision) ---
def analyze_food_image(image_url: str):
    """Standalone function to analyze food images using Gemini Vision."""
    print(f"[*] Analyzing Food Image...")
    
    try:
        # ✅ VISION: Use Gemini 2.0 Flash (Best for Image Recognition)
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash", 
            temperature=0,
            google_api_key=os.getenv("GOOGLE_API_KEY")
        )
        
        # 🧠 CULTURALLY AWARE PROMPT (Fixes the "Oatmeal" hallucination)
        prompt = """
        You are an expert nutritionist with deep knowledge of Indian and Global Cuisines.
        
        Look at this food image carefully.
        1. IDENTIFY the specific dishes accurately.
           - If you see flatbread, check if it is Chapathi, Roti, Naan, or Paratha.
           - If you see white grain with yellow/brown stew, check if it is Rice with Dal/Sambhar/Curry.
           - ⛔ DO NOT GUESS "Oatmeal" unless you clearly see oats texture.
        
        2. ESTIMATE the calories roughly.
        
        3. OUTPUT strictly a JSON string:
           {"food": "Exact Name", "calories": 123}
        
        Do not add markdown formatting.
        """
        
        msg = HumanMessage(content=[
            {"type": "text", "text": prompt},
            {"type": "image_url", "image_url": image_url}
        ])
        
        response = llm.invoke([msg])
        print(f"[✅ Vision Result] {response.content}")
        return response.content
        
    except Exception as e:
        print(f"[❌ Vision Error] {e}")
        return f'{{"error": "Failed to analyze image"}}'

# --- AGENT NODES ---

def monitor_node(state: AgentState):
    """Collects real-world data (Burned, Eaten, SLEEP)."""
    print("\n[🔍 DEBUG] Monitor: Reading Sensors...")
    loc_data = gps.get_location()
    
    # 1. Fitbit Calories (Burned)
    burned = state.get("calories_burned", 0)
    try:
        new_burned = fitbit.get_calories_today()
        if new_burned is not None and new_burned > 0:
            burned = new_burned
            print(f"[✅ DEBUG] Fitbit Burned: {burned}")
    except Exception as e:
        print(f"[❌ DEBUG] Fitbit Calorie Error: {e}")

    # 2. ✅ Fitbit Sleep (New)
    sleep_hours = state.get("sleep_hours", 7.0) # Default backup
    try:
        sleep_mins = fitbit.get_sleep_today()
        if sleep_mins > 0:
            # Convert minutes to hours (e.g. 420 mins -> 7.0 hours)
            sleep_hours = round(sleep_mins / 60, 1)
            print(f"[✅ DEBUG] Fitbit Sleep: {sleep_hours} hrs")
        else:
            print("[⚠️ DEBUG] No sleep data found (using previous).")
    except Exception as e:
        print(f"[❌ DEBUG] Fitbit Sleep Error: {e}")

    # 3. Food Log (Eaten)
    eaten = get_net_calories()

    return {
        "calories_burned": burned, 
        "calories_eaten": eaten, 
        "active_minutes": state.get("active_minutes", 0), 
        "sleep_hours": sleep_hours, # ✅ Real data passed to Brain
        "location": loc_data.get("address", "Unknown")
    }

def reason_node(state: AgentState):
    """The Autonomous Brain."""
    # ✅ BRAIN: Use Gemini 2.5 Flash
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash", 
        temperature=0.4, # Raised slightly so it can be creative with food ideas
        google_api_key=os.getenv("GOOGLE_API_KEY"),
        safety_settings={
            "HARM_CATEGORY_DANGEROUS_CONTENT": "BLOCK_NONE",
            "HARM_CATEGORY_HARASSMENT": "BLOCK_NONE",
        }
    )
    
    history = state.get("messages", [])[-5:]
    user_profile = load_profile()
    
    # Get Vitals
    burned = state.get("calories_burned", 0)
    eaten = state.get("calories_eaten", 0)
    
    # --- SCENARIO A: ONBOARDING ---
    if not user_profile:
        system_prompt = """
        You are NutriAgent. User has NO profile.
        BEHAVIOR:
        1. If "Hi", ask for Height, Weight, Goal, Timeline.
        2. If Stats provided, output JSON:
        SAVE_STRATEGY: {
            "current_weight": 55, "target_weight": 60, "daily_target": 2400, 
            "macros": {"p": 150, "c": 280, "f": 75}, "strategy_note": "Surplus"
        }
        """

    # --- SCENARIO B: ACTIVE COACHING ---
    else:
        target = user_profile.get('daily_target', 2000)
        remaining = target - eaten
        day_count = user_profile.get('current_day', 1)
        
        system_prompt = f"""
        You are NutriAgent. 
        CURRENT DAY: Day {day_count} of the Plan.
        
        **Current Status:**
        • Goal: {target} kcal
        • Eaten: {eaten} kcal
        • Burned: {burned} kcal
        • Remaining: {remaining} kcal
        
        INSTRUCTIONS:
        1. **Tracking:** If user says "I ate X" (or sends image), output JSON: 
           `SAVE_FOOD: {{"food": "Exact Name", "calories": 500}}`
           
        2. **Status:** If asked "Status", report the Numbers above.
        
        3. **Suggestions (CRITICAL):** - If the user asks "What should I eat?" or is falling behind on calories:
           - Look at the 'REMAINING' calories.
           - Suggest a specific Indian or Global meal that fits that gap.
           - Example: "You have 800 kcal left. How about a Paneer Butter Masala with 2 Roti?"
           
        4. **Reset:** If "Reset", output `RESET_PROFILE`.
        
        ⛔ Keep responses helpful but under 0 words.
        """

    prompt_messages = [SystemMessage(content=system_prompt)] + history
    
    if not history:
        prompt_messages.append(HumanMessage(content="Check system status."))

    response = llm.invoke(prompt_messages)
    return {"messages": [response], "decision": response.content}

def act_node(state: AgentState):
    """Executes the Brain's commands."""
    if state.get("messages"):
        last_message = state["messages"][-1].content
    else:
        last_message = ""
        
    print(f"DEBUG: Brain -> {last_message[:50]}...")

    # 1. SAVE STRATEGY (Profile Creation)
    if "SAVE_STRATEGY" in last_message:
        try:
            json_match = re.search(r"\{.*\}", last_message, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group(0))
                if "SAVE_STRATEGY" in data: data = data["SAVE_STRATEGY"]
                save_profile(data)
                final_msg = f"📝 **Plan Created**\nTarget: {data.get('daily_target')} kcal."
            else:
                final_msg = "❌ Error parsing strategy."
        except Exception as e:
            final_msg = f"❌ Error: {e}"
        
        send_whatsapp(final_msg)
        return {"messages": [SystemMessage(content=final_msg)]}

    # 2. SAVE FOOD (The Stomach)
    elif "SAVE_FOOD" in last_message:
        try:
            json_match = re.search(r"\{.*\}", last_message, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group(0))
                if "SAVE_FOOD" in data: data = data["SAVE_FOOD"]
                
                # Add to Log
                new_total = add_food(data["food"], data["calories"])
                
                final_msg = f"🍽️ **Logged:** {data['food']} ({data['calories']} kcal).\nTotal Today: {new_total} kcal."
            else:
                final_msg = "❌ Error parsing food data."
        except Exception as e:
            final_msg = f"❌ Error saving food: {e}"

        send_whatsapp(final_msg)
        return {"messages": [SystemMessage(content=final_msg)]}

    # 3. RESET
    elif "RESET_PROFILE" in last_message:
        reset_profile()
        final_msg = "🔄 Profile Reset."
        send_whatsapp(final_msg)
        return {"messages": [SystemMessage(content=final_msg)]}

    # 4. STANDARD CHAT
    else:
        send_whatsapp(last_message)
        return {}

# --- GRAPH ---
workflow = StateGraph(AgentState)
workflow.add_node("monitor", monitor_node)
workflow.add_node("reason", reason_node)
workflow.add_node("act", act_node)
workflow.set_entry_point("monitor")
workflow.add_edge("monitor", "reason")
workflow.add_edge("reason", "act")
workflow.add_edge("act", END)

conn = sqlite3.connect("nutriagent_memory.sqlite", check_same_thread=False)
memory = SqliteSaver(conn)
agent_app = workflow.compile(checkpointer=memory)