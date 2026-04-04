from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, timezone

from app.models.user import User
from app.models.user_resource_feedback import UserResourceFeedback
from app.models.user_learning_resource import UserLearningResource
from app.recommender.content_based import get_content_based_scores
from app.recommender.collaborative import get_collaborative_scores

# Blend weights — must sum to 1.0
CB_WEIGHT = 0.60   # content-based (VARK + level + misconceptions)
CF_WEIGHT = 0.40   # collaborative filtering


def _get_disliked_ids(db: Session, user_id) -> List[int]:
    """Resources the user explicitly disliked or rated 1–2 stars."""
    explicit = (
        db.query(UserResourceFeedback.learning_resource_id)
        .filter(
            UserResourceFeedback.user_id == user_id,
            UserResourceFeedback.liked == False,
        )
        .all()
    )
    low_rated = (
        db.query(UserResourceFeedback.learning_resource_id)
        .filter(
            UserResourceFeedback.user_id == user_id,
            UserResourceFeedback.rating <= 2,
        )
        .all()
    )
    return list({row[0] for row in explicit + low_rated})


def _get_viewed_ids(db: Session, user_id) -> List[int]:
    """Resources the user has already opened/tracked."""
    rows = (
        db.query(UserLearningResource.learning_resource_id)
        .filter(UserLearningResource.user_id == user_id)
        .all()
    )
    return [r[0] for r in rows]


def _context_multiplier(user: User) -> float:
    """
    Context-aware adjustment.
    Returns a multiplier applied to short resources when the user
    hasn't been active recently.

    Currently always 1.0 — uncomment the block below once
    User.last_active_at column is added to the users table.
    """
    # if user.last_active_at:
    #     days_inactive = (datetime.now(timezone.utc) - user.last_active_at).days
    #     if days_inactive >= 3:
    #         return 1.2   # gently favour short re-engagement resources
    return 1.0


def get_hybrid_recommendations(
    db: Session,
    user: User,
    limit: int = 20,
) -> List[dict]:
    """
    Hybrid recommender: 60% content-based + 40% collaborative filtering.

    Content-based score factors:
      - Difficulty level match
      - VARK learning style match
      - Misconception boost (resource covers a known weak area)
      - Short resource bonus
      - Duration bonus

    Collaborative score:
      - Jaccard similarity with neighbours sharing same level + VARK style
      - Resources liked by top-K neighbours the current user hasn't seen

    Cold-start fallback:
      When CF returns nothing (new user / no neighbours with interactions),
      the full 100% weight flows to content-based so the user always gets results.
    """
    from app.recommender.utils import normalize_style, normalize_level

    style = normalize_style(user.learning_style)
    level = normalize_level(user.level)

    viewed_ids   = _get_viewed_ids(db, user.id)
    disliked_ids = _get_disliked_ids(db, user.id)
    context_mult = _context_multiplier(user)

    # ── Content-based (misconception-aware) ─────────────────────────────────
    cb_results = get_content_based_scores(
        db=db,
        user_id=user.id,      # needed to fetch the user's misconception tags
        style=style,
        level=level,
        excluded_ids=viewed_ids,
        disliked_ids=disliked_ids,
        limit=60,
    )
    cb_map = {item["resource"].id: item["score"] for item in cb_results}

    # ── Collaborative filtering ──────────────────────────────────────────────
    cf_results = get_collaborative_scores(
        db=db,
        current_user=user,
        excluded_ids=viewed_ids,
        disliked_ids=disliked_ids,
        limit=60,
    )
    cf_map = {item["resource"].id: item["score"] for item in cf_results}

    # ── Effective weights (cold-start graceful fallback) ─────────────────────
    if not cf_map:
        effective_cb = 1.0
        effective_cf = 0.0
    else:
        effective_cb = CB_WEIGHT
        effective_cf = CF_WEIGHT

    # ── Merge resource pool from both sources ────────────────────────────────
    all_resources = {item["resource"].id: item["resource"] for item in cb_results}
    all_resources.update(
        {item["resource"].id: item["resource"] for item in cf_results}
    )

    # ── Compute hybrid scores ────────────────────────────────────────────────
    scored = []
    for rid in set(cb_map) | set(cf_map):
        cb_score = cb_map.get(rid, 0.0)
        cf_score = cf_map.get(rid, 0.0)
        hybrid   = effective_cb * cb_score + effective_cf * cf_score

        resource = all_resources[rid]

        # Context: small boost for short resources when user is inactive
        if resource.is_short and context_mult > 1.0:
            hybrid *= context_mult

        scored.append({
            "resource":     resource,
            "hybrid_score": round(hybrid, 4),
            "cb_score":     round(cb_score, 4),
            "cf_score":     round(cf_score, 4),
            "method":       "hybrid" if cf_map else "content_only",
        })

    scored.sort(key=lambda x: x["hybrid_score"], reverse=True)
    return scored[:limit]