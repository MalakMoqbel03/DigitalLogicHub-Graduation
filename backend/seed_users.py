"""
seed_users.py — Generate 50 realistic seed users across 5 interest clusters
and populate their learning resource interactions.

Usage:
    python seed_users.py

Requirements: psycopg2-binary, bcrypt, python-dotenv
Make sure your DATABASE_URL is set in .env before running.
"""

import os
import uuid
import random
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor
import bcrypt

load_dotenv()

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:password@localhost:5433/digitallogichub"
)

# ── Cluster persona definitions ────────────────────────────────────────────────
CLUSTERS = [
    {
        "id": 0,
        "name": "Logic Builders",
        "styles": ["visual", "reading"],
        "levels": ["beginner", "intermediate"],
        "topic_weights": {
            "Boolean_Algebra": 4,
            "Boolean Algebra": 4,
            "Combinational_Logic": 4,
            "Combinational Logic": 3,
            "Logic Simplification": 3,
            "Digital_Basics": 2,
            "Digital Basics": 2,
            "Sequential Logic": 1,
            "FSM": 1,
            "HDL_Verilog": 0,
            "Memory Systems": 0,
        },
        "count": 10,
    },
    {
        "id": 1,
        "name": "Sequential Architects",
        "styles": ["kinesthetic", "auditory"],
        "levels": ["intermediate", "advanced"],
        "topic_weights": {
            "Sequential Logic": 5,
            "FSM": 5,
            "Registers & Counters": 4,
            "Registers and Counters": 4,
            "Combinational_Logic": 2,
            "Combinational Logic": 2,
            "Boolean_Algebra": 1,
            "Boolean Algebra": 1,
            "Memory Systems": 2,
            "Digital_Basics": 1,
        },
        "count": 10,
    },
    {
        "id": 2,
        "name": "Hardware Programmers",
        "styles": ["reading", "kinesthetic"],
        "levels": ["intermediate", "advanced"],
        "topic_weights": {
            "HDL_Verilog": 5,
            "HDL Verilog": 5,
            "Combinational_Logic": 3,
            "Combinational Logic": 3,
            "Sequential Logic": 3,
            "Boolean_Algebra": 2,
            "FSM": 2,
            "Memory Systems": 2,
            "Digital_Basics": 1,
        },
        "count": 10,
    },
    {
        "id": 3,
        "name": "Systems Explorers",
        "styles": ["visual", "reading"],
        "levels": ["intermediate", "advanced"],
        "topic_weights": {
            "Memory Systems": 5,
            "Timing and Performance": 5,
            "Digital_Basics": 4,
            "Digital Basics": 4,
            "Sequential Logic": 2,
            "Combinational_Logic": 2,
            "FSM": 1,
            "Boolean_Algebra": 1,
            "HDL_Verilog": 1,
        },
        "count": 10,
    },
    {
        "id": 4,
        "name": "Digital All-Rounders",
        "styles": ["visual", "auditory", "reading", "kinesthetic"],
        "levels": ["beginner", "intermediate", "advanced"],
        "topic_weights": {
            "Boolean_Algebra": 2,
            "Boolean Algebra": 2,
            "Combinational_Logic": 2,
            "Combinational Logic": 2,
            "Sequential Logic": 2,
            "FSM": 2,
            "HDL_Verilog": 2,
            "Memory Systems": 2,
            "Digital_Basics": 2,
            "Digital Basics": 2,
            "Logic Simplification": 2,
            "Timing and Performance": 2,
            "Registers & Counters": 2,
            "Registers and Counters": 2,
        },
        "count": 10,
    },
]

# ── Name pools ─────────────────────────────────────────────────────────────────
FIRST_NAMES = [
    "Liam", "Olivia", "Noah", "Emma", "Ethan", "Ava", "Lucas", "Sophia",
    "Aiden", "Isabella", "Mason", "Mia", "Logan", "Charlotte", "James",
    "Amelia", "Elijah", "Harper", "Benjamin", "Evelyn", "Omar", "Layla",
    "Yusuf", "Fatima", "Chen", "Wei", "Arjun", "Priya", "Diego", "Camila",
    "Mateo", "Valentina", "Malik", "Aisha", "Soren", "Astrid", "Ivan",
    "Natasha", "Kenji", "Yuki", "Kwame", "Abena", "Tariq", "Zara",
    "Rafael", "Sofia", "Andrei", "Elena", "Hassan", "Nour",
]

