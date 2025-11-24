"""
Description:
    User repository for database operations on User model.

Author: Raptopoulos Petros [petrosrapto@gmail.com]
Date  : 2025/11/23
"""

from sqlalchemy.orm import Session
from typing import Optional
import sys
import os

# Add parent directories to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from logger import logger
from database.models import User


class UserRepository:
    """Repository for User database operations."""
    
    @staticmethod
    def get_or_create(db: Session, email: str) -> User:
        """
        Get existing user or create a new one if it doesn't exist.
        
        Args:
            db: Database session
            email: User email address
            
        Returns:
            User object
        """
        user = db.query(User).filter(User.email == email).first()
        if not user:
            user = User(email=email)
            db.add(user)
            db.commit()
            db.refresh(user)
            logger.info(f"Created new user: {email}")
        return user
    
    @staticmethod
    def get_by_email(db: Session, email: str) -> Optional[User]:
        """
        Get user by email address.
        
        Args:
            db: Database session
            email: User email address
            
        Returns:
            User object or None if not found
        """
        return db.query(User).filter(User.email == email).first()
