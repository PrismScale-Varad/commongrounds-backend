import os

class Settings:
    OPENAI_API_KEY: str = os.getenv('OPENAI_API_KEY', '')
    SYSTEM_PROMPT: str = os.getenv('SYSTEM_PROMPT', 'You are a chatbot')
    cors_origins = ["*"]  # Update for production
    prefix = "/api"

settings = Settings()
