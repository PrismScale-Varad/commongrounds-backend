from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from core.config import settings, logger
from contextlib import contextmanager

# Initialize the database connection
engine = create_engine(settings.database_url, echo=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    """
    Dependency generator that yields a SQLAlchemy SessionLocal instance.
    Be sure to close the session after the request is finished.
    """
    logger.info("Opening new database session")
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
        logger.info("Database session closed")

@contextmanager
def get_db_context():
    """
    Dependency to get a database session.

    This context manager yields a session that should be used within a
    with-statement block to ensure proper opening and closing.
    """
    logger.info("Opening new database session (context manager)")
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
        logger.info("Database session closed (context manager)")

def init_db():
    """
    Initializes the database by creating all tables.
    
    This function imports your SQLAlchemy models to ensure they are
    registered with the Base metadata and then creates all tables
    according to the metadata.

    This should be called during application startup.
    """
    logger.info("Initializing database")
    # Import models to register them on the Base metadata
    from models import user, oauth, chat  # Add additional model imports if necessary
    Base.metadata.create_all(bind=engine)
    logger.info("Database initialized")
