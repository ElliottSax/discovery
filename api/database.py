"""
Database configuration and connection management
"""

from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from contextlib import contextmanager
import os
from typing import Generator
import logging

logger = logging.getLogger(__name__)

# Database URL from environment
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    f"postgresql://{os.getenv('DB_USER', 'quant_user')}:"
    f"{os.getenv('DB_PASSWORD', 'changeme')}@"
    f"{os.getenv('DB_HOST', 'localhost')}:"
    f"{os.getenv('DB_PORT', '5432')}/"
    f"{os.getenv('DB_NAME', 'quant_db')}"
)

# Create SQLAlchemy engine
engine = create_engine(
    DATABASE_URL,
    pool_size=int(os.getenv('DB_POOL_SIZE', 10)),
    max_overflow=int(os.getenv('DB_MAX_OVERFLOW', 20)),
    pool_timeout=int(os.getenv('DB_POOL_TIMEOUT', 30)),
    pool_recycle=int(os.getenv('DB_POOL_RECYCLE', 3600)),
    echo=os.getenv('DB_ECHO', 'false').lower() == 'true'
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for ORM models
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """
    Dependency function for FastAPI to get database session

    Yields:
        Database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def db_session() -> Generator[Session, None, None]:
    """
    Context manager for database sessions

    Yields:
        Database session
    """
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Database error: {e}")
        raise
    finally:
        session.close()


def init_db():
    """Initialize database tables"""
    try:
        # Import all models to register them with Base
        from api import db_models

        # Create all tables
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise


def check_connection() -> bool:
    """
    Check if database connection is working

    Returns:
        True if connection successful, False otherwise
    """
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return False
