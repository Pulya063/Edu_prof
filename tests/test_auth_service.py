import pytest
from app.services.auth_service import AuthService
from app.schemas import RegisterSchema, LoginSchema
from app.core.exceptions import AppError

def test_register_user(db_session):
    """Перевірка реєстрації нового користувача."""
    service = AuthService(db_session)
    payload = RegisterSchema(
        email="test1@example.com",
        password="StrongPassword123",
        confirm_password="StrongPassword123"
    )
    
    user = service.register(payload)
    
    assert user.id is not None
    assert user.email == "test1@example.com"
    # Пароль має бути захешованим (не в чистому вигляді)
    assert user.password_hash != "StrongPassword123"

def test_register_duplicate_email(db_session):
    """Перевірка помилки при реєстрації з існуючим email."""
    service = AuthService(db_session)
    payload = RegisterSchema(
        email="duplicate@example.com",
        password="StrongPassword123",
        confirm_password="StrongPassword123"
    )
    
    service.register(payload)
    
    with pytest.raises(AppError) as exc:
        service.register(payload)
        
    assert exc.value.status_code == 409
    assert "вже існує" in str(exc.value.message).lower()

def test_login_success(db_session):
    """Перевірка успішного входу."""
    service = AuthService(db_session)
    
    # Реєструємо
    service.register(RegisterSchema(
        email="login@example.com",
        password="ValidPassword1",
        confirm_password="ValidPassword1"
    ))
    
    # Входимо
    login_payload = LoginSchema(email="login@example.com", password="ValidPassword1")
    token_response = service.login(login_payload)
    
    assert token_response.access_token is not None
    assert token_response.token_type == "bearer"

def test_login_invalid_password(db_session):
    """Перевірка невірного пароля."""
    service = AuthService(db_session)
    
    service.register(RegisterSchema(
        email="wrongpass@example.com",
        password="ValidPassword1",
        confirm_password="ValidPassword1"
    ))
    
    login_payload = LoginSchema(email="wrongpass@example.com", password="WrongPassword!")
    
    with pytest.raises(AppError) as exc:
        service.login(login_payload)
        
    assert exc.value.status_code == 401
    assert "invalid email or password" in str(exc.value.message).lower()
