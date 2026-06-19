"""
app/core/jwt.py
───────────────
JWT token creation and verification.
Uses the SECRET_KEY from .env — never hardcode this.

Note: this used to read from JWT_SECRET, which didn't match the variable
name main.py validates at startup (SECRET_KEY). Renamed to SECRET_KEY so
both checks agree and the app doesn't fail startup even when the secret
IS set, just under the other name.
"""
import os
from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import JWTError, jwt
from fastapi import HTTPException, status

# ── Config ────────────────────────────────────────────────────────────────────
_raw_secret = os.getenv("SECRET_KEY")
if not _raw_secret:
    raise RuntimeError(
        "SECRET_KEY environment variable is not set. "
        "Set it to a long random string before starting the server."
    )
SECRET_KEY = _raw_secret
ALGORITHM  = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7   # 7 days (comfortable for students)


# ── Create ────────────────────────────────────────────────────────────────────

def create_access_token(user_id: str) -> str:
    """
    Generate a signed JWT containing the user's ID.
    Expires in ACCESS_TOKEN_EXPIRE_MINUTES minutes.
    """
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": user_id,          # subject — user's UUID as a string
        "exp": expire,
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


# ── Verify ────────────────────────────────────────────────────────────────────

def decode_access_token(token: str) -> Optional[str]:
    """
    Decode and verify a JWT.
    Returns the user_id (sub) string on success.
    Raises HTTP 401 on any failure.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token. Please log in again.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        return user_id
    except JWTError:
        raise credentials_exception