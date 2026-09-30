import pytest
from unittest.mock import MagicMock, patch
from app.services.auth_service import AuthService
from app.schemas import RegisterSchema, LoginSchema
from app.core.exceptions import AppError
from app.core.security import create_jwt_access_token
from app.schemas import PasswordResetSchema


@pytest.fixture
def fake_redis():
    store = {}
    client = MagicMock()
    client.setex.side_effect = lambda key, ttl, value: store.__setitem__(key, value)
    client.get.side_effect = store.get
    client.getdel.side_effect = lambda key: store.pop(key, None)
    client.delete.side_effect = lambda key: store.pop(key, None)
    with patch("app.core.redis_client.get_redis", return_value=client):
        yield store

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

def test_login_success(db_session, fake_redis):
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


def test_access_token_cannot_be_used_as_password_reset_token(db_session, fake_redis):
    """Access tokens must not be accepted by the password reset flow."""
    service = AuthService(db_session)
    user = service.register(RegisterSchema(
        email="reset-purpose@example.com",
        password="ValidPassword1",
        confirm_password="ValidPassword1",
    ))
    access_token = create_jwt_access_token(subject=str(user.id))

    with pytest.raises(AppError) as exc:
        service.reset_password(access_token, "NewPassword2")

    assert exc.value.status_code == 400


def test_password_reset_schema_enforces_password_strength():
    with pytest.raises(ValueError):
        PasswordResetSchema(code="token", new_password="weakpassword")


def test_password_reset_token_is_single_use(db_session, fake_redis):
    service = AuthService(db_session)
    service.register(RegisterSchema(
        email="single-use@example.com",
        password="ValidPassword1",
        confirm_password="ValidPassword1",
    ))

    with patch("app.tasks.email_tasks.send_verification_email.delay") as send_email:
        service.request_password_reset("single-use@example.com")
        token = send_email.call_args.args[1]

    service.reset_password(token, "NewPassword2")
    with pytest.raises(AppError) as exc:
        service.reset_password(token, "AnotherPassword3")
    assert exc.value.status_code == 400
