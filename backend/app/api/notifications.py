"""
Notification API endpoints
Provides REST API for notification delivery and template management
"""
import logging
from flask import Blueprint, request, jsonify
from typing import Dict, Any, List

from app.services.notification_delivery import NotificationDeliveryService, DeliveryStatus
from app.services.notification_templates import NotificationTemplateService
from app.services.action_engine import ActionEngineService
from app.services.audit import AuditService
from app.services.error_handling import UserFeedbackService

logger = logging.getLogger(__name__)

# Create Blueprint
notifications_bp = Blueprint('notifications', __name__, url_prefix='/api/notifications')

# Initialize services lazily to avoid configuration issues during import
delivery_service = None
template_service = None
action_engine = None
audit_service = None
feedback_service = None

def get_delivery_service():
    global delivery_service
    if delivery_service is None:
        delivery_service = NotificationDeliveryService()
    return delivery_service

def get_template_service():
    global template_service
    if template_service is None:
        template_service = NotificationTemplateService()
    return template_service

def get_action_engine():
    global action_engine
    if action_engine is None:
        action_engine = ActionEngineService()
    return action_engine

def get_audit_service():
    global audit_service
    if audit_service is None:
        audit_service = AuditService()
    return audit_service

def get_feedback_service():
    global feedback_service
    if feedback_service is None:
        feedback_service = UserFeedbackService()
    return feedback_service

@notifications_bp.route('/deliver', methods=['POST'])
def deliver_notification():
    """
    Deliver a single notification
    
    Expected JSON payload:
    {
        "notification": {
            "platform": "google",
            "action_type": "delete",
            "subject": "...",
            "body": "...",
            "delivery_method": "email",
            "recipient_email": "support@platform.com"
        },
        "user_id": "user_uuid"
    }
    """
    try:
        data = request.get_json()
        
        if not data or 'notification' not in data:
            return jsonify({
                'error': 'Missing notification data',
                'status': 'error'
            }), 400
        
        notification = data['notification']
        user_id = data.get('user_id')
        delivery_method = data.get('delivery_method')
        
        # Validate required fields
        required_fields = ['platform', 'action_type']
        for field in required_fields:
            if field not in notification:
                return jsonify({
                    'error': f'Missing required field: {field}',
                    'status': 'error'
                }), 400
        
        # Deliver notification
        result = get_delivery_service().deliver_notification(
            notification=notification,
            delivery_method=delivery_method,
            user_id=user_id
        )
        
        return jsonify({
            'status': 'success',
            'delivery_result': result
        }), 200
        
    except Exception as e:
        logger.error(f"Error in deliver_notification endpoint: {str(e)}")
        return jsonify({
            'error': str(e),
            'status': 'error'
        }), 500

@notifications_bp.route('/deliver/batch', methods=['POST'])
def deliver_batch_notifications():
    """
    Deliver multiple notifications in batch
    
    Expected JSON payload:
    {
        "notifications": [
            {
                "platform": "google",
                "action_type": "delete",
                "subject": "...",
                "body": "..."
            }
        ],
        "user_id": "user_uuid"
    }
    """
    try:
        data = request.get_json()
        
        if not data or 'notifications' not in data:
            return jsonify({
                'error': 'Missing notifications data',
                'status': 'error'
            }), 400
        
        notifications = data['notifications']
        user_id = data.get('user_id')
        
        if not isinstance(notifications, list) or len(notifications) == 0:
            return jsonify({
                'error': 'Notifications must be a non-empty list',
                'status': 'error'
            }), 400
        
        # Deliver notifications in batch
        result = get_delivery_service().batch_deliver_notifications(
            notifications=notifications,
            user_id=user_id
        )
        
        return jsonify({
            'status': 'success',
            'batch_result': result
        }), 200
        
    except Exception as e:
        logger.error(f"Error in deliver_batch_notifications endpoint: {str(e)}")
        return jsonify({
            'error': str(e),
            'status': 'error'
        }), 500

@notifications_bp.route('/status/<notification_id>', methods=['GET'])
def get_delivery_status(notification_id: str):
    """
    Get delivery status for a specific notification
    """
    try:
        status = get_delivery_service().get_delivery_status(notification_id)
        
        if not status:
            return jsonify({
                'error': 'Notification not found',
                'status': 'error'
            }), 404
        
        return jsonify({
            'status': 'success',
            'delivery_status': status
        }), 200
        
    except Exception as e:
        logger.error(f"Error in get_delivery_status endpoint: {str(e)}")
        return jsonify({
            'error': str(e),
            'status': 'error'
        }), 500

@notifications_bp.route('/retry/process', methods=['POST'])
def process_retry_queue():
    """
    Process notifications that are ready for retry
    
    Expected JSON payload:
    {
        "user_id": "user_uuid"
    }
    """
    try:
        data = request.get_json() or {}
        user_id = data.get('user_id')
        
        # Process retry queue
        result = get_delivery_service().process_retry_queue(user_id=user_id)
        
        return jsonify({
            'status': 'success',
            'retry_result': result
        }), 200
        
    except Exception as e:
        logger.error(f"Error in process_retry_queue endpoint: {str(e)}")
        return jsonify({
            'error': str(e),
            'status': 'error'
        }), 500

