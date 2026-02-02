import os
import google.generativeai as genai
from dotenv import load_dotenv

# Load your API key
load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")

if not api_key:
    print("Error: GOOGLE_API_KEY not found in .env")
else:
    genai.configure(api_key=api_key)
    print(f"[*] Checking available models for Key ending in ...{api_key[-4:]}")
    
    try:
        print("\n--- AVAILABLE MODELS ---")
        found_any = False
        for m in genai.list_models():
            # We only care about models that can generate text
            if 'generateContent' in m.supported_generation_methods:
                print(f"- {m.name}")
                found_any = True
        
        if not found_any:
            print("No models found! This suggests an issue with the API Key scope.")
            
    except Exception as e:
        print(f"Error connecting to Google: {e}")