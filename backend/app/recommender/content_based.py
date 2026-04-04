from sqlalchemy.orm import Session
from typing import List

from app.models.learning_resource import LearningResource
from app.models.user_resource_feedback import UserResourceFeedback
from app.models.user_misconception import UserMisconception


def _get_active_misconception_tags(db: Session, user_id) -> List[str]:
    """
    Return concept tags the user has got wrong at least once,
    ordered by frequency (most repeated first).
    """
    rows = (
        db.query(UserMisconception.concept_tag)
        .filter(UserMisconception.user_id == user_id)
        .order_by(UserMisconception.count.desc())
        .all()
    )
    return [r[0].lower() for r in rows]


def _resource_matches_misconception(resource: LearningResource, tags: List[str]) -> bool:
    """
    Check if a resource's topic, subtopic, or tags field overlaps
    with any of the user's active misconception tags.
    """
    if not tags:
        return False

    # Build a single lowercase string from all resource metadata fields
    haystack = " ".join(filter(None, [
        resource.topic or "",
        resource.subtopic or "",
        resource.tags or "",
    ])).lower()

    return any(tag in haystack for tag in tags)


def get_content_based_scores(
    db: Session,
    user_id,
    style: str,
    level: str,
    excluded_ids: List[int],
    disliked_ids: List[int],
    limit: int = 40,
) -> List[dict]:
    """
    Content-based filtering with misconception-aware boosting.

    Scoring breakdown (max possible = 1.0):
      0.40  base  — resource difficulty matches user level
      0.25  bonus — VARK style matches user's learning style
      0.15  bonus — resource addresses an active user misconception  ← NEW
      0.10  bonus — resource is marked is_short
      0.10  bonus — duration <= 15 minutes

    Resources the user disliked are excluded entirely.
    """
    # ── Fetch candidate pool ────────────────────────────────────────────────
    all_excluded = list(set(excluded_ids + disliked_ids))

    q = db.query(LearningResource).filter(
        LearningResource.difficulty.ilike(level)
    )
    if all_excluded:
        q = q.filter(~LearningResource.id.in_(all_excluded))

    resources = q.limit(limit).all()

    # ── Get misconception tags for this user ─────────────────────────────────
    misconception_tags = _get_active_misconception_tags(db, user_id)

    # ── Score each resource ──────────────────────────────────────────────────
    scored = []
    for r in resources:
        score = 0.40  # base: correct difficulty level

        # VARK style match
        if r.vark_style and r.vark_style.lower() == style.lower():
            score += 0.25

        # Misconception boost — resource targets a known weak area
        if _resource_matches_misconception(r, misconception_tags):
            score += 0.15

        # Short content bonus
        if r.is_short:
            score += 0.10

        # Duration bonus
        if r.duration_minutes and r.duration_minutes <= 15:
            score += 0.10

        scored.append({"resource": r, "score": round(score, 3)})

    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored