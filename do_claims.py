import json
import os
from datetime import date
from pathlib import Path

import requests
from dotenv import load_dotenv

from token_generation import tokens

API_BASE="https://api.real.vg"
API_URL = f"{API_BASE}/cardhistoricalearnings"
DATE = date.today().isoformat()
CLAIMS_DIR = Path("claims")
MAX_CLAIMS_PER_SPORT = 2

load_dotenv()

AUTH_INFOS = {
    "RAINCANE": os.getenv("RAINCANE"),
    "RAINALT": os.getenv("RAINALT"),
    "VINO": os.getenv("VINO"),
}

def build_headers(auth_info: str, native_request_token: str, request_token: str) -> dict[str, str]:
    """
    Build HTTP headers for API requests.
    
    Args:
        auth_info (str): Authentication information
        native_request_token (str): HMAC-signed native request token
        request_token (str): Hashids-encoded request token
    
    Returns:
        dict[str, str]: Headers dictionary for HTTP requests
    """
    return {
        "Host": "api.real.vg",
        "real-device-uuid": "59A885E7-109F-4F35-8321-0B452BABEBD4",
        "Accept": "application/json",
        "real-native-request-token": native_request_token,
        "real-device-name": "iPhone17,1",
        "real-request-token": request_token,
        "real-version": "31",
        "real-device-type": "ios",
        "real-auth-info": auth_info,
        "Accept-Language": "en-CA,en-US;q=0.9,en;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "User-Agent": "real/1 CFNetwork/3860.100.1 Darwin/25.0.0",
        "Connection": "keep-alive",
        "Content-Type": "application/json",
    }


def claim_account(account_name: str, auth_info: str) -> None:
    """
    Process and submit card claims for a specific account.
    
    Reads the claims file for the given account, identifies claimable cards,
    and submits PUT requests to the API to claim them. Processes up to
    MAX_CLAIMS_PER_SPORT cards per sport.
    
    Args:
        account_name (str): Name of the account (e.g., 'RAINCANE')
        auth_info (str): Authentication credentials for the account
    
    Returns:
        None
    """
    claims_path = CLAIMS_DIR / f"{account_name}_claims_{DATE}.json"
    if not claims_path.exists():
        print(f"[{account_name}] Missing claims file: {claims_path}")
        return

    with open(claims_path, "r", encoding="utf-8") as file:
        response_data = json.load(file)

    sport_earnings = response_data.get("sportEarnings", [])
    if not sport_earnings:
        print(f"[{account_name}] No sport earnings in file: {claims_path}")
        return

    print(f"[{account_name}] Processing {len(sport_earnings)} sports from {claims_path}")

    for sport_entry in sport_earnings:
        sport_name = sport_entry.get("sport", "unknown")
        pass_earnings = sport_entry.get("passEarnings", [])
        claimable_cards = [
            pass_earning
            for pass_earning in pass_earnings
            if not pass_earning.get("isDisabled", False)
        ]

        if not claimable_cards:
            print(f"[{account_name}] {sport_name}: no claimable cards")
            continue
        
        claims_remaining = sport_entry.get("claimsRemaining", 0)
        num_claimable = min(len(claimable_cards), MAX_CLAIMS_PER_SPORT, claims_remaining)

        cards_to_claim = claimable_cards[:num_claimable]
        print(f"[{account_name}] {sport_name}: claiming {num_claimable} cards")

        for pass_earning in cards_to_claim:
            payload = {"userPassId": pass_earning["id"]}
            native_request_token, request_token = tokens()
            headers = build_headers(auth_info, native_request_token, request_token)
            response = requests.put(API_URL, headers=headers, json=payload)
            card_label = pass_earning.get("label", "unknown card")

            if response.status_code == 200:
                print(
                    f"  [{account_name}] claimed {card_label} "
                    f"userPassId={pass_earning['id']}"
                )
            else:
                try:
                    error_data = response.json()
                    error_message = error_data.get("message", response.text)
                except (json.JSONDecodeError, ValueError):
                    error_message = response.text
                
                print(f"[{account_name}] failed {card_label} userPassId={pass_earning['id']}")
                print(f"  Status code: {response.status_code}, Error: {error_message}")
        print()


def main() -> None:
    """
    Main entry point for the claims processing application.
    
    Iterates through all configured accounts and processes their claims.
    
    Returns:
        None
    """
    for account_name, auth_info in AUTH_INFOS.items():
        claim_account(account_name, auth_info)
        print()

if __name__ == "__main__":
    main()
