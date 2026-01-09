"""
Digital Asset Management API Endpoints
Handles digital asset registration, trusted contact management, and action policy creation
"""
from flask import Blueprint, request, jsonify, session, current_app
from app.models.user_profile import UserProfile
from app.models.trusted_contact import TrustedContact
from app.models.action_policy import ActionPolicy
from app.services.database import DatabaseService
from app.services.audit import AuditService
from datetime import datetime
from functools import wraps
import re

vault_bp = Blueprint('vault', __name__, url_prefix='/api/vault')

def require_auth(f):
    """Decorator to require authentication for protected endpoints"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Authentication required'}), 401
        
        # Verify user still exists and is active
        user = DatabaseService.get_by_id(UserProfile, session['user_id'])
        if not user or user.status != 'active':
            session.clear()
            return jsonify({'error': 'Invalid session'}), 401
        
        return f(*args, **kwargs)
    return decorated_function

def require_mfa(f):
    """Decorator to require MFA verification for sensitive operations"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'mfa_verified' not in session or not session['mfa_verified']:
            return jsonify({'error': 'MFA verification required'}), 403
        return f(*args, **kwargs)
    return decorated_function

# Digital Asset Management Endpoints

@vault_bp.route('/assets', methods=['GET'])
@require_auth
@require_mfa
def get_digital_assets():
    """Get all digital assets for the authenticated user"""
    try:
        user = DatabaseService.get_by_id(UserProfile, session['user_id'])
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Get decrypted metadata
        metadata = user.get_decrypted_metadata()
        if not metadata:
            return jsonify({'assets': {}}), 200
        
        # Remove sensitive credential information for API response
        safe_assets = {}
        for asset_type, assets in metadata.items():
            if asset_type in ['email', 'bank', 'social_media', 'other']:
                safe_assets[asset_type] = []
                for asset in assets:
                    safe_asset = {
                        'platform_name': asset.get('platform_name'),
                        'account_identifier': asset.get('account_identifier'),
                        'added_at': asset.get('added_at')
                    }
                    safe_assets[asset_type].append(safe_asset)
        
        return jsonify({'assets': safe_assets}), 200
        
    except Exception as e:
        current_app.logger.error(f"Get assets error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@vault_bp.route('/assets', methods=['POST'])
@require_auth
@require_mfa
def add_digital_asset():
    """
    Add a new digital asset to the user's vault
    
    Expected JSON:
    {
        "asset_type": "email|bank|social_media|other",
        "platform_name": "Gmail",
        "account_identifier": "user@gmail.com",
        "credentials": {
            "username": "user@gmail.com",
            "password": "encrypted_password",
            "recovery_email": "backup@example.com"
        }
    }
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['asset_type', 'platform_name', 'account_identifier', 'credentials']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        asset_type = data['asset_type']
        platform_name = data['platform_name'].strip()
        account_identifier = data['account_identifier'].strip()
        credentials = data['credentials']
        
        # Validate asset type
        valid_asset_types = ['email', 'bank', 'social_media', 'other']
        if asset_type not in valid_asset_types:
            return jsonify({'error': f'Invalid asset type. Must be one of: {valid_asset_types}'}), 400
        
        # Validate credentials is a dictionary
        if not isinstance(credentials, dict):
            return jsonify({'error': 'Credentials must be a dictionary'}), 400
        
        user = DatabaseService.get_by_id(UserProfile, session['user_id'])
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Add digital asset using the model method
        user.add_digital_asset(asset_type, platform_name, account_identifier, credentials)
        
        # Save updated metadata
        if DatabaseService.safe_update(user, encrypted_metadata=user.encrypted_metadata):
            # Log asset addition
            AuditService.log_user_action(
                user_id=user.user_id,
                action='asset_added',
                details={
                    'asset_type': asset_type,
                    'platform_name': platform_name,
                    'account_identifier': account_identifier,
                    'timestamp': datetime.utcnow().isoformat()
                }
            )
            
            return jsonify({
                'message': 'Digital asset added successfully',
                'asset': {
                    'asset_type': asset_type,
                    'platform_name': platform_name,
                    'account_identifier': account_identifier
                }
            }), 201
        else:
            return jsonify({'error': 'Failed to save digital asset'}), 500
            
    except Exception as e:
        current_app.logger.error(f"Add asset error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@vault_bp.route('/assets/<asset_type>', methods=['GET'])
@require_auth
@require_mfa
def get_assets_by_type(asset_type):
    """Get digital assets of a specific type"""
    try:
        valid_asset_types = ['email', 'bank', 'social_media', 'other']
        if asset_type not in valid_asset_types:
            return jsonify({'error': f'Invalid asset type. Must be one of: {valid_asset_types}'}), 400
        
        user = DatabaseService.get_by_id(UserProfile, session['user_id'])
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Get assets of specific type
        assets = user.get_digital_assets_by_type(asset_type)
        
        # Remove sensitive credential information
        safe_assets = []
        for asset in assets:
            safe_asset = {
                'platform_name': asset.get('platform_name'),
                'account_identifier': asset.get('account_identifier'),
                'added_at': asset.get('added_at')
            }
            safe_assets.append(safe_asset)
        
        return jsonify({'assets': safe_assets}), 200
        
    except Exception as e:
        current_app.logger.error(f"Get assets by type error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

# Trusted Contact Management Endpoints

@vault_bp.route('/trusted-contacts', methods=['GET'])
@require_auth
def get_trusted_contacts():
    """Get all trusted contacts for the authenticated user"""
    try:
        contacts = DatabaseService.get_all(TrustedContact, user_id=session['user_id'])
        
        return jsonify({
            'contacts': [contact.to_dict() for contact in contacts]
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Get trusted contacts error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@vault_bp.route('/trusted-contacts', methods=['POST'])
@require_auth
@require_mfa
def add_trusted_contact():
    """
    Add a new trusted contact with enhanced security verification
    
    Expected JSON:
    {
        "contact_name": "John Doe",
        "contact_email": "john@example.com",
        "contact_phone": "9876543210",
        "relationship": "spouse",
        "contact_aadhaar_number": "123456789012",
        "contact_pan_number": "ABCDE1234F",
        "contact_address_line1": "123 Main Street",
        "contact_address_line2": "Apartment 4B",
        "contact_city": "Mumbai",
        "contact_state": "Maharashtra",
        "contact_pincode": "400001",
        "authorization_level": "full"
    }
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = [
            'contact_name', 'contact_email', 'contact_phone', 'relationship',
            'contact_aadhaar_number', 'contact_pan_number', 'contact_address_line1',
            'contact_city', 'contact_state', 'contact_pincode'
        ]
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Extract and validate data
        contact_name = data['contact_name'].strip()
        contact_email = data['contact_email'].lower().strip()
        contact_phone = data['contact_phone'].strip()
        relationship = data['relationship'].strip()
        contact_aadhaar_number = re.sub(r'[\s-]', '', data['contact_aadhaar_number'])
        contact_pan_number = data['contact_pan_number'].upper().strip()
        contact_address_line1 = data['contact_address_line1'].strip()
        contact_address_line2 = data.get('contact_address_line2', '').strip()
        contact_city = data['contact_city'].strip()
        contact_state = data['contact_state'].strip()
        contact_pincode = data['contact_pincode'].strip()
        authorization_level = data.get('authorization_level', 'basic')
        
        # Validate email format
        email_regex = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
        if not email_regex.match(contact_email):
            return jsonify({'error': 'Invalid email format'}), 400
        
        # Validate KYC data using the KYC service
        from app.services.kyc_verification import KYCVerificationService
        
        kyc_data = {
            'phone_number': contact_phone,
            'aadhaar_number': contact_aadhaar_number,
            'pan_number': contact_pan_number,
            'pincode': contact_pincode,
            'full_name': contact_name,
            'email': contact_email,
            'address_line1': contact_address_line1,
            'city': contact_city,
            'state': contact_state
        }
        
        validation_result = KYCVerificationService.validate_all_kyc_data(kyc_data)
        if not validation_result['is_valid']:
            return jsonify({
                'error': 'KYC validation failed for trusted contact',
                'validation_errors': validation_result['errors']
            }), 400
        
        # Check if contact already exists for this user (by email, phone, Aadhaar, or PAN)
        existing_contact = TrustedContact.query.filter(
            (TrustedContact.user_id == session['user_id']) &
            ((TrustedContact.contact_email == contact_email) |
             (TrustedContact.contact_phone == contact_phone) |
             (TrustedContact.contact_aadhaar_number == contact_aadhaar_number) |
             (TrustedContact.contact_pan_number == contact_pan_number))
        ).first()
        
        if existing_contact:
            if existing_contact.contact_email == contact_email:
                return jsonify({'error': 'Trusted contact with this email already exists'}), 409
            elif existing_contact.contact_phone == contact_phone:
                return jsonify({'error': 'Trusted contact with this phone number already exists'}), 409
            elif existing_contact.contact_aadhaar_number == contact_aadhaar_number:
                return jsonify({'error': 'Trusted contact with this Aadhaar number already exists'}), 409
            elif existing_contact.contact_pan_number == contact_pan_number:
                return jsonify({'error': 'Trusted contact with this PAN number already exists'}), 409
        
        # Verify identity documents for trusted contact
        identity_verification = KYCVerificationService.verify_identity_documents(
            contact_aadhaar_number, contact_pan_number, contact_name, None
        )
        
        # Create new trusted contact
        contact = TrustedContact(
            user_id=session['user_id'],
            contact_name=contact_name,
            contact_email=contact_email,
            contact_phone=contact_phone,
            relationship=relationship,
            contact_aadhaar_number=contact_aadhaar_number,
            contact_pan_number=contact_pan_number,
            contact_address_line1=contact_address_line1,
            contact_address_line2=contact_address_line2,
            contact_city=contact_city,
            contact_state=contact_state,
            contact_pincode=contact_pincode,
            authorization_level=authorization_level,
            identity_verification_score=str(identity_verification['verification_score']),
            identity_documents_verified='verified' if identity_verification['status'] == 'verified' else 'pending'
        )
        
        if DatabaseService.safe_add(contact):
            # Log contact addition
            AuditService.log_user_action(
                user_id=session['user_id'],
                action='trusted_contact_added',
                details={
                    'contact_name': contact_name,
                    'contact_email': contact_email,
                    'contact_phone': contact_phone[-4:],  # Only log last 4 digits
                    'relationship': relationship,
                    'authorization_level': authorization_level,
                    'identity_verification_score': identity_verification['verification_score'],
                    'timestamp': datetime.utcnow().isoformat()
                }
            )
            
            return jsonify({
                'message': 'Trusted contact added successfully with enhanced security verification',
                'contact': contact.to_dict(),
                'identity_verification': {
                    'status': identity_verification['status'],
                    'verification_score': identity_verification['verification_score']
                }
            }), 201
        else:
            return jsonify({'error': 'Failed to add trusted contact'}), 500
            
    except Exception as e:
        current_app.logger.error(f"Add trusted contact error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@vault_bp.route('/trusted-contacts/<contact_id>', methods=['PUT'])
@require_auth
@require_mfa
def update_trusted_contact(contact_id):
    """
    Update a trusted contact
    
    Expected JSON:
    {
        "contact_name": "Updated Name",
        "contact_phone": "+1234567890",
        "relationship": "friend"
    }
    """
    try:
        data = request.get_json()
        
        # Find the contact
        contact = TrustedContact.query.filter_by(
            contact_id=contact_id,
            user_id=session['user_id']
        ).first()
        
        if not contact:
            return jsonify({'error': 'Trusted contact not found'}), 404
        
        # Track changes for audit log
        changes = {}
        
        # Update fields if provided
        if 'contact_name' in data:
            new_name = data['contact_name'].strip()
            if new_name and new_name != contact.contact_name:
                changes['contact_name'] = {'old': contact.contact_name, 'new': new_name}
                contact.contact_name = new_name
        
        if 'contact_phone' in data:
            new_phone = data['contact_phone'].strip() if data['contact_phone'] else None
            if new_phone != contact.contact_phone:
                changes['contact_phone'] = {'old': contact.contact_phone, 'new': new_phone}
                contact.contact_phone = new_phone
        
        if 'relationship' in data:
            new_relationship = data['relationship'].strip() if data['relationship'] else None
            if new_relationship != contact.relationship:
                changes['relationship'] = {'old': contact.relationship, 'new': new_relationship}
                contact.relationship = new_relationship
        
        if changes:
            if DatabaseService.safe_update(contact, **{k: v['new'] for k, v in changes.items()}):
                # Log contact update
                AuditService.log_user_action(
                    user_id=session['user_id'],
                    action='trusted_contact_updated',
                    details={
                        'contact_id': contact_id,
                        'changes': changes,
                        'timestamp': datetime.utcnow().isoformat()
                    }
                )
                
                return jsonify({
                    'message': 'Trusted contact updated successfully',
                    'contact': contact.to_dict()
                }), 200
            else:
                return jsonify({'error': 'Failed to update trusted contact'}), 500
        else:
            return jsonify({'message': 'No changes to update'}), 200
            
    except Exception as e:
        current_app.logger.error(f"Update trusted contact error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@vault_bp.route('/trusted-contacts/<contact_id>', methods=['DELETE'])
@require_auth
@require_mfa
def delete_trusted_contact(contact_id):
    """Delete a trusted contact"""
    try:
        # Find the contact
        contact = TrustedContact.query.filter_by(
            contact_id=contact_id,
            user_id=session['user_id']
        ).first()
        
        if not contact:
            return jsonify({'error': 'Trusted contact not found'}), 404
        
        contact_info = contact.to_dict()  # Save for audit log
        
        if DatabaseService.safe_delete(contact):
            # Log contact deletion
            AuditService.log_user_action(
                user_id=session['user_id'],
                action='trusted_contact_deleted',
                details={
                    'contact_id': contact_id,
                    'contact_info': contact_info,
                    'timestamp': datetime.utcnow().isoformat()
                }
            )
            
            return jsonify({'message': 'Trusted contact deleted successfully'}), 200
        else:
            return jsonify({'error': 'Failed to delete trusted contact'}), 500
            
    except Exception as e:
        current_app.logger.error(f"Delete trusted contact error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

# Action Policy Management Endpoints

@vault_bp.route('/policies', methods=['GET'])
@require_auth
def get_action_policies():
    """Get all action policies for the authenticated user"""
    try:
        policies = DatabaseService.get_all(ActionPolicy, user_id=session['user_id'])
        
        # Include decrypted policy details for user's own policies
        policy_list = []
        for policy in policies:
            policy_dict = policy.to_dict()
            try:
                policy_details = policy.get_policy_details()
                if policy_details:
                    policy_dict['policy_details_decrypted'] = policy_details
            except Exception as e:
                current_app.logger.warning(f"Could not decrypt policy details for {policy.policy_id}: {str(e)}")
            
            policy_list.append(policy_dict)
        
        return jsonify({'policies': policy_list}), 200
        
    except Exception as e:
        current_app.logger.error(f"Get action policies error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@vault_bp.route('/policies', methods=['POST'])
@require_auth
@require_mfa
def create_action_policy():
    """
    Create a new action policy
    
    Expected JSON:
    {
        "asset_type": "email|bank|social_media|other",
        "platform_name": "Gmail",
        "account_identifier": "user@gmail.com",
        "action_type": "delete|memorialize|transfer|lock",
        "natural_language_policy": "Delete my Gmail account after I die",
        "specific_instructions": "Contact Gmail support with death certificate",
        "conditions": ["death_verified", "trusted_contact_authorized"],
        "priority": 1
    }
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['asset_type', 'platform_name', 'account_identifier', 'action_type']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        asset_type = data['asset_type']
        platform_name = data['platform_name'].strip()
        account_identifier = data['account_identifier'].strip()
        action_type = data['action_type']
        natural_language_policy = data.get('natural_language_policy', '').strip()
        specific_instructions = data.get('specific_instructions', '').strip()
        conditions = data.get('conditions', [])
        priority = data.get('priority', 1)
        
        # Validate asset type
        valid_asset_types = ['email', 'bank', 'social_media', 'other']
        if asset_type not in valid_asset_types:
            return jsonify({'error': f'Invalid asset type. Must be one of: {valid_asset_types}'}), 400
        
        # Validate action type
        valid_action_types = ['delete', 'memorialize', 'transfer', 'lock']
        if action_type not in valid_action_types:
            return jsonify({'error': f'Invalid action type. Must be one of: {valid_action_types}'}), 400
        
        # Check if policy already exists for this asset
        existing_policy = ActionPolicy.query.filter_by(
            user_id=session['user_id'],
            platform_name=platform_name,
            account_identifier=account_identifier
        ).first()
        
        if existing_policy:
            return jsonify({'error': 'Policy already exists for this asset'}), 409
        
        # Create new action policy
        policy = ActionPolicy(
            user_id=session['user_id'],
            asset_type=asset_type,
            platform_name=platform_name,
            account_identifier=account_identifier,
            action_type=action_type,
            priority=priority
        )
        
        # Set encrypted policy details
        if natural_language_policy or specific_instructions or conditions:
            policy.set_natural_language_policy(
                natural_language_policy,
                specific_instructions,
                conditions
            )
        
        if DatabaseService.safe_add(policy):
            # Log policy creation
            AuditService.log_user_action(
                user_id=session['user_id'],
                action='policy_created',
                details={
                    'policy_id': policy.policy_id,
                    'asset_type': asset_type,
                    'platform_name': platform_name,
                    'account_identifier': account_identifier,
                    'action_type': action_type,
                    'timestamp': datetime.utcnow().isoformat()
                }
            )
            
            return jsonify({
                'message': 'Action policy created successfully',
                'policy': policy.to_dict()
            }), 201
        else:
            return jsonify({'error': 'Failed to create action policy'}), 500
            
    except Exception as e:
        current_app.logger.error(f"Create action policy error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@vault_bp.route('/policies/<policy_id>', methods=['PUT'])
@require_auth
@require_mfa
def update_action_policy(policy_id):
    """
    Update an action policy
    
    Expected JSON:
    {
        "action_type": "memorialize",
        "natural_language_policy": "Updated policy text",
        "specific_instructions": "Updated instructions",
        "conditions": ["updated_conditions"],
        "priority": 2
    }
    """
    try:
        data = request.get_json()
        
        # Find the policy
        policy = ActionPolicy.query.filter_by(
            policy_id=policy_id,
            user_id=session['user_id']
        ).first()
        
        if not policy:
            return jsonify({'error': 'Action policy not found'}), 404
        
        # Track changes for audit log
        changes = {}
        
        # Update action type if provided
        if 'action_type' in data:
            new_action_type = data['action_type']
            valid_action_types = ['delete', 'memorialize', 'transfer', 'lock']
            if new_action_type not in valid_action_types:
                return jsonify({'error': f'Invalid action type. Must be one of: {valid_action_types}'}), 400
            
            if new_action_type != policy.action_type:
                changes['action_type'] = {'old': policy.action_type, 'new': new_action_type}
                policy.action_type = new_action_type
        
        # Update priority if provided
        if 'priority' in data:
            new_priority = data['priority']
            if new_priority != policy.priority:
                changes['priority'] = {'old': policy.priority, 'new': new_priority}
                policy.priority = new_priority
        
        # Update policy details if provided
        policy_details_updated = False
        if any(key in data for key in ['natural_language_policy', 'specific_instructions', 'conditions']):
            # Get current policy details
            current_details = policy.get_policy_details() or {}
            
            natural_language_policy = data.get('natural_language_policy', current_details.get('natural_language_policy', ''))
            specific_instructions = data.get('specific_instructions', current_details.get('specific_instructions', ''))
            conditions = data.get('conditions', current_details.get('conditions', []))
            
            # Update policy details
            policy.set_natural_language_policy(natural_language_policy, specific_instructions, conditions)
            changes['policy_details'] = 'updated'
            policy_details_updated = True
        
        if changes:
            update_fields = {}
            if 'action_type' in changes:
                update_fields['action_type'] = changes['action_type']['new']
            if 'priority' in changes:
                update_fields['priority'] = changes['priority']['new']
            if policy_details_updated:
                update_fields['policy_details'] = policy.policy_details
            
            if DatabaseService.safe_update(policy, **update_fields):
                # Log policy update
                AuditService.log_user_action(
                    user_id=session['user_id'],
                    action='policy_updated',
                    details={
                        'policy_id': policy_id,
                        'changes': changes,
                        'timestamp': datetime.utcnow().isoformat()
                    }
                )
                
                return jsonify({
                    'message': 'Action policy updated successfully',
                    'policy': policy.to_dict()
                }), 200
            else:
                return jsonify({'error': 'Failed to update action policy'}), 500
        else:
            return jsonify({'message': 'No changes to update'}), 200
            
    except Exception as e:
        current_app.logger.error(f"Update action policy error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@vault_bp.route('/policies/<policy_id>', methods=['DELETE'])
@require_auth
@require_mfa
def delete_action_policy(policy_id):
    """Delete an action policy"""
    try:
        # Find the policy
        policy = ActionPolicy.query.filter_by(
            policy_id=policy_id,
            user_id=session['user_id']
        ).first()
        
        if not policy:
            return jsonify({'error': 'Action policy not found'}), 404
        
        policy_info = policy.to_dict()  # Save for audit log
        
        if DatabaseService.safe_delete(policy):
            # Log policy deletion
            AuditService.log_user_action(
                user_id=session['user_id'],
                action='policy_deleted',
                details={
                    'policy_id': policy_id,
                    'policy_info': policy_info,
                    'timestamp': datetime.utcnow().isoformat()
                }
            )
            
            return jsonify({'message': 'Action policy deleted successfully'}), 200
        else:
            return jsonify({'error': 'Failed to delete action policy'}), 500
            
    except Exception as e:
        current_app.logger.error(f"Delete action policy error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500