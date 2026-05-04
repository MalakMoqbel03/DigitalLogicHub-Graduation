"""
cluster_users.py
────────────────
Groups users into clusters of similar learners using K-Means.

Steps:
  1. Load every user's profile + their viewing & rating behavior
  2. Build a numerical feature vector per user (one-hot style + level,
     topic interest distribution, avg rating, activity level, ...)
  3. Standardize features (zero mean, unit variance) — K-Means is sensitive to scale
  4. Run the ELBOW METHOD to pick the best k in [2..10]
  5. Run K-Means with that best k
  6. Save each user's cluster_id back to the database
  7. Print a human-readable summary + ASCII elbow chart to terminal

Run from inside backend/ with the venv active:
    python cluster_users.py

Requires: pip install scikit-learn numpy
"""

import os
import sys
from collections import Counter, defaultdict
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Make the app package importable when running this script from backend/
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    import numpy as np
    from sklearn.cluster import KMeans
    from sklearn.preprocessing import StandardScaler
except ImportError:
    print("Missing dependencies. Run:  pip install scikit-learn numpy")
    sys.exit(1)

from app.models.user import User
from app.models.learning_resource import LearningResource
from app.models.user_learning_resource import UserLearningResource
from app.models.user_resource_feedback import UserResourceFeedback


# ── Config ────────────────────────────────────────────────────────────────────
K_MIN = 2
K_MAX = 10
RANDOM_SEED = 42   # reproducible results — important for a thesis

STYLES = ["visual", "auditory", "reading"]
LEVELS = ["beginner", "intermediate", "advanced"]


# ── Feature engineering ───────────────────────────────────────────────────────

def build_feature_matrix(session):
    """
    Return (user_ids, feature_matrix, feature_names).

    For each user we compute:
      - style_visual, style_auditory, style_reading (one-hot, 3 columns)
      - level_beginner, level_intermediate, level_advanced (one-hot, 3 columns)
      - For each topic in the DB: fraction of user's views in that topic
      - avg_rating  (3 stars if no ratings — neutral prior)
      - activity    (number of resources viewed — normalized later)
    """
    # Discover all distinct topics from the resources table
    topics = sorted({
        t for (t,) in session.query(LearningResource.topic).distinct().all() if t
    })
    print(f"Found {len(topics)} distinct topics: {topics}")

    # Index resources by id so we can look up topic quickly
    resource_topic = {
        r.id: r.topic
        for r in session.query(LearningResource).all()
    }

    # Fetch all users (both real and fake)
    users = session.query(User).all()
    print(f"Fetched {len(users)} users total (real + fake).")

    # Fetch all views grouped by user
    views_by_user = defaultdict(list)
    for v in session.query(UserLearningResource).all():
        topic = resource_topic.get(v.learning_resource_id)
        if topic:
            views_by_user[v.user_id].append(topic)

    # Fetch ratings per user
    ratings_by_user = defaultdict(list)
    for f in session.query(UserResourceFeedback).all():
        if f.rating is not None:
            ratings_by_user[f.user_id].append(f.rating)

    user_ids = []
    rows = []

    for user in users:
        # Skip users who have NO views AND NO quiz/style info — they're empty shells
        if (
            user.learning_style is None
            and user.level is None
            and not views_by_user.get(user.id)
        ):
            continue

        # One-hot: VARK style
        style_vec = [1.0 if user.learning_style == s else 0.0 for s in STYLES]

        # One-hot: level
        level_vec = [1.0 if user.level == l else 0.0 for l in LEVELS]

        # Topic distribution
        user_views = views_by_user.get(user.id, [])
        view_counts = Counter(user_views)
        total_views = sum(view_counts.values())
        if total_views:
            topic_vec = [view_counts.get(t, 0) / total_views for t in topics]
        else:
            topic_vec = [0.0] * len(topics)

        # Average rating (neutral 3.0 prior if none)
        ratings = ratings_by_user.get(user.id, [])
        avg_rating = float(np.mean(ratings)) if ratings else 3.0

        # Activity (raw count; will be standardized with the rest below)
        activity = float(total_views)

        row = style_vec + level_vec + topic_vec + [avg_rating, activity]
        rows.append(row)
        user_ids.append(user.id)

    if not rows:
        raise RuntimeError("No usable users found — nothing to cluster.")

    feature_names = (
        [f"style_{s}" for s in STYLES]
        + [f"level_{l}" for l in LEVELS]
        + [f"topic_{t}" for t in topics]
        + ["avg_rating", "activity"]
    )

    return user_ids, np.array(rows, dtype=float), feature_names


# ── Elbow method ──────────────────────────────────────────────────────────────

