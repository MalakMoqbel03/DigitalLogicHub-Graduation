"""
explain.py
──────────
Generates a short, personalised "why this was recommended" explanation
for a learning resource using the Claude API.

The explanation is:
  - 1 sentence, max ~20 words
  - Written directly to the student ("you", "your")
  - Grounded in real signals: VARK match, misconception boost, level match,
    collaborative signal, or a fallback if no strong signal exists

Caching: results are stored in Redis under
  "explain:{user_id}:{resource_id}"
with a 24-hour TTL so the same resource never calls the API twice for the
same user.
"""
from __future__ import annotations

import os
import httpx
from app.cache import cache_get, cache_set


def _build_explain_prompt(
    resource_title: str,
    resource_topic: str,
    resource_type: str,
    resource_vark: str,
    user_level: str,
    user_style: str,
    misconception_match: bool,
    cf_signal: bool,
    hybrid_score: float,
    cb_score: float,
    cf_score: float,
) -> str:
    signals = []

    if resource_vark and user_style and resource_vark.lower() == user_style.lower():
        signals.append(f"it matches the student's {user_style} learning style")

    if misconception_match:
        signals.append(
            f"it covers a concept the student has struggled with in {resource_topic}"
        )

    if cf_signal and cf_score and cf_score > 0.3:
        signals.append("students with a similar profile found it helpful")

    if not signals:
        signals.append(
            f"it's a well-matched {user_level}-level resource on {resource_topic}"
        )

    signal_text = " and ".join(signals)

    return (
        f"A digital logic student (level: {user_level}, learning style: {user_style}) "
        f"was recommended the resource \"{resource_title}\" (type: {resource_type}, topic: {resource_topic}). "
        f"The main reasons it was recommended: {signal_text}. "
        f"Recommendation scores — overall: {hybrid_score:.2f}, content match: {cb_score:.2f}, peer signal: {cf_score:.2f}.\n\n"
        f"Write exactly ONE sentence (max 18 words) directly to the student explaining why this was recommended. "
        f"Start with 'Recommended because' or 'Matches your'. "
        f"Be specific and friendly. Do NOT use markdown. Output only the sentence, nothing else."
    )


def get_recommendation_reason(
    *,
    user_id: str,
    resource_id: int,
    resource_title: str,
    resource_topic: str,
    resource_type: str,
    resource_vark: str,
    user_level: str,
    user_style: str,
    misconception_match: bool,
    cf_signal: bool,
    hybrid_score: float,
    cb_score: float,
    cf_score: float,
) -> str | None:
    """
    Returns a short explanation string, or None if the API call fails.
    Result is cached in Redis for 24 hours per (user_id, resource_id) pair.
    """
    cache_key = f"explain:{user_id}:{resource_id}"

    cached = cache_get(cache_key)
    if cached:
        return cached.get("reason")

    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        return None

    prompt = _build_explain_prompt(
        resource_title=resource_title,
        resource_topic=resource_topic,
        resource_type=resource_type,
        resource_vark=resource_vark,
        user_level=user_level,
        user_style=user_style,
        misconception_match=misconception_match,
        cf_signal=cf_signal,
        hybrid_score=hybrid_score,
        cb_score=cb_score,
        cf_score=cf_score,
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
                "model": "claude-haiku-4-5-20251001",   # fastest + cheapest; plenty for 1 sentence
                "max_tokens": 60,
                "temperature": 0.3,
                "messages": [{"role": "user", "content": prompt}],
            },
            timeout=8.0,
        )
        response.raise_for_status()
        data = response.json()
        reason = data["content"][0]["text"].strip()

        # Cache for 24 hours so we never call the API twice for the same pair
        cache_set(cache_key, {"reason": reason}, ttl_seconds=86400)
        return reason

    except Exception:
        # API failure is non-fatal — UI falls back to no explanation
        return None