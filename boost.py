import json
import os
import random
from pathlib import Path

import requests
from dotenv import load_dotenv

from token_generation import tokens

load_dotenv()

AUTH_INFO = os.getenv("RAINCANE")
SPORT = "wnba"
PLAYER_FILE = Path("players") / f"RAINCANE_{SPORT}.json"
API_BASE_URL = "https://api.real.vg"
BOOST_KEYS = [1, 2, 3, 4, 5, 21]
BOOST_RARITY = 3

MAPPINGS = {
    1: "PTS",
    2: "AST",
    3: "REB",
    4: "STL",
    5: "BLK",
    21: "3PM",
}


def build_headers(auth_info: str, native_request_token: str, request_token: str) -> dict[str, str]:
  """
  Build HTTP headers for boost requests.

  Args:
    auth_info (str): Authentication information from the environment.
    native_request_token (str): HMAC-signed native request token.
    request_token (str): Hashids-encoded request token.

  Returns:
    dict[str, str]: Headers required for the REAL API request.
  """
  return {
    "Host": "api.real.vg",
    "real-device-uuid": "59A885E7-109F-4F35-8321-0B452BABEBD4",
    "Accept": "application/json",
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


def load_players(player_file: Path) -> list[dict[str, object]]:
  """
  Load player pass data from a JSON file.

  Args:
    player_file (Path): Path to the saved player JSON file.

  Returns:
    list[dict[str, object]]: The list of player pass records.
  """
  with open(player_file, "r", encoding="utf-8") as file:
    payload = json.load(file)

  return payload.get("passes", [])


def boost_player(player: dict[str, object], auth_info: str) -> tuple[bool, str]:
  """
  Apply a random stat boost to a single player card.

  Args:
    player (dict[str, object]): Player pass record from the saved JSON file.
    auth_info (str): Authentication information from the environment.

  Returns:
    tuple[bool, str]: Success flag and a message describing the result.
  """
  player_id = player.get("id")
  player_label = player.get("label", "unknown player")
  boost_key = random.choice(BOOST_KEYS)

  native_request_token, request_token = tokens()
  url = f"{API_BASE_URL}/userpassboostercards/{player_id}/rarity/{BOOST_RARITY}"
  headers = build_headers(auth_info, native_request_token, request_token)

  response = requests.put(url, headers=headers, data=json.dumps({"statBoostKey": str(boost_key)}))

  try:
    response_data = response.json()

    if response_data["success"]:
      return True, f"boosted {player_label} userPassId={player_id} boost={MAPPINGS[boost_key]}"
    else:
      error_message = response_data.get("message", "unknown error")
      return False, f"failed to boost {player_label} userPassId={player_id} error={error_message}"

  except (json.JSONDecodeError, ValueError):
    return False, f"failed to boost {player_label} userPassId={player_id} - invalid JSON response: {response.text}"



def main() -> None:
  """
  Load RAINCANE WNBA players and apply a random boost to each one.

  Returns:
    None
  """
  if not AUTH_INFO:
    print("Missing RAINCANE auth info in .env")
    return

  if not PLAYER_FILE.exists():
    print(f"Missing players file: {PLAYER_FILE}")
    return

  players = load_players(PLAYER_FILE)
  print(f"Loaded {len(players)} players from {PLAYER_FILE}")

  results = []
  for player in players:
    if player.get("boosterCardId"):
      boost_type = MAPPINGS[int(player["boosterCardInfo"]["statBoostKey"])]
      print(f"skipping {player.get('label', 'unknown player')} userPassId={player.get('id')} - already has booster={boost_type}")
      continue

    success, message = boost_player(player, AUTH_INFO)
    print(message)
    results.append(
      {
        "playerId": player.get("id"),
        "playerLabel": player.get("label"),
        "success": success,
        "message": message,
      }
    )



if __name__ == "__main__":
  main()
