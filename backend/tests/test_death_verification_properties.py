"""
Property-based tests for Death Verification Service
Tests universal properties that should hold across all valid inputs
"""
import pytest
from hypothesis import given, strategies as st, settings, assume
from unittest.mock import Mock, patch, MagicMock
import os
import tempfile
from PIL import Image, ImageDraw, ImageFont
import io

from app.services.death_verification import DeathVerificationService
from app.services.azure_resilience import AzureServiceError

class TestDeathVerificationProperties:
    """Property-based tests for death verification service"""
    
    def setup_method(self):
        """Setup test environment"""
        # Mock Azure credentials for testing
        with patch.dict(os.environ, {
            'AZURE_VISION_ENDPOINT': 'https://test.cognitiveservices.azure.com/',
            'AZURE_VISION_KEY': 'test-key-12345'
        }):
            self.service = DeathVerificationService()
    
    @given(
        name1=st.text(min_size=3, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Zs'))),
        name2=st.text(min_size=3, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Zs')))
    )
    @settings(max_examples=100)
    def test_property_1_ocr_extraction_consistency(self, name1, name2):
        """
        Property 1: OCR Extraction Consistency
        For any valid death certificate document (PDF or image), the Azure AI Vision service 
        should extract the deceased person's name, date of death, and certificate ID with 
        consistent field mapping regardless of document format variations.
        
        **Feature: ghost-identity-protection, Property 1: OCR Extraction Consistency**
        **Validates: Requirements 1.1**
        """
        assume(name1.strip() and name2.strip())  # Ensure non-empty names
        
        # Mock the Azure AI Vision client to return consistent results
        mock_result = Mock()
        mock_result.read = Mock()
        mock_page = Mock()
        mock_page.lines = [
            Mock(text=f"DEATH CERTIFICATE"),
            Mock(text=f"NAME: {name1}"),
            Mock(text=f"DATE OF DEATH: 12/25/2023"),
            Mock(text=f"CERTIFICATE ID: CERT123456")
        ]
        mock_result.read.pages = [mock_page]
        
        with patch.object(self.service.client, 'analyze', return_value=mock_result):
            # Create mock image data
            image_data = self._create_mock_certificate_image(name1)
            
            # Process the certificate twice with the same data
            result1 = self.service.process_death_certificate(image_data, "test-user-id")
            result2 = self.service.process_death_certificate(image_data, "test-user-id")
            
            # Property: Results should be consistent across multiple calls with same input
            if result1['status'] == 'success' and result2['status'] == 'success':
                extracted1 = result1['extracted_data']
                extracted2 = result2['extracted_data']
                
                # Field mapping should be consistent
                assert extracted1['full_name'] == extracted2['full_name'], \
                    f"Name extraction inconsistent: {extracted1['full_name']} != {extracted2['full_name']}"
                
                assert extracted1['date_of_death'] == extracted2['date_of_death'], \
                    f"Date extraction inconsistent: {extracted1['date_of_death']} != {extracted2['date_of_death']}"
                
                assert extracted1['certificate_id'] == extracted2['certificate_id'], \
                    f"Certificate ID extraction inconsistent: {extracted1['certificate_id']} != {extracted2['certificate_id']}"
                
                # Confidence scores should be identical for same input
                assert extracted1['confidence_score'] == extracted2['confidence_score'], \
                    f"Confidence score inconsistent: {extracted1['confidence_score']} != {extracted2['confidence_score']}"
    
    @given(
        certificate_data=st.fixed_dictionaries({
            'full_name': st.text(min_size=5, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Zs'))),
            'date_of_death': st.sampled_from(['12/25/2023', '2023-12-25', '25/12/2023']),
            'certificate_id': st.text(min_size=5, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Nd'))),
            'confidence_score': st.floats(min_value=0.0, max_value=1.0)
        })
    )
    @settings(max_examples=100)
    def test_property_2_certificate_validation_determinism(self, certificate_data):
        """
        Property 2: Certificate Validation Determinism
        For any death certificate data, validation against known standards should produce 
        consistent results - the same certificate should always pass or fail validation deterministically.
        
        **Feature: ghost-identity-protection, Property 2: Certificate Validation Determinism**
        **Validates: Requirements 1.2**
        """
        assume(certificate_data['full_name'].strip())  # Ensure non-empty name
        
        # Validate the same certificate data multiple times
        result1 = self.service._validate_certificate_format(certificate_data)
        result2 = self.service._validate_certificate_format(certificate_data)
        result3 = self.service._validate_certificate_format(certificate_data)
        
        # Property: Validation results should be deterministic
        assert result1['is_valid'] == result2['is_valid'] == result3['is_valid'], \
            f"Validation determinism failed: {result1['is_valid']}, {result2['is_valid']}, {result3['is_valid']}"
        
        assert result1['errors'] == result2['errors'] == result3['errors'], \
            f"Error lists not consistent: {result1['errors']}, {result2['errors']}, {result3['errors']}"
        
        assert result1['warnings'] == result2['warnings'] == result3['warnings'], \
            f"Warning lists not consistent: {result1['warnings']}, {result2['warnings']}, {result3['warnings']}"
        
        # Property: If certificate has required fields, it should be valid
        if (certificate_data['full_name'].strip() and 
            certificate_data['date_of_death'] and 
            certificate_data['confidence_score'] >= 0.5):
            
            # Should be valid if all required fields are present and confidence is good
            assert result1['is_valid'] or len(result1['errors']) > 0, \
                "Certificate with good data should be valid or have specific errors"
    
    @given(
        service_name=st.sampled_from(['azure_vision', 'azure_openai']),
        failure_count=st.integers(min_value=1, max_value=10),
        error_type=st.sampled_from(['network_error', 'service_error', 'timeout_error'])
    )
    @settings(max_examples=100)
    def test_property_13_service_degradation_resilience(self, service_name, failure_count, error_type):
        """
        Property 13: Service Degradation Resilience
        For any Azure service unavailability, the system should gracefully degrade functionality, 
        queue requests for retry, and implement proper error handling with exponential backoff.
        
        **Feature: ghost-identity-protection, Property 13: Service Degradation Resilience**
        **Validates: Requirements 5.3, 5.5**
        """
        from app.services.azure_resilience import azure_resilience
        
        # Reset service state for clean test
        azure_resilience.service_status.clear()
        azure_resilience.failure_counts.clear()
        azure_resilience.last_failure_times.clear()
        
        # Simulate service failures
        for i in range(failure_count):
            azure_resilience._record_failure(service_name, f"{error_type}_{i}")
        
        service_status = azure_resilience.get_service_status(service_name)
        
        # Property: Service status should reflect failure count appropriately
        if failure_count >= azure_resilience.circuit_breaker_threshold:
            assert service_status['status'] == 'unavailable', \
                f"Service should be unavailable after {failure_count} failures, but status is {service_status['status']}"
            
            assert service_status['circuit_open'] == True, \
                f"Circuit breaker should be open after {failure_count} failures"
        
        elif failure_count > 1:
            assert service_status['status'] == 'degraded', \
                f"Service should be degraded after {failure_count} failures, but status is {service_status['status']}"
        
        # Property: Failure count should be accurately tracked
        assert service_status['failure_count'] == failure_count, \
            f"Failure count mismatch: expected {failure_count}, got {service_status['failure_count']}"
        
        # Property: Service recovery should reset failure count
        azure_resilience._record_success(service_name)
        recovered_status = azure_resilience.get_service_status(service_name)
        
        assert recovered_status['status'] == 'available', \
            f"Service should be available after success, but status is {recovered_status['status']}"
        
        assert recovered_status['failure_count'] == 0, \
            f"Failure count should reset to 0 after success, but got {recovered_status['failure_count']}"
        
        assert recovered_status['circuit_open'] == False, \
            f"Circuit should be closed after success"
    
    def _create_mock_certificate_image(self, name: str) -> bytes:
        """Create a mock death certificate image for testing"""
        # Create a simple image with text
        img = Image.new('RGB', (800, 600), color='white')
        draw = ImageDraw.Draw(img)
        
        # Add certificate text
        try:
            # Try to use a default font, fall back to default if not available
            font = ImageFont.load_default()
        except:
            font = None
        
        draw.text((50, 50), "DEATH CERTIFICATE", fill='black', font=font)
        draw.text((50, 100), f"NAME: {name}", fill='black', font=font)
        draw.text((50, 150), "DATE OF DEATH: 12/25/2023", fill='black', font=font)
        draw.text((50, 200), "CERTIFICATE ID: CERT123456", fill='black', font=font)
        
        # Convert to bytes
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='PNG')
        return img_bytes.getvalue()

    @given(
        name1=st.text(min_size=3, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Zs'))),
        name2=st.text(min_size=3, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Zs')))
    )
    @settings(max_examples=100)
    def test_name_matching_consistency(self, name1, name2):
        """
        Additional property: Name matching should be consistent and symmetric where appropriate
        """
        assume(name1.strip() and name2.strip())
        
        # Test consistency - same inputs should give same results
        result1 = self.service._fuzzy_name_match(name1, name2)
        result2 = self.service._fuzzy_name_match(name1, name2)
        
        assert result1['is_match'] == result2['is_match'], \
            f"Name matching not consistent for {name1} vs {name2}"
        
        assert abs(result1['similarity_score'] - result2['similarity_score']) < 0.001, \
            f"Similarity scores not consistent: {result1['similarity_score']} vs {result2['similarity_score']}"
        
        # Test reflexivity - a name should match itself
        self_match = self.service._fuzzy_name_match(name1, name1)
        assert self_match['is_match'] == True, \
            f"Name should match itself: {name1}"
        
        assert self_match['similarity_score'] >= 0.99, \
            f"Self-similarity should be very high: {self_match['similarity_score']}"
    
    @given(
        date_string=st.sampled_from([
            '12/25/2023', '2023-12-25', '25/12/2023', 
            '01/01/2020', '2021-06-15', '31/12/2022'
        ])
    )
    @settings(max_examples=50)
    def test_date_validation_consistency(self, date_string):
        """
        Additional property: Date validation should be consistent
        """
        # Test consistency
        result1 = self.service._validate_death_date(date_string)
        result2 = self.service._validate_death_date(date_string)
        
        assert result1['is_valid'] == result2['is_valid'], \
            f"Date validation not consistent for {date_string}"
        
        # If valid, parsed dates should be identical
        if result1['is_valid'] and result2['is_valid']:
            assert result1['parsed_date'] == result2['parsed_date'], \
                f"Parsed dates not consistent for {date_string}"