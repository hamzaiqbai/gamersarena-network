"""
Database Configuration and Session Management
"""
from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from .config import settings

# Create database engine with SSL support for DigitalOcean
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,  # Enable connection health checks
    pool_size=5,  # Maximum number of connections
    max_overflow=10,  # Additional connections when pool is exhausted
    echo=settings.DEBUG,  # Log SQL queries in debug mode
    connect_args={
        "sslmode": "require"
    } if "digitalocean" in settings.DATABASE_URL else {}
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()


def get_db():
    """
    Dependency that provides a database session.
    Yields a session and ensures it's closed after use.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """
    Initialize database tables.
    Call this on application startup.
    """
    from .models import user, wallet, tournament, transaction, registration
    Base.metadata.create_all(bind=engine)
