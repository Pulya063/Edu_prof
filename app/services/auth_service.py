import os
from datetime import timedelta

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from dotenv import load_dotenv

from app.core.exceptions import AppError
from app.core.security import create_jwt_access_token, decode_access_token, hash_password, verify_password
from app.models import User
from app.schemas import LoginSchema, RegisterSchema, TokenResponse


load_dotenv()

class AuthService:
    def __init__(self, db_session: Session) -> None:
        self.db = db_session

    def register(self, payload: RegisterSchema) -> User:
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

    def login(self, payload: LoginSchema) -> TokenResponse:
        result = self.db.execute(select(User).where(User.email == str(payload.email).lower()))
        user = result.scalar_one_or_none()
        if user is None or not user.is_active or not verify_password(payload.password, user.password_hash):
            raise AppError(
                "Invalid email or password",
                status_code=401,
                headers={"WWW-Authenticate": "Bearer"},
            )
        return self.create_access_token(user)

    def create_access_token(self, user: User) -> TokenResponse:
        token = create_jwt_access_token(
            subject=str(user.id),
            expires_delta=timedelta(minutes=int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))),
        )
        return TokenResponse(access_token=token)

    def get_current_user(self, token: str) -> User | None:
        try:
            subject = decode_access_token(token)
            user_id = int(subject)
        except (ValueError, TypeError):
            return None

        result = self.db.execute(select(User).where(User.id == user_id, User.is_active.is_(True)))
        return result.scalar_one_or_none()
