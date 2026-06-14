from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Dict, List, Optional
from uuid import UUID
from datetime import datetime

from app.dependencies import get_db
from app.models.user import User
from app.models.assessment import Question, Answer, AssessmentSession, UserResponse
from app.models.user_misconception import UserMisconception
from app.recommender.misconception_explain import get_misconception_explanation

router = APIRouter()

ASSESSMENT_TOPICS = [
    {"id": "karnaugh_map", "label": "Karnaugh Maps", "description": "Simplify Boolean expressions using K-Maps", "icon": "grid", "color": "cyan"},
    {"id": "number_conversions", "label": "Number Conversions", "description": "Convert between Binary, Decimal, Hexadecimal and Octal", "icon": "hash", "color": "purple"},
    {"id": "logic_gates", "label": "Logic Gates", "description": "AND, OR, NOT, NAND, NOR, XOR gate operations", "icon": "cpu", "color": "green"},
    {"id": "boolean_algebra", "label": "Boolean Algebra", "description": "Boolean laws, theorems and expression simplification", "icon": "function", "color": "orange"},
]

DIFFICULTY_ORDER = ["easy", "medium", "hard"]

INLINE_QUESTIONS = {
    "karnaugh_map": {
        "easy": {
            "text": "In a 2-variable K-Map, how many cells does it contain?",
            "answers": [
                {"text": "4", "correct": True, "misconception": None},
                {"text": "2", "correct": False, "misconception": "kmap_variable_count"},
                {"text": "8", "correct": False, "misconception": "kmap_variable_count"},
                {"text": "16", "correct": False, "misconception": "kmap_variable_count"},
            ],
        },
        "medium": {
            "text": "Which grouping size is NOT valid in a K-Map?",
            "answers": [
                {"text": "3", "correct": True, "misconception": None},
                {"text": "1", "correct": False, "misconception": "kmap_grouping_rules"},
                {"text": "2", "correct": False, "misconception": "kmap_grouping_rules"},
                {"text": "4", "correct": False, "misconception": "kmap_grouping_rules"},
            ],
        },
        "hard": {
            "text": "In a 4-variable K-Map, a group of 8 cells reduces the expression to how many literals?",
            "answers": [
                {"text": "1 literal", "correct": True, "misconception": None},
                {"text": "2 literals", "correct": False, "misconception": "kmap_simplification"},
                {"text": "3 literals", "correct": False, "misconception": "kmap_simplification"},
                {"text": "4 literals", "correct": False, "misconception": "kmap_simplification"},
            ],
        },
    },
    "number_conversions": {
        "easy": {
            "text": "What is the decimal value of binary 1010?",
            "answers": [
                {"text": "10", "correct": True, "misconception": None},
                {"text": "12", "correct": False, "misconception": "binary_to_decimal"},
                {"text": "8", "correct": False, "misconception": "binary_to_decimal"},
                {"text": "5", "correct": False, "misconception": "binary_to_decimal"},
            ],
        },
        "medium": {
            "text": "Convert hexadecimal 2F to decimal.",
            "answers": [
                {"text": "47", "correct": True, "misconception": None},
                {"text": "29", "correct": False, "misconception": "hex_to_decimal"},
                {"text": "63", "correct": False, "misconception": "hex_to_decimal"},
                {"text": "35", "correct": False, "misconception": "hex_to_decimal"},
            ],
        },
        "hard": {
            "text": "What is 255 in hexadecimal?",
            "answers": [
                {"text": "FF", "correct": True, "misconception": None},
                {"text": "FE", "correct": False, "misconception": "decimal_to_hex"},
                {"text": "EF", "correct": False, "misconception": "decimal_to_hex"},
                {"text": "F0", "correct": False, "misconception": "decimal_to_hex"},
            ],
        },
    },
    "logic_gates": {
        "easy": {
            "text": "What is the output of an AND gate when both inputs are 1?",
            "answers": [
                {"text": "1", "correct": True, "misconception": None},
                {"text": "0", "correct": False, "misconception": "and_gate_operation"},
                {"text": "Depends on the gate type", "correct": False, "misconception": "and_gate_operation"},
                {"text": "Undefined", "correct": False, "misconception": "and_gate_operation"},
            ],
        },
        "medium": {
            "text": "Which gate produces output 1 only when ALL inputs are 0?",
            "answers": [
                {"text": "NOR", "correct": True, "misconception": None},
                {"text": "NAND", "correct": False, "misconception": "nor_vs_nand"},
                {"text": "NOT (single input)", "correct": False, "misconception": "nor_vs_nand"},
                {"text": "XOR", "correct": False, "misconception": "nor_vs_nand"},
            ],
        },
        "hard": {
            "text": "An XOR gate with inputs A=1, B=1 produces:",
            "answers": [
                {"text": "0", "correct": True, "misconception": None},
                {"text": "1", "correct": False, "misconception": "xor_operation"},
                {"text": "Undefined", "correct": False, "misconception": "xor_operation"},
                {"text": "Depends on implementation", "correct": False, "misconception": "xor_operation"},
            ],
        },
    },
    "boolean_algebra": {
        "easy": {
            "text": "What is A + 0 in Boolean algebra?",
            "answers": [
                {"text": "A", "correct": True, "misconception": None},
                {"text": "0", "correct": False, "misconception": "boolean_identity_laws"},
                {"text": "1", "correct": False, "misconception": "boolean_identity_laws"},
                {"text": "A'", "correct": False, "misconception": "boolean_identity_laws"},
            ],
        },
        "medium": {
            "text": "De Morgan's theorem states that (A \u00b7 B)' equals:",
            "answers": [
                {"text": "A' + B'", "correct": True, "misconception": None},
                {"text": "A' \u00b7 B'", "correct": False, "misconception": "demorgan_theorem"},
                {"text": "A + B", "correct": False, "misconception": "demorgan_theorem"},
                {"text": "A \u00b7 B", "correct": False, "misconception": "demorgan_theorem"},
            ],
        },
        "hard": {
            "text": "Simplify: A + A'B using Boolean algebra.",
            "answers": [
                {"text": "A + B", "correct": True, "misconception": None},
                {"text": "A", "correct": False, "misconception": "boolean_simplification"},
                {"text": "AB", "correct": False, "misconception": "boolean_simplification"},
                {"text": "A'B", "correct": False, "misconception": "boolean_simplification"},
            ],
        },
    },
}

