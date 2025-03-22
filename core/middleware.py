from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from core.config import EXCLUDED_ROUTES, logger
from core.security import decode_access_token
from models.user import User
from core.database import SessionLocal

class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        # Skip processing for excluded routes
        if request.url.path in EXCLUDED_ROUTES:
            return await call_next(request)

        # Get the Authorization header (expects "Bearer <token>")
        auth_header = request.headers.get("Authorization")
        if auth_header:
            parts = auth_header.split()
            if len(parts) == 2 and parts[0].lower() == "bearer":
                token = parts[1]
                payload = decode_access_token(token)
                if payload and "sub" in payload:
                    db = SessionLocal()
                    try:
                        user = db.query(User).filter(User.email == payload["sub"]).first()
                        if user:
                            # Check if the token matches the active token in the user record
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
                        db.close()
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
