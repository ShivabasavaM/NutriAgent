import sqlite3
from typing import Annotated
from typing_extensions import TypedDict
from dotenv import load_dotenv

from langgraph.graph import StateGraph, START
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.sqlite import SqliteSaver
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage
from langchain_core.tools import tool

from app.fitbit_client import FitbitClient
from app import database

load_dotenv()

fitbit = FitbitClient()

@tool
def reset_profile():
    """Wipes the user's profile and food history clean. Use when they want to change goals or start over."""
    conn = sqlite3.connect(database.DB_PATH)
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET weight = NULL, daily_calorie_target = NULL WHERE id = 1")
    cursor.execute("DELETE FROM daily_logs WHERE user_id = 1") # Wipe food history
    conn.commit()
    conn.close()
    return "Profile and history successfully reset. Ready for onboarding."

@tool
def get_historical_summary(days: int):
    """Fetches the average daily calories the user has eaten over the last X days."""
    conn = sqlite3.connect(database.DB_PATH)
    cursor = conn.cursor()
    cursor.execute(f'''
        SELECT AVG(daily_total) FROM (
            SELECT SUM(calories_in) as daily_total
            FROM daily_logs
            WHERE user_id = 1 AND date >= date('now', '-{days} days')
            GROUP BY date
        )
    ''')
    row = cursor.fetchone()
    conn.close()
    
    avg_eaten = round(row[0]) if row and row[0] else 0
    return f"Data context: Over the last {days} days, the user ate an average of {avg_eaten} kcal per day."

@tool
def get_health_status():
    """Fetches user's daily calorie goal, logged food, and Fitbit calories burned."""
    conn = sqlite3.connect(database.DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS daily_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT, user_id INTEGER, food_name TEXT, calories_in INTEGER
        )
    ''')
    cursor.execute("SELECT daily_calorie_target FROM users WHERE id = 1")
    row = cursor.fetchone()
    target = row[0] if row and row[0] else 2000
    
    cursor.execute("SELECT IFNULL(SUM(calories_in), 0) FROM daily_logs WHERE user_id = 1 AND date = date('now', 'localtime')")
    eaten = cursor.fetchone()[0]
    conn.close()

    burned = fitbit.get_calories_today()
    return f"Goal: {target} kcal. Eaten: {eaten} kcal. Burned (Fitbit): {burned} kcal."

@tool
def log_food(food_name: str, calories: int):
    """Logs food eaten by the user."""
    conn = sqlite3.connect(database.DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS daily_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT, user_id INTEGER, food_name TEXT, calories_in INTEGER
        )
    ''')
    cursor.execute("INSERT INTO daily_logs (date, user_id, food_name, calories_in) VALUES (date('now', 'localtime'), 1, ?, ?)", (food_name, calories))
    conn.commit()
    conn.close()
    return f"Successfully logged {food_name} ({calories} kcal)."

@tool
def update_profile(weight: float, target_calories: int):
    """Updates the user's weight and daily calorie target."""
    conn = sqlite3.connect(database.DB_PATH)
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET weight = ?, daily_calorie_target = ? WHERE id = 1", (weight, target_calories))
    conn.commit()
    conn.close()
    return f"Profile updated. Weight: {weight}kg, Goal: {target_calories} kcal."

class State(TypedDict):
    messages: Annotated[list, add_messages]

tools = [get_health_status, log_food, update_profile, reset_profile, get_historical_summary]
llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0)
llm_with_tools = llm.bind_tools(tools)

def chatbot(state: State):
    conn = sqlite3.connect(database.DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT daily_calorie_target FROM users WHERE id = 1")
    row = cursor.fetchone()
    conn.close()
    
    target = row[0] if row else None

    # STATE A: ONBOARDING MODE
    if not target:
        system_prompt = SystemMessage(content=(
            "You are NutriAgent's assistant. The user currently has NO active profile or goals.\n"
            "RULES:\n"
            "1. Your ultimate goal is to save the user's current weight, height and daily calorie target.\n"
            "2. If the user knows their calorie target, great. If they DON'T know it, ask for their height, current weight, target weight, and timeline.\n"
            "3. If they provide those stats, CALCULATE their required daily calorie target yourself using standard BMR/TDEE formulas to meet their timeline goal.\n"
            "4. Briefly explain your math to the user (e.g., 'To gain 5kg in 3 months, you need a surplus of X calories...').\n"
            "5. Immediately use the `update_profile` tool to save their weight, height and the calculated calorie target.\n"
            "6. DO NOT log food or check Fitbit until the profile is saved."
        ))
    
    # STATE B: ACTIVE COACHING MODE
    else:
        system_prompt = SystemMessage(content=(
            f"You are NutriAgent, an autonomous health coach. The user's active goal is {target} kcal/day.\n"
            "RULES:\n"
            "1. MEAL PLANNING: If the user asks for a diet plan or what to eat, SUGGEST specific, tasty meals (Indian or Global) that fit their daily calorie goal. Do NOT tell them to see a doctor for a basic meal plan.\n"
            "2. STRICT LOGGING RULE: DO NOT use the `log_food` tool when you are just suggesting or planning meals.\n"
            "3. TRACKING FOOD: ONLY use the `log_food` tool when the user explicitly confirms they ACTUALLY ATE the food (e.g., 'I had oats for breakfast', 'I ate the lunch you suggested'). Estimate the calories yourself.\n"
            "4. STATUS: Use `get_health_status` to check their remaining calories for today.\n"
            "5. HISTORY: If they ask about past days or average performance, use `get_historical_summary`.\n"
            "6. RESET: If they want to start over, use `reset_profile`.\n"
            "Be encouraging, concise, and calculate remaining calories accurately: (Goal + Fitbit Burned) - Eaten."
        ))
    
    messages_to_pass = [system_prompt] + state["messages"]
    response = llm_with_tools.invoke(messages_to_pass)
    return {"messages": [response]}

graph_builder = StateGraph(State)
graph_builder.add_node("chatbot", chatbot)
graph_builder.add_node("tools", ToolNode(tools=tools))
graph_builder.add_edge(START, "chatbot")
graph_builder.add_conditional_edges("chatbot", tools_condition)
graph_builder.add_edge("tools", "chatbot")

conn = sqlite3.connect(database.DB_PATH, check_same_thread=False)
memory = SqliteSaver(conn)
app_graph = graph_builder.compile(checkpointer=memory)