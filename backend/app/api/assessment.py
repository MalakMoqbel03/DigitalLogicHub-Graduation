from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Dict, List
from uuid import UUID
from datetime import datetime

from app.dependencies import get_db
from app.models.user import User
from app.models.assessment import Question, Answer, AssessmentSession, UserResponse
from app.models.user_misconception import UserMisconception

router = APIRouter()


# ─────────────────────────────────────────────
# Schemas
# ─────────────────────────────────────────────

class SubmitAssessmentRequest(BaseModel):
    user_id: UUID
    answers: Dict[UUID, UUID]   # {question_id: answer_id}


# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────

def _record_misconception(db: Session, user_id: UUID, concept_tag: str) -> None:
    """
    Upsert a misconception record for the user.
    If the concept_tag already exists for this user, increment the count
    and update last_seen. Otherwise create a new row.
    """
    existing = db.query(UserMisconception).filter(
        UserMisconception.user_id == user_id,
        UserMisconception.concept_tag == concept_tag,
    ).first()

    if existing:
        existing.count += 1
        existing.last_seen = datetime.utcnow()
    else:
        db.add(UserMisconception(
            user_id=user_id,
            concept_tag=concept_tag,
            count=1,
            first_seen=datetime.utcnow(),
            last_seen=datetime.utcnow(),
        ))


# ─────────────────────────────────────────────
# GET 10 RANDOM QUESTIONS
# ─────────────────────────────────────────────

@router.get("/questions")
def get_assessment_questions(db: Session = Depends(get_db)):
    questions = (
        db.query(Question)
        .order_by(func.random())
        .limit(10)
        .all()
    )

    response = []
    for q in questions:
        answers = db.query(Answer).filter(Answer.question_id == q.id).all()
        response.append({
            "id": q.id,
            "question_text": q.question_text,
            "answers": [
                {"id": a.id, "answer_text": a.answer_text}
                for a in answers
            ],
        })

    return {"questions": response}


# ─────────────────────────────────────────────
# SUBMIT ASSESSMENT
# ─────────────────────────────────────────────

@router.post("/submit")
def submit_assessment(body: SubmitAssessmentRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == body.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if not body.answers:
        raise HTTPException(status_code=400, detail="No answers submitted")

    # Create assessment session
    session = AssessmentSession(
        user_id=user.id,
        started_at=datetime.utcnow(),
        completed_at=datetime.utcnow(),
        score=0,
        level=None,
    )
    db.add(session)
    db.commit()
    db.refresh(session)

    correct_count = 0
    total = len(body.answers)
    details = []
    triggered_misconceptions: List[str] = []

    for q_id, a_id in body.answers.items():
        question = db.query(Question).filter(Question.id == q_id).first()

        # Correct answer for this question
        correct_ans = db.query(Answer).filter(
            Answer.question_id == q_id,
            Answer.is_correct == True,
        ).first()

        # The answer the student actually chose
        selected = db.query(Answer).filter(
            Answer.id == a_id,
            Answer.question_id == q_id,
        ).first()

        is_correct = bool(selected and selected.is_correct)
        if is_correct:
            correct_count += 1

        # ── Misconception detection ──────────────────────────────────────────
        # If the student chose a wrong answer AND that answer has a
        # misconception_tag, record it against their profile.
        if not is_correct and selected and selected.misconception_tag:
            tag = selected.misconception_tag.strip()
            _record_misconception(db, user.id, tag)
            triggered_misconceptions.append(tag)

        # Save the raw response
        db.add(UserResponse(
            session_id=session.id,
            question_id=q_id,
            answer_id=a_id,
            is_correct=is_correct,
            answered_at=datetime.utcnow(),
        ))

        details.append({
            "question_id": str(q_id),
            "question_text": question.question_text if question else "",
            "selected_answer": selected.answer_text if selected else None,
            "correct_answer": correct_ans.answer_text if correct_ans else None,
            "is_correct": is_correct,
            # Surface misconception tag to frontend so it can show a hint
            "misconception_tag": (
                selected.misconception_tag
                if selected and not is_correct
                else None
            ),
        })

    # Determine level from score
    if correct_count <= 4:
        level = "beginner"
    elif correct_count <= 7:
        level = "intermediate"
    else:
        level = "advanced"

    session.score = correct_count
    session.level = level
    user.level = level
    db.commit()

    return {
        "score": correct_count,
        "total": total,
        "percentage": round((correct_count / total) * 100) if total else 0,
        "level": level,
        "details": details,
        # Summary of what misconceptions were detected this session
        "misconceptions_detected": list(set(triggered_misconceptions)),
    }


# ─────────────────────────────────────────────
# GET USER'S ACTIVE MISCONCEPTIONS
# ─────────────────────────────────────────────

@router.get("/misconceptions/{user_id}")
def get_user_misconceptions(user_id: UUID, db: Session = Depends(get_db)):
    """
    Returns the user's current misconception profile, ordered by count descending.
    Used by the recommender and the frontend dashboard.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    misconceptions = (
        db.query(UserMisconception)
        .filter(UserMisconception.user_id == user_id)
        .order_by(UserMisconception.count.desc())
        .all()
    )

    return {
        "user_id": str(user_id),
        "misconceptions": [
            {
                "concept_tag": m.concept_tag,
                "count": m.count,
                "first_seen": m.first_seen.isoformat() if m.first_seen else None,
                "last_seen": m.last_seen.isoformat() if m.last_seen else None,
            }
            for m in misconceptions
        ],
    }