@notifications_bp.route('/statistics', methods=['GET'])
def get_delivery_statistics():
    """
    Get delivery statistics across all notifications
    """
    try:
        stats = get_delivery_service().get_delivery_statistics()
        
        return jsonify({
            'status': 'success',
            'statistics': stats
        }), 200
        
    except Exception as e:
        logger.error(f"Error in get_delivery_statistics endpoint: {str(e)}")
        return jsonify({
            'error': str(e),
            'status': 'error'
        }), 500

# Template Management Endpoints

@notifications_bp.route('/templates/<platform>/<action_type>', methods=['GET'])
def get_template(platform: str, action_type: str):
    """
    Get a template for a specific platform and action
    
    Query parameters:
    - template_type: email, form, api, letter (default: email)
    """
    try:
        template_type = request.args.get('template_type', 'email')
        
        template = get_template_service().get_template(platform, action_type, template_type)
        
        if not template:
            return jsonify({
                'error': 'Template not found',
                'status': 'error'
            }), 404
        
        return jsonify({
            'status': 'success',
            'template': template
        }), 200
        
    except Exception as e:
        logger.error(f"Error in get_template endpoint: {str(e)}")
        return jsonify({
            'error': str(e),
            'status': 'error'
        }), 500

@notifications_bp.route('/templates', methods=['POST'])
def create_custom_template():
    """
    Create a custom template
    
    Expected JSON payload:
    {
        "platform": "custom_platform",
        "action_type": "delete",
        "template_type": "email",
        "template_data": {
            "subject": "...",
            "body": "...",
            "required_docs": [...],
            "delivery_method": "email"
        },
        "user_id": "user_uuid"
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'error': 'Missing request data',
                'status': 'error'
            }), 400
        
        required_fields = ['platform', 'action_type', 'template_type', 'template_data']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'error': f'Missing required field: {field}',
                    'status': 'error'
                }), 400
        
        platform = data['platform']
        action_type = data['action_type']
        template_type = data['template_type']
        template_data = data['template_data']
        user_id = data.get('user_id')
        
        # Create custom template
        success = get_template_service().create_custom_template(
            platform=platform,
            action_type=action_type,
            template_type=template_type,
            template_data=template_data,
            user_id=user_id
        )
        
        if success:
            return jsonify({
                'status': 'success',
                'message': 'Custom template created successfully'
            }), 201
        else:
            return jsonify({
                'error': 'Failed to create custom template',
                'status': 'error'
            }), 400
        
    except Exception as e:
        logger.error(f"Error in create_custom_template endpoint: {str(e)}")
        return jsonify({
            'error': str(e),
            'status': 'error'
        }), 500

@notifications_bp.route('/templates/validate', methods=['POST'])
def validate_template():
    """
    Validate template data
    
    Expected JSON payload:
    {
        "template_data": {
            "subject": "...",
            "body": "...",
            "delivery_method": "email"
        }
    }
    """
    try:
        data = request.get_json()
        
        if not data or 'template_data' not in data:
            return jsonify({
                'error': 'Missing template_data',
                'status': 'error'
            }), 400
        
        template_data = data['template_data']
        
        # Validate template
        validation_result = get_template_service().validate_template(template_data)
        
        return jsonify({
            'status': 'success',
            'validation_result': validation_result
        }), 200
        
    except Exception as e:
        logger.error(f"Error in validate_template endpoint: {str(e)}")
        return jsonify({
            'error': str(e),
            'status': 'error'
        }), 500

@notifications_bp.route('/templates/generate', methods=['POST'])
def generate_notification_from_template():
    """
    Generate a complete notification from template
    
    Expected JSON payload:
    {
        "platform": "google",
        "action_type": "delete",
        "template_type": "email",
        "context": {
            "full_name": "John Doe",
            "date_of_death": "2024-01-01",
            "account_identifier": "john.doe@gmail.com",
            "contact_name": "Jane Doe",
            "contact_email": "jane.doe@email.com",
            "relationship": "Spouse"
        }
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'error': 'Missing request data',
                'status': 'error'
            }), 400
        
        required_fields = ['platform', 'action_type', 'context']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'error': f'Missing required field: {field}',
                    'status': 'error'
                }), 400
        
        platform = data['platform']
        action_type = data['action_type']
        context = data['context']
        template_type = data.get('template_type', 'email')
        
        # Generate notification from template
        notification = get_template_service().generate_notification_from_template(
            platform=platform,
            action_type=action_type,
            context=context,
            template_type=template_type
        )
        
        if notification:
            return jsonify({
                'status': 'success',
                'notification': notification
            }), 200
        else:
            return jsonify({
                'error': 'Template not found or generation failed',
                'status': 'error'
            }), 404
        
    except Exception as e:
        logger.error(f"Error in generate_notification_from_template endpoint: {str(e)}")
        return jsonify({
            'error': str(e),
            'status': 'error'
        }), 500

