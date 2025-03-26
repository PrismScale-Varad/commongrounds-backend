from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from core.config import settings
from core.config import logger
from core.middleware import AuthMiddleware
from core.database import init_db
from routes import auth, chat

init_db()

app = FastAPI(
    title="Commongrounds Backend",
    description="Backend for the Commongrounds MVP",
    version="0.1.0",
)

# Setup CORS middleware (adjust origins as needed)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,  # Change this for production use
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(AuthMiddleware)

# Routes
app.include_router(auth.router, prefix=settings.prefix)
app.include_router(chat.router, prefix=settings.prefix)

# Health check endpoint using HEAD method
@app.head("/")
def health_check():
    return None

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000)
