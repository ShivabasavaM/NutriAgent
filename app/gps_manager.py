# app/gps_manager.py
from datetime import datetime

class GPSManager:
    def __init__(self):
        # Default starting location (can be anywhere, e.g., Hyderabad)
        self.current_location = {
            "lat": 17.3850, 
            "long": 78.4867,
            "address": "Unknown",
            "last_updated": None
        }

    def update_location(self, lat: float, long: float, address: str = "Unknown"):
        self.current_location = {
            "lat": lat,
            "long": long,
            "address": address,
            "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        print(f"[*] GPS Updated: {self.current_location}")

    def get_location(self):
        return self.current_location

# Singleton instance
gps = GPSManager()