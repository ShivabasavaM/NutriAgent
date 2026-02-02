import os
import google.generativeai as genai
from dotenv import load_dotenv

# Load your API Key
load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")

if not api_key:
    print("❌ Error: GOOGLE_API_KEY not found in .env file.")
else:
    print(f"🔑 Key found: {api_key[:10]}...")
    genai.configure(api_key=api_key)

    print("\n📡 Connecting to Google to fetch YOUR available models...")
    print("-" * 40)
    
    try:
        count = 0
        for m in genai.list_models():
            # We only care about models that can generate text (chat)
            if 'generateContent' in m.supported_generation_methods:
                print(f"✅ {m.name}")
                count += 1
        
        if count == 0:
            print("⚠️ No chat models found. Your API key might have restriction.")
            
    except Exception as e:
        print(f"❌ Error: {e}")