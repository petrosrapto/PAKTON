"""
Description:
    User model for storing user information.

Author: Raptopoulos Petros [petrosrapto@gmail.com]
Date  : 2025/11/23
"""

from sqlalchemy import Column, String, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..config import Base


class User(Base):
    """User model to store user information."""
    
    __tablename__ = "users"
    
    email = Column(String(255), primary_key=True, index=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationship to conversations
    conversations = relationship("Conversation", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User(email='{self.email}')>"
