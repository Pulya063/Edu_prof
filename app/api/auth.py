from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas import APIResponse, LoginSchema, RegisterSchema, TokenResponse
from app.services.auth_service import AuthService


router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", status_code=status.HTTP_201_CREATED, response_model=APIResponse[TokenResponse])
async def register(payload: RegisterSchema, db: Annotated[AsyncSession, Depends(get_db)]) -> APIResponse[TokenResponse]:
    service = AuthService(db)
    user = await service.register(payload)
    return APIResponse(message="Registration successful", data=service.create_access_token(user))


@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginSchema, db: Annotated[AsyncSession, Depends(get_db)]) -> TokenResponse:
    return await AuthService(db).login(payload)
