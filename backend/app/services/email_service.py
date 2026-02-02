import smtplib
from email.mime.text import MIMEText
from os import getenv
from dotenv import load_dotenv

# Load .env variables
load_dotenv()

EMAIL = getenv("EMAIL_USER")
PASSWORD = getenv("EMAIL_PASS")

SMTP_SERVER = getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(getenv("SMTP_PORT", 587))


def send_verification_email(to_email: str, code: str):
    if not EMAIL or not PASSWORD:
        raise Exception("Email credentials not loaded. Check .env")

    msg = MIMEText(f"Your verification code is: {code}")
    msg["Subject"] = "LearnSmart Email Verification"
    msg["From"] = EMAIL
    msg["To"] = to_email

    # Connect to mail server
    server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
    server.starttls()

    # Login
    server.login(EMAIL, PASSWORD)

    # Send
    server.sendmail(EMAIL, to_email, msg.as_string())

    # Close
    server.quit()
