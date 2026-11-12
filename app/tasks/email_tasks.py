import logging
import smtplib
from email.message import EmailMessage
import os
from urllib.parse import urlencode

from app.core.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, max_retries=3)
def send_user_email(self, recipient: str, subject: str, body: str, reply_to: str | None = None):
    """Send an authenticated user's message through the configured SMTP server."""
    sender = os.getenv("SMTP_USER", "noreply@roicalc.com")
    password = os.getenv("SMTP_PASSWORD", "")
    host = os.getenv("SMTP_HOST", "smtp.gmail.com")
    port = int(os.getenv("SMTP_PORT", 587))

    msg = EmailMessage()
    msg.set_content(body)
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = recipient
    if reply_to:
        msg["Reply-To"] = reply_to

    try:
        if not password:
            logger.info("[MOCK EMAIL] To: %s | Subject: %s", recipient, subject)
            return "Mock Sent"
        with smtplib.SMTP(host, port) as server:
            server.starttls()
            server.login(sender, password)
            server.send_message(msg)
        logger.info("User email sent to %s", recipient)
        return "Sent"
    except Exception as exc:
        logger.error("Failed to send user email: %s", exc)
        raise self.retry(exc=exc, countdown=60)

@celery_app.task(bind=True, max_retries=3)
def send_verification_email(self, email: str, code: str):
    """
    Асинхронне відправлення листа для скидання пароля/верифікації.
    """
    sender = os.getenv("SMTP_USER", "noreply@fence.local")
    password = os.getenv("SMTP_PASSWORD", "")
    host = os.getenv("SMTP_HOST", "smtp.gmail.com")
    port = int(os.getenv("SMTP_PORT", "587"))
    reset_page = os.getenv(
        "PASSWORD_RESET_URL",
        f"{os.getenv('FRONTEND_URL', 'http://localhost:3221').rstrip('/')}/reset-password",
    )
    # Keep the opaque token in the URL fragment so it is not sent in the HTTP request
    # or captured by ordinary reverse-proxy access logs.
    reset_link = f"{reset_page}#{urlencode({'token': code})}"
    
    msg = EmailMessage()
    msg.set_content(
        "Ви запросили зміну пароля Fence.\n\n"
        f"Відкрийте захищене посилання протягом 15 хвилин:\n{reset_link}\n\n"
        "Посилання одноразове. Якщо ви не робили цей запит, проігноруйте лист."
    )
    msg['Subject'] = 'Скидання пароля Fence'
    msg['From'] = sender
    msg['To'] = email

    try:
        # Якщо SMTP не налаштовано (локальна розробка), просто логуємо
        if not password:
            logger.info("[MOCK EMAIL] Password-reset message prepared for %s", email)
            return "Mock Sent"

        with smtplib.SMTP(host, port) as server:
            server.starttls()
            server.login(sender, password)
            server.send_message(msg)
            
        logger.info(f"Verification email sent to {email}")
        return "Sent"
    except Exception as exc:
        logger.error("Failed to send password-reset email to %s: %s", email, exc)
        raise self.retry(exc=exc, countdown=60)
