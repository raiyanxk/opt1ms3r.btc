import json
from pathlib import Path
import requests

import os
from token_generation import tokens
from dotenv import load_dotenv

load_dotenv()

AUTH_INFOS = {
    "RAINCANE": os.getenv("RAINCANE"),
    "RAINALT": os.getenv("RAINALT"),
    "VINO": os.getenv("VINO"),
}

SPORTS = ["nhl", "nba", "mlb", "wnba", "golf"]
BASE_URL = "https://api.real.vg/userpasses/" 
URL_SUFFIX = "/passes"

def build_headers(native_token: str, request_token: str) -> dict[str, str]:
    """
    Build HTTP headers for API requests.
    
    Args:
        native_token (str): HMAC-signed native request token
        request_token (str): Hashids-encoded request token
    
    Returns:
        dict[str, str]: Headers dictionary for HTTP requests
    """
    return {
        "Host": "api.real.vg",
        "real-device-uuid": "59A885E7-109F-4F35-8321-0B452BABEBD4",
        "Accept": "application/json",
        "real-device-name": "iPhone17,1",
        "Accept-Language": "en-CA,en-US;q=0.9,en;q=0.8",
        "real-native-request-token": native_token,
        "real-request-token": request_token,
        "real-version": "31",
        "real-device-type": "ios",
        "Accept-Encoding": "gzip, deflate, br",
        "User-Agent": "real/1 CFNetwork/3860.100.1 Darwin/25.0.0",
        "Connection": "keep-alive",
        "Content-Type": "application/json"
    }

output_path = Path("players.json")
output_dir = Path("players")
output_dir.mkdir(exist_ok=True)

for user in AUTH_INFOS:
    print(f"Fetching players for {user}...")

    for sport in SPORTS:
        native_token, request_token = tokens()
        params = {
            "entityType": "player",
            "season": 2026 if sport != "nhl" else 2025,
            "sport": sport,
            "_": native_token.split(".")[0]
        }
        
        headers = build_headers(native_token, request_token)
        
        print(f"Fetching players for {sport}...")
        res = requests.get(f"{BASE_URL}{AUTH_INFOS[user].split('!')[0]}{URL_SUFFIX}", headers=headers, params=params)
        res.raise_for_status()
        
        with open(Path(f"players/{user}_{sport}.json"), "w", encoding="utf-8") as file:
            json.dump(res.json(), file, indent=2, ensure_ascii=False)
        
    print()

