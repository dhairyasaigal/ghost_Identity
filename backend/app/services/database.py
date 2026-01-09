"""
Database service for connection and session management
Provides centralized database operations and transaction handling
"""
from app import db
from sqlalchemy.exc import SQLAlchemyError
from contextlib import contextmanager
from typing import Any, Optional
import logging

logger = logging.getLogger(__name__)

class DatabaseService:
    """Service for managing database connections and transactions"""
    
    @staticmethod
    @contextmanager
    def transaction():
        """
        Context manager for database transactions with automatic rollback on error
        
        Usage:
            with DatabaseService.transaction():
                # Database operations here
                db.session.add(model_instance)
                # Automatically commits on success, rolls back on exception
        """
        try:
            yield db.session
            db.session.commit()
        except SQLAlchemyError as e:
            db.session.rollback()
            logger.error(f"Database transaction failed: {str(e)}")
            raise
        except Exception as e:
            db.session.rollback()
            logger.error(f"Unexpected error in database transaction: {str(e)}")
            raise
    
    @staticmethod
    def safe_add(model_instance: Any) -> bool:
        """
        Safely add a model instance to the database
        
        Args:
            model_instance: SQLAlchemy model instance to add
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with DatabaseService.transaction():
                db.session.add(model_instance)
            return True
        except Exception as e:
            logger.error(f"Failed to add model instance: {str(e)}")
            return False
    
    @staticmethod
    def safe_update(model_instance: Any, **kwargs) -> bool:
        """
        Safely update a model instance
        
        Args:
            model_instance: SQLAlchemy model instance to update
            **kwargs: Fields to update
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with DatabaseService.transaction():
                for key, value in kwargs.items():
                    if hasattr(model_instance, key):
                        setattr(model_instance, key, value)
            return True
        except Exception as e:
            logger.error(f"Failed to update model instance: {str(e)}")
            return False
    
    @staticmethod
    def safe_delete(model_instance: Any) -> bool:
        """
        Safely delete a model instance
        
        Args:
            model_instance: SQLAlchemy model instance to delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with DatabaseService.transaction():
                db.session.delete(model_instance)
            return True
        except Exception as e:
            logger.error(f"Failed to delete model instance: {str(e)}")
            return False
    
    @staticmethod
    def get_by_id(model_class: Any, record_id: str) -> Optional[Any]:
        """
        Get a record by its ID
        
        Args:
            model_class: SQLAlchemy model class
            record_id: ID of the record to retrieve
            
        Returns:
            Model instance or None if not found
        """
        try:
            # Determine the primary key column name
            primary_key = model_class.__table__.primary_key.columns.keys()[0]
            return model_class.query.filter(getattr(model_class, primary_key) == record_id).first()
        except Exception as e:
            logger.error(f"Failed to get record by ID: {str(e)}")
            return None
    
    @staticmethod
    def get_all(model_class: Any, **filters) -> list:
        """
        Get all records with optional filters
        
        Args:
            model_class: SQLAlchemy model class
            **filters: Filter conditions
            
        Returns:
            List of model instances
        """
        try:
            query = model_class.query
            for key, value in filters.items():
                if hasattr(model_class, key):
                    query = query.filter(getattr(model_class, key) == value)
            return query.all()
        except Exception as e:
            logger.error(f"Failed to get records: {str(e)}")
            return []
    
    @staticmethod
    def count(model_class: Any, **filters) -> int:
        """
        Count records with optional filters
        
        Args:
            model_class: SQLAlchemy model class
            **filters: Filter conditions
            
        Returns:
            Number of matching records
        """
        try:
            query = model_class.query
            for key, value in filters.items():
                if hasattr(model_class, key):
                    query = query.filter(getattr(model_class, key) == value)
            return query.count()
        except Exception as e:
            logger.error(f"Failed to count records: {str(e)}")
            return 0
    
    @staticmethod
    def exists(model_class: Any, **filters) -> bool:
        """
        Check if records exist with given filters
        
        Args:
            model_class: SQLAlchemy model class
            **filters: Filter conditions
            
        Returns:
            True if at least one record exists, False otherwise
        """
        return DatabaseService.count(model_class, **filters) > 0

# Convenience functions for common operations
def create_user_profile(email: str, full_name: str, date_of_birth, **kwargs) -> Optional[Any]:
    """Create a new user profile"""
    from app.models import UserProfile
    
    user = UserProfile(
        email=email,
        full_name=full_name,
        date_of_birth=date_of_birth,
        **kwargs
    )
    
    if DatabaseService.safe_add(user):
        return user
    return None

def create_trusted_contact(user_id: str, contact_name: str, contact_email: str, **kwargs) -> Optional[Any]:
    """Create a new trusted contact"""
    from app.models import TrustedContact
    
    contact = TrustedContact(
        user_id=user_id,
        contact_name=contact_name,
        contact_email=contact_email,
        **kwargs
    )
    
    if DatabaseService.safe_add(contact):
        return contact
    return None

def create_action_policy(user_id: str, asset_type: str, platform_name: str, 
                        account_identifier: str, action_type: str, **kwargs) -> Optional[Any]:
    """Create a new action policy"""
    from app.models import ActionPolicy
    
    policy = ActionPolicy(
        user_id=user_id,
        asset_type=asset_type,
        platform_name=platform_name,
        account_identifier=account_identifier,
        action_type=action_type,
        **kwargs
    )
    
    if DatabaseService.safe_add(policy):
        return policy
    return None