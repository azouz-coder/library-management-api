import secrets
import hashlib
import smtplib
import os
from datetime import datetime , timezone,timedelta
from email.message import EmailMessage
from dotenv import load_dotenv
load_dotenv()
def create_hash_token():
    token=secrets.token_urlsafe(32)
    hash_token=hashlib.sha256(
        token.encode()
    ).hexdigest()
    expires_at=datetime.now(timezone.utc)+timedelta(minutes=10)
    return token,hash_token,expires_at
SMTP_HOST = os.getenv("SMTP_HOST")
SMTP_PORT = int(os.getenv("SMTP_PORT","587"))
EMAIL = os.getenv("EMAIL")
PASSWORD = os.getenv("EMAIL_PASSWORD")
BASE_URL = os.getenv("BASE_URL","http://localhost:8000").rstrip("/")
def _send_email(to_email: str , subject: str , body: str):
    message=EmailMessage()
    message["From"]=EMAIL
    message["To"]=to_email
    message["Subject"]=subject
    message.set_content(body)
    # "with" always closes the SMTP connection, even if login or sending fails
    with smtplib.SMTP(SMTP_HOST,SMTP_PORT,timeout=10) as server:
        server.starttls()
        server.login(EMAIL,PASSWORD)
        server.send_message(message)
def send_verification_email(email: str , token: str):
    verify_url=f"{BASE_URL}/users/verify-email?token={token}"
    _send_email(
        email,
        "Verify your email",
        f"Please verify your email by clicking this link:\n{verify_url}"
    )
def send_password_reset_email(email,token):
    reset_url=f"{BASE_URL}/users/reset-password?token={token}"
    _send_email(
        email,
        "Reset Password",
        f"Please reset password by clicking this link:\n{reset_url}"
    )
