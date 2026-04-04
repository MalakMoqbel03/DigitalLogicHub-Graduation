from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from uuid import UUID

from app.dependencies import get_db, get_current_user
from app.models.user import User
from app.models.assessment import AssessmentSession, UserResponse
from app.models.user_learning_resource import UserLearningResource
from app.models.user_misconception import UserMisconception
from app.models.learning_resource import LearningResource

router = APIRouter()


@router.get("/progress")
def get_user_progress(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Returns everything the Dashboard needs to show real progress data:
      - current level and VARK style
      - total resources viewed
      - assessment history (score, level, date)
      - latest assessment score + percentage
      - best score ever
      - active misconceptions (top 5)
      - per-topic resource completion counts
    """
    user_id = current_user.id

    # ── Assessment history ────────────────────────────────────────────────────
    sessions = (
        db.query(AssessmentSession)
        .filter(AssessmentSession.user_id == user_id)
        .order_by(AssessmentSession.completed_at.desc())
        .all()
    )

    assessment_history = []
    for s in sessions:
        total_q = db.query(UserResponse).filter(UserResponse.session_id == s.id).count()
        pct = round((s.score / total_q) * 100) if total_q else 0
        assessment_history.append({
            "session_id": str(s.id),
            "score": s.score,
            "total": total_q,
            "percentage": pct,
            "level": s.level,
            "date": s.completed_at.isoformat() if s.completed_at else None,
        })

    latest = assessment_history[0] if assessment_history else None
    best_score = max((a["score"] for a in assessment_history), default=0)
    best_pct   = max((a["percentage"] for a in assessment_history), default=0)

    # ── Resources viewed ──────────────────────────────────────────────────────
    total_viewed = (
        db.query(func.count(UserLearningResource.id))
        .filter(UserLearningResource.user_id == user_id)
        .scalar() or 0
    )

    # ── Per-topic completion ──────────────────────────────────────────────────
    # Count how many resources the user has viewed per topic,
    # and how many total exist per topic (at the user's level).
    level = (current_user.level or "beginner").lower()

    topic_totals = (
        db.query(LearningResource.topic, func.count(LearningResource.id))
        .filter(LearningResource.difficulty.ilike(level))
        .group_by(LearningResource.topic)
        .all()
    )

    viewed_by_topic = (
        db.query(LearningResource.topic, func.count(UserLearningResource.id))
        .join(UserLearningResource,
              UserLearningResource.learning_resource_id == LearningResource.id)
        .filter(UserLearningResource.user_id == user_id)
        .group_by(LearningResource.topic)
        .all()
    )
    viewed_map = {row[0]: row[1] for row in viewed_by_topic}

    topic_progress = []
    for topic, total in topic_totals:
        viewed = viewed_map.get(topic, 0)
        topic_progress.append({
            "topic": topic,
            "viewed": viewed,
            "total": total,
            "percentage": round((viewed / total) * 100) if total else 0,
        })
    # Sort by most-engaged topics first
    topic_progress.sort(key=lambda x: x["viewed"], reverse=True)

    # ── Top misconceptions ────────────────────────────────────────────────────
    misconceptions = (
        db.query(UserMisconception)
        .filter(UserMisconception.user_id == user_id)
        .order_by(UserMisconception.count.desc())
        .limit(5)
        .all()
    )

    return {
        "user_id": str(user_id),
        "name": current_user.name,
        "level": current_user.level,
        "learning_style": current_user.learning_style,
        "total_resources_viewed": total_viewed,
        "best_score": best_score,
        "best_percentage": best_pct,
        "latest_assessment": latest,
        "assessment_count": len(assessment_history),
        "assessment_history": assessment_history,
        "topic_progress": topic_progress,
        "top_misconceptions": [
            {"concept_tag": m.concept_tag, "count": m.count}
            for m in misconceptions
        ],
    }