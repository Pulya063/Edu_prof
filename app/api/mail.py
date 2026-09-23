import os

from flask import Blueprint, Response, jsonify, request
from kombu.exceptions import OperationalError
from pydantic import BaseModel, EmailStr, Field

from app.core.dependencies import get_current_user
from app.core.database import db
from app.models import MotivationLetter, University, User
from app.services.motivation_letter_service import build_university_letter
from app.tasks.email_tasks import send_user_email
from sqlalchemy import select


blueprint = Blueprint("mail", __name__)


class MailRequest(BaseModel):
    recipient: EmailStr
    subject: str = Field(min_length=1, max_length=200)
    body: str = Field(min_length=1, max_length=10000)


class UniversityLetterRequest(BaseModel):
    university_id: int = Field(gt=0)
    program_name: str = Field(min_length=2, max_length=255)
    degree: str | None = Field(default=None, max_length=255)
    applicant_message: str | None = Field(default=None, max_length=3000)
    achievements: str | None = Field(default=None, max_length=3000)


@blueprint.post("/university-letter")
@get_current_user
def create_university_letter(user: User) -> Response:
    """Create and persist a copy-ready university letter for the current user."""
    payload = UniversityLetterRequest.model_validate(request.get_json(silent=True) or {})
    university = db.session.execute(
        select(University).where(University.id == payload.university_id)
    ).scalar_one_or_none()
    if university is None:
        return jsonify({"detail": "Університет не знайдено"}), 404

    subject, body = build_university_letter(
        user=user,
        university=university,
        program_name=payload.program_name,
        degree=payload.degree,
        applicant_message=payload.applicant_message,
        achievements=payload.achievements,
    )
    letter = MotivationLetter(
        user_id=user.id,
        university_id=university.id,
        title=subject,
        content=body,
        status="draft",
    )
    db.session.add(letter)
    db.session.commit()

    return jsonify(
        {
            "success": True,
            "data": {
                "id": letter.id,
                "university_id": university.id,
                "university_name": university.name,
                "subject": subject,
                "body": body,
                "status": letter.status,
            },
        }
    ), 201


@blueprint.post("/send")
@get_current_user
def send_mail(user: User) -> Response:
    payload = MailRequest.model_validate(request.get_json(silent=True) or {})
    task_args = (str(payload.recipient), payload.subject, payload.body, str(user.email))
    try:
        send_user_email.delay(*task_args)
    except OperationalError:
        # Local development can validate the flow without a running broker.
        # Never silently bypass a real SMTP configuration in production.
        if os.getenv("APP_ENV", "development").lower() == "development" and not os.getenv("SMTP_PASSWORD"):
            send_user_email.apply(args=task_args)
            return jsonify({"success": True, "message": "Лист оброблено в dev mock режимі.", "delivery": "mock"}), 202
        return jsonify({"detail": "Сервіс відправлення листів тимчасово недоступний."}), 503
    return jsonify({"success": True, "message": "Лист поставлено в чергу на відправку.", "delivery": "queued"}), 202