@notifications_bp.route('/templates/list', methods=['GET'])
def list_available_templates():
    """
    List all available templates
    
    Query parameters:
    - platform: Optional platform filter
    """
    try:
        platform = request.args.get('platform')
        
        templates = get_template_service().list_available_templates(platform=platform)
        
        return jsonify({
            'status': 'success',
            'templates': templates
        }), 200
        
    except Exception as e:
        logger.error(f"Error in list_available_templates endpoint: {str(e)}")
        return jsonify({
            'error': str(e),
            'status': 'error'
        }), 500

@notifications_bp.route('/templates/statistics', methods=['GET'])
def get_template_statistics():
    """
    Get statistics about available templates
    """
    try:
        stats = get_template_service().get_template_statistics()
        
        return jsonify({
            'status': 'success',
            'statistics': stats
        }), 200
        
    except Exception as e:
        logger.error(f"Error in get_template_statistics endpoint: {str(e)}")
        return jsonify({
            'error': str(e),
            'status': 'error'
        }), 500

@notifications_bp.route('/templates/requirements/<platform>', methods=['GET'])
def get_platform_requirements(platform: str):
    """
    Get platform-specific requirements and contact information
    """
    try:
        requirements = get_template_service().get_platform_requirements(platform)
        
        return jsonify({
            'status': 'success',
            'requirements': requirements
        }), 200
        
    except Exception as e:
        logger.error(f"Error in get_platform_requirements endpoint: {str(e)}")
        return jsonify({
            'error': str(e),
            'status': 'error'
        }), 500

# Integration endpoint for complete workflow

@notifications_bp.route('/execute-policies', methods=['POST'])
def execute_notification_policies():
    """
    Execute complete notification workflow: interpret policies and deliver notifications
    
    Expected JSON payload:
    {
        "user_policies": [
            {
                "policy_id": "uuid",
                "platform_name": "google",
                "action_type": "delete",
                "account_identifier": "user@gmail.com"
            }
        ],
        "user_info": {
            "full_name": "John Doe",
            "date_of_death": "2024-01-01",
            "contact_name": "Jane Doe",
            "contact_email": "jane.doe@email.com",
            "relationship": "Spouse"
        },
        "user_id": "user_uuid",
        "delivery_method": "email"
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'error': 'Missing request data',
                'status': 'error'
            }), 400
        
        required_fields = ['user_policies', 'user_info', 'user_id']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'error': f'Missing required field: {field}',
                    'status': 'error'
                }), 400
        
        user_policies = data['user_policies']
        user_info = data['user_info']
        user_id = data['user_id']
        delivery_method = data.get('delivery_method', 'email')
        
        # Convert policy dictionaries to ActionPolicy-like objects for processing
        # In a real implementation, these would be proper ActionPolicy objects from the database
        
        # Step 1: Interpret policies using Action Engine
        interpreted_policies = []
        for policy_data in user_policies:
            # Create a mock ActionPolicy object for the action engine
            class MockActionPolicy:
                def __init__(self, data):
                    self.policy_id = data.get('policy_id')
                    self.platform_name = data.get('platform_name')
                    self.action_type = data.get('action_type')
                    self.account_identifier = data.get('account_identifier')
                    self.asset_type = data.get('asset_type', 'unknown')
                    self.priority = data.get('priority', 1)
                
                def get_policy_details(self):
                    return {
                        'natural_language_policy': f"{self.action_type} my {self.platform_name} account",
                        'specific_instructions': '',
                        'conditions': []
                    }
            
            mock_policy = MockActionPolicy(policy_data)
            
            # Generate notification using template service
            context = {
                **user_info,
                'platform': policy_data.get('platform_name'),
                'account_identifier': policy_data.get('account_identifier')
            }
            
            notification = get_template_service().generate_notification_from_template(
                platform=policy_data.get('platform_name'),
                action_type=policy_data.get('action_type'),
                context=context,
                template_type='email'
            )
            
            if notification:
                notification['policy_id'] = policy_data.get('policy_id')
                notification['delivery_method'] = delivery_method
                interpreted_policies.append(notification)
        
        # Step 2: Deliver notifications
        if interpreted_policies:
            delivery_result = get_delivery_service().batch_deliver_notifications(
                notifications=interpreted_policies,
                user_id=user_id
            )
            
            return jsonify({
                'status': 'success',
                'interpreted_policies': len(interpreted_policies),
                'delivery_result': delivery_result
            }), 200
        else:
            return jsonify({
                'error': 'No valid notifications could be generated',
                'status': 'error'
            }), 400
        
    except Exception as e:
        logger.error(f"Error in execute_notification_policies endpoint: {str(e)}")
        return jsonify({
            'error': str(e),
            'status': 'error'
        }), 500

# Error handling

@notifications_bp.errorhandler(404)
def not_found(error):
    return jsonify({
        'error': 'Endpoint not found',
        'status': 'error'
    }), 404

@notifications_bp.errorhandler(405)
def method_not_allowed(error):
    return jsonify({
        'error': 'Method not allowed',
        'status': 'error'
    }), 405

@notifications_bp.errorhandler(500)
def internal_error(error):
    return jsonify({
        'error': 'Internal server error',
        'status': 'error'
    }), 500