"""
User Profile Model - Core user data and digital asset storage
"""
from app import db
from app.utils.encryption import encrypt_digital_assets, decrypt_digital_assets, EncryptionError
from sqlalchemy import Column, String, DateTime, Date, Text
from datetime import datetime
import uuid
import json
from typing import Dict, Any, Optional

class UserProfile(db.Model):
    __tablename__ = 'user_profiles'
    
    user_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String(255), unique=True, nullable=False)
    phone_number = Column(String(15), nullable=False)  # Mobile number for OTP verification
    full_name = Column(String(255), nullable=False)
    date_of_birth = Column(Date, nullable=False)
    
    # KYC Identity Verification Fields
    aadhaar_number = Column(String(12), unique=True, nullable=False)  # Aadhaar card number
    pan_number = Column(String(10), unique=True, nullable=False)  # PAN card number
    address_line1 = Column(String(255), nullable=False)
    address_line2 = Column(String(255), nullable=True)
    city = Column(String(100), nullable=False)
    state = Column(String(100), nullable=False)
    pincode = Column(String(6), nullable=False)
    
    # Verification Status Fields
    kyc_status = Column(String(20), default='pending', nullable=False)  # 'pending', 'verified', 'rejected'
    phone_verified = Column(String(20), default='pending', nullable=False)  # 'pending', 'verified'
    email_verified = Column(String(20), default='pending', nullable=False)  # 'pending', 'verified'
    identity_verification_score = Column(String(10), nullable=True)  # AI-based verification score
    
    encrypted_metadata = Column(Text, nullable=True)  # JSON string for encrypted account details
    status = Column(String(20), default='active', nullable=False)  # 'active', 'deceased', 'suspended'
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    trusted_contacts = db.relationship('TrustedContact', backref='user', lazy=True, cascade='all, delete-orphan')
    action_policies = db.relationship('ActionPolicy', backref='user', lazy=True, cascade='all, delete-orphan')
    audit_logs = db.relationship('AuditLog', backref='user', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<UserProfile {self.email}>'
    
    def set_encrypted_metadata(self, assets_data: Dict[str, Any]) -> None:
        """
        Encrypt and store digital assets metadata
        
        Args:
            assets_data: Dictionary containing digital asset information
        """
        try:
            self.encrypted_metadata = encrypt_digital_assets(assets_data)
        except EncryptionError as e:
            raise ValueError(f"Failed to encrypt metadata: {str(e)}")
    
    def get_decrypted_metadata(self) -> Optional[Dict[str, Any]]:
        """
        Decrypt and return digital assets metadata
        
        Returns:
            Dictionary containing digital asset information or None if no metadata
        """
        if not self.encrypted_metadata:
            return None
        
        try:
            return decrypt_digital_assets(self.encrypted_metadata)
        except EncryptionError as e:
            raise ValueError(f"Failed to decrypt metadata: {str(e)}")
    
    def add_digital_asset(self, asset_type: str, platform_name: str, 
                         account_identifier: str, credentials: Dict[str, Any]) -> None:
        """
        Add a new digital asset to the user's encrypted metadata
        
        Args:
            asset_type: Type of asset ('email', 'bank', 'social_media', 'other')
            platform_name: Name of the platform (e.g., 'Gmail', 'Chase Bank')
            account_identifier: Account username/email/ID
            credentials: Dictionary containing login credentials and other sensitive data
        """
        # Get existing metadata or create new
        metadata = self.get_decrypted_metadata() or {}
        
        # Initialize asset type list if it doesn't exist
        if asset_type not in metadata:
            metadata[asset_type] = []
        
        # Add new asset
        asset_data = {
            'platform_name': platform_name,
            'account_identifier': account_identifier,
            'credentials': credentials,
            'added_at': datetime.utcnow().isoformat()
        }
        
        metadata[asset_type].append(asset_data)
        
        # Re-encrypt and store
        self.set_encrypted_metadata(metadata)
    
    def get_digital_assets_by_type(self, asset_type: str) -> list:
        """
        Get all digital assets of a specific type
        
        Args:
            asset_type: Type of asset to retrieve
            
        Returns:
            List of assets for the specified type
        """
        metadata = self.get_decrypted_metadata()
        if not metadata:
            return []
        
        return metadata.get(asset_type, [])
    
    def to_dict(self):
        return {
            'user_id': self.user_id,
            'email': self.email,
            'phone_number': self.phone_number,
            'full_name': self.full_name,
            'date_of_birth': self.date_of_birth.isoformat() if self.date_of_birth else None,
            'aadhaar_number': self.aadhaar_number[-4:] if self.aadhaar_number else None,  # Only show last 4 digits
            'pan_number': self.pan_number,
            'address': {
                'line1': self.address_line1,
                'line2': self.address_line2,
                'city': self.city,
                'state': self.state,
                'pincode': self.pincode
            },
            'verification_status': {
                'kyc_status': self.kyc_status,
                'phone_verified': self.phone_verified,
                'email_verified': self.email_verified,
                'identity_verification_score': self.identity_verification_score
            },
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }