from fastapi import HTTPException
from sqlalchemy.orm import Session
from core.security import create_access_token
from core.config import logger
from models.user import User

def get_or_create_user_with_oauth(email: str, token: dict, user_info: dict, db: Session) -> str:
    """
    Checks if a user exists by email. If not, creates a new user using the provided
    OAuth data. Then generates a JWT token and updates the user's active token.
    
    :param email: User email extracted from the OAuth provider.
    :param token: The token dictionary obtained from the OAuth provider.
    :param user_info: Dictionary containing user info from the provider.
    :param db: SQLAlchemy Session.
    :return: A JWT access token.
    """
    # Check if the user exists
    user = db.query(User).filter(User.email == email).first()
    if not user:
        new_user_data = {
            "email": email,
            # Use the provider's access token as password (it's uncrackable)
            "password": token.get("access_token"),
            "username": user_info.get("name"),
            "profile_pic": user_info.get("picture"),  # Might be None for some providers
            "interests": [],
            "location": None,
        }
        # Import here to avoid circular imports
        from schemas.user import UserCreate
        from services.auth_service import create_user
        user_create = UserCreate(**new_user_data)
        user = create_user(user_create, db)
    
    # Generate a JWT token and update active_token
    access_token = create_access_token(data={"sub": user.email})
    user.active_token = access_token
    db.commit()
    db.refresh(user)
    logger.info(f"User {user.email} authenticated via OAuth, token updated.")
    return access_token
