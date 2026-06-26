from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import HTMLResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models import User
from app.schemas import ROICalculationRequest, ROICalculationResponse
from app.services.auth_service import AuthService
from app.services.roi_service import ROIService


router = APIRouter(prefix="/roi", tags=["ROI"])
optional_bearer = HTTPBearer(auto_error=False)


async def get_optional_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(optional_bearer)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User | None:
    if credentials is None:
        return None
    return await AuthService(db).get_current_user(credentials.credentials)


@router.post("/calculate", response_model=ROICalculationResponse | None)
async def calculate_roi(
    payload: ROICalculationRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User | None, Depends(get_optional_user)],
    request: Request,
) -> ROICalculationResponse | HTMLResponse:
    result = await ROIService(db).calculate_roi(payload, user)
    if request.headers.get("HX-Request") == "true":
        template = request.app.state.templates
        return template.TemplateResponse(
            "partials/roi_results.html",
            {"request": request, "result": result},
        )
    return result


@router.get("/history", response_model=list[ROICalculationResponse])
async def roi_history(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> list[ROICalculationResponse]:
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user")
    return await ROIService(db).get_history(user)
