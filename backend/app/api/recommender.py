from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from uuid import UUID
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timezone
from app.cache import cache_get, cache_set, cache_delete_pattern
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
from app.recommender.explain import get_recommendation_reason
from app.recommender.collaborative import get_collaborative_scores
from app.recommender.utils import normalize_style, normalize_level

router = APIRouter()


class FeedbackRequest(BaseModel):
    user_id: UUID
    resource_id: int
    rating: Optional[int] = None
    liked: Optional[bool] = None
    comment: Optional[str] = None


def serialize_resource_with_scores(item: dict, cf_strategy: str | None, reason: str | None = None) -> dict:
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
        "reason": reason,
    }


@router.get("/recommendations/{user_id}")
def get_recommendations(
    user_id: UUID,
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id),
):
    # 1. Build a unique cache key for this user + limit combination
    cache_key = f"recommendations:{user_id}:{limit}"

    # 2. Check if we already have a cached result
    cached = cache_get(cache_key)
    if cached:
        return cached  # Returns instantly from Redis, no DB queries needed

    # 3. If no cache, run the actual recommendation logic (same as before)
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

    scored = get_hybrid_recommendations(db=db, user=user, limit=limit * 3)
    scored.sort(key=lambda item: item["resource"].id)
    scored.sort(key=lambda item: item.get("hybrid_score", 0.0), reverse=True)
    scored = scored[:limit]

    items = [serialize_resource_with_scores(item, cf_strategy) for item in scored]

    result = {
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

    # 4. Save result to cache for 1 hour (3600 seconds)
    cache_set(cache_key, result, ttl_seconds=3600)

    return result

@router.post("/track/{user_id}/{resource_id}")
def track_resource_interaction(
    user_id: UUID,
    resource_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id),
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
        # Still refresh last_active_at so the context multiplier stays accurate
        user.last_active_at = datetime.now(tz=timezone.utc)
        db.commit()
        return {"message": "Already tracked"}

    row = UserLearningResource(
        user_id=user.id,
        learning_resource_id=resource.id
    )

    db.add(row)

    # Update last_active_at on every resource interaction
    user.last_active_at = datetime.now(tz=timezone.utc)

    db.commit()
    background_tasks.add_task(cache_delete_pattern, f"recommendations:{user_id}:*")
    background_tasks.add_task(cache_delete_pattern, f"topics_pool:{user_id}")
    return {"message": "Tracked successfully"}


@router.post("/feedback")
def submit_feedback(body: FeedbackRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
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
        background_tasks.add_task(cache_delete_pattern, f"recommendations:{body.user_id}:*")
        background_tasks.add_task(cache_delete_pattern, f"topics_pool:{body.user_id}")
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
    background_tasks.add_task(cache_delete_pattern, f"recommendations:{body.user_id}:*")
    background_tasks.add_task(cache_delete_pattern, f"topics_pool:{body.user_id}")
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

# ── Topic-grouped progressive recommendations ─────────────────────────────────

@router.get("/topics/{user_id}")
def get_topic_recommendations(
    user_id: UUID,
    page: int = 1,
    per_topic: int = 3,
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id),
):
    """
    Returns learning resources grouped by topic, sorted by relevance score.
    Progressive loading: each call returns `per_topic` resources per topic.
    Already-viewed resources are excluded so the user always sees fresh content.
    Feedback (liked/disliked) influences ordering via the hybrid score.

    Caching strategy
    ────────────────
    The expensive part is get_hybrid_recommendations(limit=200) — 6-8 DB
    queries plus Python scoring over 519 resources.  This result is cached
    under "topics_pool:{user_id}" for 1 hour so that page navigation and
    refreshes are instant.

    The pool key is invalidated (via background task) whenever the user
    submits feedback or opens a new resource, so the feed stays fresh after
    meaningful interactions.

    The per-page slice is computed from the cached pool on every request —
    it is cheap Python and depends on the `page` param so it is never cached.

    Query params:
      page       – page number starting at 1 (each page adds per_topic more resources per topic)
      per_topic  – how many resources to expose per topic per page (default 3)
    """
    from collections import defaultdict

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

    # ── Layer 1: try to load the scored pool from Redis ───────────────────
    pool_cache_key = f"topics_pool:{user_id}"
    cached_pool = cache_get(pool_cache_key)

    if cached_pool is not None:
        # Pool is a list of plain dicts (resources serialized for JSON storage)
        scored_dicts = cached_pool
    else:
        # Cache miss — run the full hybrid recommender and store the result
        scored = get_hybrid_recommendations(db=db, user=user, limit=200)
        scored.sort(key=lambda item: item["resource"].id)
        scored.sort(key=lambda item: item.get("hybrid_score", 0.0), reverse=True)

        # Serialize the pool to plain dicts so it can be stored in Redis as JSON.
        # We store everything needed for the response + reason generation.
        scored_dicts = [
            {
                "id":            item["resource"].id,
                "title":         item["resource"].title,
                "description":   item["resource"].description,
                "topic":         item["resource"].topic,
                "subtopic":      item["resource"].subtopic,
                "resource_type": item["resource"].resource_type,
                "difficulty":    item["resource"].difficulty,
                "vark_style":    item["resource"].vark_style,
                "duration_minutes": item["resource"].duration_minutes,
                "is_short":      item["resource"].is_short,
                "source":        item["resource"].source,
                "external_url":  item["resource"].external_url,
                "tags":          item["resource"].tags,
                "method":        item.get("method"),
                "hybrid_score":  item.get("hybrid_score", 0.0),
                "cb_score":      item.get("cb_score", 0.0),
                "cf_score":      item.get("cf_score", 0.0),
            }
            for item in scored
        ]

        # Cache for 1 hour — same TTL as the flat recommendations endpoint
        cache_set(pool_cache_key, scored_dicts, ttl_seconds=3600)

    # ── Layer 2: group and slice (pure Python, instant) ─────────────────
    topics: dict = defaultdict(list)
    for d in scored_dicts:
        topics[d["topic"]].append(d)

    limit_per_topic = page * per_topic
    offset = (page - 1) * per_topic

    # Collect the page slice first — fast, no I/O
    page_slices: list[tuple[str, list, list]] = []
    for topic, items in sorted(topics.items()):
        full_slice = items[:limit_per_topic]
        page_slice = full_slice[offset:limit_per_topic]
        if page_slice:
            page_slices.append((topic, items, page_slice))

    # ── Layer 3: assemble response — no AI calls here ───────────────────
    # Reasons are fetched separately via POST /recommender/reasons
    # so this endpoint returns instantly regardless of cache state.
    result_topics = []
    for topic, items, page_slice in page_slices:
        serialized = [
            {**d, "cf_strategy": None, "reason": None}
            for d in page_slice
        ]
        result_topics.append({
            "topic": topic,
            "pretty_topic": topic.replace("_", " ").title() if topic else "",
            "total_available": len(items),
            "has_more": len(items) > limit_per_topic,
            "resources": serialized,
        })

    return {
        "user": {
            "id": str(user.id),
            "learning_style": user.learning_style,
            "level": user.level,
        },
        "page": page,
        "per_topic": per_topic,
        "topic_count": len(result_topics),
        "topics": result_topics,
    }



# ── AI Reasons (deferred, parallel) ──────────────────────────────────────────

class ReasonsRequest(BaseModel):
    user_id: UUID
    resources: list[dict]   # [{id, title, topic, resource_type, vark_style, cb_score, cf_score}, ...]


@router.post("/reasons")
def get_reasons(
    body: ReasonsRequest,
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id),
):
    """
    Fetch AI "why this was recommended" explanations for a list of resources.
    Called by the frontend AFTER /topics already returned and resources are
    displayed — so the user sees content immediately and reasons fill in after.

    All reason calls run in parallel (ThreadPoolExecutor).
    Cache hits (Redis) return in <5ms per resource.
    Cache misses call Claude Haiku concurrently — total wall time ≈ slowest single call.

    Returns: { reasons: { resource_id: explanation_string | null } }
    """
    from concurrent.futures import ThreadPoolExecutor, as_completed

    user = db.query(User).filter(User.id == body.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    style = normalize_style(user.learning_style) or "reading"
    level = normalize_level(user.level) or "beginner"

    def fetch_one(r: dict) -> tuple[int, str | None]:
        misc_match = r.get("cb_score", 0) > 0.55
        cf_sig = r.get("cf_score", 0) > 0.1
        reason = get_recommendation_reason(
            user_id=str(body.user_id),
            resource_id=r["id"],
            resource_title=r.get("title") or "",
            resource_topic=(r.get("topic") or "").replace("_", " "),
            resource_type=r.get("resource_type") or "",
            resource_vark=r.get("vark_style") or "",
            user_level=level,
            user_style=style,
            misconception_match=misc_match,
            cf_signal=cf_sig,
            hybrid_score=r.get("hybrid_score", 0.0),
            cb_score=r.get("cb_score", 0.0),
            cf_score=r.get("cf_score", 0.0),
        )
        return r["id"], reason

    results: dict[int, str | None] = {}
    resources = body.resources[:20]   # safety cap — never more than 20 at once

    if resources:
        with ThreadPoolExecutor(max_workers=min(8, len(resources))) as pool:
            futures = {pool.submit(fetch_one, r): r["id"] for r in resources}
            for future in as_completed(futures, timeout=12):
                try:
                    rid, reason = future.result()
                    results[rid] = reason
                except Exception:
                    results[futures[future]] = None

    return {"reasons": results}

# ── Bookmarks ─────────────────────────────────────────────────────────────────

class BookmarkRequest(BaseModel):
    user_id: UUID
    resource_id: int
    bookmarked: bool   # True = save, False = unsave


@router.post("/bookmark")
def toggle_bookmark(
    body: BookmarkRequest,
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id),
):
    """
    Save or unsave a resource for the current user.
    Creates a UserLearningResource row if one does not exist yet.
    """
    user = db.query(User).filter(User.id == body.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    resource = db.query(LearningResource).filter(LearningResource.id == body.resource_id).first()
    if not resource:
        raise HTTPException(status_code=404, detail="Resource not found")

    existing = db.query(UserLearningResource).filter(
        UserLearningResource.user_id == body.user_id,
        UserLearningResource.learning_resource_id == body.resource_id,
    ).first()

    if existing:
        existing.is_bookmarked = body.bookmarked
    else:
        db.add(UserLearningResource(
            user_id=body.user_id,
            learning_resource_id=body.resource_id,
            is_bookmarked=body.bookmarked,
        ))

    db.commit()
    return {"bookmarked": body.bookmarked}


@router.get("/bookmarks/{user_id}")
def get_bookmarks(
    user_id: UUID,
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id),
):
    """Return all bookmarked resources for a user."""
    rows = (
        db.query(UserLearningResource)
        .filter(
            UserLearningResource.user_id == user_id,
            UserLearningResource.is_bookmarked == True,
        )
        .all()
    )
    resource_ids = [r.learning_resource_id for r in rows]
    if not resource_ids:
        return {"items": []}

    resources = (
        db.query(LearningResource)
        .filter(LearningResource.id.in_(resource_ids))
        .all()
    )
    return {
        "items": [
            {
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
                "external_url": r.external_url,
                "tags": r.tags,
            }
            for r in resources
        ]
    }


