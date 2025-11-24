"""
Description:
    Database configuration and session management using SQLAlchemy.
    Provides database engine, session factory, and base class for models.

Author: Raptopoulos Petros [petrosrapto@gmail.com]
Date  : 2025/11/23
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager
import os
import sys

# Add parent directory to path for logger import
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from logger import logger

# Get database URL from environment
DATABASE_URL = os.getenv("DATABASE_URL")

# Create SQLAlchemy engine
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,  # Verify connections before using them
    pool_size=10,  # Maximum number of permanent connections
    max_overflow=20,  # Maximum number of temporary connections
    echo=False,  # Set to True for SQL query logging (development only)
)

# Create SessionLocal class for database sessions
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create Base class for declarative models
Base = declarative_base()


@contextmanager
def get_db_session():
    """
    Context manager for database sessions.
    Ensures proper session cleanup and error handling.
    
    Usage:
        with get_db_session() as db:
            # Use db session
            result = db.query(Model).all()
    """
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Database session error: {str(e)}")
        raise
    finally:
        session.close()


def get_db():
    """
    Dependency function for FastAPI to get database sessions.
    
    Usage in FastAPI endpoint:
        @app.get("/items")
        def read_items(db: Session = Depends(get_db)):
            return db.query(Item).all()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """
    Initialize database by creating all tables.
    Should only be used in development or for initial setup.
    In production, use Alembic migrations instead.
    """
    from . import models  # Import models to ensure they're registered
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created successfully")
