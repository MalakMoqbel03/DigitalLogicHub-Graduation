"""
email_service.py — sends the verification code email.

Uses Brevo's transactional email HTTPS API (https://www.brevo.com). Brevo is
used instead of raw SMTP because Railway blocks outbound SMTP ports below the
Pro plan, and unlike Resend's free tier it can send to ANY recipient once you
verify a single sender address — no domain purchase required.

Required environment variables (set these in Railway → Variables):
    BREVO_API_KEY    API key from Brevo → Settings → SMTP & API → API Keys
                     (it starts with "xkeysib-").
    EMAIL_FROM       The sender address. This MUST be a sender you have verified
                     in Brevo (Settings → Senders, Domains & Dedicated IPs →
                     add the address and click the confirmation link Brevo
                     emails you). e.g. EMAIL_FROM="digitallogichub1@gmail.com".
Optional:
    EMAIL_FROM_NAME  Display name for the sender (default "DigitalLogicHub").
"""

import logging
import re
from os import getenv
from dotenv import load_dotenv
import httpx

load_dotenv()

BREVO_API_KEY = getenv("BREVO_API_KEY")
EMAIL_FROM = getenv("EMAIL_FROM", "")
EMAIL_FROM_NAME = getenv("EMAIL_FROM_NAME", "DigitalLogicHub")
BREVO_URL = "https://api.brevo.com/v3/smtp/email"

logger = logging.getLogger(__name__)


def _parse_sender(raw: str):
    """Accept either 'email@x.com' or 'Name <email@x.com>' and return
    (name, email)."""
    raw = (raw or "").strip()
    match = re.match(r"^(.*?)<([^>]+)>$", raw)
    if match:
        name = match.group(1).strip().strip('"') or EMAIL_FROM_NAME
        return name, match.group(2).strip()
    return EMAIL_FROM_NAME, raw


def send_verification_email(to_email: str, code: str) -> bool:
    """
    Send the 6-digit verification code via Brevo's HTTP API.
    Returns True on success, False on any failure (the code is saved in the DB
    regardless, so the user can request a resend).
    """
    if not BREVO_API_KEY:
        logger.error(
            "BREVO_API_KEY is missing — email sending is disabled. Create a key "
            "in Brevo → Settings → SMTP & API → API Keys, add it in "
            "Railway → Variables, then redeploy."
        )
        return False

    sender_name, sender_email = _parse_sender(EMAIL_FROM)
    if not sender_email:
        logger.error(
            "EMAIL_FROM is missing — set it to a sender address you have "
            "verified in Brevo (Settings → Senders), then redeploy."
        )
        return False

    payload = {
        "sender": {"name": sender_name, "email": sender_email},
        "to": [{"email": to_email}],
        "subject": "DigitalLogicHub — Email Verification",
        "textContent": (
            f"Your DigitalLogicHub verification code is: {code}\n\n"
            f"This code expires in 15 minutes."
        ),
    }
    headers = {
        "api-key": BREVO_API_KEY,
        "Content-Type": "application/json",
        "accept": "application/json",
    }

    try:
        resp = httpx.post(BREVO_URL, json=payload, headers=headers, timeout=15)
    except httpx.RequestError as e:
        logger.error(f"Network error calling Brevo for {to_email}: {e}")
        return False

    if resp.status_code in (200, 201):
        logger.info(f"Verification email sent to {to_email} via Brevo")
        return True

    # Brevo returns a JSON error body, e.g. an invalid key or an unverified
    # sender address.
    logger.error(
        f"Brevo rejected email to {to_email} "
        f"(HTTP {resp.status_code}): {resp.text}"
    )
    return False
