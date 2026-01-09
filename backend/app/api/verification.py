"""
Death Verification and Policy Execution API Endpoints
Handles death certificate upload, verification, and automatic policy execution
"""
from flask import Blueprint, request, jsonify, session, current_app
from werkzeug.utils import secure_filename
from app.models.user_profile import UserProfile
from app.models.trusted_contact import TrustedContact
from app.models.action_policy import ActionPolicy
from app.services.database import DatabaseService
from app.services.audit import AuditService
from app.services.death_verification import DeathVerificationService
from app.services.action_engine import ActionEngineService
from datetime import datetime
from functools import wraps
import os
import uuid
import base64

verification_bp = Blueprint('verification', __name__, url_prefix='/api/verification')

# Allowed file extensions for death certificates
ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'tiff', 'bmp'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def require_trusted_contact_auth(f):
    """Decorator to require trusted contact authorization"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check if user is authenticated
        if 'user_id' not in session:
            return jsonify({'error': 'Authentication required'}), 401
        
        # For death verification, we need to validate trusted contact authorization
        # This will be checked in the individual endpoints based on the deceased user
        return f(*args, **kwargs)
    return decorated_function

@verification_bp.route('/upload-certificate', methods=['POST'])
@require_trusted_contact_auth
def upload_death_certificate():
    """
    Upload and process death certificate
    
    Expected form data:
    - certificate_file: Death certificate file (PDF or image)
    - deceased_user_email: Email of the deceased user
    - contact_email: Email of the trusted contact making the request
    """
    try:
        # Check if file is present
        if 'certificate_file' not in request.files:
            return jsonify({'error': 'No certificate file provided'}), 400
        
        file = request.files['certificate_file']
        deceased_user_email = request.form.get('deceased_user_email', '').lower().strip()
        contact_email = request.form.get('contact_email', '').lower().strip()
        
        if not deceased_user_email or not contact_email:
            return jsonify({'error': 'Deceased user email and contact email are required'}), 400
        
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Validate file
        if not allowed_file(file.filename):
            return jsonify({'error': f'Invalid file type. Allowed types: {", ".join(ALLOWED_EXTENSIONS)}'}), 400
        
        # Check file size
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)
        
        if file_size > MAX_FILE_SIZE:
            return jsonify({'error': 'File size too large. Maximum 10MB allowed'}), 400
        
        # Find deceased user
        deceased_user = UserProfile.query.filter_by(email=deceased_user_email).first()
        if not deceased_user:
            return jsonify({'error': 'Deceased user not found'}), 404
        
        # Verify trusted contact authorization
        trusted_contact = TrustedContact.query.filter_by(
            user_id=deceased_user.user_id,
            contact_email=contact_email,
            verification_status='verified'
        ).first()
        
        if not trusted_contact:
            # Log unauthorized verification attempt
            AuditService.create_log_entry(
                user_id=deceased_user.user_id,
                event_type='unauthorized_verification_attempt',
                event_description=f'Unauthorized death verification attempt by {contact_email}',
                input_data={
                    'contact_email': contact_email,
                    'deceased_user_email': deceased_user_email
                },
                status='failure'
            )
            return jsonify({'error': 'Unauthorized. You are not a verified trusted contact for this user'}), 403
        
        # Read file data
        file_data = file.read()
        
        # Process death certificate using Azure AI Vision
        death_verification_service = DeathVerificationService()
        verification_result = death_verification_service.process_death_certificate(file_data)
        
        # Log AI service call
        AuditService.log_ai_service_call(
            user_id=deceased_user.user_id,
            service_name='azure_vision',
            operation='death_certificate_ocr',
            input_data={
                'file_size': file_size,
                'file_type': file.filename.rsplit('.', 1)[1].lower(),
                'contact_email': contact_email
            },
            output_data=verification_result,
            status='success' if verification_result.get('status') == 'success' else 'failure'
        )
        
        if verification_result.get('status') != 'success':
            return jsonify({
                'error': 'Failed to process death certificate',
                'details': verification_result.get('error_message', 'Unknown error')
            }), 400
        
        # Verify death event against user profile
        extracted_data = verification_result.get('extracted_data', {})
        death_verified = death_verification_service.verify_death_event(extracted_data, deceased_user.user_id)
        
        if death_verified:
            # Update user status to deceased
            DatabaseService.safe_update(deceased_user, status='deceased')
            
            # Log successful death verification
            AuditService.create_log_entry(
                user_id=deceased_user.user_id,
                event_type='death_verified',
                event_description=f'Death verified by trusted contact {contact_email}',
                input_data={
                    'extracted_data': extracted_data,
                    'contact_email': contact_email,
                    'verification_confidence': verification_result.get('confidence_score', 0)
                },
                status='success'
            )
            
            # Trigger automatic policy execution
            execution_result = trigger_policy_execution(deceased_user.user_id, trusted_contact.contact_id)
            
            return jsonify({
                'message': 'Death certificate verified successfully',
                'verification_id': str(uuid.uuid4()),
                'extracted_data': extracted_data,
                'confidence_score': verification_result.get('confidence_score', 0),
                'policy_execution': execution_result
            }), 200
        else:
            # Log failed verification
            AuditService.create_log_entry(
                user_id=deceased_user.user_id,
                event_type='death_verification_failed',
                event_description='Death certificate verification failed - data mismatch',
                input_data={
                    'extracted_data': extracted_data,
                    'contact_email': contact_email
                },
                status='failure'
            )
            
            return jsonify({
                'error': 'Death certificate verification failed',
                'details': 'Extracted information does not match user profile',
                'extracted_data': extracted_data
            }), 400
            
    except Exception as e:
        current_app.logger.error(f"Death certificate upload error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

def trigger_policy_execution(user_id, trusted_contact_id):
    """
    Trigger automatic execution of user's action policies
    
    Args:
        user_id: ID of the deceased user
        trusted_contact_id: ID of the trusted contact who verified the death
        
    Returns:
        Dictionary with execution results
    """
    try:
        # Get all action policies for the user
        policies = DatabaseService.get_all(ActionPolicy, user_id=user_id)
        
        if not policies:
            return {
                'status': 'success',
                'message': 'No policies to execute',
                'executed_policies': []
            }
        
        # Get user information for policy execution
        user = DatabaseService.get_by_id(UserProfile, user_id)
        if not user:
            return {
                'status': 'error',
                'message': 'User not found'
            }
        
        # Initialize Action Engine service
        action_engine = ActionEngineService()
        
        # Prepare policies for interpretation
        policy_data = []
        for policy in policies:
            policy_dict = policy.to_dict()
            try:
                policy_details = policy.get_policy_details()
                if policy_details:
                    policy_dict['policy_details_decrypted'] = policy_details
            except Exception as e:
                current_app.logger.warning(f"Could not decrypt policy details for {policy.policy_id}: {str(e)}")
            
            policy_data.append(policy_dict)
        
        # Interpret policies using Azure OpenAI
        interpreted_policies = action_engine.interpret_policies(policy_data)
        
        # Log AI service call for policy interpretation
        AuditService.log_ai_service_call(
            user_id=user_id,
            service_name='azure_openai',
            operation='policy_interpretation',
            input_data={
                'policy_count': len(policy_data),
                'trusted_contact_id': trusted_contact_id
            },
            output_data={
                'interpreted_policies_count': len(interpreted_policies)
            },
            status='success'
        )
        
        # Generate platform notifications
        user_info = {
            'full_name': user.full_name,
            'email': user.email,
            'date_of_death': datetime.utcnow().strftime('%Y-%m-%d'),  # Use current date as death date
            'user_id': user_id
        }
        
        notifications = action_engine.generate_platform_notifications(interpreted_policies, user_info)
        
        # Log AI service call for notification generation
        AuditService.log_ai_service_call(
            user_id=user_id,
            service_name='azure_openai',
            operation='notification_generation',
            input_data={
                'policy_count': len(interpreted_policies),
                'user_info': user_info
            },
            output_data={
                'notifications_count': len(notifications)
            },
            status='success'
        )
        
        # Log policy execution
        execution_details = {
            'policies_processed': len(policies),
            'notifications_generated': len(notifications),
            'trusted_contact_id': trusted_contact_id,
            'execution_timestamp': datetime.utcnow().isoformat()
        }
        
        AuditService.create_log_entry(
            user_id=user_id,
            event_type='policies_executed',
            event_description=f'Automatic policy execution triggered by death verification',
            input_data=execution_details,
            output_data={
                'interpreted_policies': interpreted_policies,
                'notifications': notifications
            },
            status='success'
        )
        
        return {
            'status': 'success',
            'message': f'Successfully executed {len(policies)} policies',
            'executed_policies': len(policies),
            'notifications_generated': len(notifications),
            'execution_details': execution_details
        }
        
    except Exception as e:
        current_app.logger.error(f"Policy execution error: {str(e)}")
        
        # Log execution failure
        AuditService.create_log_entry(
            user_id=user_id,
            event_type='policy_execution_failed',
            event_description=f'Policy execution failed: {str(e)}',
            input_data={
                'trusted_contact_id': trusted_contact_id,
                'error': str(e)
            },
            status='failure'
        )
        
        return {
            'status': 'error',
            'message': f'Policy execution failed: {str(e)}'
        }

@verification_bp.route('/status/<user_email>', methods=['GET'])
@require_trusted_contact_auth
def get_verification_status(user_email):
    """
    Get death verification status for a user
    
    Query parameters:
    - contact_email: Email of the trusted contact making the request
    """
    try:
        contact_email = request.args.get('contact_email', '').lower().strip()
        
        if not contact_email:
            return jsonify({'error': 'Contact email is required'}), 400
        
        # Find user
        user = UserProfile.query.filter_by(email=user_email.lower()).first()
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Verify trusted contact authorization
        trusted_contact = TrustedContact.query.filter_by(
            user_id=user.user_id,
            contact_email=contact_email
        ).first()
        
        if not trusted_contact:
            return jsonify({'error': 'Unauthorized. You are not a trusted contact for this user'}), 403
        
        # Get verification status and audit trail
        audit_trail = AuditService.get_audit_trail(
            user_id=user.user_id,
            event_type='death_verified'
        )
        
        policy_execution_logs = AuditService.get_audit_trail(
            user_id=user.user_id,
            event_type='policies_executed'
        )
        
        return jsonify({
            'user_status': user.status,
            'verification_status': 'verified' if user.status == 'deceased' else 'pending',
            'trusted_contact_status': trusted_contact.verification_status,
            'death_verification_logs': audit_trail,
            'policy_execution_logs': policy_execution_logs
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Get verification status error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@verification_bp.route('/policies/<user_email>', methods=['GET'])
@require_trusted_contact_auth
def get_user_policies(user_email):
    """
    Get action policies for a deceased user (for trusted contacts)
    
    Query parameters:
    - contact_email: Email of the trusted contact making the request
    """
    try:
        contact_email = request.args.get('contact_email', '').lower().strip()
        
        if not contact_email:
            return jsonify({'error': 'Contact email is required'}), 400
        
        # Find user
        user = UserProfile.query.filter_by(email=user_email.lower()).first()
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Verify trusted contact authorization
        trusted_contact = TrustedContact.query.filter_by(
            user_id=user.user_id,
            contact_email=contact_email,
            verification_status='verified'
        ).first()
        
        if not trusted_contact:
            return jsonify({'error': 'Unauthorized. You are not a verified trusted contact for this user'}), 403
        
        # Only allow access to policies if user is deceased or verification is in progress
        if user.status not in ['deceased', 'active']:  # Allow active for demonstration purposes
            return jsonify({'error': 'Access denied. User status does not allow policy access'}), 403
        
        # Get all policies for the user
        policies = DatabaseService.get_all(ActionPolicy, user_id=user.user_id)
        
        # Return policies without sensitive details (trusted contacts don't need full policy details)
        policy_list = []
        for policy in policies:
            policy_dict = {
                'policy_id': policy.policy_id,
                'asset_type': policy.asset_type,
                'platform_name': policy.platform_name,
                'account_identifier': policy.account_identifier,
                'action_type': policy.action_type,
                'priority': policy.priority,
                'created_at': policy.created_at.isoformat() if policy.created_at else None
            }
            policy_list.append(policy_dict)
        
        return jsonify({
            'user_email': user_email,
            'user_status': user.status,
            'policies': policy_list,
            'policy_count': len(policy_list)
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Get user policies error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@verification_bp.route('/execute-policies/<user_email>', methods=['POST'])
@require_trusted_contact_auth
def manual_policy_execution(user_email):
    """
    Manually trigger policy execution for a deceased user
    
    Expected JSON:
    {
        "contact_email": "trusted@example.com",
        "reason": "Manual execution requested"
    }
    """
    try:
        data = request.get_json()
        contact_email = data.get('contact_email', '').lower().strip()
        reason = data.get('reason', 'Manual execution requested')
        
        if not contact_email:
            return jsonify({'error': 'Contact email is required'}), 400
        
        # Find user
        user = UserProfile.query.filter_by(email=user_email.lower()).first()
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Verify trusted contact authorization
        trusted_contact = TrustedContact.query.filter_by(
            user_id=user.user_id,
            contact_email=contact_email,
            verification_status='verified'
        ).first()
        
        if not trusted_contact:
            return jsonify({'error': 'Unauthorized. You are not a verified trusted contact for this user'}), 403
        
        # Only allow manual execution for deceased users
        if user.status != 'deceased':
            return jsonify({'error': 'Manual policy execution only allowed for deceased users'}), 403
        
        # Log manual execution request
        AuditService.log_user_action(
            user_id=user.user_id,
            action='manual_policy_execution_requested',
            details={
                'contact_email': contact_email,
                'reason': reason,
                'timestamp': datetime.utcnow().isoformat()
            }
        )
        
        # Trigger policy execution
        execution_result = trigger_policy_execution(user.user_id, trusted_contact.contact_id)
        
        return jsonify({
            'message': 'Manual policy execution completed',
            'execution_result': execution_result
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Manual policy execution error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@verification_bp.route('/audit-trail/<user_email>', methods=['GET'])
@require_trusted_contact_auth
def get_audit_trail(user_email):
    """
    Get audit trail for a user (for trusted contacts and administrators)
    
    Query parameters:
    - contact_email: Email of the trusted contact making the request
    - event_type: Optional filter by event type
    - start_date: Optional start date filter (YYYY-MM-DD)
    - end_date: Optional end date filter (YYYY-MM-DD)
    """
    try:
        contact_email = request.args.get('contact_email', '').lower().strip()
        event_type = request.args.get('event_type')
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')
        
        if not contact_email:
            return jsonify({'error': 'Contact email is required'}), 400
        
        # Find user
        user = UserProfile.query.filter_by(email=user_email.lower()).first()
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Verify trusted contact authorization
        trusted_contact = TrustedContact.query.filter_by(
            user_id=user.user_id,
            contact_email=contact_email,
            verification_status='verified'
        ).first()
        
        if not trusted_contact:
            return jsonify({'error': 'Unauthorized. You are not a verified trusted contact for this user'}), 403
        
        # Parse date filters
        start_date = None
        end_date = None
        
        if start_date_str:
            try:
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
            except ValueError:
                return jsonify({'error': 'Invalid start_date format. Use YYYY-MM-DD'}), 400
        
        if end_date_str:
            try:
                end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
            except ValueError:
                return jsonify({'error': 'Invalid end_date format. Use YYYY-MM-DD'}), 400
        
        # Get audit trail
        audit_trail = AuditService.get_audit_trail(
            user_id=user.user_id,
            event_type=event_type,
            start_date=start_date,
            end_date=end_date
        )
        
        # Verify audit log integrity
        integrity_report = AuditService.verify_all_logs_integrity(user_id=user.user_id)
        
        return jsonify({
            'user_email': user_email,
            'audit_trail': audit_trail,
            'integrity_report': integrity_report,
            'total_entries': len(audit_trail)
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Get audit trail error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500