class TopicAnswer(BaseModel):
    question_id: str
    answer_id: str

class SubmitAssessmentRequest(BaseModel):
    user_id: UUID
    topic_answers: Dict[str, Dict[str, TopicAnswer]]


def _record_misconception(db: Session, user_id: UUID, concept_tag: str) -> None:
    existing = db.query(UserMisconception).filter(
        UserMisconception.user_id == user_id,
        UserMisconception.concept_tag == concept_tag,
    ).first()
    if existing:
        existing.count += 1
        existing.last_seen = datetime.utcnow()
    else:
        db.add(UserMisconception(
            user_id=user_id,
            concept_tag=concept_tag,
            count=1,
            first_seen=datetime.utcnow(),
            last_seen=datetime.utcnow(),
        ))


def _score_to_topic_level(score: int) -> str:
    if score == 3:
        return "advanced"
    elif score == 2:
        return "intermediate"
    else:
        return "beginner"


def _overall_level(topic_levels: Dict[str, str]) -> str:
    counts = {"beginner": 0, "intermediate": 0, "advanced": 0}
    for lvl in topic_levels.values():
        counts[lvl] = counts.get(lvl, 0) + 1
    return max(counts, key=lambda k: (counts[k], ["beginner", "intermediate", "advanced"].index(k)))


def _get_recommendation_text(topic_id: str, level: str, misconceptions: List[str]) -> str:
    topic_labels = {
        "karnaugh_map": "Karnaugh Maps",
        "number_conversions": "Number Conversions",
        "logic_gates": "Logic Gates",
        "boolean_algebra": "Boolean Algebra",
    }
    label = topic_labels.get(topic_id, topic_id.replace("_", " ").title())
    if misconceptions:
        tag = misconceptions[0].replace("_", " ").title()
        return f"Review {label} — especially {tag}. Repeated errors suggest a conceptual gap here."
    if level == "beginner":
        return f"Start with foundational {label} materials before tackling practice problems."
    if level == "intermediate":
        return f"Good progress on {label}! Focus on harder problems and edge cases to advance."
    return f"Excellent {label} knowledge! Explore advanced applications and circuit design."


@router.get("/questions")
def get_assessment_questions(db: Session = Depends(get_db)):
    sections = []
    for topic_meta in ASSESSMENT_TOPICS:
        topic_id = topic_meta["id"]
        questions_for_topic = []
        for difficulty in DIFFICULTY_ORDER:
            inline = INLINE_QUESTIONS.get(topic_id, {}).get(difficulty)
            if inline:
                questions_for_topic.append({
                    "id": f"{topic_id}__{difficulty}",
                    "difficulty": difficulty,
                    "question_text": inline["text"],
                    "answers": [
                        {
                            "id": f"{topic_id}__{difficulty}__{i}",
                            "answer_text": a["text"],
                            "misconception_tag": a["misconception"],
                        }
                        for i, a in enumerate(inline["answers"])
                    ],
                })
        sections.append({"topic": topic_meta, "questions": questions_for_topic})
    return {"sections": sections, "topics": ASSESSMENT_TOPICS}