# ── Skip / "see another" ──────────────────────────────────────────────────────

class SkipRequest(BaseModel):
    user_id: UUID
    resource_id: int


@router.post("/skip")
def skip_resource(
    body: SkipRequest,
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id),
):
    """
    Mark a resource as skipped so it disappears from the current session
    but can be recovered from the 'Skipped' tab.
    """
    user = db.query(User).filter(User.id == body.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    existing = db.query(UserLearningResource).filter(
        UserLearningResource.user_id == body.user_id,
        UserLearningResource.learning_resource_id == body.resource_id,
    ).first()

    if existing:
        existing.is_skipped = True
    else:
        db.add(UserLearningResource(
            user_id=body.user_id,
            learning_resource_id=body.resource_id,
            is_skipped=True,
        ))

    db.commit()
    return {"skipped": True}


@router.post("/unskip")
def unskip_resource(
    body: SkipRequest,
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id),
):
    """Restore a previously skipped resource back into the feed."""
    existing = db.query(UserLearningResource).filter(
        UserLearningResource.user_id == body.user_id,
        UserLearningResource.learning_resource_id == body.resource_id,
    ).first()

    if existing:
        existing.is_skipped = False
        db.commit()

    return {"skipped": False}


@router.get("/skipped/{user_id}")
def get_skipped(
    user_id: UUID,
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id),
):
    """Return all resources the user has skipped."""
    rows = (
        db.query(UserLearningResource)
        .filter(
            UserLearningResource.user_id == user_id,
            UserLearningResource.is_skipped == True,
        )
        .all()
    )
    resource_ids = [r.learning_resource_id for r in rows]
    if not resource_ids:
        return {"items": []}

    resources = (
        db.query(LearningResource)
        .filter(LearningResource.id.in_(resource_ids))
        .all()
    )
    return {
        "items": [
            {
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
                "external_url": r.external_url,
                "tags": r.tags,
            }
            for r in resources
        ]
    }