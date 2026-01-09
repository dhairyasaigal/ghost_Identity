"""
KYC (Know Your Customer) Verification Service
Handles identity verification using Aadhaar, PAN, and other Indian identity documents
"""
import re
import requests
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Tuple
from app.services.audit import AuditService
import random
import string

class KYCVerificationService:
    """Service for handling KYC verification processes"""
    
    # Validation patterns for Indian identity documents
    AADHAAR_PATTERN = re.compile(r'^[2-9]{1}[0-9]{3}[0-9]{4}[0-9]{4}$')
    PAN_PATTERN = re.compile(r'^[A-Z]{5}[0-9]{4}[A-Z]{1}$')
    PHONE_PATTERN = re.compile(r'^[6-9]\d{9}$')  # Indian mobile numbers
    PINCODE_PATTERN = re.compile(r'^[1-9][0-9]{5}$')
    
    @staticmethod
    def validate_aadhaar(aadhaar_number: str) -> Tuple[bool, str]:
        """
        Validate Aadhaar number format and checksum
        
        Args:
            aadhaar_number: 12-digit Aadhaar number
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not aadhaar_number:
            return False, "Aadhaar number is required"
        
        # Remove spaces and hyphens
        aadhaar_clean = re.sub(r'[\s-]', '', aadhaar_number)
        
        if len(aadhaar_clean) != 12:
            return False, "Aadhaar number must be 12 digits"
        
        if not aadhaar_clean.isdigit():
            return False, "Aadhaar number must contain only digits"
        
        if not KYCVerificationService.AADHAAR_PATTERN.match(aadhaar_clean):
            return False, "Invalid Aadhaar number format"
        
        # Verhoeff algorithm checksum validation
        if not KYCVerificationService._verify_aadhaar_checksum(aadhaar_clean):
            return False, "Invalid Aadhaar number checksum"
        
        return True, ""
    
    @staticmethod
    def _verify_aadhaar_checksum(aadhaar: str) -> bool:
        """
        Verify Aadhaar checksum using Verhoeff algorithm
        """
        # Verhoeff algorithm tables
        multiplication_table = [
            [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
            [1, 2, 3, 4, 0, 6, 7, 8, 9, 5],
            [2, 3, 4, 0, 1, 7, 8, 9, 5, 6],
            [3, 4, 0, 1, 2, 8, 9, 5, 6, 7],
            [4, 0, 1, 2, 3, 9, 5, 6, 7, 8],
            [5, 9, 8, 7, 6, 0, 4, 3, 2, 1],
            [6, 5, 9, 8, 7, 1, 0, 4, 3, 2],
            [7, 6, 5, 9, 8, 2, 1, 0, 4, 3],
            [8, 7, 6, 5, 9, 3, 2, 1, 0, 4],
            [9, 8, 7, 6, 5, 4, 3, 2, 1, 0]
        ]
        
        permutation_table = [
            [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
            [1, 5, 7, 6, 2, 8, 3, 0, 9, 4],
            [5, 8, 0, 3, 7, 9, 6, 1, 4, 2],
            [8, 9, 1, 6, 0, 4, 3, 5, 2, 7],
            [9, 4, 5, 3, 1, 2, 6, 8, 7, 0],
            [4, 2, 8, 6, 5, 7, 3, 9, 0, 1],
            [2, 7, 9, 3, 8, 0, 6, 4, 1, 5],
            [7, 0, 4, 6, 9, 1, 3, 2, 5, 8]
        ]
        
        inverse_table = [0, 4, 3, 2, 1, 5, 6, 7, 8, 9]
        
        check = 0
        for i, digit in enumerate(reversed(aadhaar)):
            check = multiplication_table[check][permutation_table[i % 8][int(digit)]]
        
        return check == 0
    
    @staticmethod
    def validate_pan(pan_number: str) -> Tuple[bool, str]:
        """
        Validate PAN number format
        
        Args:
            pan_number: 10-character PAN number
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not pan_number:
            return False, "PAN number is required"
        
        pan_clean = pan_number.upper().strip()
        
        if len(pan_clean) != 10:
            return False, "PAN number must be 10 characters"
        
        if not KYCVerificationService.PAN_PATTERN.match(pan_clean):
            return False, "Invalid PAN number format (should be ABCDE1234F)"
        
        return True, ""
    
    @staticmethod
    def validate_phone_number(phone_number: str) -> Tuple[bool, str]:
        """
        Validate Indian mobile phone number
        
        Args:
            phone_number: 10-digit mobile number
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not phone_number:
            return False, "Phone number is required"
        
        phone_clean = re.sub(r'[\s\-\+]', '', phone_number)
        
        # Remove country code if present
        if phone_clean.startswith('91') and len(phone_clean) == 12:
            phone_clean = phone_clean[2:]
        elif phone_clean.startswith('+91') and len(phone_clean) == 13:
            phone_clean = phone_clean[3:]
        
        if len(phone_clean) != 10:
            return False, "Phone number must be 10 digits"
        
        if not KYCVerificationService.PHONE_PATTERN.match(phone_clean):
            return False, "Invalid Indian mobile number format"
        
        return True, ""
    
    @staticmethod
    def validate_pincode(pincode: str) -> Tuple[bool, str]:
        """
        Validate Indian postal pincode
        
        Args:
            pincode: 6-digit pincode
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not pincode:
            return False, "Pincode is required"
        
        pincode_clean = pincode.strip()
        
        if len(pincode_clean) != 6:
            return False, "Pincode must be 6 digits"
        
        if not KYCVerificationService.PINCODE_PATTERN.match(pincode_clean):
            return False, "Invalid pincode format"
        
        return True, ""
    
    @staticmethod
    def generate_otp() -> str:
        """Generate 6-digit OTP for verification"""
        return ''.join(random.choices(string.digits, k=6))
    
    @staticmethod
    def send_otp_sms(phone_number: str, otp: str) -> bool:
        """
        Send OTP via SMS (mock implementation)
        In production, integrate with SMS gateway like Twilio, MSG91, etc.
        
        Args:
            phone_number: Mobile number to send OTP
            otp: 6-digit OTP code
            
        Returns:
            True if SMS sent successfully
        """
        try:
            # Mock SMS sending - in production, use actual SMS gateway
            print(f"SMS OTP: {otp} sent to {phone_number}")
            
            # Log OTP sending for audit
            AuditService.log_system_action(
                action='otp_sent',
                details={
                    'phone_number': phone_number[-4:],  # Only log last 4 digits
                    'timestamp': datetime.utcnow().isoformat(),
                    'method': 'sms'
                }
            )
            
            return True
        except Exception as e:
            print(f"Failed to send SMS OTP: {str(e)}")
            return False
    
    @staticmethod
    def send_otp_email(email: str, otp: str) -> bool:
        """
        Send OTP via email (mock implementation)
        In production, integrate with email service
        
        Args:
            email: Email address to send OTP
            otp: 6-digit OTP code
            
        Returns:
            True if email sent successfully
        """
        try:
            # Mock email sending - in production, use actual email service
            print(f"Email OTP: {otp} sent to {email}")
            
            # Log OTP sending for audit
            AuditService.log_system_action(
                action='otp_sent',
                details={
                    'email': email,
                    'timestamp': datetime.utcnow().isoformat(),
                    'method': 'email'
                }
            )
            
            return True
        except Exception as e:
            print(f"Failed to send email OTP: {str(e)}")
            return False
    
    @staticmethod
    def verify_identity_documents(aadhaar: str, pan: str, name: str, dob: str) -> Dict[str, Any]:
        """
        Verify identity documents against government databases (mock implementation)
        In production, integrate with UIDAI and Income Tax Department APIs
        
        Args:
            aadhaar: Aadhaar number
            pan: PAN number
            name: Full name
            dob: Date of birth (YYYY-MM-DD)
            
        Returns:
            Dictionary with verification results
        """
        try:
            # Mock verification - in production, use actual government APIs
            # This would typically involve:
            # 1. UIDAI Aadhaar verification API
            # 2. Income Tax Department PAN verification API
            # 3. Cross-verification of details
            
            # Simulate verification process
            verification_score = random.uniform(0.85, 0.98)  # Mock high confidence score
            
            result = {
                'aadhaar_verified': True,
                'pan_verified': True,
                'name_match': True,
                'dob_match': True,
                'verification_score': round(verification_score, 2),
                'status': 'verified' if verification_score > 0.9 else 'needs_review',
                'verified_at': datetime.utcnow().isoformat(),
                'verification_id': ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
            }
            
            # Log verification attempt
            AuditService.log_system_action(
                action='identity_verification',
                details={
                    'aadhaar_last4': aadhaar[-4:] if aadhaar else None,
                    'pan_number': pan,
                    'verification_score': result['verification_score'],
                    'status': result['status'],
                    'timestamp': datetime.utcnow().isoformat()
                }
            )
            
            return result
            
        except Exception as e:
            print(f"Identity verification failed: {str(e)}")
            return {
                'aadhaar_verified': False,
                'pan_verified': False,
                'name_match': False,
                'dob_match': False,
                'verification_score': 0.0,
                'status': 'failed',
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }
    
    @staticmethod
    def validate_all_kyc_data(kyc_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate all KYC data fields
        
        Args:
            kyc_data: Dictionary containing all KYC information
            
        Returns:
            Dictionary with validation results
        """
        errors = {}
        
        # Validate Aadhaar
        aadhaar_valid, aadhaar_error = KYCVerificationService.validate_aadhaar(
            kyc_data.get('aadhaar_number', '')
        )
        if not aadhaar_valid:
            errors['aadhaar_number'] = aadhaar_error
        
        # Validate PAN
        pan_valid, pan_error = KYCVerificationService.validate_pan(
            kyc_data.get('pan_number', '')
        )
        if not pan_valid:
            errors['pan_number'] = pan_error
        
        # Validate phone number
        phone_valid, phone_error = KYCVerificationService.validate_phone_number(
            kyc_data.get('phone_number', '')
        )
        if not phone_valid:
            errors['phone_number'] = phone_error
        
        # Validate pincode
        pincode_valid, pincode_error = KYCVerificationService.validate_pincode(
            kyc_data.get('pincode', '')
        )
        if not pincode_valid:
            errors['pincode'] = pincode_error
        
        # Validate required fields
        required_fields = [
            'full_name', 'date_of_birth', 'address_line1', 
            'city', 'state', 'email'
        ]
        
        for field in required_fields:
            if not kyc_data.get(field, '').strip():
                errors[field] = f"{field.replace('_', ' ').title()} is required"
        
        return {
            'is_valid': len(errors) == 0,
            'errors': errors,
            'validated_at': datetime.utcnow().isoformat()
        }
    
    @staticmethod
    def calculate_risk_score(user_data: Dict[str, Any], contact_data: Dict[str, Any] = None) -> float:
        """
        Calculate risk score based on user and contact verification data
        
        Args:
            user_data: User KYC data
            contact_data: Trusted contact KYC data (optional)
            
        Returns:
            Risk score between 0.0 (high risk) and 1.0 (low risk)
        """
        score = 0.0
        
        # Base score for identity verification
        if user_data.get('kyc_status') == 'verified':
            score += 0.4
        
        if user_data.get('phone_verified') == 'verified':
            score += 0.2
        
        if user_data.get('email_verified') == 'verified':
            score += 0.2
        
        # Additional score for contact verification
        if contact_data:
            if contact_data.get('verification_status') == 'verified':
                score += 0.1
            
            if contact_data.get('background_check_status') == 'passed':
                score += 0.1
        
        return min(score, 1.0)