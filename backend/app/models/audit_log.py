"""
Audit Log Model - Tamper-proof logging for all system actions
"""
from app import db
from sqlalchemy import Column, String, DateTime, ForeignKey, Text, event
from datetime import datetime
import uuid
import hashlib
import json

class AuditLog(db.Model):
    __tablename__ = 'audit_logs'
    
    log_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey('user_profiles.user_id'), nullable=False)
    event_type = Column(String(100), nullable=False)
    event_description = Column(Text, nullable=False)
    ai_service_used = Column(String(50), nullable=True)  # 'azure_vision', 'azure_openai', or NULL
    input_data = Column(Text, nullable=True)  # JSON string
    output_data = Column(Text, nullable=True)  # JSON string
    status = Column(String(20), nullable=False)  # 'success', 'failure', 'pending'
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    hash_signature = Column(String(256), nullable=True)  # For tamper detection
    
    def _generate_hash(self):
        """Generate tamper-proof hash signature for the log entry"""
        # Use current timestamp if not set
        timestamp_str = self.timestamp.isoformat() if self.timestamp else datetime.utcnow().isoformat()
        
        hash_data = {
            'log_id': self.log_id,
            'user_id': self.user_id,
            'event_type': self.event_type,
            'event_description': self.event_description,
            'ai_service_used': self.ai_service_used,
            'input_data': self.input_data,
            'output_data': self.output_data,
            'status': self.status,
            'timestamp': timestamp_str
        }
        hash_string = json.dumps(hash_data, sort_keys=True)
        return hashlib.sha256(hash_string.encode()).hexdigest()
    
    def verify_integrity(self):
        """Verify the integrity of this log entry"""
        if not self.hash_signature:
            return False
        
        expected_hash = self._generate_hash()
        return self.hash_signature == expected_hash
    
    def __repr__(self):
        return f'<AuditLog {self.event_type} for {self.user_id}>'
    
    def to_dict(self):
        return {
            'log_id': self.log_id,
            'user_id': self.user_id,
            'event_type': self.event_type,
            'event_description': self.event_description,
            'ai_service_used': self.ai_service_used,
            'input_data': self.input_data,
            'output_data': self.output_data,
            'status': self.status,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'hash_signature': self.hash_signature
        }

# Event listener to generate hash after insert
@event.listens_for(AuditLog, 'after_insert')
def generate_hash_after_insert(mapper, connection, target):
    """Generate hash signature after the record is inserted and all fields are set"""
    if not target.hash_signature:
        # Generate hash with all fields populated
        target.hash_signature = target._generate_hash()
        
        # Update the record with the hash
        connection.execute(
            target.__table__.update().where(
                target.__table__.c.log_id == target.log_id
            ).values(hash_signature=target.hash_signature)
        )