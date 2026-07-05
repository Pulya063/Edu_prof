import logging
import smtplib
from email.message import EmailMessage
import os

from app.core.celery_app import celery_app

logger = logging.getLogger(__name__)

@celery_app.task(bind=True, max_retries=3)
def send_verification_email(self, email: str, token: str):
    """
    Асинхронне відправлення листа для скидання пароля/верифікації.
    """
    sender = os.getenv("SMTP_USER", "noreply@roicalc.com")
    password = os.getenv("SMTP_PASSWORD", "")
    host = os.getenv("SMTP_HOST", "smtp.gmail.com")
    port = int(os.getenv("SMTP_PORT", 587))
    
    msg = EmailMessage()
    msg.set_content(f"Ваш код для зміни пароля: {token}\n\nЯкщо ви не робили цей запит, проігноруйте цей лист.")
    msg['Subject'] = 'Скидання пароля - Калькулятор ROI'
    msg['From'] = sender
    msg['To'] = email

    try:
        # Якщо SMTP не налаштовано (локальна розробка), просто логуємо
        if not password:
            logger.info(f"[MOCK EMAIL] To: {email} | Token: {token}")
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
