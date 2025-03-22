from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import jwt
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError
from core.config import settings, logger, pwd_context

def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT token with an expiration time.
    
    :param data: A dictionary with the data to encode in the token.
    :param expires_delta: Optional timedelta for token expiration. 
                          If not provided, defaults to the settings.jwt_expiry_days.
    :return: A JWT token as a string.
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=settings.jwt_expiry_days)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.ALGORITHM)
    logger.info("JWT token created")
    return encoded_jwt

def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Decode a JWT token and return the payload if valid.
    
    :param token: JWT token as a string.
    :return: Decoded token payload as a dict, or None if the token is invalid.
    """
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.ALGORITHM])
        logger.info("JWT token decoded successfully")
        return payload
    except ExpiredSignatureError as e:
        logger.error(f"Token expired: {e}")
    except InvalidTokenError as e:
        logger.error(f"Invalid token: {e}")
    return None

def get_password_hash(password: str) -> str:
    """
    Hash a plain-text password.
    
    :param password: Plain text password.
    :return: Hashed password.
    """
    hashed = pwd_context.hash(password)
    logger.info("Password hashed")
    return hashed

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain-text password against the hashed version.
    
    :param plain_password: Plain text password.
    :param hashed_password: Hashed password.
    :return: True if the password matches, False otherwise.
    """
    is_valid = pwd_context.verify(plain_password, hashed_password)
    if is_valid:
        logger.info("Password verification succeeded")
    else:
        logger.warning("Password verification failed")
    return is_valid
