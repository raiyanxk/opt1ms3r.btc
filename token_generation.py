import base64
import hashlib
import hmac
import time
import uuid

from hashids import Hashids

HMAC_KEY_HEX = "ca9f58d003fa83dbe27dd104cc1cd0cd52613bd2ed323c381db73826ba336798"
HASHIDS_SALT = "hixcv4lkn"
HASHIDS_MIN_LENGTH = 16

def tokens() -> tuple[str, str]:
    """
    Generate authentication tokens for API requests.
    
    Creates a native request token using HMAC-SHA256 signature and a request token
    using Hashids encoding. Both tokens are based on the current timestamp and a 
    randomly generated nonce.
    
    Returns:
        tuple[str, str]: A tuple containing:
            - native_request_token (str): HMAC-signed token in format "timestamp.nonce.signature"
            - request_token (str): Hashids-encoded timestamp
    """
    timestamp_ms = int(time.time() * 1000)
    nonce = uuid.uuid4().hex[:8]
    message = f"{timestamp_ms}.{nonce}"

    digest = hmac.new(
        bytes.fromhex(HMAC_KEY_HEX),
        message.encode(),
        hashlib.sha256,
    ).digest()
    signature = base64.b64encode(digest[:16]).decode()

    native_request_token = f"{message}.{signature}"
    request_token = Hashids(HASHIDS_SALT, HASHIDS_MIN_LENGTH).encode(timestamp_ms)

    return native_request_token, request_token

if __name__ == "__main__":
    print(tokens())