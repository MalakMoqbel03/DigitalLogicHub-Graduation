"""
collaborative.py
────────────────
User-based collaborative filtering.

Neighbour-finding strategy:
  1. PRIMARY: find users in the same K-Means cluster as the current user.
     This uses the ML-learned similarity (23-dim feature space: VARK style,
     level, topic interests, avg rating, activity) computed by cluster_users.py.
  2. FALLBACK: if the current user has no cluster_id yet (e.g. brand-new user
     registered AFTER the last clustering run), fall back to the older rule:
     same VARK style AND same level.

N+1 fix (2024-06):
  Previously _get_user_liked_resource_ids() was called once per neighbour
  inside a loop — 3 DB queries × N neighbours = up to 90+ queries per CF run.
  Replaced with _batch_get_liked_resource_ids() which fetches all neighbours'
  interactions in 2 batch queries, then groups them in Python.
"""

from sqlalchemy.orm import Session
from typing import List, Dict, Tuple
from uuid import UUID

from app.models.user import User
from app.models.user_learning_resource import UserLearningResource
from app.models.user_resource_feedback import UserResourceFeedback
from app.models.learning_resource import LearningResource


# ── OLD single-user helper (kept for reference, no longer called in hot path) ─

def _get_user_liked_resource_ids(db: Session, user_id: UUID) -> List[int]:
    """
    Return resource IDs that the user has positively interacted with.
    Only used for the CURRENT user's own interaction set (one call, not N).
    Neighbours are now fetched in bulk via _batch_get_liked_resource_ids.
    """
    explicit = (
        db.query(UserResourceFeedback.learning_resource_id)
        .filter(
            UserResourceFeedback.user_id == user_id,
            UserResourceFeedback.liked == True,
        )
        .all()
    )
    high_rated = (
        db.query(UserResourceFeedback.learning_resource_id)
        .filter(
            UserResourceFeedback.user_id == user_id,
            UserResourceFeedback.rating >= 4,
        )
        .all()
    )
    viewed = (
        db.query(UserLearningResource.learning_resource_id)
        .filter(UserLearningResource.user_id == user_id)
        .all()
    )

    ids = set()
    for row in explicit + high_rated + viewed:
        ids.add(row[0])
    return list(ids)


# ── NEW batch helper — replaces the N-query loop ──────────────────────────────

def _batch_get_liked_resource_ids(
    db: Session,
    user_ids: List[UUID],
) -> Dict[UUID, set]:
    """
    Fetch positive interactions for ALL neighbours in 2 queries instead of 3×N.

    Returns a dict mapping user_id → set of resource_ids they positively
    interacted with (liked, rated ≥4, or viewed).

    Query 1: all feedback rows (liked=True OR rating>=4) for the full neighbour list
    Query 2: all view-tracking rows for the full neighbour list

    Both queries use the ix_urf_user_id / ix_ulr_user_id indexes and benefit
    from PostgreSQL's ability to evaluate IN(…) against an index in one pass.
    """
    if not user_ids:
        return {}

    # Initialise a set for every neighbour so absent users return empty sets
    result: Dict[UUID, set] = {uid: set() for uid in user_ids}

    # Query 1 — explicit positive feedback (liked OR highly rated)
    feedback_rows = (
        db.query(
            UserResourceFeedback.user_id,
            UserResourceFeedback.learning_resource_id,
        )
        .filter(
            UserResourceFeedback.user_id.in_(user_ids),
            (
                (UserResourceFeedback.liked == True) |
                (UserResourceFeedback.rating >= 4)
            ),
        )
        .all()
    )
    for uid, rid in feedback_rows:
        result[uid].add(rid)

    # Query 2 — all views (even without explicit feedback)
    view_rows = (
        db.query(
            UserLearningResource.user_id,
            UserLearningResource.learning_resource_id,
        )
        .filter(UserLearningResource.user_id.in_(user_ids))
        .all()
    )
    for uid, rid in view_rows:
        result[uid].add(rid)

    return result


# ── Jaccard similarity ────────────────────────────────────────────────────────

def _jaccard_similarity(set_a: set, set_b: set) -> float:
    """Simple Jaccard similarity between two sets of resource IDs."""
    if not set_a or not set_b:
        return 0.0
    intersection = len(set_a & set_b)
    union = len(set_a | set_b)
    return intersection / union if union else 0.0


