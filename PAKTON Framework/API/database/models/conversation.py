"""
Description:
    Conversation model for tracking user conversations with thread IDs.

Author: Raptopoulos Petros [petrosrapto@gmail.com]
Date  : 2025/11/23
"""

from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Integer
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..config import Base


class Conversation(Base):
    """Conversation model to track user conversations with thread IDs."""
    
    __tablename__ = "conversations"
    
    thread_id = Column(String(255), primary_key=True, index=True, nullable=False)
    user_email = Column(String(255), ForeignKey("users.email", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(500), nullable=True)  # Optional conversation title
    message_count = Column(Integer, default=0, nullable=False)  # Track number of messages in conversation
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationship to user
    user = relationship("User", back_populates="conversations")
    
    def __repr__(self):
        return f"<Conversation(thread_id='{self.thread_id}', user_email='{self.user_email}')>"
    
    def to_dict(self):
        """Convert conversation to dictionary for API responses."""
        return {
            "thread_id": self.thread_id,
            "user_email": self.user_email,
            "title": self.title,
            "message_count": self.message_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
