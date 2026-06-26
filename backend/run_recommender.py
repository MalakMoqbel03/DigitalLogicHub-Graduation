"""
run_recommender.py — run the REAL recommender code against the real DB for the
logged-in user, to see exactly what it returns and why.

Run from backend/:
    python3 run_recommender.py
    python3 run_recommender.py <user_id>     # optional: override the user id
"""

import sys
from dotenv import load_dotenv
load_dotenv()

from app.database import SessionLocal
from app.models.user import User
from app.models.learning_resource import LearningResource
from app.recommender.hybrid import get_hybrid_recommendations
from app.recommender.content_based import get_content_based_scores
from app.recommender.utils import normalize_style, normalize_level

ARG = sys.argv[1] if len(sys.argv) > 1 else "malakmoqbel18@gmail.com"

db = SessionLocal()
# Look up by email if the arg contains '@', otherwise treat it as a user id.
if "@" in ARG:
    user = db.query(User).filter(User.email == ARG.lower()).first()
else:
    user = db.query(User).filter(User.id == ARG).first()
if not user:
    print(f"No user found for {ARG!r}")
    sys.exit(1)
print(f"user id   : {user.id}")

style = normalize_style(user.learning_style)
level = normalize_level(user.level)
print(f"user      : {user.email}")
print(f"raw       : learning_style={user.learning_style!r}  level={user.level!r}")
print(f"normalized: style={style!r}  level={level!r}")

# Raw count for that normalized level
n = db.query(LearningResource).filter(LearningResource.difficulty.ilike(level)).count()
print(f"\nresources with difficulty ILIKE {level!r}: {n}")

# Content-based directly
cb = get_content_based_scores(
    db=db, user_id=user.id, style=style, level=level,
    excluded_ids=[], disliked_ids=[], limit=60,
)
print(f"content_based returned: {len(cb)} resources")

# Full hybrid (what the endpoint actually uses)
recs = get_hybrid_recommendations(db=db, user=user, limit=200)
print(f"hybrid returned       : {len(recs)} resources")
for r in recs[:5]:
    res = r["resource"]
    print(f"   [{res.difficulty}] {res.topic} — {res.title[:45]}")

db.close()
