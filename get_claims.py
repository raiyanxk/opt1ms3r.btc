from datetime import date
import json
import os
import requests
from pathlib import Path
from dotenv import load_dotenv

from token_generation import tokens

load_dotenv()

DATE = date.today().isoformat()
API_BASE="https://api.real.vg"
API_URL = f"{API_BASE}/cardhistoricalearnings"

AUTH_INFOS = {
    "RAINCANE": os.getenv("RAINCANE"),
    "RAINALT": os.getenv("RAINALT"),
    "VINO": os.getenv("VINO"),
}

def build_headers(token: str, hashid: str, auth_info: str) -> dict[str, str]:
    """
    Build HTTP headers for API requests.
    
    Args:
        token (str): HMAC-signed native request token
        hashid (str): Hashids-encoded request token
        auth_info (str): Authentication information
    
    Returns:
        dict[str, str]: Headers dictionary for HTTP requests
    """
    return {
        "Host": "api.real.vg",
        "real-device-uuid": "59A885E7-109F-4F35-8321-0B452BABEBD4",
        "Accept": "application/json",
        "real-native-request-token": token,
        "real-device-name": "iPhone17,1",
        "real-request-token": hashid,
        "real-version": "31",
        "real-device-type": "ios",
        "real-auth-info": auth_info,
        "Accept-Language": "en-CA,en-US;q=0.9,en;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "User-Agent": "real/1 CFNetwork/3860.100.1 Darwin/25.0.0",
        "Connection": "keep-alive",
        "Content-Type": "application/json"
    }

def fetch_account_claims(account_name: str, auth_info: str, output_dir: Path) -> None:
    """
    Fetch and save historical earnings claims for a single account.
    
    Generates authentication tokens, makes an API request to fetch historical
    earnings data, and saves the response as a JSON file.
    
    Args:
        account_name (str): Name of the account (e.g., 'RAINCANE')
        auth_info (str): Authentication credentials for the account
        output_dir (Path): Directory path where claims JSON file will be saved
    
    Returns:
        None
    """
    token, hashid = tokens()
    params = {
        "day": DATE,
        "_": token.split(".")[0],
    }
    output_path = output_dir / f"{account_name}_claims_{DATE}.json"
    
    headers = build_headers(token, hashid, auth_info)
    response = requests.get(API_URL, headers=headers, params=params)
    
    if response.status_code != 200:
        print(f"{account_name} Error: {response.status_code} - {response.text}")
        return
    
    with open(output_path, "w", encoding="utf-8") as file:
        json.dump(response.json(), file, indent=2, ensure_ascii=False)
    
    print(f"{account_name} claims data saved to {output_path}")

def main() -> None:
    """
    Fetch historical earnings claims data from the API for all accounts.
    
    Iterates through all configured accounts and fetches their historical
    earnings data from the API, saving the results to JSON files.
    
    Returns:
        None
    """
    output_dir = Path("claims")
    output_dir.mkdir(exist_ok=True)

    for account_name, auth_info in AUTH_INFOS.items():
        if not auth_info:
            print(f"Skipping {account_name}: missing .env value")
            continue
        
        fetch_account_claims(account_name, auth_info, output_dir)

if __name__ == "__main__":
    main()