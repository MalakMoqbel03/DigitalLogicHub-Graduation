from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr
import random
import uuid
from app.dependencies import get_db
from app.models.user import User
from app.models.vark import VarkQuestion, VarkOption, UserVarkResponse
from app.services.email_service import send_verification_email
from pydantic import BaseModel
from typing import List
from uuid import UUID
router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def generate_verification_code() -> str:
    return str(random.randint(100000, 999999))


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


# ===================== Schemas =====================

class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    password: str

class VerifyRequest(BaseModel):
    email: EmailStr
    code: str

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class ForgotRequest(BaseModel):
    email: EmailStr

class ResetVerifyRequest(BaseModel):
    email: EmailStr
    code: str

class ResetPasswordRequest(BaseModel):
    email: EmailStr
    code: str
    new_password: str
class VarkSubmitRequest(BaseModel):
    user_id: UUID
    option_ids: List[int]



# ===================== Auth Routes =====================

@router.post("/register")
def register(body: RegisterRequest, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.email == body.email.lower()).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    code = generate_verification_code()

    new_user = User(
        name=body.name.strip(),
        email=body.email.lower(),
        password_hash=hash_password(body.password),  # ✅ FIXED
        verification_code=code,
        is_verified=False
    )

    db.add(new_user)
    db.commit()

    send_verification_email(new_user.email, code)
    return {"message": "Verification code sent"}


@router.post("/verify")
def verify_email(body: VerifyRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == body.email.lower()).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.is_verified:
        # Return user so frontend can continue to dashboard if needed
        return {"message": "Already verified", "user": {"id": str(user.id), "name": user.name, "email": user.email}}

    if user.verification_code != body.code:
        raise HTTPException(status_code=400, detail="Invalid verification code")

    user.is_verified = True
    user.verification_code = None
    db.commit()

    return {
        "message": "Account verified successfully",
        "user": {"id": str(user.id), "name": user.name, "email": user.email}
    }


@router.post("/login")
def login(body: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == body.email.lower()).first()
    if not user:
        raise HTTPException(status_code=404, detail="User doesn't have an account")

    if not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Wrong password")

    if not user.is_verified:
        raise HTTPException(status_code=401, detail="Please verify your email before logging in")

    return {
        "message": "Login successful",
        "user": {"id": str(user.id), "name": user.name, "email": user.email,
                 "learning_style": user.learning_style, "level": user.level}
    }


@router.post("/forgot")
def forgot_password(body: ForgotRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == body.email.lower()).first()
    if not user:
        raise HTTPException(status_code=404, detail="User doesn't have an account")

    code = generate_verification_code()
    user.verification_code = code
    db.commit()

    send_verification_email(user.email, code)
    return {"message": "Reset code sent to your email"}


@router.post("/reset/verify")
def verify_reset_code(body: ResetVerifyRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == body.email.lower()).first()
    if not user or user.verification_code != body.code:
        raise HTTPException(status_code=400, detail="Invalid code")
    return {"message": "Code verified"}


@router.post("/reset/password")
def reset_password(body: ResetPasswordRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == body.email.lower()).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.verification_code != body.code:
        raise HTTPException(status_code=400, detail="Invalid code")

    user.password_hash = hash_password(body.new_password)
    user.verification_code = None
    db.commit()

    return {"message": "Password reset successful"}

@router.get("/vark/questions")
def get_vark_questions(db: Session = Depends(get_db)):
    questions = db.query(VarkQuestion).all()

    result = []
    for q in questions:
        options = db.query(VarkOption).filter(
            VarkOption.question_id == q.id
        ).all()

        result.append({
            "id": q.id,
            "question_text": q.question_text,
            "options": [
                {
                    "id": o.id,
                    "option_text": o.option_text
                }
                for o in options
            ]
        })

    return {"questions": result}


@router.post("/vark/submit")
def submit_vark(body: VarkSubmitRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == body.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Clear previous responses (optional but recommended)
    db.query(UserVarkResponse).filter(
        UserVarkResponse.user_id == user.id
    ).delete()

    # Count VARK types
    scores = {
        "visual": 0,
        "auditory": 0,
        "reading": 0,
        "kinesthetic": 0,
    }

    for opt_id in body.option_ids:
        opt = db.query(VarkOption).filter(VarkOption.id == opt_id).first()
        if not opt:
            continue

        scores[opt.vark_type] += 1
        db.add(
            UserVarkResponse(
                user_id=user.id,
                vark_option_id=opt.id
            )
        )

    # Determine dominant style
    dominant = max(scores, key=scores.get)

    # Save to user table
    user.learning_style = dominant
    db.commit()

    return {
        "learning_style": dominant,
        "scores": scores
    }
