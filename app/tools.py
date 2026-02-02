import os
import requests
from dotenv import load_dotenv

load_dotenv()

def find_healthy_food(lat: float, lng: float):
    """
    Searches for RESTAURANTS (not furniture stores) nearby using Google Places API (New).
    """
    api_key = os.getenv("GOOGLE_API_KEY")
    url = "https://places.googleapis.com/v1/places:searchNearby"
    
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": api_key,
        # We only ask for the specific fields we need to save data/latency
        "X-Goog-FieldMask": "places.displayName,places.formattedAddress,places.googleMapsUri,places.types,places.rating"
    }
    
    payload = {
        "includedTypes": ["restaurant", "indian_restaurant", "vegetarian_restaurant"],
        "excludedTypes": ["furniture_store", "lodging"], # Explicitly block IKEA/Hotels if needed
        "maxResultCount": 3,
        "locationRestriction": {
            "circle": {
                "center": {
                    "latitude": lat,
                    "longitude": lng
                },
                "radius": 1000.0 # Look within 1 km (Tight radius for "Nearby")
            }
        },
        "rankPreference": "DISTANCE" # Sort by closest first
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        data = response.json()
        
        places = data.get("places", [])
        if not places:
            return "No restaurants found within 1km. Try sending a new location?"
            
        # Format the top result
        top_place = places[0]
        name = top_place.get("displayName", {}).get("text", "Unknown Place")
        maps_link = top_place.get("googleMapsUri", "No Link")
        rating = top_place.get("rating", "N/A")
        
        return f"{name} ({rating}⭐) - {maps_link}"
        
    except Exception as e:
        print(f"Error searching Google Maps: {e}")
        return "Food search failed (Check Console)."

def send_whatsapp(message: str):
    """
    Mock Sender for Streamlit Testing.
    Instead of calling Twilio, we just print.
    """
    if not message: return
    
    print(f"\n[📱 MOCK WHATSAPP] {message}\n")
    # """Sends a message via Twilio (Safe Mode)."""
    # if not message or message.strip() == "":
    #     return
        
    # # --- SAFETY CUT ---
    # # WhatsApp Limit is 1600. We cut at 1500 to be safe.
    # if len(message) > 1500:
    #     print(f"[!] Warning: Message too long ({len(message)} chars). Truncating.")
    #     message = message[:1500] + "...(message cut)"
    # # ------------------
    
    # from twilio.rest import Client
    
    # account_sid = os.getenv("TWILIO_ACCOUNT_SID")
    # auth_token = os.getenv("TWILIO_AUTH_TOKEN")
    # from_whatsapp = os.getenv("TWILIO_WHATSAPP_FROM") 
    # to_whatsapp = os.getenv("MY_PHONE_NUMBER")        
    
    # client = Client(account_sid, auth_token)
    
    # try:
    #     client.messages.create(
    #         body=message,
    #         from_=from_whatsapp,
    #         to=to_whatsapp
    #     )
    #     print(f"[*] WhatsApp Sent: {message[:30]}...")
    # except Exception as e:
    #     print(f"[!] Twilio Error: {e}")