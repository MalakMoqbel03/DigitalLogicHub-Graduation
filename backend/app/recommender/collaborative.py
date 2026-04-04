from sqlalchemy.orm import Session
from typing import List, Dict
from uuid import UUID

from app.models.user import User
from app.models.user_learning_resource import UserLearningResource
from app.models.user_resource_feedback import UserResourceFeedback
from app.models.learning_resource import LearningResource


def _get_user_liked_resource_ids(db: Session, user_id: UUID) -> List[int]:
    """
    Return resource IDs that the user has positively interacted with.
    'Positive' means: rating >= 4  OR  liked == True  OR  viewed (tracked).
    We use a union so even users with no explicit ratings still contribute.
    """
    # Explicitly liked / highly rated
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
    # Simply viewed
    viewed = (
        db.query(UserLearningResource.learning_resource_id)
        .filter(UserLearningResource.user_id == user_id)
        .all()
    )

    ids = set()
    for row in explicit + high_rated + viewed:
        ids.add(row[0])
    return list(ids)


def _jaccard_similarity(set_a: set, set_b: set) -> float:
    """Simple Jaccard similarity between two sets of resource IDs."""
    if not set_a or not set_b:
        return 0.0
    intersection = len(set_a & set_b)
    union = len(set_a | set_b)
    return intersection / union if union else 0.0


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
      1. Find all other users who share the same VARK style and level (neighbourhood).
      2. Compute Jaccard similarity between the current user's interactions and each neighbour's.
      3. Keep the top-K most similar neighbours.
      4. Collect resources those neighbours liked that the current user hasn't seen yet.
      5. Score each candidate resource by the sum of neighbour similarities that liked it,
         normalised to a 0-1 range so it blends cleanly with the CB score.

    Falls back to an empty list (triggering content-only mode) when:
      - The user hasn't interacted with anything yet (cold start).
      - No similar neighbours are found above min_similarity.
    """
    current_user_resource_ids = set(
        _get_user_liked_resource_ids(db, current_user.id)
    )

    # Cold-start guard: if current user has no interactions, CF can't run
    if not current_user_resource_ids:
        return []

    # Find candidate neighbours: same level AND learning style
    neighbour_users = (
        db.query(User)
        .filter(
            User.id != current_user.id,
            User.level == current_user.level,
            User.learning_style == current_user.learning_style,
        )
        .all()
    )

    if not neighbour_users:
        return []

    # Compute similarities
    similarities: Dict[UUID, float] = {}
    neighbour_resource_map: Dict[UUID, set] = {}

    for neighbour in neighbour_users:
        n_resources = set(_get_user_liked_resource_ids(db, neighbour.id))
        if not n_resources:
            continue
        sim = _jaccard_similarity(current_user_resource_ids, n_resources)
        if sim >= min_similarity:
            similarities[neighbour.id] = sim
            neighbour_resource_map[neighbour.id] = n_resources

    if not similarities:
        return []

    # Keep top-K neighbours
    top_neighbours = sorted(similarities.items(), key=lambda x: x[1], reverse=True)[
        :top_k_neighbors
    ]

    # Aggregate resource scores from top neighbours
    all_excluded = set(excluded_ids + disliked_ids) | current_user_resource_ids
    resource_scores: Dict[int, float] = {}

    for neighbour_id, sim in top_neighbours:
        for rid in neighbour_resource_map[neighbour_id]:
            if rid in all_excluded:
                continue
            resource_scores[rid] = resource_scores.get(rid, 0.0) + sim

    if not resource_scores:
        return []

    # Normalise scores to [0, 1]
    max_score = max(resource_scores.values())
    if max_score == 0:
        return []

    # Fetch the actual resource objects
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
        scored.append({"resource": r, "score": normalised})

    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored