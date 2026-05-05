import smtplib
import logging
from email.mime.text import MIMEText
from os import getenv
from dotenv import load_dotenv

# Load .env variables
load_dotenv()

EMAIL = getenv("EMAIL_USER")
PASSWORD = getenv("EMAIL_PASS")

SMTP_SERVER = getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(getenv("SMTP_PORT", 587))

logger = logging.getLogger(__name__)


def send_verification_email(to_email: str, code: str) -> bool:
    """
    Bug #1 fix: wrapped entire SMTP session in try/except so failures are
    logged clearly instead of crashing the server silently.
    Returns True on success, False on any failure (caller can still respond
    to the user — the code is saved in the DB regardless).
    """
    # Bug #7 fix: clear, actionable error when credentials are missing
    if not EMAIL or not PASSWORD:
        logger.error(
            "EMAIL_USER or EMAIL_PASS is missing from .env — "
            "email sending is disabled. Add them and restart the server."
        )
        return False

    msg = MIMEText(
        f"Your DigitalLogicHub verification code is: {code}\n\n"
        f"This code expires in 15 minutes."
    )
    msg["Subject"] = "DigitalLogicHub — Email Verification"
    msg["From"] = EMAIL
    msg["To"] = to_email

    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(EMAIL, PASSWORD)
        server.sendmail(EMAIL, to_email, msg.as_string())
        server.quit()
        logger.info(f"Verification email sent to {to_email}")
        return True

    except smtplib.SMTPAuthenticationError:
        logger.error(
            "SMTP authentication failed — EMAIL_PASS must be a Gmail App Password "
            "(not your regular password). Generate one at "
            "https://myaccount.google.com/apppasswords"
        )
    except smtplib.SMTPRecipientsRefused:
        logger.error(f"Recipient address refused by server: {to_email}")
    except smtplib.SMTPException as e:
        logger.error(f"SMTP error sending to {to_email}: {e}")
    except OSError as e:
        logger.error(f"Network error sending to {to_email}: {e}")

    return False