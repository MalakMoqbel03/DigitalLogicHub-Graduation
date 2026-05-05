from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timezone

try:
    from app.models.user_resource_feedback import UserResourceFeedback
except Exception as e:
    print("Failed importing UserResourceFeedback:", e)
    raise

from app.dependencies import get_db, get_current_user_id
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
    current_user_id: str = Depends(get_current_user_id),   # Bug #6 fix
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

    # Task 10: update last_active_at on every resource interaction
    user.last_active_at = datetime.now(tz=timezone.utc)

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


# ── Bug #5 fix: cluster recommendations (N+1 → single aggregated query) ───────

@router.get("/user-cluster/{user_id}")
def get_user_cluster(
    user_id: UUID,
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id),   # Bug #6 fix
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {
        "cluster_id": user.cluster_id,
        "learning_style": user.learning_style,
        "level": user.level,
    }


@router.get("/cluster-recommendations/{user_id}")
def cluster_recommendations(
    user_id: UUID,
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id),   # Bug #6 fix
):
    """
    'Popular with learners like you' — collaborative signal from peers
    who share the same learning style and level.

    Bug #5 fix: the original code called get_user_cluster() inside a loop
    over ALL users, causing O(n²) DB queries (one per user).

    Fixed approach — 3 queries total regardless of user count:
      1. Load current user (already done via auth).
      2. One query to find all peer user-IDs (same style + level).
      3. One aggregated GROUP BY query to count interactions for those peers.
    """
    from sqlalchemy import func as sqlfunc
    from app.models.user_learning_resource import UserLearningResource
    from app.models.learning_resource import LearningResource

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    style = user.learning_style
    level = user.level

    if not style or not level:
        raise HTTPException(
            status_code=400,
            detail="Complete the VARK quiz and assessment first"
        )

    # Step 1 — find all peer IDs in one query (no loop!)
    peer_ids = [
        row[0]
        for row in db.query(User.id)
        .filter(
            User.learning_style == style,
            User.level == level,
            User.id != user_id,
        )
        .all()
    ]

    if not peer_ids:
        return {"items": [], "source": "no_peers_yet", "cluster": {"learning_style": style, "level": level}}

    # Step 2 — aggregate interactions across ALL peers in one GROUP BY query
    popular = (
        db.query(
            UserLearningResource.resource_id,
            sqlfunc.count(UserLearningResource.id).label("cnt"),
        )
        .filter(UserLearningResource.user_id.in_(peer_ids))
        .group_by(UserLearningResource.resource_id)
        .order_by(sqlfunc.count(UserLearningResource.id).desc())
        .limit(limit)
        .all()
    )

    if not popular:
        return {"items": [], "source": "no_peer_interactions_yet", "cluster": {"learning_style": style, "level": level}}

    resource_ids = [row[0] for row in popular]
    resources_by_id = {
        r.id: r
        for r in db.query(LearningResource).filter(LearningResource.id.in_(resource_ids)).all()
    }

    items = [
        {
            "id": r_id,
            "title": resources_by_id[r_id].title if r_id in resources_by_id else None,
            "topic": resources_by_id[r_id].topic if r_id in resources_by_id else None,
            "subtopic": resources_by_id[r_id].subtopic if r_id in resources_by_id else None,
            "resource_type": resources_by_id[r_id].resource_type if r_id in resources_by_id else None,
            "difficulty": resources_by_id[r_id].difficulty if r_id in resources_by_id else None,
            "vark_style": resources_by_id[r_id].vark_style if r_id in resources_by_id else None,
            "duration_minutes": resources_by_id[r_id].duration_minutes if r_id in resources_by_id else None,
            "description": resources_by_id[r_id].description if r_id in resources_by_id else None,
            "external_url": resources_by_id[r_id].external_url if r_id in resources_by_id else None,
            "is_short": resources_by_id[r_id].is_short if r_id in resources_by_id else None,
        }
        for r_id in resource_ids
        if r_id in resources_by_id
    ]

    return {
        "cluster": {"learning_style": style, "level": level},
        "items": items,
        "source": "cluster_collaborative",
    }