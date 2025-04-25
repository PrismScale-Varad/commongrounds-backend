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
from services.oauth_service import create_authorization_url, handle_oauth_callback

router = APIRouter(
    prefix="/api/v1/oauth",
    tags=["OAuth"]
)

# Initialize OAuth client
oauth = OAuth()


@router.get("/google/login")
async def google_login_url(request: Request):
    authorization_url = create_authorization_url(oauth, "google")
    return JSONResponse({"authorization_url": authorization_url})


@router.get("/apple/login")
async def apple_login_url(request: Request):
    authorization_url = create_authorization_url(oauth, "apple")
    return JSONResponse({"authorization_url": authorization_url})


@router.get("/github/login")
async def github_login_url(request: Request):
    authorization_url = create_authorization_url(oauth, "github")
    return JSONResponse({"authorization_url": authorization_url})


@router.get("/google/callback")
async def google_callback(request: Request, db: Session = Depends(get_db)):
    return await handle_oauth_callback(oauth, request, db, "google")


@router.get("/apple/callback")
async def apple_callback(request: Request, db: Session = Depends(get_db)):
    return await handle_oauth_callback(oauth, request, db, "apple")


@router.get("/github/callback")
async def github_callback(request: Request, db: Session = Depends(get_db)):
    return await handle_oauth_callback(oauth, request, db, "github")


@router.put("/setup-profile", response_model=OAuthUserResponse)
def setup_profile(profile: OAuthSetupProfile, request: Request, db: Session = Depends(get_db)):
    current_user: User = request.state.user
    if not current_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    update_data = profile.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(current_user, key, value)
    db.commit()
    db.refresh(current_user)
    
    return current_user
