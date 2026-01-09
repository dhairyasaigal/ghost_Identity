"""
Encryption utilities for sensitive data fields
Provides AES encryption for digital asset credentials and personal information
"""
import os
import base64
import json
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from typing import Dict, Any, Optional

class EncryptionService:
    """Service for encrypting and decrypting sensitive data"""
    
    def __init__(self, encryption_key: Optional[str] = None):
        """
        Initialize encryption service with key from environment or provided key
        
        Args:
            encryption_key: Base64 encoded encryption key, if None uses ENCRYPTION_KEY env var
        """
        if encryption_key:
            self.key = encryption_key.encode()
        else:
            # Get key from environment or generate a new one
            env_key = os.getenv('ENCRYPTION_KEY')
            if env_key:
                self.key = base64.urlsafe_b64decode(env_key.encode())
            else:
                # Generate a new key for development (should be set in production)
                self.key = Fernet.generate_key()
                print("WARNING: Using generated encryption key. Set ENCRYPTION_KEY in production!")
        
        self.cipher_suite = Fernet(self.key)
    
    def encrypt_data(self, data: Dict[str, Any]) -> str:
        """
        Encrypt a dictionary of data and return base64 encoded string
        
        Args:
            data: Dictionary containing sensitive data to encrypt
            
        Returns:
            Base64 encoded encrypted string
        """
        try:
            # Convert dict to JSON string
            json_data = json.dumps(data, sort_keys=True)
            
            # Encrypt the JSON string
            encrypted_data = self.cipher_suite.encrypt(json_data.encode())
            
            # Return base64 encoded result
            return base64.urlsafe_b64encode(encrypted_data).decode()
            
        except Exception as e:
            raise EncryptionError(f"Failed to encrypt data: {str(e)}")
    
    def decrypt_data(self, encrypted_data: str) -> Dict[str, Any]:
        """
        Decrypt base64 encoded string and return original dictionary
        
        Args:
            encrypted_data: Base64 encoded encrypted string
            
        Returns:
            Original dictionary data
        """
        try:
            # Decode from base64
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_data.encode())
            
            # Decrypt the data
            decrypted_bytes = self.cipher_suite.decrypt(encrypted_bytes)
            
            # Convert back to dictionary
            json_data = decrypted_bytes.decode()
            return json.loads(json_data)
            
        except Exception as e:
            raise EncryptionError(f"Failed to decrypt data: {str(e)}")
    
    def encrypt_string(self, text: str) -> str:
        """
        Encrypt a single string value
        
        Args:
            text: String to encrypt
            
        Returns:
            Base64 encoded encrypted string
        """
        try:
            encrypted_data = self.cipher_suite.encrypt(text.encode())
            return base64.urlsafe_b64encode(encrypted_data).decode()
        except Exception as e:
            raise EncryptionError(f"Failed to encrypt string: {str(e)}")
    
    def decrypt_string(self, encrypted_text: str) -> str:
        """
        Decrypt a single string value
        
        Args:
            encrypted_text: Base64 encoded encrypted string
            
        Returns:
            Original string
        """
        try:
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_text.encode())
            decrypted_bytes = self.cipher_suite.decrypt(encrypted_bytes)
            return decrypted_bytes.decode()
        except Exception as e:
            raise EncryptionError(f"Failed to decrypt string: {str(e)}")

class EncryptionError(Exception):
    """Custom exception for encryption/decryption errors"""
    pass

# Global encryption service instance
_encryption_service = None

def get_encryption_service() -> EncryptionService:
    """Get global encryption service instance"""
    global _encryption_service
    if _encryption_service is None:
        _encryption_service = EncryptionService()
    return _encryption_service

def encrypt_digital_assets(assets_data: Dict[str, Any]) -> str:
    """
    Convenience function to encrypt digital assets data
    
    Args:
        assets_data: Dictionary containing digital asset information
        
    Returns:
        Encrypted string suitable for database storage
    """
    service = get_encryption_service()
    return service.encrypt_data(assets_data)

def decrypt_digital_assets(encrypted_data: str) -> Dict[str, Any]:
    """
    Convenience function to decrypt digital assets data
    
    Args:
        encrypted_data: Encrypted string from database
        
    Returns:
        Original digital assets dictionary
    """
    service = get_encryption_service()
    return service.decrypt_data(encrypted_data)