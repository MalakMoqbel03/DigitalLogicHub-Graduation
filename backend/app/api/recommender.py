from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc, case
from uuid import UUID
from pydantic import BaseModel
from typing import Optional

try:
    from app.models.user_resource_feedback import UserResourceFeedback
except Exception as e:
    print("Failed importing UserResourceFeedback:", e)
    raise

from app.dependencies import get_db
from app.models.user import User
from app.models.learning_resource import LearningResource
from app.models.user_learning_resource import UserLearningResource

router = APIRouter()

# =========================
# Request Schema
# =========================
class FeedbackRequest(BaseModel):
    user_id: UUID
    resource_id: int
    rating: Optional[int] = None
    liked: Optional[bool] = None
    comment: Optional[str] = None


# =========================
# Helpers
# =========================
def normalize_style(style: str | None) -> str | None:
    if not style:
        return None
    s = style.strip().lower()

    if s in ["aural", "audio"]:
        return "auditory"

    if s in ["read/write", "read", "write"]:
        return "reading"

    return s


def normalize_level(level: str | None) -> str | None:
    if not level:
        return None
    return level.strip().lower()


def serialize_resource(r: LearningResource):
    return {
        "id": r.id,
        "title": r.title,
        "description": r.description,
        "topic": r.topic,
        "subtopic": r.subtopic,
        "resource_type": r.resource_type,
        "difficulty": r.difficulty,
        "vark_style": r.vark_style,
        "duration_minutes": r.duration_minutes,
        "is_short": r.is_short,
        "source": r.source,
        "external_url": r.external_url,
        "tags": r.tags,
    }


# =========================
# RECOMMENDATIONS (FIXED 🔥)
# =========================
@router.get("/recommendations/{user_id}")
def get_recommendations(
    user_id: UUID,
    limit: int = 20,
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    style = normalize_style(user.learning_style)
    level = normalize_level(user.level)

    if not style or not level:
        raise HTTPException(
            status_code=400,
            detail="User must complete VARK quiz and assessment first"
        )

    # =========================
    # Get used resources
    # =========================
    used_resource_ids = (
        db.query(UserLearningResource.learning_resource_id)
        .filter(UserLearningResource.user_id == user.id)
        .all()
    )
    used_resource_ids = [x[0] for x in used_resource_ids]

    # =========================
    # BASE QUERY (IMPORTANT FIX)
    # =========================
    q = db.query(LearningResource).filter(
        LearningResource.difficulty.ilike(level)
    )

    # exclude already used
    if used_resource_ids:
        q = q.filter(~LearningResource.id.in_(used_resource_ids))

    # =========================
    # SMART ORDERING (KEY FIX 🔥)
    # =========================
    style_priority = case(
        (LearningResource.vark_style.ilike(style), 1),
        else_=0
    )

    items = q.order_by(
        desc(style_priority),                         # match style FIRST
        desc(LearningResource.is_short),              # short content preferred
        LearningResource.duration_minutes.asc().nullslast(),
        LearningResource.id.asc()
    ).limit(limit).all()

    return {
        "user": {
            "id": str(user.id),
            "learning_style": user.learning_style,
            "level": user.level,
        },
        "count": len(items),
        "items": [serialize_resource(x) for x in items],
    }


# =========================
# TRACK USER INTERACTION
# =========================
@router.post("/track/{user_id}/{resource_id}")
def track_resource_interaction(
    user_id: UUID,
    resource_id: int,
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    resource = db.query(LearningResource).filter(LearningResource.id == resource_id).first()
    if not resource:
        raise HTTPException(status_code=404, detail="Resource not found")

    existing = db.query(UserLearningResource).filter(
        UserLearningResource.user_id == user.id,
        UserLearningResource.learning_resource_id == resource.id
    ).first()

    if existing:
        return {"message": "Already tracked"}

    row = UserLearningResource(
        user_id=user.id,
        learning_resource_id=resource.id
    )

    db.add(row)
    db.commit()

    return {"message": "Tracked successfully"}


# =========================
# FEEDBACK (WITH VALIDATION 🔥)
# =========================
@router.post("/feedback")
def submit_feedback(body: FeedbackRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == body.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    resource = db.query(LearningResource).filter(LearningResource.id == body.resource_id).first()
    if not resource:
        raise HTTPException(status_code=404, detail="Resource not found")

    # ⭐ VALIDATION
    if body.rating is not None and not (1 <= body.rating <= 5):
        raise HTTPException(status_code=400, detail="Rating must be between 1 and 5")

    existing = db.query(UserResourceFeedback).filter(
        UserResourceFeedback.user_id == body.user_id,
        UserResourceFeedback.learning_resource_id == body.resource_id
    ).first()

    if existing:
        existing.rating = body.rating
        existing.liked = body.liked
        existing.comment = body.comment
        db.commit()
        return {"message": "Feedback updated"}

    feedback = UserResourceFeedback(
        user_id=body.user_id,
        learning_resource_id=body.resource_id,
        rating=body.rating,
        liked=body.liked,
        comment=body.comment
    )

    db.add(feedback)
    db.commit()

    return {"message": "Feedback saved"}


# =========================
# GET FEEDBACK
# =========================
@router.get("/feedback/{user_id}/{resource_id}")
def get_feedback(user_id: UUID, resource_id: int, db: Session = Depends(get_db)):
    feedback = db.query(UserResourceFeedback).filter(
        UserResourceFeedback.user_id == user_id,
        UserResourceFeedback.learning_resource_id == resource_id
    ).first()

    if not feedback:
        return {
            "rating": None,
            "liked": None,
            "comment": ""
        }

    return {
        "rating": feedback.rating,
        "liked": feedback.liked,
        "comment": feedback.comment or ""
    }