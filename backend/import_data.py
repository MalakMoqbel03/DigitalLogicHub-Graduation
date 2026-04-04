"""
import_data.py
─────────────
Imports all CSV data into the database.
Run from inside backend/:
    python3 import_data.py

CSVs expected in a folder called 'Data/' next to this script:
    Data/questions.csv
    Data/answers.csv
    Data/learning_resources.csv
    Data/vark_questions.csv      (optional — skips if already seeded)
    Data/vark_options_clean.csv  (optional — skips if already seeded)
"""

import os
import csv
import uuid
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL not set in .env")

engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

# Path to the Data folder (same directory as this script)
DATA_DIR = os.path.join(os.path.dirname(__file__), "Data")


def read_csv(filename):
    path = os.path.join(DATA_DIR, filename)
    if not os.path.exists(path):
        print(f"  WARNING: {path} not found — skipping.")
        return []
    with open(path, newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


# ─────────────────────────────────────────────────────────────────────────────
# 1. QUESTIONS + ANSWERS
# ─────────────────────────────────────────────────────────────────────────────

def import_questions(session):
    existing = session.execute(text("SELECT COUNT(*) FROM questions")).scalar()
    if existing > 0:
        print(f"  questions: already has {existing} rows — skipping.")
        return

    questions_rows = read_csv("questions.csv")
    answers_rows   = read_csv("answers.csv")

    if not questions_rows or not answers_rows:
        return

    # questions.csv has no question code — assign Q1, Q2... by row order
    # answers.csv references Q1, Q2... via question_code column
    question_code_to_uuid = {}

    print(f"  Inserting {len(questions_rows)} questions...")
    for i, row in enumerate(questions_rows, start=1):
        code    = f"Q{i}"
        q_id    = str(uuid.uuid4())
        difficulty = row["difficulty"].strip().lower()
        is_entry   = row.get("is_entry", "FALSE").strip().upper() == "TRUE"

        session.execute(
            text("""
                INSERT INTO questions (id, question_text, difficulty, is_entry)
                VALUES (:id, :text, :diff, :entry)
            """),
            {
                "id":    q_id,
                "text":  row["question_text"].strip(),
                "diff":  difficulty,
                "entry": is_entry,
            },
        )
        question_code_to_uuid[code] = q_id

    print(f"  Inserting {len(answers_rows)} answers...")
    skipped = 0
    for row in answers_rows:
        q_code = row["question_code"].strip()
        q_id   = question_code_to_uuid.get(q_code)
        if not q_id:
            skipped += 1
            continue

        is_correct       = row["is_correct"].strip().upper() == "TRUE"
        misconception_tag = row.get("misconception_code", "").strip() or None

        session.execute(
            text("""
                INSERT INTO answers (id, question_id, answer_text, is_correct, misconception_tag)
                VALUES (:id, :qid, :text, :correct, :tag)
            """),
            {
                "id":      str(uuid.uuid4()),
                "qid":     q_id,
                "text":    row["answer_text"].strip(),
                "correct": is_correct,
                "tag":     misconception_tag,
            },
        )

    if skipped:
        print(f"  WARNING: {skipped} answers skipped (question code not found).")

    session.commit()
    print(f"  Done — questions and answers imported.")


# ─────────────────────────────────────────────────────────────────────────────
# 2. LEARNING RESOURCES
# ─────────────────────────────────────────────────────────────────────────────

def import_resources(session):
    existing = session.execute(text("SELECT COUNT(*) FROM learning_resources")).scalar()
    if existing > 0:
        print(f"  learning_resources: already has {existing} rows — skipping.")
        return

    rows = read_csv("learning_resources.csv")
    if not rows:
        return

    print(f"  Inserting {len(rows)} learning resources...")
    for row in rows:
        # Convert is_short TRUE/FALSE string to boolean
        is_short_raw = row.get("is_short", "FALSE").strip().upper()
        is_short = is_short_raw == "TRUE"

        # duration_minutes may be empty
        dur_raw = row.get("duration_minutes", "").strip()
        duration = int(dur_raw) if dur_raw.isdigit() else None

        session.execute(
            text("""
                INSERT INTO learning_resources
                    (title, description, topic, subtopic, resource_type,
                     difficulty, vark_style, duration_minutes, is_short,
                     source, external_url, tags)
                VALUES
                    (:title, :desc, :topic, :subtopic, :rtype,
                     :diff, :vark, :dur, :short,
                     :source, :url, :tags)
            """),
            {
                "title":   row.get("title", "").strip(),
                "desc":    row.get("description", "").strip() or None,
                "topic":   row.get("topic", "").strip(),
                "subtopic":row.get("subtopic", "").strip() or None,
                "rtype":   row.get("resource_type", "").strip(),
                "diff":    row.get("difficulty", "").strip().lower(),
                "vark":    row.get("vark_style", "").strip().lower() or None,
                "dur":     duration,
                "short":   is_short,
                "source":  row.get("source", "").strip() or None,
                "url":     row.get("external_url", "").strip() or None,
                "tags":    row.get("tags", "").strip() or None,
            },
        )

    session.commit()
    print(f"  Done — {len(rows)} learning resources imported.")


# ─────────────────────────────────────────────────────────────────────────────
# 3. VARK QUESTIONS + OPTIONS (skip if already seeded)
# ─────────────────────────────────────────────────────────────────────────────

def import_vark(session):
    existing = session.execute(text("SELECT COUNT(*) FROM vark_questions")).scalar()
    if existing > 0:
        print(f"  vark_questions: already has {existing} rows — skipping.")
        return

    q_rows = read_csv("vark_questions.csv")
    o_rows = read_csv("vark_options_clean.csv")

    if not q_rows or not o_rows:
        return

    print(f"  Inserting {len(q_rows)} VARK questions...")
    for row in q_rows:
        session.execute(
            text("INSERT INTO vark_questions (id, question_text) VALUES (:id, :text)"),
            {"id": int(row["id"]), "text": row["question_text"].strip()},
        )

    print(f"  Inserting {len(o_rows)} VARK options...")
    for row in o_rows:
        session.execute(
            text("""
                INSERT INTO vark_options (id, question_id, option_text, vark_type)
                VALUES (:id, :qid, :text, :vtype)
            """),
            {
                "id":    int(row["id"]),
                "qid":   int(row["question_id"]),
                "text":  row["option_text"].strip(),
                "vtype": row["vark_type"].strip().lower(),
            },
        )

    session.commit()
    print(f"  Done — VARK questions and options imported.")


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────

def main():
    print(f"\nLooking for CSV files in: {DATA_DIR}")
    if not os.path.exists(DATA_DIR):
        print(f"\nERROR: '{DATA_DIR}' folder not found.")
        print("Place the Data/ folder next to this script and try again.")
        sys.exit(1)

    with Session() as session:
        print("\n── Questions & Answers ──────────────────────────")
        import_questions(session)

        print("\n── Learning Resources ───────────────────────────")
        import_resources(session)

        print("\n── VARK Questions & Options ─────────────────────")
        import_vark(session)

    print("\n✅ All done! Run the row count check to verify:")
    print("   python3 -c \"import os,psycopg2; from dotenv import load_dotenv; load_dotenv(); conn=psycopg2.connect(os.environ['DATABASE_URL']); cur=conn.cursor(); [print(t, cur.execute(f'SELECT COUNT(*) FROM {t}') or cur.fetchone()[0]) for t in ['questions','answers','learning_resources','vark_questions']]\"")


if __name__ == "__main__":
    main()