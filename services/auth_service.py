from datetime import timedelta
from sqlalchemy.orm import Session
from core.config import settings, logger
from core.database import SessionLocal
from models.user import User
from schemas.user import UserCreate, UserUpdate
from core.security import get_password_hash, create_access_token, decode_access_token

def create_user(user_create: UserCreate, db: Session) -> User:
    """
    Create a new user in the database.
    """
    hashed_password = get_password_hash(user_create.password)
    new_user = User(
        email=user_create.email,
        hashed_password=hashed_password,
        username=user_create.username,
        profile_pic=user_create.profile_pic,
        location=user_create.location,
        interests=user_create.interests,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    logger.info(f"Created new user: {new_user.email}")
    return new_user

def update_user(user: User, user_update: UserUpdate, db: Session) -> User:
    """
    Update an existing user in the database.
    Only fields provided in the update schema will be modified.
    """
    update_data = user_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(user, key, value)
    db.commit()
    db.refresh(user)
    logger.info(f"Updated user: {user.email}")
    return user

def generate_password_reset_token(user: User, db: Session, expires_in_hours: int = 1) -> str:
    """
    Generate a password reset token for the user with a short expiration.
    The token is stored in the user's active_token field.
    """
    token = create_access_token(
        data={"sub": user.email, "action": "reset_password"},
        expires_delta=timedelta(hours=expires_in_hours)
    )
    user.active_token = token
    db.commit()
    logger.info(f"Generated password reset token for user: {user.email}")
    return token

def reset_password(token: str, new_password: str, db: Session) -> bool:
    """
    Reset a user's password given a valid reset token.
    The token is decoded to obtain the user's email, and the token in the db must match.
    """
    payload = decode_access_token(token)
    if not payload or payload.get("action") != "reset_password":
        logger.error("Invalid password reset token payload.")
        return False

    user_email = payload.get("sub")
    if not user_email:
        logger.error("Token payload does not contain a user identifier.")
        return False

    user = db.query(User).filter(User.email == user_email).first()
    if not user:
        logger.error(f"User not found for email: {user_email}")
        return False

    # Ensure the token matches the one stored for the user
    if user.active_token != token:
        logger.error("The provided token does not match the stored token.")
        return False

    # Update the password and clear the active token
    user.hashed_password = get_password_hash(new_password)
    user.active_token = None
    db.commit()
    logger.info(f"Password reset successful for user: {user.email}")
    return True
