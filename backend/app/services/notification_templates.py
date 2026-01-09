"""
Notification Templates and Customization Service
Provides templates for major platforms and custom notification format support
"""
import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from enum import Enum
import re

from app.services.audit import AuditService

logger = logging.getLogger(__name__)

class TemplateType(Enum):
    """Enumeration for template types"""
    EMAIL = "email"
    FORM = "form"
    API = "api"
    LETTER = "letter"

class ActionType(Enum):
    """Enumeration for action types"""
    DELETE = "delete"
    MEMORIALIZE = "memorialize"
    LOCK = "lock"
    TRANSFER = "transfer"

class NotificationTemplateService:
    """
    Service for managing notification templates and customization
    """
    
    def __init__(self):
        """Initialize the Notification Template Service"""
        self.audit_service = AuditService()
        
        # Template storage (in production, this would be database-backed)
        self.templates = {}
        self.custom_templates = {}
        
        # Initialize built-in templates
        self._initialize_builtin_templates()
        
        # Template validation patterns
        self.required_placeholders = {
            'basic': ['full_name', 'date_of_death', 'platform_name'],
            'account': ['account_identifier'],
            'contact': ['contact_name', 'contact_email'],
            'legal': ['relationship', 'legal_authority']
        }
        
        # Platform-specific requirements
        self.platform_requirements = {
            'google': {
                'required_docs': ['death_certificate', 'id_verification', 'account_recovery_info'],
                'contact_methods': ['email', 'form'],
                'special_requirements': ['Google account recovery information required'],
                'processing_time': '2-4 weeks',
                'contact_info': {
                    'email': 'accounts-support@google.com',
                    'form_url': 'https://support.google.com/accounts/contact/deceased'
                }
            },
            'facebook': {
                'required_docs': ['death_certificate', 'relationship_proof'],
                'contact_methods': ['form'],
                'special_requirements': ['Must use Facebook memorialization request form'],
                'processing_time': '1-2 weeks',
                'contact_info': {
                    'form_url': 'https://www.facebook.com/help/contact/228813257197480'
                }
            },
            'instagram': {
                'required_docs': ['death_certificate', 'relationship_proof'],
                'contact_methods': ['form'],
                'special_requirements': ['Must use Instagram memorialization request form'],
                'processing_time': '1-2 weeks',
                'contact_info': {
                    'form_url': 'https://help.instagram.com/contact/1474899482730688'
                }
            },
            'twitter': {
                'required_docs': ['death_certificate', 'id_verification'],
                'contact_methods': ['email', 'form'],
                'special_requirements': ['Use Twitter deactivation request process'],
                'processing_time': '1-3 weeks',
                'contact_info': {
                    'email': 'support@twitter.com',
                    'form_url': 'https://help.twitter.com/forms/privacy'
                }
            },
            'linkedin': {
                'required_docs': ['death_certificate', 'relationship_proof'],
                'contact_methods': ['form'],
                'special_requirements': ['Use LinkedIn memorial request form'],
                'processing_time': '1-2 weeks',
                'contact_info': {
                    'form_url': 'https://www.linkedin.com/help/linkedin/answer/2842'
                }
            },
            'chase_bank': {
                'required_docs': ['death_certificate', 'estate_documents', 'id_verification'],
                'contact_methods': ['phone', 'mail', 'email'],
                'special_requirements': ['Contact estate services department', 'Executor documentation required'],
                'processing_time': '2-6 weeks',
                'contact_info': {
                    'phone': '1-800-935-9935',
                    'email': 'estate.services@chase.com',
                    'address': 'Chase Estate Services, P.O. Box 36520, Louisville, KY 40233'
                }
            },
            'wells_fargo': {
                'required_docs': ['death_certificate', 'estate_documents', 'id_verification'],
                'contact_methods': ['phone', 'mail', 'email'],
                'special_requirements': ['Contact estate services department', 'Probate documentation may be required'],
                'processing_time': '2-6 weeks',
                'contact_info': {
                    'phone': '1-800-869-3557',
                    'email': 'estate.services@wellsfargo.com'
                }
            },
            'bank_of_america': {
                'required_docs': ['death_certificate', 'estate_documents', 'id_verification'],
                'contact_methods': ['phone', 'mail', 'email'],
                'special_requirements': ['Contact estate administration services', 'Legal documentation required'],
                'processing_time': '3-8 weeks',
                'contact_info': {
                    'phone': '1-800-432-1000',
                    'email': 'estate.administration@bankofamerica.com'
                }
            },
            'apple': {
                'required_docs': ['death_certificate', 'court_order'],
                'contact_methods': ['email', 'form'],
                'special_requirements': ['Apple requires court order for account access', 'Legal process required'],
                'processing_time': '4-12 weeks',
                'contact_info': {
                    'email': 'privacy@apple.com',
                    'form_url': 'https://privacy.apple.com/contact'
                }
            },
            'microsoft': {
                'required_docs': ['death_certificate', 'id_verification'],
                'contact_methods': ['form', 'email'],
                'special_requirements': ['Use Microsoft account closure request'],
                'processing_time': '2-4 weeks',
                'contact_info': {
                    'form_url': 'https://account.microsoft.com/profile/contact-info'
                }
            }
        }
    
    def _initialize_builtin_templates(self):
        """Initialize built-in templates for major platforms"""
        
        # Google/Gmail Templates
        self.templates['google'] = {
            'delete': {
                'email': {
                    'subject': 'Request for Account Closure - {full_name} (Deceased)',
                    'body': '''Dear Google Account Support,

I am writing to request the closure of a Google account belonging to {full_name}, who passed away on {date_of_death}.

Account Information:
- Account Holder: {full_name}
- Email Address: {account_identifier}
- Date of Death: {date_of_death}

I am {relationship} and am authorized to handle the digital affairs of the deceased. I am requesting that this account be permanently deleted in accordance with the deceased person's wishes.

Required Documentation:
I have attached the following required documentation:
- Certified copy of death certificate
- My identification as the authorized representative
- Google account recovery information (if available)

Please confirm receipt of this request and provide information about the account closure process and timeline.

Thank you for your assistance during this difficult time.

Sincerely,
{contact_name}
{relationship} of {full_name}
{contact_email}
{contact_phone}

Date: {current_date}''',
                    'required_docs': ['death_certificate', 'id_verification', 'account_recovery_info'],
                    'delivery_method': 'email'
                }
            },
            'memorialize': {
                'email': {
                    'subject': 'Request for Account Memorialization - {full_name} (Deceased)',
                    'body': '''Dear Google Account Support,

I am writing to request the memorialization of a Google account belonging to {full_name}, who passed away on {date_of_death}.

Account Information:
- Account Holder: {full_name}
- Email Address: {account_identifier}
- Date of Death: {date_of_death}

I am {relationship} and am authorized to handle the digital affairs of the deceased. I am requesting that this account be converted to a memorial account to preserve the digital legacy of the deceased.

Required Documentation:
I have attached the following required documentation:
- Certified copy of death certificate
- My identification and proof of relationship to the deceased
- Google account recovery information (if available)

Please provide information about the memorialization process and any additional steps required.

Thank you for your assistance.

Sincerely,
{contact_name}
{relationship} of {full_name}
{contact_email}
{contact_phone}

Date: {current_date}''',
                    'required_docs': ['death_certificate', 'relationship_proof', 'account_recovery_info'],
                    'delivery_method': 'email'
                }
            }
        }
        
        # Facebook Templates
        self.templates['facebook'] = {
            'delete': {
                'form': {
                    'subject': 'Request for Account Deletion - {full_name} (Deceased)',
                    'body': '''I am submitting a request for the deletion of a Facebook account belonging to {full_name}, who passed away on {date_of_death}.

Account Information:
- Account Holder: {full_name}
- Profile URL/Email: {account_identifier}
- Date of Death: {date_of_death}

The deceased person specifically requested that their Facebook account be deleted after their death. I am {relationship} and have the authority to make this request.

I have attached the required documentation including the death certificate and proof of my relationship to the deceased.

Please process this deletion request and confirm when the account has been permanently removed.

Contact Information:
{contact_name}
{contact_email}
{contact_phone}''',
                    'required_docs': ['death_certificate', 'relationship_proof'],
                    'delivery_method': 'form',
                    'form_url': 'https://www.facebook.com/help/contact/228813257197480'
                }
            },
            'memorialize': {
                'form': {
                    'subject': 'Request for Account Memorialization - {full_name} (Deceased)',
                    'body': '''I am submitting a request for the memorialization of a Facebook account belonging to {full_name}, who passed away on {date_of_death}.

Account Information:
- Account Holder: {full_name}
- Profile URL/Email: {account_identifier}
- Date of Death: {date_of_death}

I would like to request that this account be converted to a memorial account to honor the memory of the deceased. I am {relationship} and have the authority to make this request.

I have attached the required documentation including the death certificate and proof of my relationship to the deceased.

Please provide information about the memorialization process and timeline.

Contact Information:
{contact_name}
{contact_email}
{contact_phone}''',
                    'required_docs': ['death_certificate', 'relationship_proof'],
                    'delivery_method': 'form',
                    'form_url': 'https://www.facebook.com/help/contact/228813257197480'
                }
            }
        }
        
        # Banking Templates (Chase Bank example)
        self.templates['chase_bank'] = {
            'lock': {
                'email': {
                    'subject': 'Estate Services - Account Security Request for {full_name} (Deceased)',
                    'body': '''Dear Chase Estate Services,

I am writing to notify you of the death of {full_name} and to request that their banking accounts be secured immediately.

Deceased Account Holder Information:
- Full Name: {full_name}
- Date of Birth: {date_of_birth}
- Date of Death: {date_of_death}
- Account Number/Identifier: {account_identifier}
- Social Security Number: [Last 4 digits: {ssn_last_four}]

I am {relationship} and am the authorized representative for the estate. I am requesting that all accounts be frozen to prevent unauthorized access while estate matters are being resolved.

Required Documentation:
I have attached the following required documentation:
- Certified copy of death certificate
- Estate documentation (will, probate court appointment, etc.)
- My identification as the authorized representative

Please confirm that the accounts have been secured and provide information about the next steps in the estate process.

Contact Information for Follow-up:
{contact_name}
{relationship} of {full_name}
Email: {contact_email}
Phone: {contact_phone}
Address: {contact_address}

Thank you for your prompt attention to this matter.

Sincerely,
{contact_name}

Date: {current_date}''',
                    'required_docs': ['death_certificate', 'estate_documents', 'id_verification'],
                    'delivery_method': 'email'
                }
            },
            'delete': {
                'email': {
                    'subject': 'Estate Services - Account Closure Request for {full_name} (Deceased)',
                    'body': '''Dear Chase Estate Services,

I am writing to notify you of the death of {full_name} and to request the closure of their banking accounts.

Deceased Account Holder Information:
- Full Name: {full_name}
- Date of Birth: {date_of_birth}
- Date of Death: {date_of_death}
- Account Number/Identifier: {account_identifier}

I am {relationship} and am the authorized representative for the estate. I am requesting that all accounts be closed and funds be handled according to estate procedures.

Required Documentation:
I have attached the following required documentation:
- Certified copy of death certificate
- Estate documentation (will, letters testamentary, etc.)
- My identification as the authorized representative
- Tax identification number for the estate (if applicable)

Please contact me to discuss the account closure process, fund distribution, and any additional requirements.

Contact Information:
{contact_name}
{relationship} of {full_name}
Email: {contact_email}
Phone: {contact_phone}
Address: {contact_address}

Thank you for your assistance.

Sincerely,
{contact_name}

Date: {current_date}''',
                    'required_docs': ['death_certificate', 'estate_documents', 'id_verification'],
                    'delivery_method': 'email'
                }
            }
        }
        
        # Generic template for unknown platforms
        self.templates['generic'] = {
            'delete': {
                'email': {
                    'subject': 'Death Notification - Account Deletion Request for {full_name}',
                    'body': '''Dear {platform_name} Customer Service,

I am writing to notify you of the death of {full_name} and to request that their account be deleted.

Account Information:
- Account Holder: {full_name}
- Account Identifier: {account_identifier}
- Date of Death: {date_of_death}

I am {relationship} and am authorized to handle the digital affairs of the deceased. The deceased person requested that their {platform_name} account be permanently deleted.

I have attached the required documentation as per your platform's procedures. Please let me know if you need any additional information or documentation.

Thank you for your assistance during this difficult time.

Sincerely,
{contact_name}
{contact_email}
{contact_phone}

Date: {current_date}''',
                    'required_docs': ['death_certificate', 'id_verification'],
                    'delivery_method': 'email'
                }
            },
            'memorialize': {
                'email': {
                    'subject': 'Death Notification - Account Memorialization Request for {full_name}',
                    'body': '''Dear {platform_name} Customer Service,

I am writing to notify you of the death of {full_name} and to request that their account be memorialized.

Account Information:
- Account Holder: {full_name}
- Account Identifier: {account_identifier}
- Date of Death: {date_of_death}

I am {relationship} and am authorized to handle the digital affairs of the deceased. I would like to request that this account be converted to a memorial account to preserve the digital legacy of the deceased.

I have attached the required documentation as per your platform's procedures. Please provide information about your memorialization process and any additional steps required.

Thank you for your assistance.

Sincerely,
{contact_name}
{contact_email}
{contact_phone}

Date: {current_date}''',
                    'required_docs': ['death_certificate', 'relationship_proof'],
                    'delivery_method': 'email'
                }
            }
        }
    
    def get_template(self, platform: str, action_type: str, 
                    template_type: str = 'email') -> Optional[Dict[str, Any]]:
        """
        Get a template for a specific platform and action
        
        Args:
            platform: Platform name (e.g., 'google', 'facebook')
            action_type: Action type (e.g., 'delete', 'memorialize')
            template_type: Template type (e.g., 'email', 'form')
            
        Returns:
            Template dictionary or None if not found
        """
        platform_key = platform.lower()
        action_key = action_type.lower()
        type_key = template_type.lower()
        
        # Check custom templates first
        if platform_key in self.custom_templates:
            custom_platform = self.custom_templates[platform_key]
            if action_key in custom_platform and type_key in custom_platform[action_key]:
                return custom_platform[action_key][type_key]
        
        # Check built-in templates
        if platform_key in self.templates:
            builtin_platform = self.templates[platform_key]
            if action_key in builtin_platform and type_key in builtin_platform[action_key]:
                return builtin_platform[action_key][type_key]
        
        # Fall back to generic template
        if 'generic' in self.templates:
            generic_platform = self.templates['generic']
            if action_key in generic_platform and type_key in generic_platform[action_key]:
                return generic_platform[action_key][type_key]
        
        return None
    
    def create_custom_template(self, platform: str, action_type: str, 
                             template_type: str, template_data: Dict[str, Any],
                             user_id: str = None) -> bool:
        """
        Create a custom template for a platform
        
        Args:
            platform: Platform name
            action_type: Action type
            template_type: Template type
            template_data: Template data dictionary
            user_id: User ID for audit logging
            
        Returns:
            Boolean indicating success
        """
        try:
            # Validate template data
            validation_result = self.validate_template(template_data)
            if not validation_result['valid']:
                logger.error(f"Template validation failed: {validation_result['errors']}")
                return False
            
            # Initialize nested dictionaries if needed
            platform_key = platform.lower()
            action_key = action_type.lower()
            type_key = template_type.lower()
            
            if platform_key not in self.custom_templates:
                self.custom_templates[platform_key] = {}
            if action_key not in self.custom_templates[platform_key]:
                self.custom_templates[platform_key][action_key] = {}
            
            # Add metadata
            template_data['created_at'] = datetime.utcnow().isoformat()
            template_data['created_by'] = user_id
            template_data['template_version'] = '1.0'
            
            # Store template
            self.custom_templates[platform_key][action_key][type_key] = template_data
            
            # Log template creation
            if user_id:
                self.audit_service.create_log_entry(
                    user_id=user_id,
                    event_type="custom_template_created",
                    event_description=f"Created custom template for {platform} {action_type} {template_type}",
                    input_data={
                        'platform': platform,
                        'action_type': action_type,
                        'template_type': template_type
                    },
                    output_data=template_data,
                    status="success"
                )
            
            return True
            
        except Exception as e:
            logger.error(f"Error creating custom template: {str(e)}")
            return False
    
    def validate_template(self, template_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate template data structure and content
        
        Args:
            template_data: Template data to validate
            
        Returns:
            Dictionary containing validation results
        """
        validation_result = {
            'valid': True,
            'errors': [],
            'warnings': []
        }
        
        # Check required fields
        required_fields = ['subject', 'body']
        for field in required_fields:
            if field not in template_data or not template_data[field]:
                validation_result['valid'] = False
                validation_result['errors'].append(f"Missing required field: {field}")
        
        # Check for required placeholders
        if 'body' in template_data:
            body = template_data['body']
            
            # Check for basic placeholders
            basic_placeholders = ['full_name', 'date_of_death']
            for placeholder in basic_placeholders:
                if f'{{{placeholder}}}' not in body:
                    validation_result['warnings'].append(f"Missing recommended placeholder: {{{placeholder}}}")
            
            # Check for potentially dangerous content
            dangerous_patterns = [
                r'<script.*?>.*?</script>',  # Script tags
                r'javascript:',              # JavaScript URLs
                r'on\w+\s*=',               # Event handlers
            ]
            
            for pattern in dangerous_patterns:
                if re.search(pattern, body, re.IGNORECASE | re.DOTALL):
                    validation_result['valid'] = False
                    validation_result['errors'].append("Template contains potentially dangerous content")
                    break
        
        # Validate delivery method
        if 'delivery_method' in template_data:
            valid_methods = ['email', 'form', 'api', 'letter']
            if template_data['delivery_method'] not in valid_methods:
                validation_result['valid'] = False
                validation_result['errors'].append(f"Invalid delivery method: {template_data['delivery_method']}")
        
        return validation_result
    
    def personalize_template(self, template: Dict[str, Any], 
                           context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Personalize a template with context data
        
        Args:
            template: Template dictionary
            context: Context data for personalization
            
        Returns:
            Personalized template dictionary
        """
        personalized = template.copy()
        
        # Default context values
        default_context = {
            'current_date': datetime.utcnow().strftime('%B %d, %Y'),
            'platform_name': context.get('platform', 'Platform'),
            'relationship': context.get('relationship', 'Authorized Representative'),
            'contact_name': context.get('contact_name', '[Contact Name]'),
            'contact_email': context.get('contact_email', '[Contact Email]'),
            'contact_phone': context.get('contact_phone', '[Contact Phone]'),
            'contact_address': context.get('contact_address', '[Contact Address]')
        }
        
        # Merge context with defaults
        full_context = {**default_context, **context}
        
        # Personalize subject and body
        for field in ['subject', 'body']:
            if field in personalized and personalized[field]:
                personalized[field] = self._replace_placeholders(personalized[field], full_context)
        
        # Add personalization metadata
        personalized['personalized_at'] = datetime.utcnow().isoformat()
        personalized['context_used'] = list(full_context.keys())
        
        return personalized
    
    def _replace_placeholders(self, text: str, context: Dict[str, Any]) -> str:
        """
        Replace placeholders in text with context values
        
        Args:
            text: Text containing placeholders
            context: Context data
            
        Returns:
            Text with placeholders replaced
        """
        result = text
        
        for key, value in context.items():
            placeholder = f'{{{key}}}'
            if placeholder in result:
                result = result.replace(placeholder, str(value) if value is not None else f'[{key}]')
        
        return result
    
    def get_platform_requirements(self, platform: str) -> Dict[str, Any]:
        """
        Get platform-specific requirements and contact information
        
        Args:
            platform: Platform name
            
        Returns:
            Dictionary containing platform requirements
        """
        platform_key = platform.lower()
        return self.platform_requirements.get(platform_key, {
            'required_docs': ['death_certificate'],
            'contact_methods': ['email'],
            'special_requirements': ['Contact customer service'],
            'processing_time': '2-4 weeks',
            'contact_info': {}
        })
    
    def generate_notification_from_template(self, platform: str, action_type: str,
                                          context: Dict[str, Any],
                                          template_type: str = 'email') -> Optional[Dict[str, Any]]:
        """
        Generate a complete notification from template
        
        Args:
            platform: Platform name
            action_type: Action type
            context: Context data for personalization
            template_type: Template type
            
        Returns:
            Complete notification dictionary or None if template not found
        """
        # Get template
        template = self.get_template(platform, action_type, template_type)
        if not template:
            logger.warning(f"No template found for {platform} {action_type} {template_type}")
            return None
        
        # Personalize template
        personalized_template = self.personalize_template(template, context)
        
        # Get platform requirements
        platform_reqs = self.get_platform_requirements(platform)
        
        # Create complete notification
        notification = {
            'platform': platform,
            'action_type': action_type,
            'template_type': template_type,
            'subject': personalized_template.get('subject', ''),
            'body': personalized_template.get('body', ''),
            'delivery_method': personalized_template.get('delivery_method', 'email'),
            'required_documents': personalized_template.get('required_docs', platform_reqs.get('required_docs', [])),
            'contact_information': self._format_contact_info(platform_reqs.get('contact_info', {})),
            'form_url': personalized_template.get('form_url') or platform_reqs.get('contact_info', {}).get('form_url'),
            'processing_time': platform_reqs.get('processing_time', '2-4 weeks'),
            'special_requirements': platform_reqs.get('special_requirements', []),
            'generated_at': datetime.utcnow().isoformat(),
            'template_used': True,
            'personalization_context': context
        }
        
        return notification
    
    def _format_contact_info(self, contact_info: Dict[str, Any]) -> str:
        """
        Format contact information into a readable string
        
        Args:
            contact_info: Contact information dictionary
            
        Returns:
            Formatted contact information string
        """
        contact_parts = []
        
        if contact_info.get('email'):
            contact_parts.append(f"Email: {contact_info['email']}")
        
        if contact_info.get('phone'):
            contact_parts.append(f"Phone: {contact_info['phone']}")
        
        if contact_info.get('address'):
            contact_parts.append(f"Address: {contact_info['address']}")
        
        if contact_info.get('form_url'):
            contact_parts.append(f"Online Form: {contact_info['form_url']}")
        
        return " | ".join(contact_parts) if contact_parts else "Contact customer service"
    
    def list_available_templates(self, platform: str = None) -> Dict[str, Any]:
        """
        List all available templates, optionally filtered by platform
        
        Args:
            platform: Optional platform filter
            
        Returns:
            Dictionary containing available templates
        """
        available_templates = {
            'builtin_templates': {},
            'custom_templates': {},
            'total_count': 0
        }
        
        # Count built-in templates
        for plat, actions in self.templates.items():
            if platform and plat != platform.lower():
                continue
            
            available_templates['builtin_templates'][plat] = {}
            for action, types in actions.items():
                available_templates['builtin_templates'][plat][action] = list(types.keys())
                available_templates['total_count'] += len(types)
        
        # Count custom templates
        for plat, actions in self.custom_templates.items():
            if platform and plat != platform.lower():
                continue
            
            available_templates['custom_templates'][plat] = {}
            for action, types in actions.items():
                available_templates['custom_templates'][plat][action] = list(types.keys())
                available_templates['total_count'] += len(types)
        
        return available_templates
    
    def export_templates(self, platform: str = None) -> Dict[str, Any]:
        """
        Export templates for backup or sharing
        
        Args:
            platform: Optional platform filter
            
        Returns:
            Dictionary containing exported templates
        """
        export_data = {
            'export_timestamp': datetime.utcnow().isoformat(),
            'platform_filter': platform,
            'builtin_templates': {},
            'custom_templates': {}
        }
        
        # Export built-in templates
        for plat, actions in self.templates.items():
            if platform and plat != platform.lower():
                continue
            export_data['builtin_templates'][plat] = actions
        
        # Export custom templates
        for plat, actions in self.custom_templates.items():
            if platform and plat != platform.lower():
                continue
            export_data['custom_templates'][plat] = actions
        
        return export_data
    
    def import_templates(self, import_data: Dict[str, Any], 
                        user_id: str = None, overwrite: bool = False) -> Dict[str, Any]:
        """
        Import templates from exported data
        
        Args:
            import_data: Exported template data
            user_id: User ID for audit logging
            overwrite: Whether to overwrite existing templates
            
        Returns:
            Dictionary containing import results
        """
        import_results = {
            'imported_count': 0,
            'skipped_count': 0,
            'error_count': 0,
            'errors': []
        }
        
        try:
            # Import custom templates
            if 'custom_templates' in import_data:
                for platform, actions in import_data['custom_templates'].items():
                    for action, types in actions.items():
                        for template_type, template_data in types.items():
                            try:
                                # Check if template already exists
                                existing = self.get_template(platform, action, template_type)
                                if existing and not overwrite:
                                    import_results['skipped_count'] += 1
                                    continue
                                
                                # Validate and import template
                                if self.create_custom_template(platform, action, template_type, 
                                                             template_data, user_id):
                                    import_results['imported_count'] += 1
                                else:
                                    import_results['error_count'] += 1
                                    import_results['errors'].append(
                                        f"Failed to import template: {platform}/{action}/{template_type}"
                                    )
                                    
                            except Exception as e:
                                import_results['error_count'] += 1
                                import_results['errors'].append(
                                    f"Error importing {platform}/{action}/{template_type}: {str(e)}"
                                )
            
            # Log import results
            if user_id:
                self.audit_service.create_log_entry(
                    user_id=user_id,
                    event_type="templates_imported",
                    event_description=f"Imported {import_results['imported_count']} templates",
                    input_data={'import_source': 'file'},
                    output_data=import_results,
                    status="success" if import_results['error_count'] == 0 else "partial_success"
                )
            
        except Exception as e:
            logger.error(f"Error during template import: {str(e)}")
            import_results['errors'].append(f"Import failed: {str(e)}")
            import_results['error_count'] += 1
        
        return import_results
    
    def get_template_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about available templates
        
        Returns:
            Dictionary containing template statistics
        """
        stats = {
            'total_builtin_templates': 0,
            'total_custom_templates': 0,
            'platforms_with_templates': set(),
            'action_types_supported': set(),
            'template_types_available': set(),
            'platform_breakdown': {}
        }
        
        # Analyze built-in templates
        for platform, actions in self.templates.items():
            stats['platforms_with_templates'].add(platform)
            platform_count = 0
            
            for action, types in actions.items():
                stats['action_types_supported'].add(action)
                for template_type in types.keys():
                    stats['template_types_available'].add(template_type)
                    stats['total_builtin_templates'] += 1
                    platform_count += 1
            
            stats['platform_breakdown'][platform] = {
                'builtin_count': platform_count,
                'custom_count': 0
            }
        
        # Analyze custom templates
        for platform, actions in self.custom_templates.items():
            stats['platforms_with_templates'].add(platform)
            custom_count = 0
            
            for action, types in actions.items():
                stats['action_types_supported'].add(action)
                for template_type in types.keys():
                    stats['template_types_available'].add(template_type)
                    stats['total_custom_templates'] += 1
                    custom_count += 1
            
            if platform not in stats['platform_breakdown']:
                stats['platform_breakdown'][platform] = {'builtin_count': 0, 'custom_count': 0}
            stats['platform_breakdown'][platform]['custom_count'] = custom_count
        
        # Convert sets to lists for JSON serialization
        stats['platforms_with_templates'] = list(stats['platforms_with_templates'])
        stats['action_types_supported'] = list(stats['action_types_supported'])
        stats['template_types_available'] = list(stats['template_types_available'])
        
        return stats