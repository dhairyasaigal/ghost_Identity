"""
Property-based tests for Action Engine Service
Tests universal properties that should hold across all valid inputs
"""
import pytest
from hypothesis import given, strategies as st, settings, assume
from unittest.mock import Mock, patch, MagicMock
import os
import json
from datetime import datetime

from app.services.action_engine import ActionEngineService
from app.models.action_policy import ActionPolicy
from app.services.azure_resilience import AzureServiceError

class TestActionEngineProperties:
    """Property-based tests for action engine service"""
    
    def setup_method(self):
        """Setup test environment"""
        # Mock Azure OpenAI credentials for testing
        with patch.dict(os.environ, {
            'AZURE_OPENAI_ENDPOINT': 'https://test.openai.azure.com/',
            'AZURE_OPENAI_KEY': 'test-key-12345',
            'AZURE_OPENAI_DEPLOYMENT': 'test-deployment'
        }):
            # Mock the AzureOpenAI client to avoid initialization issues
            with patch('app.services.action_engine.AzureOpenAI') as mock_azure_openai:
                mock_client = Mock()
                mock_azure_openai.return_value = mock_client
                self.service = ActionEngineService()
                self.service.client = mock_client
    
    @given(
        policy_text1=st.text(min_size=10, max_size=200, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Zs', 'Po'))),
        policy_text2=st.text(min_size=10, max_size=200, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Zs', 'Po'))),
        platform_name=st.sampled_from(['gmail', 'facebook', 'chase_bank', 'twitter', 'linkedin']),
        action_type=st.sampled_from(['delete', 'memorialize', 'lock'])
    )
    @settings(max_examples=100)
    def test_property_8_ai_policy_interpretation_consistency(self, policy_text1, policy_text2, platform_name, action_type):
        """
        Property 8: AI Policy Interpretation Consistency
        For any natural language action policy, the Azure OpenAI service should interpret 
        the policy and generate structured action plans that preserve the original intent 
        across multiple interpretations.
        
        **Feature: ghost-identity-protection, Property 8: AI Policy Interpretation Consistency**
        **Validates: Requirements 3.1**
        """
        assume(policy_text1.strip() and policy_text2.strip())  # Ensure non-empty policies
        
        # Create mock action policies
        policy1 = self._create_mock_policy(policy_text1, platform_name, action_type)
        policy2 = self._create_mock_policy(policy_text2, platform_name, action_type)
        
        # Mock Azure OpenAI responses to be consistent
        mock_interpretation = {
            'action_type': action_type,
            'platform_name': platform_name,
            'account_identifier': 'test@example.com',
            'interpretation_confidence': 0.85,
            'structured_actions': [
                f'Contact {platform_name} customer service',
                f'Request {action_type} action for account',
                'Provide required documentation',
                'Follow platform procedures'
            ],
            'required_documentation': ['death_certificate', 'id_verification'],
            'estimated_timeline': '2-3 weeks',
            'potential_issues': ['May require additional verification'],
            'requires_manual_review': False,
            'ambiguity_flags': []
        }
        
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message = Mock()
        mock_response.choices[0].message.content = json.dumps(mock_interpretation)
        
        with patch.object(self.service.client.chat.completions, 'create', return_value=mock_response):
            # Interpret the same policy multiple times
            result1 = self.service.interpret_policies([policy1], "test-user-id")
            result2 = self.service.interpret_policies([policy1], "test-user-id")
            
            # Property: Same policy should produce consistent interpretations
            if len(result1) > 0 and len(result2) > 0:
                interp1 = result1[0]
                interp2 = result2[0]
                
                # Core action should be preserved
                assert interp1['action_type'] == interp2['action_type'], \
                    f"Action type inconsistent: {interp1['action_type']} != {interp2['action_type']}"
                
                # Platform should be preserved
                assert interp1['platform_name'] == interp2['platform_name'], \
                    f"Platform name inconsistent: {interp1['platform_name']} != {interp2['platform_name']}"
                
                # Confidence should be consistent for same input
                confidence_diff = abs(interp1.get('interpretation_confidence', 0) - 
                                    interp2.get('interpretation_confidence', 0))
                assert confidence_diff < 0.1, \
                    f"Confidence scores too different: {interp1.get('interpretation_confidence')} vs {interp2.get('interpretation_confidence')}"
                
                # Required documentation should be consistent
                docs1 = set(interp1.get('required_documentation', []))
                docs2 = set(interp2.get('required_documentation', []))
                assert docs1 == docs2, \
                    f"Required documentation inconsistent: {docs1} != {docs2}"
                
                # Manual review flag should be consistent
                assert interp1.get('requires_manual_review') == interp2.get('requires_manual_review'), \
                    f"Manual review flag inconsistent: {interp1.get('requires_manual_review')} != {interp2.get('requires_manual_review')}"
        
        # Property: Different policies for same platform/action should have similar structure
        with patch.object(self.service.client.chat.completions, 'create', return_value=mock_response):
            result_diff1 = self.service.interpret_policies([policy1], "test-user-id")
            result_diff2 = self.service.interpret_policies([policy2], "test-user-id")
            
            if len(result_diff1) > 0 and len(result_diff2) > 0:
                interp_diff1 = result_diff1[0]
                interp_diff2 = result_diff2[0]
                
                # Same platform/action should have same core properties
                assert interp_diff1['action_type'] == interp_diff2['action_type'], \
                    f"Same action type should be preserved across different policy texts"
                
                assert interp_diff1['platform_name'] == interp_diff2['platform_name'], \
                    f"Same platform should be preserved across different policy texts"
                
                # Should have similar required documentation for same platform
                docs_diff1 = set(interp_diff1.get('required_documentation', []))
                docs_diff2 = set(interp_diff2.get('required_documentation', []))
                common_docs = docs_diff1.intersection(docs_diff2)
                assert len(common_docs) > 0, \
                    f"Same platform should have some common documentation requirements"
    
    @given(
        platform_name=st.sampled_from(['gmail', 'facebook', 'chase_bank', 'twitter', 'linkedin']),
        action_type=st.sampled_from(['delete', 'memorialize', 'lock']),
        user_name=st.text(min_size=5, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Zs'))),
        account_id=st.text(min_size=5, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Po')))
    )
    @settings(max_examples=100)
    def test_property_9_platform_notification_generation_completeness(self, platform_name, action_type, user_name, account_id):
        """
        Property 9: Platform Notification Generation Completeness
        For any policy execution (delete, memorialize, or lock), the Action Engine should 
        generate platform-specific notifications containing all required documentation 
        references and proper formatting.
        
        **Feature: ghost-identity-protection, Property 9: Platform Notification Generation Completeness**
        **Validates: Requirements 3.2, 3.3, 8.1, 8.2**
        """
        assume(user_name.strip() and account_id.strip())  # Ensure non-empty values
        
        # Create mock interpreted policy
        mock_policy = {
            'policy_id': 'test-policy-123',
            'action_type': action_type,
            'platform_name': platform_name,
            'account_identifier': account_id,
            'interpretation_confidence': 0.9,
            'structured_actions': [f'Contact {platform_name}', f'Request {action_type}'],
            'requires_manual_review': False
        }
        
        # Create mock user info
        user_info = {
            'full_name': user_name,
            'date_of_death': '2023-12-25',
            'user_id': 'test-user-456'
        }
        
        # Mock Azure OpenAI response for notification generation
        mock_notification = {
            'subject': f'Death Notification - Account {action_type.title()} Request for {user_name}',
            'body': f'Formal notification body for {platform_name} regarding {action_type} action',
            'required_documents': ['death_certificate', 'id_verification'],
            'contact_information': 'Contact details for follow-up',
            'delivery_method': 'email',
            'urgency_level': 'normal',
            'follow_up_timeline': '2-3 weeks',
            'additional_notes': 'Platform-specific instructions'
        }
        
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message = Mock()
        mock_response.choices[0].message.content = json.dumps(mock_notification)
        
        with patch.object(self.service.client.chat.completions, 'create', return_value=mock_response):
            # Generate notification
            notifications = self.service.generate_platform_notifications([mock_policy], user_info, "test-user-id")
            
            # Property: Should generate exactly one notification for valid policy
            assert len(notifications) == 1, \
                f"Should generate exactly one notification, got {len(notifications)}"
            
            notification = notifications[0]
            
            # Property: Notification should contain all required fields
            required_fields = ['subject', 'body', 'required_documents', 'contact_information', 
                             'delivery_method', 'platform', 'action_type', 'generated_at']
            
            for field in required_fields:
                assert field in notification, \
                    f"Notification missing required field: {field}"
                
                assert notification[field] is not None, \
                    f"Required field {field} should not be None"
            
            # Property: Platform and action type should match input
            assert notification['platform'] == platform_name, \
                f"Platform mismatch: expected {platform_name}, got {notification['platform']}"
            
            assert notification['action_type'] == action_type, \
                f"Action type mismatch: expected {action_type}, got {notification['action_type']}"
            
            # Property: User name should appear in subject or body
            subject_body_text = (notification['subject'] + ' ' + notification['body']).lower()
            assert user_name.lower() in subject_body_text, \
                f"User name '{user_name}' should appear in notification text"
            
            # Property: Required documents should include death certificate
            required_docs = notification.get('required_documents', [])
            assert isinstance(required_docs, list), \
                f"Required documents should be a list, got {type(required_docs)}"
            
            assert len(required_docs) > 0, \
                f"Should have at least one required document"
            
            # Death certificate should always be required
            doc_names = [doc.lower() for doc in required_docs]
            assert any('death' in doc and 'certificate' in doc for doc in doc_names), \
                f"Death certificate should be in required documents: {required_docs}"
            
            # Property: Notification should have valid timestamp
            generated_at = notification.get('generated_at')
            assert generated_at is not None, \
                f"Notification should have generated_at timestamp"
            
            # Should be valid ISO format
            try:
                datetime.fromisoformat(generated_at.replace('Z', '+00:00'))
            except ValueError:
                pytest.fail(f"Invalid timestamp format: {generated_at}")
            
            # Property: Status should indicate readiness
            assert notification.get('status') == 'ready', \
                f"Notification status should be 'ready', got {notification.get('status')}"
    
    @given(
        error_scenario=st.sampled_from(['json_parse_error', 'azure_service_error', 'network_timeout']),
        platform_name=st.sampled_from(['gmail', 'facebook', 'chase_bank']),
        action_type=st.sampled_from(['delete', 'memorialize'])
    )
    @settings(max_examples=50)
    def test_ai_interpretation_error_handling_consistency(self, error_scenario, platform_name, action_type):
        """
        Additional property: Error handling should be consistent and provide fallback interpretations
        """
        # Create mock policy
        policy = self._create_mock_policy("Delete my account when I die", platform_name, action_type)
        
        if error_scenario == 'json_parse_error':
            # Mock response with invalid JSON
            mock_response = Mock()
            mock_response.choices = [Mock()]
            mock_response.choices[0].message = Mock()
            mock_response.choices[0].message.content = "Invalid JSON response"
            
            with patch.object(self.service.client.chat.completions, 'create', return_value=mock_response):
                result = self.service.interpret_policies([policy], "test-user-id")
                
                # Should provide fallback interpretation
                assert len(result) == 1, "Should provide fallback interpretation"
                interpretation = result[0]
                
                # Should flag for manual review
                assert interpretation.get('requires_manual_review') == True, \
                    "JSON parse error should require manual review"
                
                # Should have interpretation error
                assert 'interpretation_error' in interpretation, \
                    "Should record interpretation error"
                
                # Should preserve basic policy info
                assert interpretation['action_type'] == action_type, \
                    "Should preserve action type in fallback"
                
                assert interpretation['platform_name'] == platform_name, \
                    "Should preserve platform name in fallback"
        
        elif error_scenario == 'azure_service_error':
            # Mock Azure service error
            with patch.object(self.service.client.chat.completions, 'create', 
                            side_effect=Exception("Azure service unavailable")):
                result = self.service.interpret_policies([policy], "test-user-id")
                
                # Should provide fallback interpretation
                assert len(result) == 1, "Should provide fallback interpretation"
                interpretation = result[0]
                
                # Should flag for manual review
                assert interpretation.get('requires_manual_review') == True, \
                    "Service error should require manual review"
                
                # Should have fallback flag
                assert interpretation.get('fallback_interpretation') == True, \
                    "Should mark as fallback interpretation"
    
    def _create_mock_policy(self, policy_text: str, platform_name: str, action_type: str) -> ActionPolicy:
        """Create a mock ActionPolicy for testing"""
        policy = Mock(spec=ActionPolicy)
        policy.policy_id = f"test-policy-{hash(policy_text) % 10000}"
        policy.platform_name = platform_name
        policy.action_type = action_type
        policy.account_identifier = "test@example.com"
        policy.priority = 1
        
        # Mock policy details
        policy_details = {
            'natural_language_policy': policy_text,
            'specific_instructions': f'Please {action_type} my {platform_name} account',
            'conditions': ['After death verification'],
            'created_at': datetime.utcnow().isoformat()
        }
        
        policy.get_policy_details.return_value = policy_details
        
        return policy
    
    @given(
        confidence_score=st.floats(min_value=0.0, max_value=1.0),
        platform_name=st.sampled_from(['gmail', 'facebook', 'chase_bank'])
    )
    @settings(max_examples=50)
    def test_confidence_threshold_consistency(self, confidence_score, platform_name):
        """
        Additional property: Low confidence interpretations should consistently require manual review
        """
        # Create mock interpretation with specific confidence
        interpretation = {
            'action_type': 'delete',
            'platform_name': platform_name,
            'account_identifier': 'test@example.com',
            'interpretation_confidence': confidence_score,
            'structured_actions': ['Contact platform'],
            'required_documentation': ['death_certificate'],
            'estimated_timeline': '2 weeks',
            'potential_issues': [],
            'requires_manual_review': False,
            'ambiguity_flags': []
        }
        
        # Create mock policy for validation
        mock_policy = Mock(spec=ActionPolicy)
        mock_policy.action_type = 'delete'
        mock_policy.platform_name = platform_name
        mock_policy.account_identifier = 'test@example.com'
        
        # Test validation
        validation_result = self.service._validate_interpretation(interpretation, mock_policy)
        
        # Property: Low confidence should trigger manual review
        if confidence_score < 0.7:
            assert interpretation.get('requires_manual_review') == True, \
                f"Low confidence ({confidence_score}) should require manual review"
            
            assert len(validation_result['validation_issues']) > 0, \
                f"Low confidence should generate validation issues"
        
        # Property: High confidence should not automatically require manual review
        elif confidence_score >= 0.9:
            # Should not require manual review unless there are other issues
            if not validation_result['validation_issues']:
                assert interpretation.get('requires_manual_review') == False, \
                    f"High confidence ({confidence_score}) should not require manual review if no other issues"