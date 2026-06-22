"""
clean_users.py — Safely inspect and delete users from the database.

Most common use: remove stale UNVERIFIED accounts (e.g. ones created when the
verification email failed to send) so those emails can register again.

Usage (run from the backend/ folder, with DATABASE_URL set in .env):

    python clean_users.py --list                 # show all users (safe, default)
    python clean_users.py --unverified           # DRY RUN: show unverified users
    python clean_users.py --unverified --yes      # actually delete unverified users
    python clean_users.py --email me@x.com        # DRY RUN: show that one user
    python clean_users.py --email me@x.com --yes  # actually delete that one user
    python clean_users.py --all --yes             # delete ALL users (careful!)

Nothing is deleted unless you pass --yes. All deletes also remove the user's
related rows (assessments, VARK answers, etc.) in foreign-key-safe order, so
you never hit a constraint error.

Requirements: psycopg2-binary, python-dotenv (already in requirements.txt)
"""

import os
import sys
import argparse
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("ERROR: DATABASE_URL is not set. Add it to your .env (the same value "
          "you use on Railway).", file=sys.stderr)
    sys.exit(1)

# Child tables that reference users.id, in the order they must be deleted.
# user_responses is removed via its parent assessment_sessions first.
CHILD_DELETES = [
    # (sql, human label)
    ("DELETE FROM user_responses WHERE session_id IN "
     "(SELECT id FROM assessment_sessions WHERE user_id = ANY(%s))", "assessment answers"),
    ("DELETE FROM assessment_sessions WHERE user_id = ANY(%s)", "assessment sessions"),
    ("DELETE FROM user_vark_responses WHERE user_id = ANY(%s)", "VARK responses"),
    ("DELETE FROM user_learning_resources WHERE user_id = ANY(%s)", "learning interactions"),
    ("DELETE FROM user_resource_feedback WHERE user_id = ANY(%s)", "resource feedback"),
    ("DELETE FROM user_resource_quiz_attempts WHERE user_id = ANY(%s)", "quiz attempts"),
    ("DELETE FROM user_misconceptions WHERE user_id = ANY(%s)", "misconceptions"),
]


def fetch_users(cur, where_sql, params):
    cur.execute(
        f"SELECT id, email, name, is_verified, verification_code_sent_at "
        f"FROM users {where_sql} ORDER BY email",
        params,
    )
    return cur.fetchall()


def main():
    p = argparse.ArgumentParser(description="Inspect / clean users.")
    g = p.add_mutually_exclusive_group()
    g.add_argument("--list", action="store_true", help="List all users (default).")
    g.add_argument("--unverified", action="store_true", help="Target unverified users.")
    g.add_argument("--email", type=str, help="Target a single user by email.")
    g.add_argument("--all", action="store_true", help="Target ALL users.")
    p.add_argument("--yes", action="store_true",
                   help="Actually perform the deletion (otherwise dry run).")
    args = p.parse_args()

    # Decide the WHERE clause for the target set.
    if args.unverified:
        where_sql, params, label = "WHERE is_verified = false", (), "UNVERIFIED users"
    elif args.email:
        where_sql, params, label = "WHERE email = %s", (args.email.lower(),), f"user '{args.email.lower()}'"
    elif args.all:
        where_sql, params, label = "", (), "ALL users"
    else:
        # default: just list everything
        args.list = True
        where_sql, params, label = "", (), "all users"

    conn = psycopg2.connect(DATABASE_URL)
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            users = fetch_users(cur, where_sql, params)

            if not users:
                print(f"No matching users found ({label}).")
                return

            print(f"\nMatched {len(users)} {label}:")
            print("-" * 70)
            for u in users:
                status = "verified" if u["is_verified"] else "UNVERIFIED"
                print(f"  {u['email']:<35} {u['name']:<20} [{status}]")
            print("-" * 70)

            if args.list:
                print("\n(List only — nothing deleted.)")
                return

            if not args.yes:
                print(f"\nDRY RUN — would delete the {len(users)} user(s) above "
                      f"and all their related data.")
                print("Re-run with --yes to actually delete.")
                return

            # Perform the deletion.
            ids = [u["id"] for u in users]
            with conn.cursor() as wcur:
                for sql, child_label in CHILD_DELETES:
                    wcur.execute(sql, (ids,))
                    if wcur.rowcount:
                        print(f"  removed {wcur.rowcount} {child_label}")
                wcur.execute("DELETE FROM users WHERE id = ANY(%s)", (ids,))
                deleted = wcur.rowcount
            conn.commit()
            print(f"\nDeleted {deleted} user(s) and their related data.")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