LAST_NAMES = [
    "Ahmed", "Johnson", "Chen", "Martinez", "Williams", "Brown", "Garcia",
    "Kim", "Patel", "Nguyen", "Smith", "Taylor", "Anderson", "Thomas",
    "Jackson", "White", "Harris", "Martin", "Thompson", "Young",
    "Lewis", "Walker", "Hall", "Allen", "Wright", "Scott", "Green",
    "Adams", "Baker", "Nelson", "Carter", "Mitchell", "Perez", "Roberts",
    "Turner", "Phillips", "Campbell", "Parker", "Evans", "Edwards",
    "Collins", "Stewart", "Sanchez", "Morris", "Rogers", "Reed", "Cook",
    "Bell", "Murphy", "Bailey",
]

DEFAULT_PASSWORD = "DigitalLogic2024!"


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def weighted_choice(weights: dict) -> str:
    topics = [t for t, w in weights.items() if w > 0]
    wts = [weights[t] for t in topics]
    return random.choices(topics, weights=wts, k=1)[0]


def main():
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor(cursor_factory=RealDictCursor)

    # ── Fetch available resources grouped by topic+difficulty ──────────────────
    cur.execute("SELECT id, topic, difficulty FROM learning_resources")
    resources = cur.fetchall()
    resource_map: dict = {}  # (topic, difficulty) → [id, ...]
    for r in resources:
        key = (r["topic"], (r["difficulty"] or "beginner").strip().lower())
        resource_map.setdefault(key, []).append(r["id"])

    print(f"Loaded {len(resources)} resources from DB")

    name_index = 0
    total_created = 0
    total_interactions = 0

    for cluster in CLUSTERS:
        print(f"\n── Cluster {cluster['id']}: {cluster['name']} ({cluster['count']} users) ──")

        for i in range(cluster["count"]):
            first = FIRST_NAMES[name_index % len(FIRST_NAMES)]
            last = LAST_NAMES[name_index % len(LAST_NAMES)]
            name_index += 1

            email = f"{first.lower()}.{last.lower()}{cluster['id']}{i}@dlhub.edu"
            style = random.choice(cluster["styles"])
            level = random.choice(cluster["levels"])
            user_id = str(uuid.uuid4())
            pw_hash = hash_password(DEFAULT_PASSWORD)

            # Insert user
            try:
                cur.execute(
                    """
                    INSERT INTO users (id, email, password_hash, name, is_verified, learning_style, level)
                    VALUES (%s, %s, %s, %s, true, %s, %s)
                    ON CONFLICT (email) DO NOTHING
                    """,
                    (user_id, email, pw_hash, f"{first} {last}", style, level)
                )
                if cur.rowcount == 0:
                    print(f"  Skipped (exists): {email}")
                    continue

                total_created += 1

                # ── Generate 5–15 resource interactions ──────────────────────
                num_interactions = random.randint(5, 15)
                used_ids = set()

                for _ in range(num_interactions):
                    topic = weighted_choice(cluster["topic_weights"])
                    key = (topic, level)
                    candidates = resource_map.get(key, [])

                    # Fallback: same topic any difficulty
                    if not candidates:
                        fallback_keys = [k for k in resource_map if k[0] == topic]
                        for fk in fallback_keys:
                            candidates.extend(resource_map[fk])

                    if not candidates:
                        continue

                    rid = random.choice([c for c in candidates if c not in used_ids] or candidates)
                    if rid in used_ids:
                        continue

                    used_ids.add(rid)
                    cur.execute(
                        """
                        INSERT INTO user_learning_resources (user_id, learning_resource_id)
                        VALUES (%s, %s)
                        ON CONFLICT DO NOTHING
                        """,
                        (user_id, rid)
                    )
                    total_interactions += 1

                print(f"  ✓ {first} {last} | {style} | {level} | {len(used_ids)} interactions")

            except Exception as e:
                print(f"  ✗ Error for {email}: {e}")
                conn.rollback()
                continue

        conn.commit()

    cur.close()
    conn.close()

    print(f"\n{'='*50}")
    print(f"✅ Seeding complete!")
    print(f"   Users created:       {total_created}")
    print(f"   Interactions logged: {total_interactions}")
    print(f"   Default password:    {DEFAULT_PASSWORD}")
    print(f"{'='*50}")


if __name__ == "__main__":
    main()