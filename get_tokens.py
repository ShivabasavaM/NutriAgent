import os
import json
import base64
import requests
import hashlib
import secrets
import time
from urllib.parse import urlencode
from dotenv import load_dotenv

load_dotenv()

CLIENT_ID = os.getenv("FITBIT_CLIENT_ID")
CLIENT_SECRET = os.getenv("FITBIT_CLIENT_SECRET")
REDIRECT_URI = "http://localhost:8080"
TOKEN_FILE = "fitbit_tokens.json"

def save_tokens(tokens):
    # Add an expiry timestamp (now + seconds)
    tokens["expires_at"] = time.time() + tokens["expires_in"]
    with open(TOKEN_FILE, "w") as f:
        json.dump(tokens, f, indent=4)
    print(f"\n💾 Saved fresh tokens to {TOKEN_FILE}")

def generate_tokens():
    if not CLIENT_ID or not CLIENT_SECRET:
        print("❌ Error: Missing CLIENT_ID/SECRET in .env")
        return

    # 1. PKCE Auth
    code_verifier = secrets.token_urlsafe(64)
    code_challenge = base64.urlsafe_b64encode(
        hashlib.sha256(code_verifier.encode()).digest()
    ).decode().rstrip("=")

    params = {
        "client_id": CLIENT_ID,
        "response_type": "code",
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
        "scope": "activity nutrition sleep profile heartrate",
        "redirect_uri": REDIRECT_URI
    }
    auth_url = f"https://www.fitbit.com/oauth2/authorize?{urlencode(params)}"

    print("\n🔗 CLICK THIS LINK TO AUTHORIZE:")
    print(auth_url)
    
    callback_url = input("\n📋 Paste the full localhost URL here:\n> ").strip()

    try:
        from urllib.parse import urlparse, parse_qs
        query = parse_qs(urlparse(callback_url).query)
        auth_code = query["code"][0]
    except:
        print("❌ Invalid URL.")
        return

    # 2. Exchange for Tokens
    token_url = "https://api.fitbit.com/oauth2/token"
    auth_header = base64.b64encode(f"{CLIENT_ID}:{CLIENT_SECRET}".encode()).decode()
    
    headers = {"Authorization": f"Basic {auth_header}", "Content-Type": "application/x-www-form-urlencoded"}
    data = {
        "client_id": CLIENT_ID, "grant_type": "authorization_code",
        "redirect_uri": REDIRECT_URI, "code": auth_code, "code_verifier": code_verifier
    }

    response = requests.post(token_url, headers=headers, data=data)
    if response.status_code == 200:
        save_tokens(response.json())
        print("✅ SUCCESS! You are ready to run the app.")
    else:
        print(f"❌ Failed: {response.text}")

if __name__ == "__main__":
    generate_tokens()