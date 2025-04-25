import json
import os
import logging
from passlib.context import CryptContext
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Settings(BaseSettings):
    """
    Configuration settings loaded from environment variables.
    Contains API prefixes, CORS settings, database URL, JWT settings, OAuth client settings, and security keys.
    """
    # API Route prefix
    prefix: str="/api/v1"

    # CORS origins loaded from environment variable as JSON list
    cors_origins: list[str] = json.loads(os.getenv("ORIGINS"))

    # Database connection URL
    database_url: str = "localhost:5432/mydb"

    # JWT configuration
    jwt_expiry_days: int = 180
    ALGORITHM: str = "HS256"

    # OAuth Settings for Google
    GOOGLE_CLIENT_ID: str = os.getenv("GOOGLE_CLIENT_ID", "")
    GOOGLE_CLIENT_SECRET: str = os.getenv("GOOGLE_CLIENT_SECRET", "")
    GOOGLE_REDIRECT_URI: str = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8000/api/v1/oauth/google/callback")

    # OAuth Settings for Apple
    APPLE_CLIENT_ID: str = os.getenv("APPLE_CLIENT_ID", "")
    APPLE_TEAM_ID: str = os.getenv("APPLE_TEAM_ID", "")
    APPLE_KEY_ID: str = os.getenv("APPLE_KEY_ID", "")
    APPLE_PRIVATE_KEY: str = os.getenv("APPLE_PRIVATE_KEY", "")
    APPLE_REDIRECT_URI: str = os.getenv("APPLE_REDIRECT_URI", "http://localhost:8000/api/v1/oauth/apple/callback")

    # Security settings (add more as needed)
    secret_key: str = os.getenv("SECRET")

# Instantiate global settings object
settings = Settings()

# Configure logging for the application
logging.basicConfig(
    level="INFO",
    format="%(asctime)s - [%(levelname)s] - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

# Logger instance for this module
logger = logging.getLogger(__name__)

# Password hashing context using bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Set of API routes that do not require authentication
EXCLUDED_ROUTES = {
    "/",
    "/api/v1/auth/login",
    "/api/v1/auth/reset-password",
    "/api/v1/auth/reset-password/request",
    "/docs",
    "/redoc",
    "/openapi.json",
}

# OpenAI API key from environment
OPENAI_API_KEY: str = os.getenv('OPENAI_API_KEY', '')
