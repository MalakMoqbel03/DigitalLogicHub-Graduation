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


def send_verification_email(to_email: str, code: str):
    if not EMAIL or not PASSWORD:
        logger.error("Email credentials not loaded. Check .env")
        raise Exception("Email credentials not loaded. Check .env")

    msg = MIMEText(f"Your verification code is: {code}")
    msg["Subject"] = "LearnSmart Email Verification"
    msg["From"] = EMAIL
    msg["To"] = to_email

    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(EMAIL, PASSWORD)
        server.sendmail(EMAIL, to_email, msg.as_string())
        server.quit()
        logger.info(f"Verification email sent to {to_email}")

    except smtplib.SMTPAuthenticationError:
        logger.error("SMTP authentication failed — check EMAIL_USER and EMAIL_PASS in .env")
        raise
    except smtplib.SMTPException as e:
        logger.error(f"SMTP error when sending to {to_email}: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error sending email to {to_email}: {e}")
        raise