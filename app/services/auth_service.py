from datetime import timedelta

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.security import create_jwt_access_token, decode_access_token, hash_password, verify_password
from app.models import User
from app.schemas import LoginSchema, RegisterSchema, TokenResponse


class AuthService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def register(self, payload: RegisterSchema) -> User:
        user = User(email=str(payload.email).lower(), password_hash=hash_password(payload.password))
        self.db.add(user)
        try:
            await self.db.commit()
        except IntegrityError as exc:
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A user with this email already exists",
            ) from exc
        await self.db.refresh(user)
        return user

    async def login(self, payload: LoginSchema) -> TokenResponse:
        result = await self.db.execute(select(User).where(User.email == str(payload.email).lower()))
        user = result.scalar_one_or_none()
        if user is None or not user.is_active or not verify_password(payload.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return self.create_access_token(user)

    def create_access_token(self, user: User) -> TokenResponse:
        settings = get_settings()
        token = create_jwt_access_token(
            subject=str(user.id),
            expires_delta=timedelta(minutes=settings.access_token_expire_minutes),
        )
        return TokenResponse(access_token=token)

    async def get_current_user(self, token: str) -> User | None:
        try:
            subject = decode_access_token(token)
            user_id = int(subject)
        except (ValueError, TypeError):
            return None

        result = await self.db.execute(select(User).where(User.id == user_id, User.is_active.is_(True)))
        return result.scalar_one_or_none()
