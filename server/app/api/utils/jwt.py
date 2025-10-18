from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import jwt
from enum import Enum
from app.config import settings


class TokenType(str, Enum):
    """Token type enumeration"""
    ACCESS = "access"
    REFRESH = "refresh"


def create_token(
    data: Dict[str, Any],
    token_type: TokenType = TokenType.ACCESS,
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create a JWT token (access or refresh)
    
    Args:
        data: Payload data to encode
        token_type: "access" or "refresh"
        expires_delta: Optional custom expiration time
    """
    to_encode = data.copy()
    
    # Set expiration based on token type or custom delta
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    elif token_type == "access":
        expire = datetime.utcnow() + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    else:  # refresh
        expire = datetime.utcnow() + timedelta(days=7)
    
    # Add metadata to token
    to_encode.update({
        "exp": expire,
        "type": token_type,
        "iat": datetime.utcnow()  # Issued at time
    })
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )
    return encoded_jwt

def verify_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Verify and decode a JWT token
    """
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.JWTError:
        return None