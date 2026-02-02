# Metabolic Health Coach | LangGraph & Biometric Orchestration 

NutriAgent is an autonomous "agentic" AI application that acts as a personalized health coach. It connects your real-world activity data (via Fitbit) with a generative AI brain (Google Gemini) to offer real-time dietary advice, calorie tracking, and meal planning.

Unlike standard chatbots, NutriAgent has a "nervous system"—it senses your actual physical stats and remembers what you eat.

##  Key Features (Working)

### 1. The "Brain" (Google Gemini 2.5)
* **Contextual Coaching:** Remembers your goals (e.g., "Bulking", "Weight Loss") and daily progress.
* **Adaptive Advice:** Suggests meals dynamically based on your *remaining* calories for the day.
* **Culturally Aware:** Designed to understand and recommend diverse cuisines (Indian & Global) without generic defaults.

### 2. Fitbit "Nervous System"
* **Live Calorie Tracking:** Automatically fetches "Calories Burned" from your Fitbit device every time you interact.
* **Sleep Monitoring:** Pulls last night's sleep duration to contextually adjust energy recommendations.
* **Token Management:** Self-healing authentication system that automatically refreshes Fitbit OAuth2 tokens (access & refresh) so the connection never breaks.

### 3. The "Stomach" (Persistent Food Logging)
* **Daily Food Diary:** Tracks every meal you log (e.g., "I ate 2 idlis").
* **Math Engine:** Automatically estimates calories for logged items and subtracts them from your daily goal.
* **Daily Reset:** Automatically wipes the log at midnight to start a fresh day.

### 4. Interface
* **Streamlit Chat UI:** A clean, chat-based interface to talk to the agent.
* **Mock WhatsApp Output:** Simulation of sending alerts/summaries to a messaging platform.

---

## 🛠️ Tech Stack

* **Brain:** LangChain & LangGraph (State management), Google Gemini 2.5 Flash (LLM).
* **Sensors:** Fitbit Web API (OAuth2).
* **Memory:** SQLite (Chat history & State), JSON (Token storage & Food logs).
* **Frontend:** Streamlit (Python-based UI).
* **Environment:** Python 3.14.

---

## 🚀 How to Run

### Prerequisites
1.  **Google API Key:** Enabled for Gemini 2.5 Flash.
2.  **Fitbit Developer App:** Registered at `dev.fitbit.com`.
3.  **Python 3.10+**

### Installation
1.  **Clone the repo:**
    ```bash
    git clone [https://github.com/yourusername/NutriAgent.git](https://github.com/yourusername/NutriAgent.git)
    cd NutriAgent
    ```

2.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Setup Credentials:**
    Create a `.env` file and add:
    ```ini
    GOOGLE_API_KEY="your_google_key"
    FITBIT_CLIENT_ID="your_fitbit_id"
    FITBIT_CLIENT_SECRET="your_fitbit_secret"
    ```

4.  **Authorize Fitbit (First Time Only):**
    Run the token generator to perform the initial handshake:
    ```bash
    python get_tokens.py
    ```
    *Follow the link, authorize, and paste the localhost redirect URL back into the terminal.*

5.  **Launch the Agent:**
    ```bash
    streamlit run streamlit_app.py
    ```

---

## 📝 Usage Guide

* **Start:** Type "Hi" to create your profile (Height/Weight/Goal).
* **Check Status:** Type `Status` to see a live dashboard of Goal vs. Eaten vs. Burned.
* **Log Food:** Type natural phrases like `I ate Chicken Biryani` or `Had a bowl of oatmeal`.
* **Get Suggestions:** Ask `What should I eat for dinner?` to get a recommendation based on your remaining calorie budget.

---

## ⚠️ Known Limitations
* **Vision/GPS:** Code references exist but are currently disabled/experimental in this build.
* **Single User:** Currently designed for a local single-user instance.

---

## 📜 License
MIT License. Built for educational purposes.
