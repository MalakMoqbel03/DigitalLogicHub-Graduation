from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Dict
from uuid import UUID
from datetime import datetime

from app.dependencies import get_db
from app.models.user import User

# If your models are in different paths, adjust imports
from app.models.assessment import Question, Answer, AssessmentSession, UserResponse

router = APIRouter()


# =========================
# Schemas
# =========================
class SubmitAssessmentRequest(BaseModel):
    user_id: UUID
    answers: Dict[UUID, UUID]  # {question_id: answer_id}


# =========================
# GET 10 QUESTIONS (NO is_correct exposed)
# =========================

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
        answers = (
            db.query(Answer)
            .filter(Answer.question_id == q.id)
            .all()
        )

        response.append({
            "id": q.id,
            "question_text": q.question_text,
            "answers": [
                {
                    "id": a.id,
                    "answer_text": a.answer_text
                }
                for a in answers
            ]
        })

    return {"questions": response}

# =========================
# SUBMIT ASSESSMENT
# =========================
@router.post("/submit")
def submit_assessment(body: SubmitAssessmentRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == body.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if not body.answers or len(body.answers) == 0:
        raise HTTPException(status_code=400, detail="No answers submitted")

    # Create session
    session = AssessmentSession(
        user_id=user.id,
        started_at=datetime.utcnow(),
        completed_at=datetime.utcnow(),
        score=0,
        level=None
    )
    db.add(session)
    db.commit()
    db.refresh(session)

    correct_count = 0
    total = len(body.answers)
    details = []

    for q_id, a_id in body.answers.items():
        q = db.query(Question).filter(Question.id == q_id).first()

        # Get correct answer text
        correct_ans = db.query(Answer).filter(
            Answer.question_id == q_id,
            Answer.is_correct == True
        ).first()

        correct_text = correct_ans.answer_text if correct_ans else None

        # Get selected answer (must belong to that question)
        selected = db.query(Answer).filter(
            Answer.id == a_id,
            Answer.question_id == q_id
        ).first()

        selected_text = selected.answer_text if selected else None
        is_correct = bool(selected.is_correct) if selected else False

        if is_correct:
            correct_count += 1

        # Save response
        db.add(UserResponse(
            session_id=session.id,
            question_id=q_id,
            answer_id=a_id,
            is_correct=is_correct,
            answered_at=datetime.utcnow()
        ))

        details.append({
            "question_id": str(q_id),
            "question_text": q.question_text if q else "",
            "selected_answer": selected_text,
            "correct_answer": correct_text,
            "is_correct": is_correct
        })

  

    # Decide level (simple thresholds)
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
        "details": details
    }
