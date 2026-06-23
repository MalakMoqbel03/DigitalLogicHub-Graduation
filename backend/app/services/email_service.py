"""
email_service.py — sends the verification code email via the Gmail API.

Sends as your own Gmail account (EMAIL_FROM) using an OAuth2 refresh token.
All traffic is HTTPS (port 443), which Railway allows — and there is no
third-party activation gate, unlike Brevo/SendGrid. The server only needs
httpx; the heavier google libraries are used once, locally, to mint the
refresh token (see get_gmail_token.py).

Required environment variables (set these in Railway → Variables):
    GMAIL_CLIENT_ID       OAuth client ID from Google Cloud Console
    GMAIL_CLIENT_SECRET   OAuth client secret
    GMAIL_REFRESH_TOKEN   Long-lived refresh token (from get_gmail_token.py)
    EMAIL_FROM            The Gmail address you authorized, e.g.
                          digitallogichub1@gmail.com
Optional:
    EMAIL_FROM_NAME       Display name (default "DigitalLogicHub")
"""

import base64
import logging
from email.mime.text import MIMEText
from os import getenv
from dotenv import load_dotenv
import httpx

load_dotenv()

CLIENT_ID = getenv("GMAIL_CLIENT_ID")
CLIENT_SECRET = getenv("GMAIL_CLIENT_SECRET")
REFRESH_TOKEN = getenv("GMAIL_REFRESH_TOKEN")
EMAIL_FROM = getenv("EMAIL_FROM", "")
EMAIL_FROM_NAME = getenv("EMAIL_FROM_NAME", "DigitalLogicHub")

TOKEN_URL = "https://oauth2.googleapis.com/token"
SEND_URL = "https://gmail.googleapis.com/gmail/v1/users/me/messages/send"

logger = logging.getLogger(__name__)


def _get_access_token() -> str | None:
    """Exchange the long-lived refresh token for a short-lived access token."""
    try:
        resp = httpx.post(
            TOKEN_URL,
            data={
                "client_id": CLIENT_ID,
                "client_secret": CLIENT_SECRET,
                "refresh_token": REFRESH_TOKEN,
                "grant_type": "refresh_token",
            },
            timeout=15,
        )
    except httpx.RequestError as e:
        logger.error(f"Network error getting Gmail access token: {e}")
        return None

    if resp.status_code != 200:
        logger.error(
            f"Could not refresh Gmail access token (HTTP {resp.status_code}): "
            f"{resp.text} — check GMAIL_CLIENT_ID / GMAIL_CLIENT_SECRET / "
            f"GMAIL_REFRESH_TOKEN."
        )
        return None
    return resp.json().get("access_token")


def send_verification_email(to_email: str, code: str) -> bool:
    """
    Send the 6-digit verification code via the Gmail API.
    Returns True on success, False on any failure (the code is saved in the DB
    regardless, so the user can request a resend).
    """
    if not (CLIENT_ID and CLIENT_SECRET and REFRESH_TOKEN):
        logger.error(
            "Gmail OAuth is not configured — set GMAIL_CLIENT_ID, "
            "GMAIL_CLIENT_SECRET and GMAIL_REFRESH_TOKEN in Railway → Variables "
            "(run get_gmail_token.py once to obtain the refresh token)."
        )
        return False
    if not EMAIL_FROM:
        logger.error("EMAIL_FROM is missing — set it to your Gmail address.")
        return False

    access_token = _get_access_token()
    if not access_token:
        return False

    msg = MIMEText(
        f"Your DigitalLogicHub verification code is: {code}\n\n"
        f"This code expires in 15 minutes."
    )
    msg["Subject"] = "DigitalLogicHub — Email Verification"
    msg["From"] = f"{EMAIL_FROM_NAME} <{EMAIL_FROM}>"
    msg["To"] = to_email
    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()

    try:
        resp = httpx.post(
            SEND_URL,
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
            },
            json={"raw": raw},
            timeout=15,
        )
    except httpx.RequestError as e:
        logger.error(f"Network error calling Gmail API for {to_email}: {e}")
        return False

    if resp.status_code in (200, 201):
        logger.info(f"Verification email sent to {to_email} via Gmail API")
        return True

    logger.error(
        f"Gmail API rejected email to {to_email} "
        f"(HTTP {resp.status_code}): {resp.text}"
    )
    return False
