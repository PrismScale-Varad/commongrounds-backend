from fastapi import APIRouter, Depends, Request, HTTPException, status
from starlette.responses import JSONResponse
from sqlalchemy.orm import Session
import jwt

from core.config import settings, logger
from core.database import get_db
from authlib.integrations.starlette_client import OAuth

from schemas.oauth import OAuthSetupProfile, OAuthUserResponse
from models.user import User
from utils.oauth import get_or_create_user_with_oauth

router = APIRouter(
    prefix="/api/v1/oauth",
    tags=["OAuth"]
)

# Initialize OAuth client
oauth = OAuth()
oauth.register(
    name="google",
    client_id=settings.GOOGLE_CLIENT_ID,
    client_secret=settings.GOOGLE_CLIENT_SECRET,
    access_token_url="https://oauth2.googleapis.com/token",
    authorize_url="https://accounts.google.com/o/oauth2/v2/auth",
    api_base_url="https://www.googleapis.com/oauth2/v3/",
    client_kwargs={"scope": "openid email profile"},
)

# Similarly, register Apple if needed
oauth.register(
    name="apple",
    client_id=settings.APPLE_CLIENT_ID,
    client_secret=settings.APPLE_PRIVATE_KEY,
    access_token_url="https://appleid.apple.com/auth/token",
    authorize_url="https://appleid.apple.com/auth/authorize",
    api_base_url="https://appleid.apple.com",
    client_kwargs={"scope": "name email"},
)

@router.get("/google/login")
async def google_login_url(request: Request):
    """
    Returns the Google OAuth authorization URL.
    You can either redirect the user or send the URL to the frontend.
    """
    redirect_uri = settings.GOOGLE_REDIRECT_URI
    # Generate the authorization URL and state
    authorization_url, state = oauth.google.create_authorization_url(redirect_uri)
    # Optionally store 'state' in session for later verification.
    logger.info(f"Generated Google auth URL: {authorization_url}")
    return JSONResponse({"authorization_url": authorization_url})

@router.get("/apple/login")
async def apple_login_url(request: Request):
    """
    Returns the Apple OAuth authorization URL.
    """
    redirect_uri = settings.APPLE_REDIRECT_URI
    authorization_url, state = oauth.apple.create_authorization_url(redirect_uri)
    logger.info(f"Generated Apple auth URL: {authorization_url}")
    return JSONResponse({"authorization_url": authorization_url})

@router.get("/google/callback")
async def google_callback(request: Request, db: Session = Depends(get_db)):
    """
    Handles Google OAuth callback.
    Exchanges the authorization code for tokens and user info,
    then creates or retrieves the user, generates a JWT token,
    and returns it.
    """
    try:
        token = await oauth.google.authorize_access_token(request)
    except Exception as e:
        logger.error(f"Google auth error: {e}")
        raise HTTPException(status_code=400, detail="Google authorization failed")
    
    try:
        user_info = await oauth.google.parse_id_token(request, token)
    except Exception as e:
        logger.error(f"Failed to parse Google ID token: {e}")
        raise HTTPException(status_code=400, detail="Failed to retrieve user info from Google")
    
    email = user_info.get("email")
    if not email:
        raise HTTPException(status_code=400, detail="Google account did not return an email")
    
    access_token = get_or_create_user_with_oauth(email, token, user_info, db)
    return JSONResponse({"access_token": access_token, "token_type": "bearer"})

@router.get("/apple/callback")
async def apple_callback(request: Request, db: Session = Depends(get_db)):
    """
    Handles Apple OAuth callback.
    Exchanges the authorization code for tokens and user info,
    then creates or retrieves the user, generates a JWT token,
    and returns it.
    """
    try:
        token = await oauth.apple.authorize_access_token(request)
    except Exception as e:
        logger.error(f"Apple auth error: {e}")
        raise HTTPException(status_code=400, detail="Apple authorization failed")
    
    id_token = token.get("id_token")
    if not id_token:
        raise HTTPException(status_code=400, detail="Apple did not return an id_token")
    
    try:
        # WARNING: For production, validate the signature using Apple's public keys.
        user_info = jwt.decode(id_token, options={"verify_signature": False})
    except Exception as e:
        logger.error(f"Error decoding Apple id_token: {e}")
        raise HTTPException(status_code=400, detail="Failed to decode Apple id_token")
    
    email = user_info.get("email")
    if not email:
        raise HTTPException(status_code=400, detail="Apple account did not return an email")
    
    access_token = get_or_create_user_with_oauth(email, token, user_info, db)
    return JSONResponse({"access_token": access_token, "token_type": "bearer"})

@router.put("/setup-profile", response_model=OAuthUserResponse)
def setup_profile(profile: OAuthSetupProfile, request: Request, db: Session = Depends(get_db)):
    """
    Setup or update additional profile data for OAuth users.
    Expects that the current authenticated user is attached to request.state.user.
    """
    current_user: User = request.state.user
    if not current_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    
    update_data = profile.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(current_user, key, value)
    db.commit()
    db.refresh(current_user)
    
    return current_user
