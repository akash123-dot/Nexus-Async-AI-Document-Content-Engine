from app.config.settings import settings
from jose import jwt, JWTError
from datetime import datetime, timedelta, timezone
import uuid

def create_access_token(
        subject: str,
        expires_delta: timedelta | None = None,
) ->str:
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta( minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    payload = {
        "sub": subject,
        "type": "access_token",
        "exp": expire,
    }

    encoded_jwt = jwt.encode(
        payload,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )
    return encoded_jwt


def create_refresh_token(
        subject: str,
        expires_delta: timedelta | None = None,
) -> tuple[str, str]:
    
    jti = str(uuid.uuid4())

    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta( days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    payload = {
        "sub": subject,
        "type": "refresh",
        "jti": jti,
        "exp": expire,
    }

    encode_token = jwt.encode(
        payload,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )

    return encode_token, jti


def decode_token(token: str) -> dict | None:
    
    try:
        return jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=settings.JWT_ALGORITHM,  
        )
    except JWTError:
        return None