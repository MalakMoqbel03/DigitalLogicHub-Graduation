"""
email_service.py — sends the verification code email.

Uses Resend's HTTPS API (https://resend.com) instead of raw SMTP, because
Railway blocks outbound SMTP ports (587/465) on all plans below Pro. An HTTPS
API call goes out over port 443, which is never blocked.

Required environment variables (set these in Railway → Variables):
    RESEND_API_KEY   API key from https://resend.com/api-keys (starts with "re_")
    EMAIL_FROM       Sender address. Until you verify your own domain in Resend,
                     use "onboarding@resend.dev" — but note that the test sender
                     can ONLY deliver to the email you signed up to Resend with.
                     To send codes to any student email, add and verify a domain
                     at https://resend.com/domains, then set e.g.
                     EMAIL_FROM="DigitalLogicHub <noreply@yourdomain.com>".
"""

import logging
from os import getenv
from dotenv import load_dotenv
import httpx

load_dotenv()

RESEND_API_KEY = getenv("RESEND_API_KEY")
EMAIL_FROM = getenv("EMAIL_FROM", "onboarding@resend.dev")
RESEND_URL = "https://api.resend.com/emails"

logger = logging.getLogger(__name__)


def send_verification_email(to_email: str, code: str) -> bool:
    """
    Send the 6-digit verification code via Resend's HTTP API.
    Returns True on success, False on any failure (the code is saved in the DB
    regardless, so the user can request a resend).
    """
    if not RESEND_API_KEY:
        logger.error(
            "RESEND_API_KEY is missing — email sending is disabled. "
            "Create a key at https://resend.com/api-keys and add it in "
            "Railway → Variables, then redeploy."
        )
        return False

    payload = {
        "from": EMAIL_FROM,
        "to": [to_email],
        "subject": "DigitalLogicHub — Email Verification",
        "text": (
            f"Your DigitalLogicHub verification code is: {code}\n\n"
            f"This code expires in 15 minutes."
        ),
    }
    headers = {
        "Authorization": f"Bearer {RESEND_API_KEY}",
        "Content-Type": "application/json",
    }

    try:
        resp = httpx.post(RESEND_URL, json=payload, headers=headers, timeout=15)
    except httpx.RequestError as e:
        logger.error(f"Network error calling Resend for {to_email}: {e}")
        return False

    if resp.status_code in (200, 201):
        logger.info(f"Verification email sent to {to_email} via Resend")
        return True

    # Resend returns a JSON error body explaining what went wrong, e.g. an
    # invalid API key, an unverified sender domain, or a recipient the test
    # sender isn't allowed to email.
    logger.error(
        f"Resend rejected email to {to_email} "
        f"(HTTP {resp.status_code}): {resp.text}"
    )
    return False
