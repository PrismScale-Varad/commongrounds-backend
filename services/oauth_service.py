from fastapi import HTTPException
from starlette.responses import JSONResponse
from sqlalchemy.orm import Session
import jwt

from core.config import settings, logger
from authlib.integrations.starlette_client import OAuth

from utils.oauth import get_or_create_user_with_oauth

# Initialize OAuth client
oauth = OAuth()


def create_authorization_url(provider_name: str) -> str:
    """
    Helper function to create the authorization URL for a given OAuth provider.
    """
    redirect_uri_map = {
        "google": settings.GOOGLE_REDIRECT_URI,
        "apple": settings.APPLE_REDIRECT_URI,
        "github": settings.GITHUB_REDIRECT_URI,
    }
    redirect_uri = redirect_uri_map.get(provider_name)
    if not redirect_uri:
        logger.error(f"Redirect URI not found for provider: {provider_name}")
        raise HTTPException(status_code=400, detail="Invalid OAuth provider")

    authorization_url, state = getattr(oauth, provider_name).create_authorization_url(redirect_uri)
    logger.info(f"Generated {provider_name.capitalize()} auth URL: {authorization_url}")
    return authorization_url


async def handle_oauth_callback(
    request, db: Session, provider_name: str
) -> JSONResponse:
    try:
        oauth_token = await getattr(oauth, provider_name).authorize_access_token(request)
    except Exception as e:
        logger.error(f"{provider_name.capitalize()} auth error: {e}")
        raise HTTPException(status_code=400, detail=f"{provider_name.capitalize()} authorization failed")

    if provider_name == "apple":
        id_token = oauth_token.get("id_token")
        if not id_token:
            raise HTTPException(status_code=400, detail="Apple did not return an id_token")
        try:
            oauth_user_info = jwt.decode(id_token, options={"verify_signature": False})
        except Exception as e:
            logger.error(f"Error decoding Apple id_token: {e}")
            raise HTTPException(status_code=400, detail="Failed to decode Apple id_token")
    elif provider_name == "github":
        user_resp = await oauth.github.get("user")
        emails_resp = await oauth.github.get("user/emails")
        emails_json = emails_resp.json()
        email = emails_json[0]["email"] if emails_json and len(emails_json) > 0 else None
        oauth_user_info = user_resp.json()
        oauth_user_info["email"] = email
        if not email:
            raise HTTPException(status_code=400, detail="GitHub account did not return an email")
    else:
        try:
            oauth_user_info = await getattr(oauth, provider_name).parse_id_token(request, oauth_token)
        except Exception as e:
            logger.error(f"Failed to parse {provider_name.capitalize()} ID token: {e}")
            raise HTTPException(status_code=400, detail=f"Failed to retrieve user info from {provider_name.capitalize()}")

    email = oauth_user_info.get("email")
    if not email:
        raise HTTPException(status_code=400, detail=f"{provider_name.capitalize()} account did not return an email")

    access_token = get_or_create_user_with_oauth(email, oauth_token, oauth_user_info, db)
    return JSONResponse({"access_token": access_token, "token_type": "bearer"})
