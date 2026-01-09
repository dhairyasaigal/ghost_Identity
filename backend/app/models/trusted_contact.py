"""
Trusted Contact Model - Emergency contacts for death verification
"""
from app import db
from sqlalchemy import Column, String, DateTime, ForeignKey
from datetime import datetime
import uuid

class TrustedContact(db.Model):
    __tablename__ = 'trusted_contacts'
    
    contact_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey('user_profiles.user_id'), nullable=False)
    contact_name = Column(String(255), nullable=False)
    contact_email = Column(String(255), nullable=False)
    contact_phone = Column(String(20), nullable=False)
    relationship = Column(String(100), nullable=False)
    
    # Enhanced Security Verification for Trusted Contacts
    contact_aadhaar_number = Column(String(12), nullable=False)  # Aadhaar for identity verification
    contact_pan_number = Column(String(10), nullable=False)  # PAN for additional verification
    contact_address_line1 = Column(String(255), nullable=False)
    contact_address_line2 = Column(String(255), nullable=True)
    contact_city = Column(String(100), nullable=False)
    contact_state = Column(String(100), nullable=False)
    contact_pincode = Column(String(6), nullable=False)
    
    # Verification and Authorization Fields
    verification_status = Column(String(20), default='pending', nullable=False)  # 'pending', 'verified', 'revoked'
    authorization_level = Column(String(20), default='basic', nullable=False)  # 'basic', 'full', 'emergency_only'
    identity_verification_score = Column(String(10), nullable=True)  # AI-based verification score
    background_check_status = Column(String(20), default='pending', nullable=False)  # 'pending', 'passed', 'failed'
    
    # Document Verification
    identity_documents_verified = Column(String(20), default='pending', nullable=False)  # 'pending', 'verified', 'rejected'
    relationship_proof_verified = Column(String(20), default='pending', nullable=False)  # 'pending', 'verified', 'rejected'
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    verified_at = Column(DateTime, nullable=True)  # When verification was completed
    
    def __repr__(self):
        return f'<TrustedContact {self.contact_name} for {self.user_id}>'
    
    def to_dict(self):
        return {
            'contact_id': self.contact_id,
            'user_id': self.user_id,
            'contact_name': self.contact_name,
            'contact_email': self.contact_email,
            'contact_phone': self.contact_phone,
            'relationship': self.relationship,
            'contact_aadhaar_number': self.contact_aadhaar_number[-4:] if self.contact_aadhaar_number else None,  # Only last 4 digits
            'contact_pan_number': self.contact_pan_number,
            'contact_address': {
                'line1': self.contact_address_line1,
                'line2': self.contact_address_line2,
                'city': self.contact_city,
                'state': self.contact_state,
                'pincode': self.contact_pincode
            },
            'verification_details': {
                'verification_status': self.verification_status,
                'authorization_level': self.authorization_level,
                'identity_verification_score': self.identity_verification_score,
                'background_check_status': self.background_check_status,
                'identity_documents_verified': self.identity_documents_verified,
                'relationship_proof_verified': self.relationship_proof_verified,
                'verified_at': self.verified_at.isoformat() if self.verified_at else None
            },
            'created_at': self.created_at.isoformat() if self.created_at else None
        }