def find_elbow_k(X, k_min=K_MIN, k_max=K_MAX):
    """
    Run K-Means for each k in [k_min, k_max], record inertia, and pick the
    'elbow' using the max-distance-from-line heuristic.

    Returns (best_k, inertias list).
    """
    inertias = []
    ks = list(range(k_min, k_max + 1))

    for k in ks:
        km = KMeans(n_clusters=k, n_init=10, random_state=RANDOM_SEED)
        km.fit(X)
        inertias.append(km.inertia_)

    # The elbow is the point on the inertia curve farthest from the straight
    # line drawn from (k_min, inertia[0]) to (k_max, inertia[-1]).
    p1 = np.array([ks[0], inertias[0]])
    p2 = np.array([ks[-1], inertias[-1]])
    line_vec = p2 - p1
    line_vec_norm = line_vec / np.linalg.norm(line_vec)

    distances = []
    for k, inertia in zip(ks, inertias):
        point = np.array([k, inertia])
        point_vec = point - p1
        projection_len = np.dot(point_vec, line_vec_norm)
        projection = projection_len * line_vec_norm
        dist = np.linalg.norm(point_vec - projection)
        distances.append(dist)

    best_idx = int(np.argmax(distances))
    return ks[best_idx], ks, inertias


def print_ascii_elbow(ks, inertias, best_k):
    """Pretty-print an ASCII chart of the elbow to the terminal."""
    max_inertia = max(inertias)
    min_inertia = min(inertias)
    range_i = max_inertia - min_inertia or 1.0
    width = 40   # character width of the bars

    print("\nElbow method — inertia for each k:")
    print("-" * 60)
    for k, inertia in zip(ks, inertias):
        normalized = (inertia - min_inertia) / range_i
        bar_len = int(normalized * width)
        marker = "  <-- elbow" if k == best_k else ""
        print(f"  k={k:>2}: {'#' * bar_len}{'.' * (width - bar_len)}  {inertia:>10.2f}{marker}")
    print("-" * 60)
    print(f"Best k (by elbow method): {best_k}")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    load_dotenv()
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        raise RuntimeError("DATABASE_URL not set.")

    engine = create_engine(db_url)
    Session = sessionmaker(bind=engine)
    session = Session()

    print("Building feature matrix from database...")
    user_ids, X, feature_names = build_feature_matrix(session)
    print(f"Feature matrix shape: {X.shape}  ({X.shape[0]} users, {X.shape[1]} features)")

    if X.shape[0] < K_MAX:
        # Can't run k up to K_MAX if we have fewer users
        print(f"Note: only {X.shape[0]} users — capping k_max at {X.shape[0] - 1}.")

    k_max_effective = min(K_MAX, X.shape[0] - 1)
    if k_max_effective < K_MIN:
        raise RuntimeError(
            f"Need at least {K_MIN + 1} users to cluster. Found {X.shape[0]}."
        )

    # Standardize features (zero mean, unit variance)
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # Find elbow
    best_k, ks, inertias = find_elbow_k(X_scaled, K_MIN, k_max_effective)
    print_ascii_elbow(ks, inertias, best_k)

    # Final clustering with chosen k
    print(f"\nRunning final K-Means with k={best_k}...")
    kmeans = KMeans(n_clusters=best_k, n_init=10, random_state=RANDOM_SEED)
    labels = kmeans.fit_predict(X_scaled)

    # Save results back to the users table
    print("Saving cluster_id to each user...")
    for user_id, label in zip(user_ids, labels):
        session.query(User).filter(User.id == user_id).update(
            {"cluster_id": int(label)}
        )
    session.commit()
    print("Saved.")

    # Per-cluster summary
    print(f"\nCluster summary (k={best_k}):")
    print("=" * 70)
    for cluster_id in range(best_k):
        cluster_user_ids = [
            uid for uid, lbl in zip(user_ids, labels) if lbl == cluster_id
        ]
        size = len(cluster_user_ids)

        # Get those users' profile fields to describe the cluster
        cluster_users = session.query(User).filter(
            User.id.in_(cluster_user_ids)
        ).all()

        styles = Counter(u.learning_style for u in cluster_users if u.learning_style)
        levels = Counter(u.level for u in cluster_users if u.level)

        top_style = styles.most_common(1)[0] if styles else ("-", 0)
        top_level = levels.most_common(1)[0] if levels else ("-", 0)

        print(f"Cluster {cluster_id}: {size} users")
        style_pct = (top_style[1] / size * 100) if size else 0
        level_pct = (top_level[1] / size * 100) if size else 0
        print(f"  Dominant style: {top_style[0]} ({top_style[1]}/{size}, {style_pct:.0f}%)")
        print(f"  Dominant level: {top_level[0]} ({top_level[1]}/{size}, {level_pct:.0f}%)")
    print("=" * 70)

    # Extra metrics (optional but impressive)
    try:
        from sklearn.metrics import silhouette_score
        if best_k >= 2 and X_scaled.shape[0] > best_k:
            score = silhouette_score(X_scaled, labels)
            print(f"\nSilhouette score: {score:.3f} "
                  f"(1.0 = perfect separation, 0 = overlapping, <0 = bad)")
    except ImportError:
        pass

    session.close()
    print("\nDone. Users have been clustered and cluster_id saved to DB.")


if __name__ == "__main__":
    main()
