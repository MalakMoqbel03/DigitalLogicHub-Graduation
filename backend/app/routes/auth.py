from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr
import random

from app.dependencies import get_db
from app import models
from app.services.email_service import send_verification_email

router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# =========================
# Helpers
# =========================
def generate_code() -> str:
    return str(random.randint(100000, 999999))


# =========================
# Schemas
# =========================
class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    password: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class VerifyRequest(BaseModel):
    email: EmailStr
    code: str


# =========================
# Routes
# =========================
@router.post("/register")
def register(body: RegisterRequest, db: Session = Depends(get_db)):
    exists = db.query(models.User).filter(models.User.email == body.email).first()
    if exists:
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed = pwd_context.hash(body.password)
    code = generate_code()

    user = models.User(
        name=body.name,
        email=body.email,
        password_hash=hashed,
        verification_code=code,
        is_verified=False
    )

    db.add(user)
    db.commit()

    send_verification_email(body.email, code)

    return {"message": "Verification code sent"}


@router.post("/verify")
def verify(body: VerifyRequest, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == body.email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.is_verified:
        return {"message": "Already verified"}

    if user.verification_code != body.code:
        raise HTTPException(status_code=400, detail="Invalid code")

    user.is_verified = True
    user.verification_code = None
    db.commit()

    return {"message": "Account verified"}


@router.post("/login")
def login(body: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == body.email).first()
    if not user:
        raise HTTPException(status_code=404, detail="Account not found")

    if not pwd_context.verify(body.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Incorrect password")

    if not user.is_verified:
        raise HTTPException(status_code=401, detail="Verify your email first")

    return {
        "message": "Login success",
        "user": {
            "id": str(user.id),
            "email": user.email,
            "name": user.name
        }
    }
