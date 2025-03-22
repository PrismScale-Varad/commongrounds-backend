from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from core.database import get_db
from models.user import User
from schemas.user import PasswordReset, UserCreate, UserResponse, TokenResponse, LoginCredentials
from services.auth_service import create_user, generate_password_reset_token, reset_password
from core.security import verify_password, create_access_token

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)

@router.post("/signup", response_model=TokenResponse)
def signup(user_create: UserCreate, db: Session = Depends(get_db)):
    """
    Create a new user account.
    Generates an access token for the new user and sets it as the active token.
    """
    existing_user = db.query(User).filter(User.email == user_create.email).first()
    if existing_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
    
    # Create the new user record
    user = create_user(user_create, db)
    
    # Generate an access token and set it as the active token
    access_token = create_access_token(data={"sub": user.email})
    user.active_token = access_token
    db.commit()
    db.refresh(user)
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/login", response_model=TokenResponse)
def login(credentials: LoginCredentials, db: Session = Depends(get_db)):
    """
    Authenticate a user and return an access token.
    Sets the active token on the user record.
    """
    user = db.query(User).filter(User.email == credentials.email).first()
    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    
    access_token = create_access_token(data={"sub": user.email})
    user.active_token = access_token
    db.commit()
    db.refresh(user)
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=UserResponse)
def read_current_user(request: Request):
    """
    Return the current authenticated user.
    Expects that the authentication middleware has stored the user in request.state.user.
    """
    current_user: User = request.state.user
    if not current_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    return current_user

@router.post("/logout")
def logout(request: Request, db: Session = Depends(get_db)):
    """
    Log out the current user by clearing the active token.
    Assumes that the current user is stored in request.state.user by the authentication middleware.
    """
    current_user: User = request.state.user
    if not current_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    
    # Re-query the user using the current session
    user_in_db = db.query(User).filter(User.id == current_user.id).first()
    if not user_in_db:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    user_in_db.active_token = None
    db.commit()
    return {"message": "Logged out successfully"}

@router.post("/reset-password/request")
def request_password_reset(email: EmailStr, db: Session = Depends(get_db)):
    """
    Request a password reset token.
    In a real application, this token would be emailed to the user.
    """
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    token = generate_password_reset_token(user, db)
    # For demonstration, return the token directly.
    return {"message": "Password reset token generated", "reset_token": token}

@router.post("/reset-password")
def reset_password_endpoint(token: str, reset_data: PasswordReset, db: Session = Depends(get_db)):
    """
    Reset the user's password.
    Requires the reset token and new password data.
    """
    success = reset_password(token, reset_data.password, db)
    if not success:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Password reset failed")
    return {"message": "Password reset successful"}