# ── Cluster-aware neighbour lookup ────────────────────────────────────────────

def _find_candidate_neighbours(db: Session, current_user: User) -> Tuple[List[User], str]:
    """
    Return (neighbours, strategy_used).

    strategy_used is "cluster" if we could use K-Means, "style_level" otherwise.
    """
    if current_user.cluster_id is not None:
        neighbours = (
            db.query(User)
            .filter(
                User.id != current_user.id,
                User.cluster_id == current_user.cluster_id,
            )
            .all()
        )
        if neighbours:
            return neighbours, "cluster"

    neighbours = (
        db.query(User)
        .filter(
            User.id != current_user.id,
            User.level == current_user.level,
            User.learning_style == current_user.learning_style,
        )
        .all()
    )
    return neighbours, "style_level"


# ── Main entry point ──────────────────────────────────────────────────────────

def get_collaborative_scores(
    db: Session,
    current_user: User,
    excluded_ids: List[int],
    disliked_ids: List[int],
    limit: int = 40,
    min_similarity: float = 0.05,
    top_k_neighbors: int = 10,
) -> List[dict]:
    """
    User-based collaborative filtering.

    Steps:
      1. Find candidate neighbours (same K-Means cluster, or style+level fallback).
      2. Fetch ALL neighbours' interactions in 2 batch queries (N+1 fix).
      3. Compute Jaccard similarity between the current user and each neighbour.
      4. Keep the top-K most similar neighbours above min_similarity.
      5. Collect resources those neighbours liked that the current user hasn't seen.
      6. Score each candidate by the sum of neighbour similarities, normalised to [0,1].

    DB query count:
      Before fix: 3 + (3 × N_neighbours)   e.g. 3 + 90 = 93 for 30 neighbours
      After fix:  3 + 2 = 5 regardless of neighbour count
    """
    # Current user's own interactions (3 queries — unchanged, runs once)
    current_user_resource_ids = set(
        _get_user_liked_resource_ids(db, current_user.id)
    )

    if not current_user_resource_ids:
        return []  # cold-start: CF can't help without any interactions

    # Step 1 — find neighbours (1 query)
    neighbour_users, strategy = _find_candidate_neighbours(db, current_user)
    if not neighbour_users:
        return []

    # Step 2 — batch fetch ALL neighbours' interactions in 2 queries (N+1 fix)
    neighbour_ids = [n.id for n in neighbour_users]
    neighbour_resource_map = _batch_get_liked_resource_ids(db, neighbour_ids)

    # Step 3 — compute Jaccard similarity for each neighbour
    similarities: Dict[UUID, float] = {}
    for neighbour in neighbour_users:
        n_resources = neighbour_resource_map.get(neighbour.id, set())
        if not n_resources:
            continue
        sim = _jaccard_similarity(current_user_resource_ids, n_resources)
        if sim >= min_similarity:
            similarities[neighbour.id] = sim

    if not similarities:
        return []

    # Step 4 — keep top-K neighbours
    top_neighbours = sorted(
        similarities.items(), key=lambda x: x[1], reverse=True
    )[:top_k_neighbors]

    # Step 5 — aggregate resource scores, excluding already-seen / disliked
    all_excluded = set(excluded_ids + disliked_ids) | current_user_resource_ids
    resource_scores: Dict[int, float] = {}

    for neighbour_id, sim in top_neighbours:
        for rid in neighbour_resource_map[neighbour_id]:
            if rid in all_excluded:
                continue
            resource_scores[rid] = resource_scores.get(rid, 0.0) + sim

    if not resource_scores:
        return []

    # Step 6 — normalise and fetch resource objects (1 query)
    max_score = max(resource_scores.values())
    if max_score == 0:
        return []

    candidate_ids = list(resource_scores.keys())[:limit]
    resources = (
        db.query(LearningResource)
        .filter(LearningResource.id.in_(candidate_ids))
        .all()
    )

    scored = []
    for r in resources:
        raw = resource_scores.get(r.id, 0.0)
        normalised = round(raw / max_score, 3)
        scored.append({
            "resource": r,
            "score": normalised,
            "cf_strategy": strategy,
        })

    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored