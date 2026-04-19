from sqlalchemy.orm import Session
from sqlalchemy import case
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
      0.15  bonus — resource addresses an active user misconception
      0.10  bonus — resource is marked is_short
      0.10  bonus — duration <= 15 minutes

    Resources the user disliked are excluded entirely.

    Candidate selection — IMPORTANT:
      We prioritise VARK-matching resources when building the pool. Without
      this, the pool can fill up with non-matching items (e.g. 60 auditory
      videos) before any matching items appear, leaving the scorer nothing
      to find. The SQL `CASE` expression assigns priority 0 to matches and
      1 to non-matches so ORDER BY surfaces matches first; the tie-break is
      id for deterministic, stable ordering across requests.
    """
    all_excluded = list(set(excluded_ids + disliked_ids))

    # Priority: 0 if VARK matches (comes first), 1 otherwise.
    # ilike() is case-insensitive so "Visual" / "visual" / "VISUAL" all match.
    vark_priority = case(
        (LearningResource.vark_style.ilike(style), 0),
        else_=1,
    )

    q = db.query(LearningResource).filter(
        LearningResource.difficulty.ilike(level)
    )
    if all_excluded:
        q = q.filter(~LearningResource.id.in_(all_excluded))

    # Order: matching style first, then id for stable tie-break.
    resources = (
        q.order_by(vark_priority.asc(), LearningResource.id.asc())
         .limit(limit)
         .all()
    )

    misconception_tags = _get_active_misconception_tags(db, user_id)

    scored = []
    for r in resources:
        score = 0.40  # base: correct difficulty level

        if r.vark_style and r.vark_style.lower() == style.lower():
            score += 0.25

        if _resource_matches_misconception(r, misconception_tags):
            score += 0.15

        if r.is_short:
            score += 0.10

        if r.duration_minutes and r.duration_minutes <= 15:
            score += 0.10

        scored.append({"resource": r, "score": round(score, 3)})

    # Stable compound sort: score DESC, then id ASC (tie-break).
    scored.sort(key=lambda x: x["resource"].id)
    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored
