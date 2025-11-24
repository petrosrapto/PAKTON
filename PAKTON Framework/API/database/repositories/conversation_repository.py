"""
Description:
    Conversation repository for database operations on Conversation model.

Author: Raptopoulos Petros [petrosrapto@gmail.com]
Date  : 2025/11/23
"""

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from typing import List, Optional
from datetime import datetime
import sys
import os

# Add parent directories to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from logger import logger
from database.models import Conversation
from database.repositories.user_repository import UserRepository


class ConversationRepository:
    """Repository for Conversation database operations."""
    
    @staticmethod
    def create(
        db: Session,
        thread_id: str,
        user_email: str,
        title: Optional[str] = None
    ) -> Conversation:
        """
        Create a new conversation.
        
        Args:
            db: Database session
            thread_id: Unique thread identifier
            user_email: User's email address
            title: Optional conversation title
            
        Returns:
            Created Conversation object
        """
        try:
            # Ensure user exists
            UserRepository.get_or_create(db, user_email)
            
            conversation = Conversation(
                thread_id=thread_id,
                user_email=user_email,
                title=title
            )
            db.add(conversation)
            db.commit()
            db.refresh(conversation)
            logger.info(f"Created conversation {thread_id} for user {user_email}")
            return conversation
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Error creating conversation: {str(e)}")
            raise
    
    @staticmethod
    def get_by_thread_id(db: Session, thread_id: str) -> Optional[Conversation]:
        """
        Get conversation by thread ID.
        
        Args:
            db: Database session
            thread_id: Thread identifier
            
        Returns:
            Conversation object or None if not found
        """
        return db.query(Conversation).filter(Conversation.thread_id == thread_id).first()
    
    @staticmethod
    def get_by_user_email(
        db: Session,
        user_email: str,
        limit: Optional[int] = None,
        offset: int = 0
    ) -> List[Conversation]:
        """
        Get all conversations for a specific user.
        
        Args:
            db: Database session
            user_email: User's email address
            limit: Optional limit on number of results
            offset: Number of records to skip (for pagination)
            
        Returns:
            List of Conversation objects ordered by updated_at descending
        """
        query = db.query(Conversation).filter(
            Conversation.user_email == user_email
        ).order_by(Conversation.updated_at.desc())
        
        if limit:
            query = query.limit(limit)
        
        if offset:
            query = query.offset(offset)
            
        return query.all()
    
    @staticmethod
    def update(
        db: Session,
        thread_id: str,
        title: Optional[str] = None
    ) -> Optional[Conversation]:
        """
        Update an existing conversation.
        
        Args:
            db: Database session
            thread_id: Thread identifier
            title: Optional new title
            
        Returns:
            Updated Conversation object or None if not found
        """
        try:
            conversation = ConversationRepository.get_by_thread_id(db, thread_id)
            if not conversation:
                return None
            
            if title is not None:
                conversation.title = title
            
            conversation.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(conversation)
            logger.info(f"Updated conversation {thread_id}")
            return conversation
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Error updating conversation: {str(e)}")
            raise
    
    @staticmethod
    def get_or_create(
        db: Session,
        thread_id: str,
        user_email: str,
        title: Optional[str] = None
    ) -> Conversation:
        """
        Get existing conversation or create a new one if it doesn't exist.
        
        Args:
            db: Database session
            thread_id: Unique thread identifier
            user_email: User's email address
            title: Optional conversation title
            
        Returns:
            Conversation object
        """
        conversation = ConversationRepository.get_by_thread_id(db, thread_id)
        if not conversation:
            conversation = ConversationRepository.create(
                db, thread_id, user_email, title
            )
        return conversation
    
    @staticmethod
    def delete(db: Session, thread_id: str) -> bool:
        """
        Delete a conversation by thread ID.
        
        Args:
            db: Database session
            thread_id: Thread identifier
            
        Returns:
            True if deleted, False if not found
        """
        try:
            conversation = ConversationRepository.get_by_thread_id(db, thread_id)
            if not conversation:
                return False
            
            db.delete(conversation)
            db.commit()
            logger.info(f"Deleted conversation {thread_id}")
            return True
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Error deleting conversation: {str(e)}")
            raise
    
    @staticmethod
    def count_by_user(db: Session, user_email: str) -> int:
        """
        Count total conversations for a user.
        
        Args:
            db: Database session
            user_email: User's email address
            
        Returns:
            Number of conversations
        """
        return db.query(Conversation).filter(
            Conversation.user_email == user_email
        ).count()
    
    @staticmethod
    def count_human_and_ai_messages(messages) -> int:
        """
        Count only human and AI messages, excluding tool calls.
        
        Args:
            messages: List of message objects
            
        Returns:
            Number of human and AI messages
        """
        if not messages:
            return 0
        return sum(1 for msg in messages if hasattr(msg, 'type') and msg.type in ['human', 'ai'])
    
    @staticmethod
    def update_message_count_and_timestamp(
        db: Session,
        thread_id: str,
        message_count: int
    ) -> Optional[Conversation]:
        """
        Update message count and updated_at timestamp for a conversation.
        
        Args:
            db: Database session
            thread_id: Thread identifier
            message_count: New message count
            
        Returns:
            Updated Conversation object or None if not found
        """
        try:
            conversation = ConversationRepository.get_by_thread_id(db, thread_id)
            if not conversation:
                return None
            
            conversation.message_count = message_count
            conversation.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(conversation)
            logger.info(f"Updated message count to {message_count} for conversation {thread_id}")
            return conversation
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Error updating conversation message count: {str(e)}")
            raise
