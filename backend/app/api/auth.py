from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr
from typing import List
from uuid import UUID
import random

from app.dependencies import get_db
from app.models.user import User
from app.models.vark import VarkQuestion, VarkOption, UserVarkResponse
from app.models.assessment import AssessmentSession, UserResponse
from app.services.email_service import send_verification_email
from app.core.jwt import create_access_token
from datetime import datetime, timedelta

CODE_EXPIRY_MINUTES = 15

def is_code_expired(sent_at) -> bool:
    if not sent_at:
        return True
    return datetime.utcnow() - sent_at > timedelta(minutes=CODE_EXPIRY_MINUTES)

router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ── Helpers ───────────────────────────────────────────────────────────────────

def generate_verification_code() -> str:
    return str(random.randint(100000, 999999))

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


# ── Schemas ───────────────────────────────────────────────────────────────────

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


# ── Shared helper: build full user payload ────────────────────────────────────

def _build_user_payload(user: User, db: Session, token: str) -> dict:
    """
    Builds the user object the frontend stores in localStorage.
    Includes the JWT token, VARK result, and assessment history.
    """
    # VARK scores
    scores = {"visual": 0, "auditory": 0, "reading": 0}
    vark_counts = (
        db.query(VarkOption.vark_type, func.count(UserVarkResponse.id))
        .join(UserVarkResponse, UserVarkResponse.vark_option_id == VarkOption.id)
        .filter(UserVarkResponse.user_id == user.id)
        .group_by(VarkOption.vark_type)
        .all()
    )
    for vark_type, count in vark_counts:
        scores[vark_type] = count

    vark_result = None
    if user.learning_style:
        vark_result = {"learning_style": user.learning_style, "scores": scores}

    # Assessment history
    sessions = (
        db.query(AssessmentSession)
        .filter(AssessmentSession.user_id == user.id)
        .order_by(AssessmentSession.completed_at.desc())
        .limit(10)
        .all()
    )
    assessment_results = []
    for s in sessions:
        total = db.query(UserResponse).filter(UserResponse.session_id == s.id).count()
        percentage = round((s.score / total) * 100) if total else 0
        assessment_results.append({
            "session_id": str(s.id),
            "score": s.score,
            "total": total,
            "percentage": percentage,
            "level": s.level,
            "date": s.completed_at.isoformat() if s.completed_at else None,
        })

    return {
        "id": str(user.id),
        "name": user.name,
        "email": user.email,
        "learning_style": user.learning_style,
        "level": user.level,
        "token": token,                        # ← JWT token stored by frontend
        "varkResult": vark_result,
        "assessmentResults": assessment_results,
    }


# ── Routes ────────────────────────────────────────────────────────────────────

@router.post("/register")
def register(body: RegisterRequest, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == body.email.lower()).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    code = generate_verification_code()
    new_user = User(
        name=body.name.strip(),
        email=body.email.lower(),
        password_hash=hash_password(body.password),
        verification_code=code,
        verification_code_sent_at=datetime.utcnow(),
        is_verified=False,
          

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

    # In /verify route
    if not user.is_verified:
        if is_code_expired(user.verification_code_sent_at):
            raise HTTPException(status_code=400, detail="Verification code has expired, request a new one")
        if user.verification_code != body.code:
            raise HTTPException(status_code=400, detail="Invalid verification code")
        user.is_verified = True
        user.verification_code = None
        user.verification_code_sent_at = None  # ← clean up
        db.commit()

        

    # Issue token immediately on verification — user goes straight to dashboard
    token = create_access_token(str(user.id))
    return {
        "message": "Account verified successfully",
        "user": _build_user_payload(user, db, token),
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

    token = create_access_token(str(user.id))
    return {
        "message": "Login successful",
        "user": _build_user_payload(user, db, token),
    }


@router.post("/forgot")
def forgot_password(body: ForgotRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == body.email.lower()).first()
    if not user:
        raise HTTPException(status_code=404, detail="User doesn't have an account")

    code = generate_verification_code()
    user.verification_code = code
    user.verification_code_sent_at = datetime.utcnow()
    db.commit()

    send_verification_email(user.email, code)
    return {"message": "Reset code sent to your email"}


@router.post("/reset/verify")
def verify_reset_code(body: ResetVerifyRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == body.email.lower()).first()
    if not user:
        raise HTTPException(status_code=400, detail="Invalid code")

    if is_code_expired(user.verification_code_sent_at):
        raise HTTPException(status_code=400, detail="Reset code has expired, request a new one")

    if user.verification_code != body.code:
        raise HTTPException(status_code=400, detail="Invalid code")

    return {"message": "Code verified"}


@router.post("/reset/password")
def reset_password(body: ResetPasswordRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == body.email.lower()).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if is_code_expired(user.verification_code_sent_at):
        raise HTTPException(status_code=400, detail="Reset code has expired, request a new one")

    if user.verification_code != body.code:
        raise HTTPException(status_code=400, detail="Invalid code")

    user.password_hash = hash_password(body.new_password)
    user.verification_code = None
    user.verification_code_sent_at = None
    db.commit()
    return {"message": "Password reset successful"}


# ── VARK ──────────────────────────────────────────────────────────────────────

@router.get("/vark/questions")
def get_vark_questions(db: Session = Depends(get_db)):
    questions = db.query(VarkQuestion).all()
    result = []
    for q in questions:
        options = db.query(VarkOption).filter(VarkOption.question_id == q.id).all()
        result.append({
            "id": q.id,
            "question_text": q.question_text,
            "options": [{"id": o.id, "option_text": o.option_text} for o in options],
        })
    return {"questions": result}


@router.post("/vark/submit")
def submit_vark(body: VarkSubmitRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == body.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Clear previous responses
    db.query(UserVarkResponse).filter(UserVarkResponse.user_id == user.id).delete()

    scores = {"visual": 0, "auditory": 0, "reading": 0}

    for opt_id in body.option_ids:
        opt = db.query(VarkOption).filter(VarkOption.id == opt_id).first()
        if not opt or opt.vark_type == "kinesthetic":   # ← add this
            continue
        scores[opt.vark_type] += 1

    dominant = max(scores, key=scores.get)
    user.learning_style = dominant
    db.commit()

    return {"learning_style": dominant, "scores": scores}