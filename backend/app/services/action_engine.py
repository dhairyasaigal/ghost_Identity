"""
Azure OpenAI Action Engine Service
Provides AI-powered policy interpretation and notification generation
"""
import os
import json
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

from openai import AzureOpenAI
from azure.core.exceptions import AzureError

from app.services.azure_resilience import with_azure_retry, AzureServiceError
from app.services.audit import AuditService
from app.models.action_policy import ActionPolicy
from app.models.user_profile import UserProfile

logger = logging.getLogger(__name__)

class ActionEngineService:
    """
    Service for interpreting natural language policies and generating platform notifications
    using Azure OpenAI
    """
    
    def __init__(self):
        """Initialize the Action Engine Service with Azure OpenAI client"""
        self.audit_service = AuditService()
        
        # Azure OpenAI configuration
        self.endpoint = os.getenv('AZURE_OPENAI_ENDPOINT')
        self.api_key = os.getenv('AZURE_OPENAI_KEY')
        self.deployment_name = os.getenv('AZURE_OPENAI_DEPLOYMENT')
        
        if not all([self.endpoint, self.api_key, self.deployment_name]):
            raise ValueError("Missing required Azure OpenAI configuration. Check AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_KEY, and AZURE_OPENAI_DEPLOYMENT environment variables.")
        
        # Initialize Azure OpenAI client
        self.client = AzureOpenAI(
            api_key=self.api_key,
            api_version="2024-02-01",
            azure_endpoint=self.endpoint
        )
        
        # Policy interpretation configuration
        self.interpretation_temperature = 0.1  # Low temperature for consistent interpretation
        self.notification_temperature = 0.2    # Slightly higher for more natural language
        self.max_tokens = 1000
        
        # Platform-specific templates and requirements
        self.platform_requirements = {
            'gmail': {
                'required_docs': ['death_certificate', 'id_verification'],
                'contact_method': 'email',
                'special_instructions': 'Must include Google account recovery information',
                'contact_email': 'accounts-support@google.com',
                'form_url': 'https://support.google.com/accounts/contact/deceased'
            },
            'facebook': {
                'required_docs': ['death_certificate', 'relationship_proof'],
                'contact_method': 'form',
                'special_instructions': 'Use Facebook memorialization request form',
                'contact_email': None,
                'form_url': 'https://www.facebook.com/help/contact/228813257197480'
            },
            'instagram': {
                'required_docs': ['death_certificate', 'relationship_proof'],
                'contact_method': 'form',
                'special_instructions': 'Use Instagram memorialization request form',
                'contact_email': None,
                'form_url': 'https://help.instagram.com/contact/1474899482730688'
            },
            'chase_bank': {
                'required_docs': ['death_certificate', 'estate_documents', 'id_verification'],
                'contact_method': 'phone_and_mail',
                'special_instructions': 'Contact estate services department',
                'contact_phone': '1-800-935-9935',
                'contact_email': 'estate.services@chase.com'
            },
            'wells_fargo': {
                'required_docs': ['death_certificate', 'estate_documents', 'id_verification'],
                'contact_method': 'phone_and_mail',
                'special_instructions': 'Contact estate services department',
                'contact_phone': '1-800-869-3557',
                'contact_email': 'estate.services@wellsfargo.com'
            },
            'bank_of_america': {
                'required_docs': ['death_certificate', 'estate_documents', 'id_verification'],
                'contact_method': 'phone_and_mail',
                'special_instructions': 'Contact estate administration services',
                'contact_phone': '1-800-432-1000',
                'contact_email': 'estate.administration@bankofamerica.com'
            },
            'twitter': {
                'required_docs': ['death_certificate', 'id_verification'],
                'contact_method': 'email',
                'special_instructions': 'Use Twitter deactivation request process',
                'contact_email': 'support@twitter.com',
                'form_url': 'https://help.twitter.com/forms/privacy'
            },
            'linkedin': {
                'required_docs': ['death_certificate', 'relationship_proof'],
                'contact_method': 'form',
                'special_instructions': 'Use LinkedIn memorial request form',
                'contact_email': None,
                'form_url': 'https://www.linkedin.com/help/linkedin/answer/2842'
            },
            'apple': {
                'required_docs': ['death_certificate', 'court_order'],
                'contact_method': 'email',
                'special_instructions': 'Apple requires court order for account access',
                'contact_email': 'privacy@apple.com',
                'form_url': 'https://privacy.apple.com/contact'
            },
            'microsoft': {
                'required_docs': ['death_certificate', 'id_verification'],
                'contact_method': 'form',
                'special_instructions': 'Use Microsoft account closure request',
                'contact_email': None,
                'form_url': 'https://account.microsoft.com/profile/contact-info'
            }
        }
    
    @with_azure_retry('azure_openai')
    def interpret_policies(self, user_policies: List[ActionPolicy], user_id: str) -> List[Dict[str, Any]]:
        """
        Use Azure OpenAI to interpret natural language policies and generate structured action plans
        
        Args:
            user_policies: List of ActionPolicy objects to interpret
            user_id: ID of the user for audit logging
            
        Returns:
            List of interpreted policy dictionaries with structured action plans
            
        Raises:
            AzureServiceError: When Azure OpenAI service fails
        """
        interpreted_policies = []
        
        for policy in user_policies:
            try:
                # Get policy details
                policy_details = policy.get_policy_details()
                if not policy_details:
                    # Create basic policy details if none exist
                    policy_details = {
                        'natural_language_policy': f"{policy.action_type} my {policy.platform_name} account",
                        'specific_instructions': '',
                        'conditions': []
                    }
                
                # Create interpretation prompt
                prompt = self._create_policy_interpretation_prompt(policy, policy_details)
                
                # Log the interpretation attempt
                self.audit_service.create_log_entry(
                    user_id=user_id,
                    event_type="policy_interpretation_attempt",
                    event_description=f"Interpreting policy for {policy.platform_name}",
                    ai_service_used="azure_openai",
                    input_data={
                        'policy_id': policy.policy_id,
                        'platform_name': policy.platform_name,
                        'action_type': policy.action_type,
                        'policy_text': policy_details.get('natural_language_policy', '')
                    }
                )
                
                # Call Azure OpenAI
                response = self.client.chat.completions.create(
                    model=self.deployment_name,
                    messages=[
                        {
                            "role": "system", 
                            "content": "You are an AI assistant that interprets digital legacy policies and generates structured action plans. Always respond with valid JSON."
                        },
                        {
                            "role": "user", 
                            "content": prompt
                        }
                    ],
                    temperature=self.interpretation_temperature,
                    max_tokens=self.max_tokens
                )
                
                # Parse the response
                response_content = response.choices[0].message.content.strip()
                
                try:
                    interpreted_policy = json.loads(response_content)
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse JSON response for policy {policy.policy_id}: {response_content}")
                    # Create a fallback interpretation
                    interpreted_policy = self._create_fallback_interpretation(policy, policy_details)
                    interpreted_policy['interpretation_error'] = f"JSON parsing failed: {str(e)}"
                    interpreted_policy['requires_manual_review'] = True
                
                # Add metadata
                interpreted_policy['policy_id'] = policy.policy_id
                interpreted_policy['original_policy'] = policy_details
                interpreted_policy['interpretation_timestamp'] = datetime.utcnow().isoformat()
                
                # Validate interpretation
                validation_result = self._validate_interpretation(interpreted_policy, policy)
                interpreted_policy.update(validation_result)
                
                interpreted_policies.append(interpreted_policy)
                
                # Log successful interpretation
                self.audit_service.create_log_entry(
                    user_id=user_id,
                    event_type="policy_interpretation_success",
                    event_description=f"Successfully interpreted policy for {policy.platform_name}",
                    ai_service_used="azure_openai",
                    input_data={'policy_id': policy.policy_id},
                    output_data=interpreted_policy,
                    status="success"
                )
                
            except AzureError as e:
                logger.error(f"Azure OpenAI error interpreting policy {policy.policy_id}: {str(e)}")
                
                # Create fallback interpretation
                fallback_interpretation = self._create_fallback_interpretation(policy, policy_details or {})
                fallback_interpretation['interpretation_error'] = f"Azure OpenAI error: {str(e)}"
                fallback_interpretation['requires_manual_review'] = True
                interpreted_policies.append(fallback_interpretation)
                
                # Log the error
                self.audit_service.create_log_entry(
                    user_id=user_id,
                    event_type="policy_interpretation_error",
                    event_description=f"Azure OpenAI error interpreting policy for {policy.platform_name}: {str(e)}",
                    ai_service_used="azure_openai",
                    input_data={'policy_id': policy.policy_id},
                    status="failure"
                )
                
            except Exception as e:
                logger.error(f"Unexpected error interpreting policy {policy.policy_id}: {str(e)}")
                
                # Create fallback interpretation
                fallback_interpretation = self._create_fallback_interpretation(policy, policy_details or {})
                fallback_interpretation['interpretation_error'] = f"Unexpected error: {str(e)}"
                fallback_interpretation['requires_manual_review'] = True
                interpreted_policies.append(fallback_interpretation)
                
                # Log the error
                self.audit_service.create_log_entry(
                    user_id=user_id,
                    event_type="policy_interpretation_error",
                    event_description=f"Unexpected error interpreting policy for {policy.platform_name}: {str(e)}",
                    ai_service_used="azure_openai",
                    input_data={'policy_id': policy.policy_id},
                    status="failure"
                )
        
        return interpreted_policies
    
    @with_azure_retry('azure_openai')
    def generate_platform_notifications(self, policies: List[Dict[str, Any]], 
                                      user_info: Dict[str, Any], user_id: str) -> List[Dict[str, Any]]:
        """
        Generate professional notification emails/requests for third-party platforms
        
        Args:
            policies: List of interpreted policy dictionaries
            user_info: Dictionary containing deceased person's information
            user_id: ID of the user for audit logging
            
        Returns:
            List of notification dictionaries with platform-specific formatting
            
        Raises:
            AzureServiceError: When Azure OpenAI service fails
        """
        notifications = []
        
        for policy in policies:
            try:
                # Skip policies that require manual review
                if policy.get('requires_manual_review', False):
                    logger.info(f"Skipping notification generation for policy {policy.get('policy_id')} - requires manual review")
                    continue
                
                # Only generate notifications for actionable policies
                action_type = policy.get('action_type', '').lower()
                if action_type not in ['delete', 'memorialize', 'lock']:
                    logger.info(f"Skipping notification generation for policy {policy.get('policy_id')} - action type '{action_type}' not supported")
                    continue
                
                # Generate notification
                notification = self._generate_notification_for_platform(policy, user_info, user_id)
                notifications.append(notification)
                
            except Exception as e:
                logger.error(f"Error generating notification for policy {policy.get('policy_id', 'unknown')}: {str(e)}")
                
                # Create error notification
                error_notification = {
                    'policy_id': policy.get('policy_id'),
                    'platform': policy.get('platform_name', 'unknown'),
                    'status': 'error',
                    'error_message': str(e),
                    'requires_manual_intervention': True,
                    'generated_at': datetime.utcnow().isoformat()
                }
                notifications.append(error_notification)
                
                # Log the error
                self.audit_service.create_log_entry(
                    user_id=user_id,
                    event_type="notification_generation_error",
                    event_description=f"Error generating notification for {policy.get('platform_name', 'unknown')}: {str(e)}",
                    ai_service_used="azure_openai",
                    input_data={'policy_id': policy.get('policy_id')},
                    status="failure"
                )
        
        return notifications
    
    def _create_policy_interpretation_prompt(self, policy: ActionPolicy, 
                                           policy_details: Dict[str, Any]) -> str:
        """
        Create a prompt for Azure OpenAI to interpret a natural language policy
        
        Args:
            policy: ActionPolicy object
            policy_details: Dictionary containing policy details
            
        Returns:
            Formatted prompt string
        """
        natural_language_policy = policy_details.get('natural_language_policy', '')
        specific_instructions = policy_details.get('specific_instructions', '')
        conditions = policy_details.get('conditions', [])
        
        prompt = f"""
Interpret the following digital legacy policy and generate a structured action plan:

Platform: {policy.platform_name}
Asset Type: {policy.asset_type}
Account Identifier: {policy.account_identifier}
Requested Action: {policy.action_type}
Priority: {policy.priority}

Natural Language Policy: "{natural_language_policy}"
Specific Instructions: "{specific_instructions}"
Conditions: {json.dumps(conditions)}

Please analyze this policy and respond with a JSON object containing:
1. "action_type": The specific action to take (delete, memorialize, lock, transfer)
2. "platform_name": The platform name (normalized)
3. "account_identifier": The account to act upon
4. "interpretation_confidence": A score from 0.0 to 1.0 indicating confidence in interpretation
5. "structured_actions": A list of specific steps to execute the policy
6. "required_documentation": List of documents needed for the platform
7. "estimated_timeline": Expected time to complete the action
8. "potential_issues": List of potential complications or requirements
9. "requires_manual_review": Boolean indicating if human review is needed
10. "ambiguity_flags": List of any ambiguous aspects that need clarification

Consider platform-specific requirements and procedures. If the policy is ambiguous or conflicting, set "requires_manual_review" to true and explain the issues in "ambiguity_flags".

Respond only with valid JSON.
"""
        return prompt
    
    def _generate_notification_for_platform(self, policy: Dict[str, Any], 
                                          user_info: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """
        Generate platform-specific notification using Azure OpenAI
        
        Args:
            policy: Interpreted policy dictionary
            user_info: Dictionary containing deceased person's information
            user_id: ID of the user for audit logging
            
        Returns:
            Dictionary containing notification details
        """
        platform_name = policy.get('platform_name', '').lower()
        action_type = policy.get('action_type', '').lower()
        
        # Get platform-specific requirements
        platform_reqs = self.platform_requirements.get(platform_name, {
            'required_docs': ['death_certificate'],
            'contact_method': 'email',
            'special_instructions': 'Contact customer service'
        })
        
        # Create notification generation prompt
        prompt = self._create_notification_prompt(policy, user_info, platform_reqs)
        
        try:
            # Log notification generation attempt
            self.audit_service.create_log_entry(
                user_id=user_id,
                event_type="notification_generation_attempt",
                event_description=f"Generating {action_type} notification for {platform_name}",
                ai_service_used="azure_openai",
                input_data={
                    'policy_id': policy.get('policy_id'),
                    'platform_name': platform_name,
                    'action_type': action_type
                }
            )
            
            # Call Azure OpenAI
            response = self.client.chat.completions.create(
                model=self.deployment_name,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a professional legal assistant generating formal death notifications for financial and digital platforms. Always respond with valid JSON."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=self.notification_temperature,
                max_tokens=self.max_tokens
            )
            
            # Parse response
            response_content = response.choices[0].message.content.strip()
            
            try:
                notification_data = json.loads(response_content)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse notification JSON for {platform_name}: {response_content}")
                # Create fallback notification
                notification_data = self._create_fallback_notification(policy, user_info, platform_reqs)
                notification_data['generation_error'] = f"JSON parsing failed: {str(e)}"
            
            # Add metadata
            notification_data['policy_id'] = policy.get('policy_id')
            notification_data['platform'] = platform_name
            notification_data['action_type'] = action_type
            notification_data['generated_at'] = datetime.utcnow().isoformat()
            notification_data['status'] = 'ready'
            
            # Log successful generation
            self.audit_service.create_log_entry(
                user_id=user_id,
                event_type="notification_generation_success",
                event_description=f"Successfully generated {action_type} notification for {platform_name}",
                ai_service_used="azure_openai",
                input_data={'policy_id': policy.get('policy_id')},
                output_data=notification_data,
                status="success"
            )
            
            return notification_data
            
        except AzureError as e:
            logger.error(f"Azure OpenAI error generating notification for {platform_name}: {str(e)}")
            
            # Create fallback notification
            fallback_notification = self._create_fallback_notification(policy, user_info, platform_reqs)
            fallback_notification['generation_error'] = f"Azure OpenAI error: {str(e)}"
            fallback_notification['requires_manual_intervention'] = True
            
            # Log the error
            self.audit_service.create_log_entry(
                user_id=user_id,
                event_type="notification_generation_error",
                event_description=f"Azure OpenAI error generating notification for {platform_name}: {str(e)}",
                ai_service_used="azure_openai",
                input_data={'policy_id': policy.get('policy_id')},
                status="failure"
            )
            
            return fallback_notification
    
    def _create_notification_prompt(self, policy: Dict[str, Any], 
                                  user_info: Dict[str, Any], 
                                  platform_reqs: Dict[str, Any]) -> str:
        """
        Create a prompt for generating platform-specific notifications
        
        Args:
            policy: Interpreted policy dictionary
            user_info: Dictionary containing deceased person's information
            platform_reqs: Platform-specific requirements
            
        Returns:
            Formatted prompt string
        """
        platform_name = policy.get('platform_name', '')
        action_type = policy.get('action_type', '')
        account_identifier = policy.get('account_identifier', '')
        
        prompt = f"""
Generate a professional notification for {platform_name} to {action_type} the account of a deceased person.

Deceased Person Information:
- Full Name: {user_info.get('full_name', '')}
- Date of Death: {user_info.get('date_of_death', '')}
- Account Identifier: {account_identifier}

Requested Action: {action_type}
Platform Requirements:
- Required Documents: {platform_reqs.get('required_docs', [])}
- Contact Method: {platform_reqs.get('contact_method', 'email')}
- Special Instructions: {platform_reqs.get('special_instructions', '')}

Policy Details:
{json.dumps(policy.get('structured_actions', []), indent=2)}

Please generate a formal notification with the following JSON structure:
{{
    "subject": "Professional email subject line",
    "body": "Formal notification body with all required information",
    "required_documents": ["list", "of", "required", "documents"],
    "contact_information": "Contact details for follow-up",
    "delivery_method": "email/form/phone/mail",
    "urgency_level": "normal/high/urgent",
    "follow_up_timeline": "Expected response timeframe",
    "additional_notes": "Any special considerations or instructions"
}}

The notification should be:
1. Professional and respectful in tone
2. Include all necessary legal and identification information
3. Reference the specific account and requested action
4. List all required documentation
5. Provide clear next steps and contact information
6. Follow platform-specific procedures when known

Respond only with valid JSON.
"""
        return prompt
    
    def _create_fallback_interpretation(self, policy: ActionPolicy, 
                                     policy_details: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a basic fallback interpretation when AI processing fails
        
        Args:
            policy: ActionPolicy object
            policy_details: Dictionary containing policy details
            
        Returns:
            Basic interpretation dictionary
        """
        return {
            'action_type': policy.action_type,
            'platform_name': policy.platform_name,
            'account_identifier': policy.account_identifier,
            'interpretation_confidence': 0.5,
            'structured_actions': [
                f"Contact {policy.platform_name} customer service",
                f"Request {policy.action_type} action for account {policy.account_identifier}",
                "Provide death certificate and identification",
                "Follow platform-specific procedures"
            ],
            'required_documentation': ['death_certificate', 'id_verification'],
            'estimated_timeline': '2-4 weeks',
            'potential_issues': ['May require additional documentation', 'Platform-specific procedures may vary'],
            'requires_manual_review': True,
            'ambiguity_flags': ['AI interpretation failed - manual review required'],
            'fallback_interpretation': True
        }
    
    def _create_fallback_notification(self, policy: Dict[str, Any], 
                                    user_info: Dict[str, Any], 
                                    platform_reqs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a basic fallback notification when AI generation fails
        
        Args:
            policy: Interpreted policy dictionary
            user_info: Dictionary containing deceased person's information
            platform_reqs: Platform-specific requirements
            
        Returns:
            Basic notification dictionary
        """
        platform_name = policy.get('platform_name', '')
        action_type = policy.get('action_type', '')
        full_name = user_info.get('full_name', '')
        
        return {
            'subject': f"Death Notification - Account {action_type.title()} Request for {full_name}",
            'body': f"""
Dear {platform_name} Customer Service,

I am writing to notify you of the death of {full_name} and to request that their account be {action_type}d according to their wishes.

Account Information:
- Account Holder: {full_name}
- Account Identifier: {policy.get('account_identifier', '')}
- Date of Death: {user_info.get('date_of_death', '')}

Requested Action: {action_type.title()} the account

I have attached the required documentation as per your platform's procedures. Please let me know if you need any additional information or documentation.

Thank you for your assistance during this difficult time.

Sincerely,
[Trusted Contact Name]
[Contact Information]
            """.strip(),
            'required_documents': platform_reqs.get('required_docs', ['death_certificate']),
            'contact_information': 'Please provide trusted contact information',
            'delivery_method': platform_reqs.get('contact_method', 'email'),
            'urgency_level': 'normal',
            'follow_up_timeline': '2-3 weeks',
            'additional_notes': 'This is a fallback notification - manual review recommended',
            'fallback_notification': True
        }
    
    def _validate_interpretation(self, interpretation: Dict[str, Any], 
                               original_policy: ActionPolicy) -> Dict[str, Any]:
        """
        Validate the AI interpretation against the original policy
        
        Args:
            interpretation: AI-generated interpretation
            original_policy: Original ActionPolicy object
            
        Returns:
            Dictionary with validation results
        """
        validation_result = {
            'validation_passed': True,
            'validation_issues': []
        }
        
        # Check if action type matches
        if interpretation.get('action_type', '').lower() != original_policy.action_type.lower():
            validation_result['validation_passed'] = False
            validation_result['validation_issues'].append(
                f"Action type mismatch: expected '{original_policy.action_type}', got '{interpretation.get('action_type')}'"
            )
        
        # Check if platform name is consistent
        if interpretation.get('platform_name', '').lower() != original_policy.platform_name.lower():
            validation_result['validation_passed'] = False
            validation_result['validation_issues'].append(
                f"Platform name mismatch: expected '{original_policy.platform_name}', got '{interpretation.get('platform_name')}'"
            )
        
        # Check confidence level
        confidence = interpretation.get('interpretation_confidence', 0.0)
        if confidence < 0.7:
            interpretation['requires_manual_review'] = True
            validation_result['validation_issues'].append(
                f"Low confidence score: {confidence} - manual review recommended"
            )
        
        # Check for required fields
        required_fields = ['structured_actions', 'required_documentation', 'estimated_timeline']
        for field in required_fields:
            if field not in interpretation or not interpretation[field]:
                validation_result['validation_passed'] = False
                validation_result['validation_issues'].append(f"Missing required field: {field}")
        
        return validation_result
    
    def create_personalized_message(self, template: str, user_info: Dict[str, Any], 
                                   policy: Dict[str, Any]) -> str:
        """
        Create personalized message using deceased person's data
        
        Args:
            template: Message template with placeholders
            user_info: Dictionary containing deceased person's information
            policy: Policy information for context
            
        Returns:
            Personalized message string
        """
        try:
            # Define available placeholders
            placeholders = {
                'full_name': user_info.get('full_name', '[Name]'),
                'first_name': user_info.get('full_name', '[Name]').split()[0] if user_info.get('full_name') else '[First Name]',
                'date_of_death': user_info.get('date_of_death', '[Date of Death]'),
                'platform_name': policy.get('platform_name', '[Platform]'),
                'account_identifier': policy.get('account_identifier', '[Account]'),
                'action_type': policy.get('action_type', '[Action]').title(),
                'current_date': datetime.utcnow().strftime('%B %d, %Y')
            }
            
            # Replace placeholders in template
            personalized_message = template
            for placeholder, value in placeholders.items():
                personalized_message = personalized_message.replace(f'{{{placeholder}}}', str(value))
            
            return personalized_message
            
        except Exception as e:
            logger.error(f"Error personalizing message: {str(e)}")
            return template  # Return original template if personalization fails
    
    def get_platform_specific_template(self, platform_name: str, action_type: str) -> Dict[str, str]:
        """
        Get platform-specific notification templates
        
        Args:
            platform_name: Name of the platform
            action_type: Type of action (delete, memorialize, lock)
            
        Returns:
            Dictionary containing subject and body templates
        """
        platform_templates = {
            'gmail': {
                'delete': {
                    'subject': 'Request for Account Closure - {full_name} (Deceased)',
                    'body': '''Dear Google Account Support,

I am writing to request the closure of a Google account belonging to {full_name}, who passed away on {date_of_death}.

Account Information:
- Account Holder: {full_name}
- Email Address: {account_identifier}
- Date of Death: {date_of_death}

I am requesting that this account be permanently deleted in accordance with the deceased person's wishes. I have attached the required documentation including the death certificate and my identification.

Please confirm receipt of this request and provide information about the account closure process and timeline.

Thank you for your assistance during this difficult time.

Sincerely,
[Trusted Contact Name]
[Contact Information]'''
                },
                'memorialize': {
                    'subject': 'Request for Account Memorialization - {full_name} (Deceased)',
                    'body': '''Dear Google Account Support,

I am writing to request the memorialization of a Google account belonging to {full_name}, who passed away on {date_of_death}.

Account Information:
- Account Holder: {full_name}
- Email Address: {account_identifier}
- Date of Death: {date_of_death}

I am requesting that this account be converted to a memorial account to preserve the digital legacy of the deceased. I have attached the required documentation including the death certificate and proof of my relationship to the deceased.

Please provide information about the memorialization process and any additional steps required.

Thank you for your assistance.

Sincerely,
[Trusted Contact Name]
[Contact Information]'''
                }
            },
            'facebook': {
                'delete': {
                    'subject': 'Request for Account Deletion - {full_name} (Deceased)',
                    'body': '''Dear Facebook Support,

I am submitting a request for the deletion of a Facebook account belonging to {full_name}, who passed away on {date_of_death}.

Account Information:
- Account Holder: {full_name}
- Profile URL/Email: {account_identifier}
- Date of Death: {date_of_death}

The deceased person specifically requested that their Facebook account be deleted after their death. I have attached the required documentation including the death certificate and proof of my relationship to the deceased.

Please process this deletion request and confirm when the account has been permanently removed.

Thank you for your assistance.

Sincerely,
[Trusted Contact Name]
[Contact Information]'''
                },
                'memorialize': {
                    'subject': 'Request for Account Memorialization - {full_name} (Deceased)',
                    'body': '''Dear Facebook Support,

I am submitting a request for the memorialization of a Facebook account belonging to {full_name}, who passed away on {date_of_death}.

Account Information:
- Account Holder: {full_name}
- Profile URL/Email: {account_identifier}
- Date of Death: {date_of_death}

I would like to request that this account be converted to a memorial account to honor the memory of the deceased. I have attached the required documentation including the death certificate and proof of my relationship to the deceased.

Please provide information about the memorialization process and timeline.

Thank you for your assistance.

Sincerely,
[Trusted Contact Name]
[Contact Information]'''
                }
            },
            'chase_bank': {
                'delete': {
                    'subject': 'Estate Services - Account Closure Request for {full_name} (Deceased)',
                    'body': '''Dear Chase Estate Services,

I am writing to notify you of the death of {full_name} and to request the closure of their banking accounts.

Deceased Account Holder Information:
- Full Name: {full_name}
- Account Number/Identifier: {account_identifier}
- Date of Death: {date_of_death}

I am the authorized representative for the estate and am requesting that all accounts be closed and funds be handled according to estate procedures. I have attached the required documentation including:
- Certified death certificate
- Estate documentation
- My identification as the authorized representative

Please contact me to discuss the account closure process and any additional requirements.

Thank you for your assistance.

Sincerely,
[Trusted Contact Name]
[Title/Relationship to Deceased]
[Contact Information]'''
                },
                'lock': {
                    'subject': 'Estate Services - Account Security Request for {full_name} (Deceased)',
                    'body': '''Dear Chase Estate Services,

I am writing to notify you of the death of {full_name} and to request that their banking accounts be secured immediately.

Deceased Account Holder Information:
- Full Name: {full_name}
- Account Number/Identifier: {account_identifier}
- Date of Death: {date_of_death}

I am requesting that all accounts be frozen to prevent unauthorized access while estate matters are being resolved. I have attached the required documentation including:
- Certified death certificate
- Estate documentation
- My identification as the authorized representative

Please confirm that the accounts have been secured and provide information about the next steps in the estate process.

Thank you for your prompt attention to this matter.

Sincerely,
[Trusted Contact Name]
[Title/Relationship to Deceased]
[Contact Information]'''
                }
            }
        }
        
        # Get platform-specific template or use generic template
        platform_key = platform_name.lower()
        action_key = action_type.lower()
        
        if platform_key in platform_templates and action_key in platform_templates[platform_key]:
            return platform_templates[platform_key][action_key]
        else:
            # Return generic template
            return {
                'subject': f'Death Notification - Account {action_type.title()} Request for {{full_name}}',
                'body': f'''Dear {platform_name} Customer Service,

I am writing to notify you of the death of {{full_name}} and to request that their account be {action_type}d.

Account Information:
- Account Holder: {{full_name}}
- Account Identifier: {{account_identifier}}
- Date of Death: {{date_of_death}}

I have attached the required documentation as per your platform's procedures. Please let me know if you need any additional information.

Thank you for your assistance during this difficult time.

Sincerely,
[Trusted Contact Name]
[Contact Information]'''
            }
    
    def generate_notification_with_template(self, policy: Dict[str, Any], 
                                          user_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate notification using platform-specific templates
        
        Args:
            policy: Interpreted policy dictionary
            user_info: Dictionary containing deceased person's information
            
        Returns:
            Dictionary containing notification with personalized content
        """
        platform_name = policy.get('platform_name', '').lower()
        action_type = policy.get('action_type', '').lower()
        
        # Get platform requirements
        platform_reqs = self.platform_requirements.get(platform_name, {
            'required_docs': ['death_certificate'],
            'contact_method': 'email',
            'special_instructions': 'Contact customer service'
        })
        
        # Get template
        template = self.get_platform_specific_template(platform_name, action_type)
        
        # Personalize the message
        personalized_subject = self.create_personalized_message(template['subject'], user_info, policy)
        personalized_body = self.create_personalized_message(template['body'], user_info, policy)
        
        # Create notification
        notification = {
            'policy_id': policy.get('policy_id'),
            'platform': platform_name,
            'action_type': action_type,
            'subject': personalized_subject,
            'body': personalized_body,
            'required_documents': platform_reqs.get('required_docs', ['death_certificate']),
            'contact_information': self._get_platform_contact_info(platform_name, platform_reqs),
            'delivery_method': platform_reqs.get('contact_method', 'email'),
            'urgency_level': 'normal',
            'follow_up_timeline': '2-3 weeks',
            'additional_notes': platform_reqs.get('special_instructions', ''),
            'generated_at': datetime.utcnow().isoformat(),
            'status': 'ready',
            'template_used': True
        }
        
        return notification
    
    def _get_platform_contact_info(self, platform_name: str, platform_reqs: Dict[str, Any]) -> str:
        """
        Get formatted contact information for a platform
        
        Args:
            platform_name: Name of the platform
            platform_reqs: Platform requirements dictionary
            
        Returns:
            Formatted contact information string
        """
        contact_info_parts = []
        
        if platform_reqs.get('contact_email'):
            contact_info_parts.append(f"Email: {platform_reqs['contact_email']}")
        
        if platform_reqs.get('contact_phone'):
            contact_info_parts.append(f"Phone: {platform_reqs['contact_phone']}")
        
        if platform_reqs.get('form_url'):
            contact_info_parts.append(f"Online Form: {platform_reqs['form_url']}")
        
        if not contact_info_parts:
            contact_info_parts.append(f"Contact {platform_name} customer service")
        
        return " | ".join(contact_info_parts)
    
    def batch_generate_notifications(self, policies: List[Dict[str, Any]], 
                                   user_info: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """
        Generate notifications for multiple policies with batch processing
        
        Args:
            policies: List of interpreted policy dictionaries
            user_info: Dictionary containing deceased person's information
            user_id: ID of the user for audit logging
            
        Returns:
            Dictionary containing batch results and individual notifications
        """
        batch_results = {
            'total_policies': len(policies),
            'successful_notifications': 0,
            'failed_notifications': 0,
            'notifications': [],
            'errors': [],
            'batch_id': f"batch_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{hash(user_id) % 10000}",
            'generated_at': datetime.utcnow().isoformat()
        }
        
        # Log batch start
        self.audit_service.create_log_entry(
            user_id=user_id,
            event_type="notification_batch_start",
            event_description=f"Starting batch notification generation for {len(policies)} policies",
            ai_service_used="azure_openai",
            input_data={'batch_id': batch_results['batch_id'], 'policy_count': len(policies)}
        )
        
        for policy in policies:
            try:
                # Skip policies that require manual review
                if policy.get('requires_manual_review', False):
                    batch_results['errors'].append({
                        'policy_id': policy.get('policy_id'),
                        'error': 'Policy requires manual review',
                        'action': 'skipped'
                    })
                    continue
                
                # Generate notification using template first, fall back to AI if needed
                try:
                    notification = self.generate_notification_with_template(policy, user_info)
                    batch_results['notifications'].append(notification)
                    batch_results['successful_notifications'] += 1
                    
                except Exception as template_error:
                    logger.warning(f"Template generation failed for policy {policy.get('policy_id')}, falling back to AI: {str(template_error)}")
                    
                    # Fall back to AI generation
                    ai_notifications = self.generate_platform_notifications([policy], user_info, user_id)
                    if ai_notifications:
                        batch_results['notifications'].extend(ai_notifications)
                        batch_results['successful_notifications'] += len(ai_notifications)
                    else:
                        raise Exception("Both template and AI generation failed")
                
            except Exception as e:
                logger.error(f"Error generating notification for policy {policy.get('policy_id', 'unknown')}: {str(e)}")
                batch_results['failed_notifications'] += 1
                batch_results['errors'].append({
                    'policy_id': policy.get('policy_id'),
                    'error': str(e),
                    'action': 'failed'
                })
        
        # Log batch completion
        self.audit_service.create_log_entry(
            user_id=user_id,
            event_type="notification_batch_complete",
            event_description=f"Batch notification generation complete: {batch_results['successful_notifications']} successful, {batch_results['failed_notifications']} failed",
            ai_service_used="azure_openai",
            input_data={'batch_id': batch_results['batch_id']},
            output_data=batch_results,
            status="success" if batch_results['failed_notifications'] == 0 else "partial_success"
        )
        
        return batch_results