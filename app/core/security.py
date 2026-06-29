"""Security Utilities — JWT, HMAC, Encryption"""
import hmac
import hashlib
import time
from datetime import datetime, timedelta
from typing import Dict, Optional

from jose import jwt, JWTError
from app.core.config import settings


def create_jwt_token(data: Dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(hours=settings.JWT_EXPIRATION_HOURS))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY.get_secret_value(), algorithm=settings.JWT_ALGORITHM)


def verify_jwt_token(token: str) -> Optional[Dict]:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY.get_secret_value(), algorithms=[settings.JWT_ALGORITHM])
        return payload
    except JWTError:
        return None


def verify_hmac_signature(payload: bytes, signature: str, secret: str, timestamp: Optional[str] = None) -> bool:
    """Verify HMAC-SHA256 signature with optional anti-replay timestamp"""
    if timestamp:
        ts = int(timestamp)
        now = int(time.time())
        if abs(now - ts) > 300:  # 5 minutes window
            return False

    expected = hmac.new(
        secret.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature)


def generate_kaybic_signature(payload: bytes, timestamp: str) -> str:
    """Generate HMAC signature for Kaybic requests"""
    secret = settings.KAYBIC_WEBHOOK_SECRET.get_secret_value()
    message = f"{timestamp}.{payload.decode()}"
    return hmac.new(secret.encode(), message.encode(), hashlib.sha256).hexdigest()
