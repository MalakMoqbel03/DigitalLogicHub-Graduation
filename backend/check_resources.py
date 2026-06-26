"""
check_resources.py — show what's actually in the production database.

Run from backend/ (it reads DATABASE_URL from your .env, which points at Neon):

    python3 check_resources.py

Tells you whether the learning_resources table is populated, broken down by
difficulty. If it shows 0 rows, the import never ran — run import_data.py.
"""

import sys

# read DATABASE_URL straight from .env (no extra deps needed beyond psycopg2)
url = None
for line in open(".env", encoding="utf-8", errors="replace"):
    if line.strip().startswith("DATABASE_URL"):
        url = line.split("=", 1)[1].strip().strip('"').strip("'")
        break

if not url:
    print("No DATABASE_URL found in .env")
    sys.exit(1)

import psycopg2

conn = psycopg2.connect(url, connect_timeout=15)
cur = conn.cursor()

cur.execute("SELECT COUNT(*) FROM learning_resources")
total = cur.fetchone()[0]
print(f"learning_resources total rows: {total}")

if total:
    cur.execute(
        "SELECT lower(difficulty), COUNT(*) FROM learning_resources "
        "GROUP BY lower(difficulty) ORDER BY 2 DESC"
    )
    print("by difficulty:")
    for diff, n in cur.fetchall():
        print(f"   {diff or '(blank)':12s} {n}")
else:
    print(">>> EMPTY — run:  python3 import_data.py")

conn.close()
