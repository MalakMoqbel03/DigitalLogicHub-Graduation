"""
misconception_explain.py
────────────────────────
Generates a short, personalised explanation for a wrong answer detected
during the digital logic assessment.

For each incorrect answer the explanation covers:
  1. WHY the student's chosen answer is wrong
  2. WHY the correct answer is right
  3. The underlying concept they should revisit

Design decisions
────────────────
- Uses claude-haiku (fastest, cheapest) with max_tokens=120 — enough for
  2-3 sentences, not so much it becomes a lecture.
- Cached in Redis under "misc_explain:{hash}" for 7 days. The hash is built
  from (concept_tag, question_text, selected_answer) so:
    * Same wrong answer on retake = instant cache hit, no API call
    * Different wrong answer on same question = different cache entry
- Returns None silently on any failure — the UI falls back gracefully.
- Temperature 0.2 keeps explanations consistent and factual.
"""
from __future__ import annotations

import os
import hashlib
import httpx

from app.cache import cache_get, cache_set

# Friendly labels for concept tags shown to the student
_TAG_LABELS = {
    "kmap_variable_count":    "K-Map cell count",
    "kmap_grouping_rules":    "K-Map grouping rules",
    "kmap_simplification":    "K-Map simplification",
    "binary_to_decimal":      "binary-to-decimal conversion",
    "hex_to_decimal":         "hex-to-decimal conversion",
    "decimal_to_hex":         "decimal-to-hex conversion",
    "and_gate_operation":     "AND gate behaviour",
    "nor_vs_nand":            "NOR vs NAND gates",
    "xor_operation":          "XOR gate behaviour",
    "boolean_identity_laws":  "Boolean identity laws",
    "demorgan_theorem":       "De Morgan's theorem",
    "boolean_simplification": "Boolean expression simplification",
}


def _build_prompt(
    question_text: str,
    selected_answer: str,
    correct_answer: str,
    concept_tag: str,
) -> str:
    concept_label = _TAG_LABELS.get(concept_tag, concept_tag.replace("_", " "))
    return (
        f"A student answered a digital logic question incorrectly.\n\n"
        f"Question: {question_text}\n"
        f"Student's answer: {selected_answer}\n"
        f"Correct answer: {correct_answer}\n"
        f"Misconception category: {concept_label}\n\n"
        f"Write exactly 2-3 sentences directly to the student (use 'you'):\n"
        f"1. Why their answer is wrong\n"
        f"2. Why the correct answer is right\n"
        f"3. The key concept to revisit\n\n"
        f"Be encouraging, specific, and clear. No markdown. Plain sentences only."
    )


def get_misconception_explanation(
    *,
    question_text: str,
    selected_answer: str,
    correct_answer: str,
    concept_tag: str,
) -> str | None:
    """
    Returns a 2-3 sentence explanation string, or None if the API call fails.
    Result is cached in Redis for 7 days per unique (tag, question, answer) combo.
    """
    # Build a stable cache key from the inputs
    raw = f"{concept_tag}|{question_text}|{selected_answer}"
    key_hash = hashlib.sha256(raw.encode()).hexdigest()[:16]
    cache_key = f"misc_explain:{key_hash}"

    cached = cache_get(cache_key)
    if cached:
        return cached.get("explanation")

    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        return None

    prompt = _build_prompt(
        question_text=question_text,
        selected_answer=selected_answer,
        correct_answer=correct_answer,
        concept_tag=concept_tag,
    )

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
                "max_tokens": 120,
                "temperature": 0.2,
                "messages": [{"role": "user", "content": prompt}],
            },
            timeout=8.0,
        )
        response.raise_for_status()
        data = response.json()
        explanation = data["content"][0]["text"].strip()

        # Cache 7 days — wrong answers don't change, no need to regenerate
        cache_set(cache_key, {"explanation": explanation}, ttl_seconds=604800)
        return explanation

    except Exception:
        return None