@router.post("/submit")
def submit_assessment(body: SubmitAssessmentRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == body.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if not body.topic_answers:
        raise HTTPException(status_code=400, detail="No answers submitted")

    session = AssessmentSession(
        user_id=user.id,
        started_at=datetime.utcnow(),
        completed_at=datetime.utcnow(),
        score=0,
        level=None,
    )
    db.add(session)
    db.commit()
    db.refresh(session)

    topic_results = {}
    topic_levels = {}
    all_misconceptions = []
    total_correct = 0
    total_questions = 0

    for topic_id, difficulty_map in body.topic_answers.items():
        topic_correct = 0
        topic_details = []
        topic_misconceptions = []

        for difficulty, ans in difficulty_map.items():
            q_id_str = ans.question_id
            a_id_str = ans.answer_id
            is_correct = False
            question_text = ""
            selected_text = ""
            correct_text = ""
            misconception_tag = None

            inline_topic = INLINE_QUESTIONS.get(topic_id, {})
            inline_q = inline_topic.get(difficulty)
            if inline_q:
                question_text = inline_q["text"]
                try:
                    idx = int(a_id_str.split("__")[-1])
                    chosen = inline_q["answers"][idx]
                    is_correct = chosen["correct"]
                    selected_text = chosen["text"]
                    correct_a = next((a for a in inline_q["answers"] if a["correct"]), None)
                    correct_text = correct_a["text"] if correct_a else ""
                    misconception_tag = chosen.get("misconception") if not is_correct else None
                except (IndexError, ValueError):
                    pass

            if is_correct:
                topic_correct += 1
                total_correct += 1
            total_questions += 1

            if misconception_tag:
                _record_misconception(db, user.id, misconception_tag)
                topic_misconceptions.append(misconception_tag)
                all_misconceptions.append(misconception_tag)

            # AI explanation — only generated for wrong answers with a known tag.
            # Returns None silently on failure; UI degrades gracefully.
            ai_explanation = None
            if not is_correct and misconception_tag and question_text:
                ai_explanation = get_misconception_explanation(
                    question_text=question_text,
                    selected_answer=selected_text,
                    correct_answer=correct_text,
                    concept_tag=misconception_tag,
                )

            topic_details.append({
                "difficulty": difficulty,
                "question_text": question_text,
                "selected_answer": selected_text,
                "correct_answer": correct_text,
                "is_correct": is_correct,
                "misconception_tag": misconception_tag,
                "ai_explanation": ai_explanation,
            })

        topic_level = _score_to_topic_level(topic_correct)
        topic_levels[topic_id] = topic_level
        topic_results[topic_id] = {
            "score": topic_correct,
            "total": len(topic_details),
            "level": topic_level,
            "misconceptions": list(set(topic_misconceptions)),
            "details": topic_details,
        }

    overall_level = _overall_level(topic_levels) if topic_levels else "beginner"
    session.score = total_correct
    session.level = overall_level
    user.level = overall_level
    db.commit()

    topic_suggestions = {}
    for topic_id, result in topic_results.items():
        topic_suggestions[topic_id] = {
            "level": result["level"],
            "focus_areas": result["misconceptions"],
            "recommendation": _get_recommendation_text(topic_id, result["level"], result["misconceptions"]),
        }

    return {
        "score": total_correct,
        "total": total_questions,
        "percentage": round((total_correct / total_questions) * 100) if total_questions else 0,
        "level": overall_level,
        "topic_levels": topic_levels,
        "topic_results": topic_results,
        "topic_suggestions": topic_suggestions,
        "misconceptions_detected": list(set(all_misconceptions)),
    }


@router.get("/misconceptions/{user_id}")
def get_user_misconceptions(user_id: UUID, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    misconceptions = (
        db.query(UserMisconception)
        .filter(UserMisconception.user_id == user_id)
        .order_by(UserMisconception.count.desc())
        .all()
    )
    return {
        "user_id": str(user_id),
        "misconceptions": [
            {"concept_tag": m.concept_tag, "count": m.count,
             "first_seen": m.first_seen.isoformat() if m.first_seen else None,
             "last_seen": m.last_seen.isoformat() if m.last_seen else None}
            for m in misconceptions
        ],
    }