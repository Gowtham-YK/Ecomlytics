"""
Cryptographic security primitives for Ecomlytics.
Includes PBKDF2-SHA256 password hashing with salt and constant-time comparison,
plus HMAC-SHA256 signed session token generation and verification.
"""

import base64
import hashlib
import hmac
import os
import secrets
import time
from typing import Optional

SECRET_KEY = os.getenv("SESSION_SECRET", "ecomlytics-dev-secret-key-must-be-long-and-random-32bytes")
ITERATIONS = 260_000
SALT_SIZE = 16
SESSION_MAX_AGE_SECONDS = 7 * 24 * 3600  # 7 days


def hash_password(password: str) -> str:
    """Hash a password using PBKDF2-HMAC-SHA256 with a cryptographically secure salt."""
    salt = secrets.token_bytes(SALT_SIZE)
    key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, ITERATIONS)
    # Format: pbkdf2_sha256$iterations$salt_b64$key_b64
    salt_b64 = base64.b64encode(salt).decode("ascii")
    key_b64 = base64.b64encode(key).decode("ascii")
    return f"pbkdf2_sha256${ITERATIONS}${salt_b64}${key_b64}"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a stored PBKDF2-HMAC-SHA256 hash."""
    try:
        parts = hashed_password.split("$")
        if len(parts) != 4 or parts[0] != "pbkdf2_sha256":
            return False
        iterations = int(parts[1])
        salt = base64.b64decode(parts[2].encode("ascii"))
        expected_key = base64.b64decode(parts[3].encode("ascii"))
        derived_key = hashlib.pbkdf2_hmac("sha256", plain_password.encode("utf-8"), salt, iterations)
        return hmac.compare_digest(derived_key, expected_key)
    except Exception:
        return False


def create_session_token(user_id: str) -> str:
    """Create a tamper-proof signed session token embedding user_id and expiration timestamp."""
    timestamp = int(time.time())
    payload = f"{user_id}.{timestamp}"
    signature = hmac.new(SECRET_KEY.encode("utf-8"), payload.encode("utf-8"), hashlib.sha256).hexdigest()
    raw_token = f"{payload}.{signature}"
    return base64.urlsafe_b64encode(raw_token.encode("utf-8")).decode("ascii")


def verify_session_token(token: str, max_age: int = SESSION_MAX_AGE_SECONDS) -> Optional[str]:
    """Verify a session token signature and check expiration. Returns user_id if valid, else None."""
    try:
        raw_token = base64.urlsafe_b64decode(token.encode("ascii")).decode("utf-8")
        parts = raw_token.split(".")
        if len(parts) != 3:
            return None
        user_id, timestamp_str, received_sig = parts
        timestamp = int(timestamp_str)
        
        # Verify expiration
        if time.time() - timestamp > max_age:
            return None
        
        # Verify HMAC signature
        payload = f"{user_id}.{timestamp_str}"
        expected_sig = hmac.new(SECRET_KEY.encode("utf-8"), payload.encode("utf-8"), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(received_sig, expected_sig):
            return None
        
        return user_id
    except Exception:
        return None
