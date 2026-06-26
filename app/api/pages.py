from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse


router = APIRouter(tags=["Pages"])


@router.get("/", response_class=HTMLResponse)
async def home(request: Request) -> HTMLResponse:
    return request.app.state.templates.TemplateResponse("home.html", {"request": request})


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request) -> HTMLResponse:
    return request.app.state.templates.TemplateResponse("login.html", {"request": request})


@router.get("/register", response_class=HTMLResponse)
async def register_page(request: Request) -> HTMLResponse:
    return request.app.state.templates.TemplateResponse("register.html", {"request": request})


@router.get("/calculator", response_class=HTMLResponse)
async def calculator_page(request: Request) -> HTMLResponse:
    return request.app.state.templates.TemplateResponse("calculator.html", {"request": request})
