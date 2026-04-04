"""
app/dependencies.py
───────────────────
FastAPI dependencies shared across all routers.
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.core.jwt import decode_access_token

# ── Database ──────────────────────────────────────────────────────────────────

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ── Auth ──────────────────────────────────────────────────────────────────────

bearer_scheme = HTTPBearer()


def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> str:
    """
    Extracts and validates the Bearer token from the Authorization header.
    Returns the user_id string.
    Raises HTTP 401 if token is missing, invalid, or expired.
    """
    return decode_access_token(credentials.credentials)


def get_current_user(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """
    Resolves the full User object from the token's user_id.
    Raises HTTP 401 if the user no longer exists in the database.
    """
    from app.models.user import User
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account not found.",
        )
    return user