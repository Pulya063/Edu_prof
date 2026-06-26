from datetime import UTC, datetime, timedelta
from typing import Any

from dns.dnssecalgs import algorithms
from jose import JWTError, jwt
from passlib.context import CryptContext
import os
from dotenv import load_dotenv

load_dotenv()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

secret_key = os.getenv("SECRET_KEY")
access_token_expire_minutes = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES"))
algorithm = os.getenv("ALGORITHM")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, password_hash: str) -> bool:
    return pwd_context.verify(plain_password, password_hash)


def create_jwt_access_token(subject: str, expires_delta: timedelta | None = None) -> str:
    expire = datetime.now(UTC) + (
        expires_delta if expires_delta is not None else timedelta(minutes=int(access_token_expire_minutes))
    )
    payload: dict[str, Any] = {"sub": subject, "exp": expire}
    return jwt.encode(payload, secret_key, algorithm=algorithm)


def decode_access_token(token: str) -> str:
    try:
        payload = jwt.decode(token, secret_key, algorithms=[algorithm])
        subject = payload.get("sub")
    except JWTError as exc:
        raise ValueError("Invalid access token") from exc
    if not isinstance(subject, str) or not subject:
        raise ValueError("Invalid access token subject")
    return subject
