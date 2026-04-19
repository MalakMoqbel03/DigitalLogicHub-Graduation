from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
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
from app.recommender.hybrid import get_hybrid_recommendations
from app.recommender.collaborative import get_collaborative_scores
from app.recommender.utils import normalize_style, normalize_level

router = APIRouter()


class FeedbackRequest(BaseModel):
    user_id: UUID
    resource_id: int
    rating: Optional[int] = None
    liked: Optional[bool] = None
    comment: Optional[str] = None


def serialize_resource_with_scores(item: dict, cf_strategy: str | None) -> dict:
    r: LearningResource = item["resource"]
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
        "method": item.get("method"),
        "hybrid_score": item.get("hybrid_score"),
        "cb_score": item.get("cb_score"),
        "cf_score": item.get("cf_score"),
        "cf_strategy": cf_strategy,
    }


@router.get("/recommendations/{user_id}")
def get_recommendations(
    user_id: UUID,
    limit: int = 20,
    db: Session = Depends(get_db),
):
    """
    Personalised recommendations for a user.

    Stable ordering rule (first key wins):
      1. Higher hybrid_score first.
      2. Tie-break: lower resource id first — gives a predictable, repeatable
         order for items with identical scores, preventing cards from
         reshuffling between page visits.
    """
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

    cf_probe = get_collaborative_scores(
        db=db,
        current_user=user,
        excluded_ids=[],
        disliked_ids=[],
        limit=1,
    )
    cf_strategy = cf_probe[0]["cf_strategy"] if cf_probe else None

    # Fetch 3x the requested count so the tie-break has breathing room
    scored = get_hybrid_recommendations(db=db, user=user, limit=limit * 3)

    # Stable sort: primary by hybrid_score DESC, tie-break by resource id ASC.
    # Python's sort is stable, so applying the tie-break first then the main
    # key yields a proper compound ordering.
    scored.sort(key=lambda item: item["resource"].id)
    scored.sort(key=lambda item: item.get("hybrid_score", 0.0), reverse=True)

    scored = scored[:limit]

    items = [serialize_resource_with_scores(item, cf_strategy) for item in scored]

    return {
        "user": {
            "id": str(user.id),
            "learning_style": user.learning_style,
            "level": user.level,
            "cluster_id": user.cluster_id,
        },
        "count": len(items),
        "cf_strategy": cf_strategy,
        "items": items,
    }


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


@router.post("/feedback")
def submit_feedback(body: FeedbackRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == body.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    resource = db.query(LearningResource).filter(LearningResource.id == body.resource_id).first()
    if not resource:
        raise HTTPException(status_code=404, detail="Resource not found")

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
