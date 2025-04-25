from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from core.config import EXCLUDED_ROUTES, logger
from core.security import decode_access_token
from models.user import User
from core.database import SessionLocal

class AuthMiddleware(BaseHTTPMiddleware):
    """
    Middleware to handle authentication via Bearer tokens in the Authorization header.
    It validates JWT tokens and attaches the authenticated user to the request state.
    """
    async def dispatch(self, request: Request, call_next) -> Response:
        # Skip processing for excluded routes
        if request.url.path in EXCLUDED_ROUTES:
            return await call_next(request)

        authorization_header = request.headers.get("Authorization")
        if authorization_header:
            parts = authorization_header.split()
            if len(parts) == 2 and parts[0].lower() == "bearer":
                token = parts[1]
                token_payload = decode_access_token(token)
                if token_payload and "sub" in token_payload:
                    db_session = SessionLocal()
                    try:
                        user = db_session.query(User).filter(User.email == token_payload["sub"]).first()
                        if user:
                            if user.active_token != token:
                                logger.warning("Active token mismatch. Session expired.")
                                return JSONResponse(
                                    status_code=401,
                                    content={"detail": "Session expired or invalid token."}
                                )
                            request.state.user = user
                            logger.info(f"Authenticated user: {user.email}")
                        else:
                            logger.warning("User not found for token payload")
                            request.state.user = None
                    except Exception as e:
                        logger.error(f"Error retrieving user: {e}")
                        request.state.user = None
                    finally:
                        db_session.close()
                else:
                    logger.warning("Token payload invalid or missing 'sub' claim")
                    request.state.user = None
            else:
                logger.warning("Authorization header is malformed")
                request.state.user = None
        else:
            request.state.user = None

        response = await call_next(request)
        return response
