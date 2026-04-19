"""
seed_fake_users.py
──────────────────
Generates 100 synthetic users for the DigitalLogicHub recommender system.

Each fake user has:
  - Realistic-ish name and a clearly fake email ending in '@fake.dlh'
    (so you can delete them later with: DELETE FROM users WHERE email LIKE '%@fake.dlh';)
  - Randomly assigned VARK learning style (visual / auditory / reading)
  - Randomly assigned level (beginner / intermediate / advanced)
  - Simulated "views" on resources that match their style + level
  - Simulated ratings on some of those viewed resources

Run from inside backend/ with the venv active:
    python seed_fake_users.py

Safe to re-run: it checks for existing fake users and skips if already seeded.
"""

import os
import random
import uuid
import sys
from datetime import datetime, timedelta

from dotenv import load_dotenv
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from passlib.hash import bcrypt

# Make the app package importable when running this script from backend/
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.models.user import User
from app.models.learning_resource import LearningResource
from app.models.user_learning_resource import UserLearningResource
from app.models.user_resource_feedback import UserResourceFeedback

# ── Config ────────────────────────────────────────────────────────────────────
NUM_USERS = 100
FAKE_EMAIL_DOMAIN = "@fake.dlh"   # DO NOT CHANGE — used to identify fake users later
DEFAULT_PASSWORD = "FakeUser123"   # all fake users share this (they can't actually log in)

# VARK / level distributions (realistic mix, not uniform)
VARK_STYLES = ["visual", "auditory", "reading"]
VARK_WEIGHTS = [0.5, 0.25, 0.25]   # more visual learners, as is common in reality

LEVELS = ["beginner", "intermediate", "advanced"]
LEVEL_WEIGHTS = [0.45, 0.4, 0.15]  # students skew beginner-to-intermediate

# Simple name pool — mix of common first/last names
FIRST_NAMES = [
    "Ahmad", "Sara", "Malak", "Rand", "Leen", "Omar", "Yusuf", "Dana",
    "Maya", "Zaid", "Huda", "Kareem", "Lina", "Tariq", "Nour", "Sami",
    "Reem", "Jad", "Farah", "Hassan", "Layla", "Adam", "Joud", "Raya",
    "Tala", "Murad", "Bana", "Saeed", "Noor", "Hala",
]
LAST_NAMES = [
    "Khalil", "Ahmad", "Hassan", "Ibrahim", "Saleh", "Mahmoud", "Awad",
    "Haddad", "Khoury", "Nasser", "Saad", "Said", "Hamdan", "Barghouti",
    "Abu-Salem", "Qasem", "Ewaida", "Moqbel", "Awadallah", "Odeh",
]


# ── Helpers ───────────────────────────────────────────────────────────────────

def make_name() -> str:
    return f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"


def make_email(existing: set) -> str:
    """Build a unique fake email address."""
    while True:
        base = f"user{random.randint(1000, 9999)}"
        email = base + FAKE_EMAIL_DOMAIN
        if email not in existing:
            existing.add(email)
            return email


def pick_resources_for_user(
    session, style: str, level: str, all_resources: list
) -> list:
    """
    Pick a realistic subset of resources for this fake user to "view".
    Matches resources to the user's style and level, with some noise so clusters
    are not perfectly separable (which would make clustering trivial and boring).
    """
    # Base pool: resources that match this user's style or level
    matching = [
        r for r in all_resources
        if (r.vark_style == style or r.difficulty == level)
    ]

    # Fall back to all resources if no match (shouldn't happen but safety)
    pool = matching if matching else all_resources

    # Each user views 5-20 resources — varies so some users are "active" and others not
    n_views = random.randint(5, 20)
    n_views = min(n_views, len(pool))
    views = random.sample(pool, n_views)

    # Add 10% noise: 1-2 random resources outside their usual taste
    noise_count = random.randint(0, 2)
    noise_pool = [r for r in all_resources if r not in views]
    if noise_pool and noise_count:
        views += random.sample(noise_pool, min(noise_count, len(noise_pool)))

    return views


def rating_for(style_match: bool, level_match: bool) -> int:
    """
    Return a realistic 1-5 rating based on whether the resource matches
    the user's style/level. Perfect matches → higher ratings on average.
    """
    if style_match and level_match:
        return random.choices([3, 4, 5], weights=[0.15, 0.45, 0.4])[0]
    if style_match or level_match:
        return random.choices([2, 3, 4], weights=[0.2, 0.5, 0.3])[0]
    return random.choices([1, 2, 3], weights=[0.3, 0.4, 0.3])[0]


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    load_dotenv()
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        raise RuntimeError("DATABASE_URL not set. Create a .env with DATABASE_URL.")

    engine = create_engine(db_url)
    Session = sessionmaker(bind=engine)
    session = Session()

    # Skip if already seeded
    existing_fake = session.query(User).filter(
        User.email.like(f"%{FAKE_EMAIL_DOMAIN}")
    ).count()
    if existing_fake >= NUM_USERS:
        print(f"Already have {existing_fake} fake users — skipping.")
        print("To reseed: DELETE FROM users WHERE email LIKE '%@fake.dlh'; then rerun.")
        session.close()
        return

    # Load all resources once
    all_resources = session.query(LearningResource).all()
    if not all_resources:
        raise RuntimeError(
            "No learning resources found in DB. Run import_data.py first."
        )
    print(f"Loaded {len(all_resources)} learning resources from DB.")

    # Hash the default password ONCE (bcrypt is slow on purpose)
    print("Hashing default password (bcrypt is intentionally slow)...")
    password_hash = bcrypt.hash(DEFAULT_PASSWORD)

    existing_emails = {e for (e,) in session.query(User.email).all()}

    print(f"Creating {NUM_USERS} fake users...")
    created = 0
    for i in range(NUM_USERS):
        # 1. Make the user
        style = random.choices(VARK_STYLES, weights=VARK_WEIGHTS)[0]
        level = random.choices(LEVELS, weights=LEVEL_WEIGHTS)[0]
        user = User(
            id=uuid.uuid4(),
            name=make_name(),
            email=make_email(existing_emails),
            password_hash=password_hash,
            is_verified=True,
            learning_style=style,
            level=level,
        )
        session.add(user)
        session.flush()   # so user.id is populated for FK use below

        # 2. Pick resources they "viewed"
        viewed = pick_resources_for_user(session, style, level, all_resources)

        for r in viewed:
            session.add(UserLearningResource(
                user_id=user.id,
                learning_resource_id=r.id,
            ))

            # 3. Out of viewed resources, they rate ~60% of them
            if random.random() < 0.6:
                style_match = (r.vark_style == style)
                level_match = (r.difficulty == level)
                rating = rating_for(style_match, level_match)
                liked = rating >= 4

                # Spread ratings over the last 90 days so "latest" queries work nicely
                created_at = datetime.utcnow() - timedelta(
                    days=random.randint(0, 90),
                    hours=random.randint(0, 23),
                )

                session.add(UserResourceFeedback(
                    user_id=user.id,
                    learning_resource_id=r.id,
                    rating=rating,
                    liked=liked,
                    comment=None,
                    created_at=created_at,
                ))

        created += 1
        if created % 20 == 0:
            session.commit()
            print(f"  Created {created}/{NUM_USERS} users...")

    session.commit()
    print(f"Done! Created {created} fake users.")
    print(f"All fake users have emails ending in {FAKE_EMAIL_DOMAIN}")
    print(f"To clean up later:  DELETE FROM users WHERE email LIKE '%{FAKE_EMAIL_DOMAIN}';")
    session.close()


if __name__ == "__main__":
    main()
