"""
chat.py
───────
AI study assistant endpoint for DigitalLogicHub.

POST /chat/{user_id}
  Body: { message: str, history: [{role, content}] }

The assistant knows the student's:
  - Current level (beginner / intermediate / advanced)
  - VARK learning style
  - Active misconceptions (top 5 from their assessment history)
  - Topics covered: Karnaugh Maps, Number Conversions, Logic Gates, Boolean Algebra

It answers digital logic questions in a style tuned to the student's profile:
  - Visual learners get ASCII diagrams where helpful
  - Kinesthetic learners get step-by-step worked examples
  - Auditory/reading learners get clear prose explanations

Design decisions
────────────────
- claude-haiku: fastest response time for a chat interface. Sonnet would be
  higher quality but students expect chat to feel instant.
- max_tokens: 400 — enough for a thorough explanation, not so long the student
  won't read it. Students can ask follow-up questions for more depth.
- System prompt is rebuilt on every request from the live DB record — so if the
  student retakes the assessment mid-session, the next message uses their new level.
- history is passed in by the frontend (last 10 messages) to maintain context.
  We don't store chat history in the DB — it lives in React state only.
  This keeps it stateless and privacy-friendly.
- The endpoint requires auth (get_current_user_id) so random users can't call it.
"""

import os
import httpx

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List
from uuid import UUID
from sqlalchemy.orm import Session

from app.dependencies import get_db, get_current_user_id
from app.models.user import User
from app.models.user_misconception import UserMisconception

router = APIRouter(prefix="/chat", tags=["chat"])


class ChatMessage(BaseModel):
    role: str    # "user" or "assistant"
    content: str


class ChatRequest(BaseModel):
    message: str
    history: List[ChatMessage] = []


_VARK_STYLE_HINTS = {
    "visual": (
        "This student is a visual learner. Where helpful, use ASCII diagrams, "
        "truth tables, K-Map grids, or structured layouts to illustrate concepts. "
        "Label columns and rows clearly."
    ),
    "auditory": (
        "This student learns well through verbal explanation. Use analogies, "
        "step-by-step narration, and conversational language. "
        "Explain your reasoning out loud as you go."
    ),
    "reading": (
        "This student prefers reading and writing. Use clear structured prose, "
        "definitions before examples, and precise terminology. "
        "Numbered steps are helpful."
    ),
    "kinesthetic": (
        "This student learns by doing. Lead with a worked example first, then "
        "explain the rule. Give them something to try themselves at the end. "
        "Keep explanations grounded in concrete values."
    ),
}

_MISCONCEPTION_LABELS = {
    "kmap_variable_count":    "counting K-Map variables",
    "kmap_grouping_rules":    "K-Map grouping rules (groups must be powers of 2)",
    "kmap_simplification":    "reading simplified Boolean expressions from K-Maps",
    "binary_to_decimal":      "binary-to-decimal conversion (place values)",
    "hex_to_decimal":         "hexadecimal-to-decimal conversion",
    "decimal_to_hex":         "decimal-to-hexadecimal conversion",
    "and_gate_operation":     "AND gate truth table",
    "nor_vs_nand":            "difference between NOR and NAND gates",
    "xor_operation":          "XOR gate (outputs 1 only when inputs differ)",
    "boolean_identity_laws":  "Boolean identity laws (A+0=A, A·1=A, etc.)",
    "demorgan_theorem":       "De Morgan's theorem",
    "boolean_simplification": "simplifying Boolean expressions",
}


def _build_system_prompt(user: User, misconceptions: list[str]) -> str:
    level = (user.level or "beginner").lower()
    style = (user.learning_style or "reading").lower()

    style_hint = _VARK_STYLE_HINTS.get(style, _VARK_STYLE_HINTS["reading"])

    if misconceptions:
        misc_list = "\n".join(
            f"  - {_MISCONCEPTION_LABELS.get(m, m.replace('_', ' '))}"
            for m in misconceptions[:5]
        )
        misc_section = (
            f"\nThe student has repeatedly made errors in these areas — "
            f"pay extra attention if these topics come up:\n{misc_list}"
        )
    else:
        misc_section = ""

    level_guidance = {
        "beginner": (
            "Explain from first principles. Avoid jargon without defining it first. "
            "Use simple numbers (0s and 1s) in examples."
        ),
        "intermediate": (
            "You can assume knowledge of basic gates and binary. "
            "Focus on clarity and correct application of rules."
        ),
        "advanced": (
            "You can use formal notation and assume solid foundations. "
            "Challenge the student to think deeper where appropriate."
        ),
    }.get(level, "")

    return f"""You are a friendly and knowledgeable digital logic study assistant for DigitalLogicHub, \
a university learning platform.

You help students understand four topics: Karnaugh Maps (K-Maps), Number System Conversions \
(binary, decimal, hexadecimal), Logic Gates (AND, OR, NOT, NAND, NOR, XOR, XNOR), \
and Boolean Algebra (simplification, De Morgan's theorem, identity laws).

Student profile:
  - Level: {level}
  - Learning style: {style}
{misc_section}

Level guidance: {level_guidance}

Teaching style: {style_hint}

Rules:
- Only answer questions related to digital logic and the four topics above.
- If the student asks about something unrelated, politely redirect them.
- Keep responses concise — aim for 3-6 sentences or a short worked example.
- End with a follow-up question or suggestion to keep the student engaged.
- Be warm and encouraging. Learning digital logic is hard; celebrate progress.
- Do not use markdown headers. Use plain text and line breaks only."""


@router.post("/{user_id}")
def chat(
    user_id: UUID,
    body: ChatRequest,
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        raise HTTPException(
            status_code=503,
            detail="AI assistant is not configured on this server."
        )

    # Fetch top misconceptions for the system prompt
    misc_rows = (
        db.query(UserMisconception.concept_tag)
        .filter(UserMisconception.user_id == user_id)
        .order_by(UserMisconception.count.desc())
        .limit(5)
        .all()
    )
    misconceptions = [r[0] for r in misc_rows]

    system_prompt = _build_system_prompt(user, misconceptions)

    # Build messages: last 10 exchanges from history + the new message
    history_trimmed = body.history[-10:]
    messages = [
        {"role": msg.role, "content": msg.content}
        for msg in history_trimmed
    ] + [{"role": "user", "content": body.message}]

    try:
        response = httpx.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": "claude-haiku-4-5-20251001",
                "max_tokens": 400,
                "system": system_prompt,
                "messages": messages,
            },
            timeout=15.0,
        )
        response.raise_for_status()
        data = response.json()
        reply = data["content"][0]["text"].strip()
        return {"reply": reply}

    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="AI assistant timed out. Please try again.")
    except Exception as e:
        raise HTTPException(status_code=502, detail="AI assistant unavailable. Please try again.")