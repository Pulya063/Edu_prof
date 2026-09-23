import os
import logging
import secrets
from datetime import timedelta

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from dotenv import load_dotenv

from app.core.exceptions import AppError
from app.core.security import create_jwt_access_token, decode_access_token, hash_password, verify_password
from app.core.logging_config import log_call
from app.core.config import get_refresh_token_ttl
from app.core.redis_client import (
    delete_refresh_token,
    get_user_id_by_refresh_token,
    store_refresh_token,
)
from app.models import User
from app.schemas import LoginSchema, RegisterSchema, TokenPairResponse, TokenResponse


load_dotenv()
logger = logging.getLogger(__name__)


class AuthService:
    def __init__(self, db_session: Session) -> None:
        self.db = db_session

    @log_call
    def register(self, payload: RegisterSchema) -> User:
        logger.info("Registering user email=%s", payload.email)
        email = str(payload.email).lower()
        # Генеруємо унікальний username з email-префіксу
        base_username = email.split("@")[0][:50]
        username = base_username
        counter = 1
        while self.db.execute(select(User).where(User.username == username)).scalar_one_or_none():
            username = f"{base_username}{counter}"[:50]
            counter += 1

        user = User(
            email=email,
            username=username,
            password_hash=hash_password(payload.password),
        )
        self.db.add(user)
        try:
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            raise AppError("Користувач з таким email вже існує", status_code=409) from exc
        self.db.refresh(user)
        return user

    @log_call
    def login(self, payload: LoginSchema) -> TokenPairResponse:
        logger.info("Authenticating user email=%s", payload.email)
        result = self.db.execute(select(User).where(User.email == str(payload.email).lower()))
        user = result.scalar_one_or_none()
        if user is None or not user.is_active or not verify_password(payload.password, user.password_hash):
            raise AppError(
                "Invalid email or password",
                status_code=401,
                headers={"WWW-Authenticate": "Bearer"},
            )
        return self.create_token_pair(user)

    @log_call
    def create_access_token(self, user: User) -> TokenResponse:
        """Legacy helper — kept for backward compat (Google OAuth, etc.)."""
        logger.info("Creating access token for user_id=%s", user.id)
        token = create_jwt_access_token(
            subject=str(user.id),
            expires_delta=timedelta(minutes=int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))),
        )
        return TokenResponse(access_token=token)

    @log_call
    def create_token_pair(self, user: User) -> TokenPairResponse:
        """Generate a short-lived JWT access token + long-lived opaque refresh token.

        The refresh token is stored in Redis with the configured TTL so it can
        be revoked on logout and rotated on every refresh call.
        """
        logger.info("Creating token pair for user_id=%s", user.id)
        access_token = create_jwt_access_token(
            subject=str(user.id),
            expires_delta=timedelta(minutes=int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))),
        )
        refresh_token = secrets.token_urlsafe(48)
        ttl = get_refresh_token_ttl()
        store_refresh_token(refresh_token, user.id, ttl)
        logger.info("Issued refresh token for user_id=%s ttl=%ss", user.id, ttl)
        return TokenPairResponse(access_token=access_token, refresh_token=refresh_token)

    @log_call
    def refresh_tokens(self, refresh_token: str) -> TokenPairResponse:
        """Rotate refresh token: validate, revoke old, issue new pair.

        Raises AppError(401) if the token is invalid/expired.
        """
        logger.info("Refreshing token pair")
        user_id = get_user_id_by_refresh_token(refresh_token)
        if user_id is None:
            raise AppError("Refresh token недійсний або прострочений", status_code=401)

        # Revoke the old refresh token immediately (rotation)
        delete_refresh_token(refresh_token)

        result = self.db.execute(select(User).where(User.id == user_id, User.is_active.is_(True)))
        user = result.scalar_one_or_none()
        if user is None:
            raise AppError("Користувача не знайдено або заблоковано", status_code=401)

        return self.create_token_pair(user)

    @log_call
    def revoke_refresh_token(self, refresh_token: str) -> None:
        """Revoke a refresh token on logout."""
        if refresh_token:
            delete_refresh_token(refresh_token)
            logger.info("Refresh token revoked on logout")

    @log_call
    def get_current_user(self, token: str) -> User | None:
        logger.info("Resolving current user from access token")
        try:
            subject = decode_access_token(token)
            user_id = int(subject)
        except (ValueError, TypeError):
            return None

        result = self.db.execute(select(User).where(User.id == user_id, User.is_active.is_(True)))
        return result.scalar_one_or_none()

    @log_call
    def request_password_reset(self, email: str) -> None:
        from app.tasks.email_tasks import send_verification_email

        email = email.lower()
        result = self.db.execute(select(User).where(User.email == email, User.is_active.is_(True)))
        user = result.scalar_one_or_none()

        if user:
            code = f"{secrets.randbelow(1_000_000):06d}"
            # Створюємо короткочасний токен на 15 хвилин
            token = create_jwt_access_token(
                subject=code,
                expires_delta=timedelta(minutes=15),
                purpose="password_reset",
            )
            send_verification_email.delay(email, token)

    @log_call
    def reset_password(self, token: str, new_password: str) -> None:
        try:
            subject = decode_access_token(token, expected_purpose="password_reset")
            user_id = int(subject)
        except (ValueError, TypeError):
            raise AppError("Недійсний або прострочений токен", status_code=400)

        result = self.db.execute(select(User).where(User.id == user_id, User.is_active.is_(True)))
        user = result.scalar_one_or_none()

        if not user:
            raise AppError("Користувача не знайдено", status_code=404)

        user.password_hash = hash_password(new_password)
        self.db.commit()