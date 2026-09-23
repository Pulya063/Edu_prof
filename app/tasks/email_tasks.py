import logging
import smtplib
from email.message import EmailMessage
import os

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
    sender = os.getenv("SMTP_USER")
    password = os.getenv("SMTP_PASSWORD")
    host = os.getenv("SMTP_HOST")
    port = int(os.getenv("SMTP_PORT"))
    
    msg = EmailMessage()
    msg.set_content(f"Ваш код для зміни пароля: {code}\n\nЯкщо ви не робили цей запит, проігноруйте цей лист.")
    msg['Subject'] = 'Скидання пароля - Калькулятор ROI'
    msg['From'] = sender
    msg['To'] = email

    try:
        # Якщо SMTP не налаштовано (локальна розробка), просто логуємо
        if not password:
            logger.info(f"[MOCK EMAIL] To: {email} | Token: {code}")
            return "Mock Sent"

        with smtplib.SMTP(host, port) as server:
            server.starttls()
            server.login(sender, password)
            server.send_message(msg)
            
        logger.info(f"Verification email sent to {email}")
        return "Sent"
    except Exception as exc:
        logger.error(f"Failed to send email to {email}: {exc}")
        self.retry(exc=exc, countdown=60)
