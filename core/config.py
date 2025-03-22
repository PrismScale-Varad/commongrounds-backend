import json
import os
import logging
from passlib.context import CryptContext
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):    
    # API Route prefix
    prefix: str="/api/v1"

    # CORS
    cors_origins: list[str] = json.loads(os.getenv("ORIGINS"))

    # Database settings
    database_url: str = os.getenv("DATABASE_URL")

    # JWT
    jwt_expiry_days: int = 180
    ALGORITHM: str = "HS256"

    # Security settings (add more as needed)
    secret_key: str = os.getenv("SECRET")

settings = Settings()

logging.basicConfig(
    level="INFO",
    format="%(asctime)s - [%(levelname)s] - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

logger = logging.getLogger(__name__)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

EXCLUDED_ROUTES = {
    "/",
    "/api/v1/auth/login",
    "/api/v1/auth/reset-password",
    "/api/v1/auth/reset-password/request",
    "/docs",
    "/redoc",
    "/openapi.json",
}

