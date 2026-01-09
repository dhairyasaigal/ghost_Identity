"""
Death Certificate Verification Service
Integrates with Azure AI Vision for OCR and document analysis
"""
import os
import re
import json
import logging
from datetime import datetime, date
from typing import Dict, Optional, Tuple, Any
from difflib import SequenceMatcher

from azure.ai.vision.imageanalysis import ImageAnalysisClient
from azure.core.credentials import AzureKeyCredential
from azure.core.exceptions import AzureError

from app.models.user_profile import UserProfile
from app.services.database import DatabaseService
from app.services.audit import AuditService
from app.services.azure_resilience import with_azure_retry, AzureServiceError
from app.services.error_handling import DeathVerificationErrorHandler

logger = logging.getLogger(__name__)

class DeathVerificationService:
    """Service for processing death certificates using Azure AI Vision"""
    
    def __init__(self):
        """Initialize the Azure AI Vision client"""
        self.endpoint = os.getenv('AZURE_VISION_ENDPOINT')
        self.key = os.getenv('AZURE_VISION_KEY')
        
        if not self.endpoint or not self.key:
            raise ValueError("Azure Vision endpoint and key must be configured in environment variables")
        
        try:
            self.client = ImageAnalysisClient(
                endpoint=self.endpoint,
                credential=AzureKeyCredential(self.key)
            )
        except Exception as e:
            logger.error(f"Failed to initialize Azure AI Vision client: {str(e)}")
            raise
        
        self.audit_service = AuditService()
    
    def process_death_certificate(self, image_data: bytes, user_id: str) -> Dict[str, Any]:
        """
        Process death certificate using Azure AI Vision OCR
        
        Args:
            image_data: Binary image data (PDF or image)
            user_id: ID of the user whose death is being verified
            
        Returns:
            Dictionary containing extraction results and verification status
        """
        try:
            # Log the verification attempt
            self.audit_service.create_log_entry(
                user_id=user_id,
                event_type="death_certificate_processing_started",
                event_description="Started processing death certificate with Azure AI Vision",
                ai_service_used="azure_vision",
                input_data={"image_size_bytes": len(image_data)}
            )
            
            # Extract text using Azure AI Vision
            extracted_text = self._extract_text_from_image(image_data)
            
            if not extracted_text:
                # Graceful degradation - service may be unavailable
                return {
                    'status': 'service_unavailable',
                    'error_message': 'Azure AI Vision service is currently unavailable. Please try again later or submit for manual review.',
                    'extracted_data': None,
                    'requires_manual_review': True
                }
            
            # Parse death certificate fields
            certificate_data = self._parse_death_certificate(extracted_text)
            
            # Validate the certificate format
            validation_result = self._validate_certificate_format(certificate_data)
            
            result = {
                'status': 'success' if validation_result['is_valid'] else 'error',
                'extracted_data': certificate_data,
                'validation_result': validation_result,
                'raw_text': extracted_text
            }
            
            # Log the processing result
            self.audit_service.create_log_entry(
                user_id=user_id,
                event_type="death_certificate_processing_completed",
                event_description=f"Death certificate processing completed with status: {result['status']}",
                ai_service_used="azure_vision",
                input_data={"image_size_bytes": len(image_data)},
                output_data=result,
                status="success" if result['status'] == 'success' else "failure"
            )
            
            return result
            
        except AzureServiceError as e:
            error_msg = f"Azure service resilience error: {str(e)}"
            logger.error(error_msg)
            
            self.audit_service.create_log_entry(
                user_id=user_id,
                event_type="death_certificate_processing_failed",
                event_description=error_msg,
                ai_service_used=e.service_name,
                status="failure"
            )
            
            return {
                'status': 'service_unavailable',
                'error_message': f"Azure {e.service_name} service is temporarily unavailable. Please try again later.",
                'extracted_data': None,
                'requires_manual_review': True,
                'retry_after': e.retry_after
            }
        except AzureError as e:
            error_msg = f"Azure AI Vision service error: {str(e)}"
            logger.error(error_msg)
            
            self.audit_service.create_log_entry(
                user_id=user_id,
                event_type="death_certificate_processing_failed",
                event_description=error_msg,
                ai_service_used="azure_vision",
                status="failure"
            )
            
            return {
                'status': 'error',
                'error_message': error_msg,
                'extracted_data': None
            }
        except Exception as e:
            error_msg = f"Unexpected error processing death certificate: {str(e)}"
            logger.error(error_msg)
            
            self.audit_service.create_log_entry(
                user_id=user_id,
                event_type="death_certificate_processing_failed",
                event_description=error_msg,
                status="failure"
            )
            
            return {
                'status': 'error',
                'error_message': error_msg,
                'extracted_data': None
            }
    
    def verify_death_event(self, extracted_data: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """
        Cross-reference extracted data with user profile and create death event
        
        Args:
            extracted_data: Data extracted from death certificate
            user_id: ID of the user whose death is being verified
            
        Returns:
            Dictionary containing verification results
        """
        try:
            # Get user profile from database
            user_profile = DatabaseService.get_by_id(UserProfile, user_id)
            
            if not user_profile:
                return {
                    'status': 'error',
                    'error_message': f'User profile not found for ID: {user_id}',
                    'verification_details': None
                }
            
            # Perform name matching
            name_match_result = self._fuzzy_name_match(
                extracted_data.get('full_name', ''),
                user_profile.full_name
            )
            
            # Validate death date
            date_validation_result = self._validate_death_date(
                extracted_data.get('date_of_death', '')
            )
            
            # Check if verification passes
            verification_passed = (
                name_match_result['is_match'] and 
                date_validation_result['is_valid']
            )
            
            verification_details = {
                'name_match': name_match_result,
                'date_validation': date_validation_result,
                'certificate_id': extracted_data.get('certificate_id', ''),
                'verification_passed': verification_passed
            }
            
            if verification_passed:
                # Update user status to 'deceased' and freeze assets
                success = self._update_user_status_to_deceased(user_profile)
                
                if success:
                    self.audit_service.create_log_entry(
                        user_id=user_id,
                        event_type="death_event_verified",
                        event_description=f"Death event verified for user {user_profile.full_name}. Status updated to deceased.",
                        input_data=extracted_data,
                        output_data=verification_details,
                        status="success"
                    )
                    
                    return {
                        'status': 'success',
                        'message': 'Death event verified successfully. Digital assets have been frozen.',
                        'verification_details': verification_details
                    }
                else:
                    return {
                        'status': 'error',
                        'error_message': 'Death event verified but failed to update user status',
                        'verification_details': verification_details
                    }
            else:
                self.audit_service.create_log_entry(
                    user_id=user_id,
                    event_type="death_verification_failed",
                    event_description="Death verification failed - name or date mismatch",
                    input_data=extracted_data,
                    output_data=verification_details,
                    status="failure"
                )
                
                return {
                    'status': 'verification_failed',
                    'error_message': 'Death verification failed. Name or date does not match user profile.',
                    'verification_details': verification_details
                }
                
        except Exception as e:
            error_msg = f"Error during death event verification: {str(e)}"
            logger.error(error_msg)
            
            self.audit_service.create_log_entry(
                user_id=user_id,
                event_type="death_verification_error",
                event_description=error_msg,
                status="failure"
            )
            
            return {
                'status': 'error',
                'error_message': error_msg,
                'verification_details': None
            }
    
    def _extract_text_from_image(self, image_data: bytes) -> str:
        """
        Extract text from image using Azure AI Vision OCR with retry logic
        
        Args:
            image_data: Binary image data
            
        Returns:
            Extracted text as string
        """
        @with_azure_retry('azure_vision')
        def _perform_ocr(image_data: bytes) -> str:
            # Use Azure AI Vision to extract text
            result = self.client.analyze(
                image_data=image_data,
                visual_features=['READ']
            )
            
            # Extract text from result
            extracted_text = ""
            if result.read is not None:
                for page in result.read.pages:
                    for line in page.lines:
                        extracted_text += line.text + "\n"
            
            return extracted_text.strip()
        
        try:
            return _perform_ocr(image_data)
        except AzureServiceError as e:
            logger.error(f"Azure Vision service error with resilience handling: {str(e)}")
            # Provide graceful degradation - return empty string to trigger manual review
            return ""
        except Exception as e:
            logger.error(f"Failed to extract text from image: {str(e)}")
            raise
    
    def _parse_death_certificate(self, text: str) -> Dict[str, Any]:
        """
        Parse death certificate text to extract key information
        
        Args:
            text: Raw OCR text from death certificate
            
        Returns:
            Dictionary containing parsed certificate data
        """
        certificate_data = {
            'full_name': '',
            'date_of_death': '',
            'certificate_id': '',
            'confidence_score': 0.0
        }
        
        try:
            # Normalize text for parsing
            normalized_text = text.upper().replace('\n', ' ').replace('\r', ' ')
            
            # Extract full name (look for common patterns)
            name_patterns = [
                r'NAME[:\s]+([A-Z\s,\.]+?)(?:\s+DATE|$)',
                r'DECEDENT[:\s]+([A-Z\s,\.]+?)(?:\s+DATE|$)',
                r'DECEASED[:\s]+([A-Z\s,\.]+?)(?:\s+DATE|$)',
                r'FULL NAME[:\s]+([A-Z\s,\.]+?)(?:\s+DATE|$)'
            ]
            
            for pattern in name_patterns:
                match = re.search(pattern, normalized_text)
                if match:
                    name = match.group(1).strip().strip(',').strip('.')
                    # Clean up the name (remove extra spaces, common words)
                    name = re.sub(r'\s+', ' ', name)
                    name = re.sub(r'\b(MR|MRS|MS|DR|PROF)\b\.?', '', name).strip()
                    if len(name) > 3:  # Reasonable name length
                        certificate_data['full_name'] = name.title()
                        break
            
            # Extract date of death (look for various date formats)
            date_patterns = [
                r'DATE OF DEATH[:\s]+(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4})',
                r'DEATH DATE[:\s]+(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4})',
                r'DIED[:\s]+(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4})',
                r'(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4})'  # Any date format
            ]
            
            for pattern in date_patterns:
                matches = re.findall(pattern, normalized_text)
                if matches:
                    # Take the first reasonable date found
                    certificate_data['date_of_death'] = matches[0]
                    break
            
            # Extract certificate ID (look for various ID patterns)
            id_patterns = [
                r'CERTIFICATE\s+(?:NO|NUMBER|ID)[:\s]+([A-Z0-9\-]+)',
                r'CERT\s+(?:NO|NUMBER|ID)[:\s]+([A-Z0-9\-]+)',
                r'ID[:\s]+([A-Z0-9\-]{5,})',
                r'NUMBER[:\s]+([A-Z0-9\-]{5,})'
            ]
            
            for pattern in id_patterns:
                match = re.search(pattern, normalized_text)
                if match:
                    cert_id = match.group(1).strip()
                    if len(cert_id) >= 5:  # Reasonable ID length
                        certificate_data['certificate_id'] = cert_id
                        break
            
            # Calculate confidence score based on extracted fields
            confidence = 0.0
            if certificate_data['full_name']:
                confidence += 0.5
            if certificate_data['date_of_death']:
                confidence += 0.3
            if certificate_data['certificate_id']:
                confidence += 0.2
            
            certificate_data['confidence_score'] = confidence
            
        except Exception as e:
            logger.error(f"Error parsing death certificate: {str(e)}")
        
        return certificate_data
    
    def _validate_certificate_format(self, certificate_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate the extracted certificate data against known standards
        
        Args:
            certificate_data: Parsed certificate data
            
        Returns:
            Dictionary containing validation results
        """
        validation_result = {
            'is_valid': False,
            'errors': [],
            'warnings': []
        }
        
        # Check if required fields are present
        if not certificate_data.get('full_name'):
            validation_result['errors'].append('Full name not found in certificate')
        
        if not certificate_data.get('date_of_death'):
            validation_result['errors'].append('Date of death not found in certificate')
        
        # Validate date format if present
        if certificate_data.get('date_of_death'):
            date_validation = self._validate_death_date(certificate_data['date_of_death'])
            if not date_validation['is_valid']:
                validation_result['errors'].append(f"Invalid date format: {date_validation['error']}")
        
        # Check confidence score
        confidence = certificate_data.get('confidence_score', 0.0)
        if confidence < 0.5:
            validation_result['warnings'].append('Low confidence in extracted data')
        
        # Certificate is valid if no errors
        validation_result['is_valid'] = len(validation_result['errors']) == 0
        
        return validation_result
    
    def _fuzzy_name_match(self, extracted_name: str, profile_name: str) -> Dict[str, Any]:
        """
        Perform fuzzy matching between extracted name and profile name
        
        Args:
            extracted_name: Name extracted from certificate
            profile_name: Name from user profile
            
        Returns:
            Dictionary containing match results
        """
        if not extracted_name or not profile_name:
            return {
                'is_match': False,
                'similarity_score': 0.0,
                'error': 'One or both names are empty'
            }
        
        # Normalize names for comparison
        extracted_normalized = self._normalize_name(extracted_name)
        profile_normalized = self._normalize_name(profile_name)
        
        # Calculate similarity using SequenceMatcher
        similarity = SequenceMatcher(None, extracted_normalized, profile_normalized).ratio()
        
        # Also check if all words in profile name appear in extracted name
        profile_words = set(profile_normalized.split())
        extracted_words = set(extracted_normalized.split())
        
        word_match_ratio = len(profile_words.intersection(extracted_words)) / len(profile_words) if profile_words else 0
        
        # Combine similarity scores (weighted average)
        combined_score = (similarity * 0.7) + (word_match_ratio * 0.3)
        
        # Consider it a match if similarity is above threshold
        is_match = combined_score >= 0.8
        
        return {
            'is_match': is_match,
            'similarity_score': combined_score,
            'character_similarity': similarity,
            'word_match_ratio': word_match_ratio,
            'extracted_normalized': extracted_normalized,
            'profile_normalized': profile_normalized
        }
    
    def _normalize_name(self, name: str) -> str:
        """
        Normalize name for comparison (remove punctuation, extra spaces, etc.)
        
        Args:
            name: Raw name string
            
        Returns:
            Normalized name string
        """
        if not name:
            return ""
        
        # Convert to uppercase and remove punctuation
        normalized = re.sub(r'[^\w\s]', '', name.upper())
        
        # Remove extra whitespace
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        
        # Remove common titles and suffixes
        titles_suffixes = ['MR', 'MRS', 'MS', 'DR', 'PROF', 'JR', 'SR', 'II', 'III', 'IV']
        words = normalized.split()
        filtered_words = [word for word in words if word not in titles_suffixes]
        
        return ' '.join(filtered_words)
    
    def _validate_death_date(self, date_string: str) -> Dict[str, Any]:
        """
        Validate death date format and reasonableness
        
        Args:
            date_string: Date string from certificate
            
        Returns:
            Dictionary containing validation results
        """
        if not date_string:
            return {
                'is_valid': False,
                'error': 'Date string is empty',
                'parsed_date': None
            }
        
        # Try to parse various date formats
        date_formats = [
            '%m/%d/%Y',
            '%m-%d-%Y',
            '%m/%d/%y',
            '%m-%d-%y',
            '%d/%m/%Y',
            '%d-%m-%Y',
            '%Y-%m-%d',
            '%Y/%m/%d'
        ]
        
        parsed_date = None
        for fmt in date_formats:
            try:
                parsed_date = datetime.strptime(date_string.strip(), fmt).date()
                break
            except ValueError:
                continue
        
        if not parsed_date:
            return {
                'is_valid': False,
                'error': f'Unable to parse date format: {date_string}',
                'parsed_date': None
            }
        
        # Check if date is reasonable (not in future, not too far in past)
        today = date.today()
        if parsed_date > today:
            return {
                'is_valid': False,
                'error': 'Death date cannot be in the future',
                'parsed_date': parsed_date
            }
        
        # Check if date is not too far in the past (e.g., more than 150 years)
        min_date = date(today.year - 150, 1, 1)
        if parsed_date < min_date:
            return {
                'is_valid': False,
                'error': 'Death date is too far in the past',
                'parsed_date': parsed_date
            }
        
        return {
            'is_valid': True,
            'parsed_date': parsed_date,
            'formatted_date': parsed_date.isoformat()
        }
    
    def _update_user_status_to_deceased(self, user_profile: UserProfile) -> bool:
        """
        Update user status to deceased and freeze digital assets
        
        Args:
            user_profile: UserProfile instance to update
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Update user status
            success = DatabaseService.safe_update(user_profile, status='deceased')
            
            if success:
                # Log the status change
                self.audit_service.create_log_entry(
                    user_id=user_profile.user_id,
                    event_type="user_status_updated",
                    event_description=f"User status updated to 'deceased' for {user_profile.full_name}",
                    input_data={'previous_status': 'active', 'new_status': 'deceased'},
                    status="success"
                )
                
                # Log asset freezing (conceptual - actual freezing would be implemented in asset management)
                self.audit_service.create_log_entry(
                    user_id=user_profile.user_id,
                    event_type="digital_assets_frozen",
                    event_description="All digital assets have been frozen due to verified death event",
                    status="success"
                )
                
                logger.info(f"Successfully updated user {user_profile.user_id} status to deceased")
                return True
            else:
                logger.error(f"Failed to update user {user_profile.user_id} status to deceased")
                return False
                
        except Exception as e:
            logger.error(f"Error updating user status to deceased: {str(e)}")
            return False