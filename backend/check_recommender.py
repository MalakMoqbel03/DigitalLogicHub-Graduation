"""
check_recommender.py — reproduce the recommender's resource query directly,
to see why it returns nothing despite the table being populated.

Run from backend/:
    python3 check_recommender.py
"""

import sys

url = None
for line in open(".env", encoding="utf-8", errors="replace"):
    if line.strip().startswith("DATABASE_URL"):
        url = line.split("=", 1)[1].strip().strip('"').strip("'")
        break
if not url:
    print("No DATABASE_URL in .env"); sys.exit(1)

import psycopg2
conn = psycopg2.connect(url, connect_timeout=15)
cur = conn.cursor()

print("=== distinct difficulty values (quoted, with length) ===")
cur.execute("SELECT DISTINCT difficulty, length(difficulty) FROM learning_resources")
for val, ln in cur.fetchall():
    print(f"   {val!r:20s} length={ln}")

print("\n=== distinct vark_style values (quoted) ===")
cur.execute("SELECT DISTINCT vark_style FROM learning_resources")
print("   ", [v for (v,) in cur.fetchall()])

print("\n=== users who finished setup (level + style) ===")
cur.execute(
    "SELECT email, learning_style, level FROM users "
    "WHERE level IS NOT NULL ORDER BY email"
)
for email, style, level in cur.fetchall():
    print(f"   {email:30s} style={style!r:12s} level={level!r}")

print("\n=== the exact recommender filter: difficulty ILIKE 'beginner' ===")
cur.execute("SELECT COUNT(*) FROM learning_resources WHERE difficulty ILIKE 'beginner'")
print("   exact ILIKE 'beginner' →", cur.fetchone()[0], "rows")
cur.execute("SELECT COUNT(*) FROM learning_resources WHERE TRIM(difficulty) ILIKE 'beginner'")
print("   TRIM()  ILIKE 'beginner' →", cur.fetchone()[0], "rows")

conn.close()
