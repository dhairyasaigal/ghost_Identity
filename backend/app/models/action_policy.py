"""
Action Policy Model - User-defined rules for digital asset management
"""
from app import db
from app.utils.encryption import get_encryption_service, EncryptionError
from sqlalchemy import Column, String, DateTime, ForeignKey, Integer, Text
from datetime import datetime
import uuid
import json
from typing import Dict, Any, Optional

class ActionPolicy(db.Model):
    __tablename__ = 'action_policies'
    
    policy_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey('user_profiles.user_id'), nullable=False)
    asset_type = Column(String(20), nullable=False)  # 'email', 'bank', 'social_media', 'other'
    platform_name = Column(String(100), nullable=False)
    account_identifier = Column(String(255), nullable=False)
    action_type = Column(String(20), nullable=False)  # 'delete', 'memorialize', 'transfer', 'lock'
    policy_details = Column(Text, nullable=True)  # JSON string for natural language policy and specific instructions
    priority = Column(Integer, default=1, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f'<ActionPolicy {self.platform_name}:{self.action_type} for {self.user_id}>'
    
    def set_policy_details(self, policy_data: Dict[str, Any]) -> None:
        """
        Encrypt and store policy details
        
        Args:
            policy_data: Dictionary containing natural language policy and specific instructions
        """
        try:
            encryption_service = get_encryption_service()
            self.policy_details = encryption_service.encrypt_data(policy_data)
        except EncryptionError as e:
            raise ValueError(f"Failed to encrypt policy details: {str(e)}")
    
    def get_policy_details(self) -> Optional[Dict[str, Any]]:
        """
        Decrypt and return policy details
        
        Returns:
            Dictionary containing policy details or None if no details
        """
        if not self.policy_details:
            return None
        
        try:
            encryption_service = get_encryption_service()
            return encryption_service.decrypt_data(self.policy_details)
        except EncryptionError as e:
            raise ValueError(f"Failed to decrypt policy details: {str(e)}")
    
    def set_natural_language_policy(self, policy_text: str, instructions: str = "", 
                                   conditions: list = None) -> None:
        """
        Set policy details with natural language policy and instructions
        
        Args:
            policy_text: Natural language description of the policy
            instructions: Specific instructions for execution
            conditions: List of conditions that must be met
        """
        policy_data = {
            'natural_language_policy': policy_text,
            'specific_instructions': instructions,
            'conditions': conditions or [],
            'created_at': datetime.utcnow().isoformat()
        }
        self.set_policy_details(policy_data)
    
    def to_dict(self):
        return {
            'policy_id': self.policy_id,
            'user_id': self.user_id,
            'asset_type': self.asset_type,
            'platform_name': self.platform_name,
            'account_identifier': self.account_identifier,
            'action_type': self.action_type,
            'policy_details': self.policy_details,
            'priority': self.priority,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }