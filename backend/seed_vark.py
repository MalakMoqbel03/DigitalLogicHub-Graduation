import csv
import sys
from pathlib import Path
from sqlalchemy import text
from app.database import SessionLocal

BASE_DIR = Path(__file__).resolve().parent

QUESTIONS_CSV = BASE_DIR / "Data" / "vark_questions.csv"
OPTIONS_CSV = BASE_DIR / "Data" / "vark_options_clean.csv"


def seed_vark(replace=False):
    db = SessionLocal()

    try:
        if replace:
            print("Deleting old VARK data...")

            db.execute(text("DELETE FROM user_vark_responses"))
            db.execute(text("DELETE FROM vark_options"))
            db.execute(text("DELETE FROM vark_questions"))

            db.commit()

        print("Loading questions...")

        with open(QUESTIONS_CSV, newline="", encoding="utf-8-sig") as file:
            reader = csv.DictReader(file)

            for row in reader:
                db.execute(
                    text("""
                        INSERT INTO vark_questions (id, question_text)
                        VALUES (:id, :question_text)
                    """),
                    {
                        "id": int(row["id"]),
                        "question_text": row["question_text"]
                    }
                )

        print("Loading options...")

        with open(OPTIONS_CSV, newline="", encoding="utf-8-sig") as file:
            reader = csv.DictReader(file)

            for row in reader:
                db.execute(
                    text("""
                        INSERT INTO vark_options (id, question_id, option_text, vark_type)
                        VALUES (:id, :question_id, :option_text, :vark_type)
                    """),
                    {
                        "id": int(row["id"]),
                        "question_id": int(row["question_id"]),
                        "option_text": row["option_text"],
                        "vark_type": row["vark_type"]
                    }
                )

        db.commit()

        print("VARK data seeded successfully!")

    except Exception as e:
        db.rollback()
        print("Error:", e)

    finally:
        db.close()


if __name__ == "__main__":
    seed_vark(replace="--replace" in sys.argv)