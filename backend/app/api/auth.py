"""
Authentication and User Management API Endpoints
Handles user registration, authentication, and profile management with enhanced KYC verification
"""
from flask import Blueprint, request, jsonify, session, current_app
from werkzeug.security import generate_password_hash, check_password_hash
from app.models.user_profile import UserProfile
from app.services.database import DatabaseService
from app.services.audit import AuditService
from app.services.kyc_verification import KYCVerificationService
from datetime import datetime, date
import secrets
import pyotp
import qrcode
import io
import base64
from functools import wraps
import re

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

# Email validation regex
EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')

def validate_email(email):
    """Validate email format"""
    return EMAIL_REGEX.match(email) is not None

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

@auth_bp.route('/register', methods=['POST'])
def register():
    """
    Register a new user account with comprehensive KYC verification
    
    Expected JSON:
    {
        "email": "user@example.com",
        "password": "secure_password",
        "phone_number": "9876543210",
        "full_name": "John Doe",
        "date_of_birth": "1990-01-01",
        "aadhaar_number": "123456789012",
        "pan_number": "ABCDE1234F",
        "address_line1": "123 Main Street",
        "address_line2": "Apartment 4B",
        "city": "Mumbai",
        "state": "Maharashtra",
        "pincode": "400001"
    }
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = [
            'email', 'password', 'phone_number', 'full_name', 'date_of_birth',
            'aadhaar_number', 'pan_number', 'address_line1', 'city', 'state', 'pincode'
        ]
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Extract and clean data
        email = data['email'].lower().strip()
        password = data['password']
        phone_number = data['phone_number'].strip()
        full_name = data['full_name'].strip()
        date_of_birth_str = data['date_of_birth']
        aadhaar_number = re.sub(r'[\s-]', '', data['aadhaar_number'])
        pan_number = data['pan_number'].upper().strip()
        address_line1 = data['address_line1'].strip()
        address_line2 = data.get('address_line2', '').strip()
        city = data['city'].strip()
        state = data['state'].strip()
        pincode = data['pincode'].strip()
        
        # Validate email format
        if not validate_email(email):
            return jsonify({'error': 'Invalid email format'}), 400
        
        # Validate password strength
        if len(password) < 8:
            return jsonify({'error': 'Password must be at least 8 characters long'}), 400
        
        # Comprehensive KYC validation
        kyc_data = {
            'email': email,
            'phone_number': phone_number,
            'full_name': full_name,
            'date_of_birth': date_of_birth_str,
            'aadhaar_number': aadhaar_number,
            'pan_number': pan_number,
            'address_line1': address_line1,
            'address_line2': address_line2,
            'city': city,
            'state': state,
            'pincode': pincode
        }
        
        validation_result = KYCVerificationService.validate_all_kyc_data(kyc_data)
        if not validation_result['is_valid']:
            return jsonify({
                'error': 'KYC validation failed',
                'validation_errors': validation_result['errors']
            }), 400
        
        # Parse date of birth
        try:
            date_of_birth = datetime.strptime(date_of_birth_str, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400
        
        # Check if user already exists (email, phone, Aadhaar, or PAN)
        existing_user = UserProfile.query.filter(
            (UserProfile.email == email) |
            (UserProfile.phone_number == phone_number) |
            (UserProfile.aadhaar_number == aadhaar_number) |
            (UserProfile.pan_number == pan_number)
        ).first()
        
        if existing_user:
            if existing_user.email == email:
                return jsonify({'error': 'User with this email already exists'}), 409
            elif existing_user.phone_number == phone_number:
                return jsonify({'error': 'User with this phone number already exists'}), 409
            elif existing_user.aadhaar_number == aadhaar_number:
                return jsonify({'error': 'User with this Aadhaar number already exists'}), 409
            elif existing_user.pan_number == pan_number:
                return jsonify({'error': 'User with this PAN number already exists'}), 409
        
        # Verify identity documents
        identity_verification = KYCVerificationService.verify_identity_documents(
            aadhaar_number, pan_number, full_name, date_of_birth_str
        )
        
        # Create new user
        user = UserProfile(
            email=email,
            phone_number=phone_number,
            full_name=full_name,
            date_of_birth=date_of_birth,
            aadhaar_number=aadhaar_number,
            pan_number=pan_number,
            address_line1=address_line1,
            address_line2=address_line2,
            city=city,
            state=state,
            pincode=pincode,
            kyc_status='verified' if identity_verification['status'] == 'verified' else 'pending',
            identity_verification_score=str(identity_verification['verification_score'])
        )
        
        # Generate password hash and store in encrypted metadata
        password_hash = generate_password_hash(password)
        user.set_encrypted_metadata({
            'password_hash': password_hash,
            'mfa_secret': pyotp.random_base32(),
            'identity_verification': identity_verification,
            'created_at': datetime.utcnow().isoformat()
        })
        
        # Save user to database
        if DatabaseService.safe_add(user):
            # Generate and send OTP for phone verification
            phone_otp = KYCVerificationService.generate_otp()
            email_otp = KYCVerificationService.generate_otp()
            
            # Store OTPs in session for verification
            session[f'phone_otp_{user.user_id}'] = phone_otp
            session[f'email_otp_{user.user_id}'] = email_otp
            session[f'otp_generated_at_{user.user_id}'] = datetime.utcnow().isoformat()
            
            # Send OTPs
            KYCVerificationService.send_otp_sms(phone_number, phone_otp)
            KYCVerificationService.send_otp_email(email, email_otp)
            
            # Log user registration
            AuditService.log_user_action(
                user_id=user.user_id,
                action='register',
                details={
                    'email': email,
                    'phone_number': phone_number[-4:],  # Only log last 4 digits
                    'full_name': full_name,
                    'kyc_status': user.kyc_status,
                    'identity_verification_score': identity_verification['verification_score'],
                    'registration_timestamp': datetime.utcnow().isoformat()
                }
            )
            
            return jsonify({
                'message': 'User registered successfully. Please verify your phone and email.',
                'user_id': user.user_id,
                'email': user.email,
                'phone_number': phone_number,
                'full_name': user.full_name,
                'kyc_status': user.kyc_status,
                'verification_required': {
                    'phone_verification': user.phone_verified == 'pending',
                    'email_verification': user.email_verified == 'pending'
                },
                'identity_verification_score': identity_verification['verification_score']
            }), 201
        else:
            return jsonify({'error': 'Failed to create user account'}), 500
            
    except Exception as e:
        current_app.logger.error(f"Registration error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@auth_bp.route('/verify-otp', methods=['POST'])
def verify_otp():
    """
    Verify OTP for phone or email verification
    
    Expected JSON:
    {
        "user_id": "user_uuid",
        "otp_type": "phone" or "email",
        "otp": "123456"
    }
    """
    try:
        data = request.get_json()
        
        user_id = data.get('user_id')
        otp_type = data.get('otp_type')  # 'phone' or 'email'
        otp = data.get('otp', '').strip()
        
        if not all([user_id, otp_type, otp]):
            return jsonify({'error': 'Missing required fields'}), 400
        
        if otp_type not in ['phone', 'email']:
            return jsonify({'error': 'Invalid OTP type. Must be "phone" or "email"'}), 400
        
        if len(otp) != 6 or not otp.isdigit():
            return jsonify({'error': 'Invalid OTP format'}), 400
        
        # Get user
        user = DatabaseService.get_by_id(UserProfile, user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Check if OTP exists in session
        otp_key = f'{otp_type}_otp_{user_id}'
        stored_otp = session.get(otp_key)
        
        if not stored_otp:
            return jsonify({'error': 'No OTP found. Please request a new OTP.'}), 400
        
        # Check OTP expiry (10 minutes)
        otp_generated_at = session.get(f'otp_generated_at_{user_id}')
        if otp_generated_at:
            generated_time = datetime.fromisoformat(otp_generated_at)
            if (datetime.utcnow() - generated_time).total_seconds() > 600:  # 10 minutes
                # Clear expired OTP
                session.pop(otp_key, None)
                session.pop(f'otp_generated_at_{user_id}', None)
                return jsonify({'error': 'OTP has expired. Please request a new OTP.'}), 400
        
        # Verify OTP
        if stored_otp != otp:
            return jsonify({'error': 'Invalid OTP'}), 401
        
        # Update verification status
        if otp_type == 'phone':
            user.phone_verified = 'verified'
        elif otp_type == 'email':
            user.email_verified = 'verified'
        
        # Clear OTP from session
        session.pop(otp_key, None)
        session.pop(f'otp_generated_at_{user_id}', None)
        
        # Save user
        if DatabaseService.safe_update(user):
            # Log verification
            AuditService.log_user_action(
                user_id=user.user_id,
                action=f'{otp_type}_verified',
                details={
                    'verification_type': otp_type,
                    'timestamp': datetime.utcnow().isoformat()
                }
            )
            
            return jsonify({
                'message': f'{otp_type.title()} verification successful',
                'verification_status': {
                    'phone_verified': user.phone_verified,
                    'email_verified': user.email_verified
                }
            }), 200
        else:
            return jsonify({'error': 'Failed to update verification status'}), 500
            
    except Exception as e:
        current_app.logger.error(f"OTP verification error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@auth_bp.route('/resend-otp', methods=['POST'])
def resend_otp():
    """
    Resend OTP for phone or email verification
    
    Expected JSON:
    {
        "user_id": "user_uuid",
        "otp_type": "phone" or "email"
    }
    """
    try:
        data = request.get_json()
        
        user_id = data.get('user_id')
        otp_type = data.get('otp_type')  # 'phone' or 'email'
        
        if not all([user_id, otp_type]):
            return jsonify({'error': 'Missing required fields'}), 400
        
        if otp_type not in ['phone', 'email']:
            return jsonify({'error': 'Invalid OTP type. Must be "phone" or "email"'}), 400
        
        # Get user
        user = DatabaseService.get_by_id(UserProfile, user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Check if already verified
        if otp_type == 'phone' and user.phone_verified == 'verified':
            return jsonify({'error': 'Phone number already verified'}), 400
        elif otp_type == 'email' and user.email_verified == 'verified':
            return jsonify({'error': 'Email already verified'}), 400
        
        # Generate new OTP
        new_otp = KYCVerificationService.generate_otp()
        
        # Store OTP in session
        session[f'{otp_type}_otp_{user_id}'] = new_otp
        session[f'otp_generated_at_{user_id}'] = datetime.utcnow().isoformat()
        
        # Send OTP
        if otp_type == 'phone':
            success = KYCVerificationService.send_otp_sms(user.phone_number, new_otp)
        else:
            success = KYCVerificationService.send_otp_email(user.email, new_otp)
        
        if success:
            return jsonify({
                'message': f'OTP sent to your {otp_type}',
                'expires_in': 600  # 10 minutes
            }), 200
        else:
            return jsonify({'error': f'Failed to send OTP to {otp_type}'}), 500
            
    except Exception as e:
        current_app.logger.error(f"Resend OTP error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500
@auth_bp.route('/login', methods=['POST'])
def login():
    """
    Authenticate user with email/phone and password
    
    Expected JSON:
    {
        "login_id": "user@example.com" or "9876543210",
        "password": "secure_password"
    }
    """
    try:
        data = request.get_json()
        
        login_id = data.get('login_id', '').strip()
        password = data.get('password', '')
        
        if not login_id or not password:
            return jsonify({'error': 'Login ID and password are required'}), 400
        
        # Determine if login_id is email or phone
        user = None
        if validate_email(login_id.lower()):
            user = UserProfile.query.filter_by(email=login_id.lower()).first()
        else:
            # Try phone number
            phone_clean = re.sub(r'[\s\-\+]', '', login_id)
            if phone_clean.startswith('91') and len(phone_clean) == 12:
                phone_clean = phone_clean[2:]
            user = UserProfile.query.filter_by(phone_number=phone_clean).first()
        
        if not user:
            return jsonify({'error': 'Invalid credentials'}), 401
        
        # Check if user is active
        if user.status != 'active':
            return jsonify({'error': 'Account is not active'}), 401
        
        # Check KYC status
        if user.kyc_status != 'verified':
            return jsonify({
                'error': 'Account verification incomplete',
                'kyc_status': user.kyc_status,
                'verification_required': {
                    'phone_verification': user.phone_verified != 'verified',
                    'email_verification': user.email_verified != 'verified'
                }
            }), 403
        
        # Get encrypted metadata to verify password
        metadata = user.get_decrypted_metadata()
        if not metadata or 'password_hash' not in metadata:
            return jsonify({'error': 'Account configuration error'}), 500
        
        # Verify password
        if not check_password_hash(metadata['password_hash'], password):
            # Log failed login attempt
            AuditService.log_user_action(
                user_id=user.user_id,
                action='login_failed',
                details={
                    'login_id': login_id,
                    'timestamp': datetime.utcnow().isoformat(),
                    'reason': 'invalid_password'
                },
                status='failure'
            )
            return jsonify({'error': 'Invalid credentials'}), 401
        
        # Set session
        session['user_id'] = user.user_id
        session['email'] = user.email
        session['mfa_verified'] = False  # Require MFA for sensitive operations
        
        # Log successful login
        AuditService.log_user_action(
            user_id=user.user_id,
            action='login_success',
            details={
                'login_id': login_id,
                'timestamp': datetime.utcnow().isoformat()
            }
        )
        
        return jsonify({
            'message': 'Login successful',
            'user': user.to_dict(),
            'mfa_required': True  # Always require MFA for vault access
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Login error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@auth_bp.route('/mfa/setup', methods=['GET'])
@require_auth
def setup_mfa():
    """
    Get MFA setup information (QR code and secret)
    """
    try:
        user = DatabaseService.get_by_id(UserProfile, session['user_id'])
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        metadata = user.get_decrypted_metadata()
        if not metadata or 'mfa_secret' not in metadata:
            return jsonify({'error': 'MFA not configured'}), 500
        
        mfa_secret = metadata['mfa_secret']
        
        # Generate QR code for authenticator app
        totp_uri = pyotp.totp.TOTP(mfa_secret).provisioning_uri(
            name=user.email,
            issuer_name="Ghost Identity Protection"
        )
        
        # Create QR code image
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(totp_uri)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        img_buffer = io.BytesIO()
        img.save(img_buffer, format='PNG')
        img_buffer.seek(0)
        
        qr_code_base64 = base64.b64encode(img_buffer.getvalue()).decode()
        
        return jsonify({
            'mfa_secret': mfa_secret,
            'qr_code': f"data:image/png;base64,{qr_code_base64}",
            'manual_entry_key': mfa_secret
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"MFA setup error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@auth_bp.route('/mfa/verify', methods=['POST'])
@require_auth
def verify_mfa():
    """
    Verify MFA token
    
    Expected JSON:
    {
        "token": "123456"
    }
    """
    try:
        data = request.get_json()
        token = data.get('token', '').strip()
        
        if not token or len(token) != 6 or not token.isdigit():
            return jsonify({'error': 'Invalid MFA token format'}), 400
        
        user = DatabaseService.get_by_id(UserProfile, session['user_id'])
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        metadata = user.get_decrypted_metadata()
        if not metadata or 'mfa_secret' not in metadata:
            return jsonify({'error': 'MFA not configured'}), 500
        
        mfa_secret = metadata['mfa_secret']
        totp = pyotp.TOTP(mfa_secret)
        
        if totp.verify(token):
            session['mfa_verified'] = True
            
            # Log successful MFA verification
            AuditService.log_user_action(
                user_id=user.user_id,
                action='mfa_verified',
                details={
                    'timestamp': datetime.utcnow().isoformat()
                }
            )
            
            return jsonify({'message': 'MFA verification successful'}), 200
        else:
            # Log failed MFA attempt
            AuditService.log_user_action(
                user_id=user.user_id,
                action='mfa_failed',
                details={
                    'timestamp': datetime.utcnow().isoformat()
                },
                status='failure'
            )
            return jsonify({'error': 'Invalid MFA token'}), 401
            
    except Exception as e:
        current_app.logger.error(f"MFA verification error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@auth_bp.route('/profile', methods=['GET'])
@require_auth
def get_profile():
    """Get current user's profile information"""
    try:
        user = DatabaseService.get_by_id(UserProfile, session['user_id'])
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        return jsonify({
            'user': user.to_dict(),
            'mfa_verified': session.get('mfa_verified', False)
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Get profile error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@auth_bp.route('/profile', methods=['PUT'])
@require_auth
@require_mfa
def update_profile():
    """
    Update user profile information
    
    Expected JSON:
    {
        "full_name": "Updated Name",
        "date_of_birth": "1990-01-01"
    }
    """
    try:
        data = request.get_json()
        user = DatabaseService.get_by_id(UserProfile, session['user_id'])
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Track changes for audit log
        changes = {}
        
        # Update full name if provided
        if 'full_name' in data:
            new_name = data['full_name'].strip()
            if new_name and new_name != user.full_name:
                changes['full_name'] = {'old': user.full_name, 'new': new_name}
                user.full_name = new_name
        
        # Update date of birth if provided
        if 'date_of_birth' in data:
            try:
                new_dob = datetime.strptime(data['date_of_birth'], '%Y-%m-%d').date()
                if new_dob != user.date_of_birth:
                    changes['date_of_birth'] = {
                        'old': user.date_of_birth.isoformat() if user.date_of_birth else None,
                        'new': new_dob.isoformat()
                    }
                    user.date_of_birth = new_dob
            except ValueError:
                return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400
        
        if changes:
            # Save changes
            if DatabaseService.safe_update(user, **{k: v['new'] for k, v in changes.items()}):
                # Log profile update
                AuditService.log_user_action(
                    user_id=user.user_id,
                    action='profile_updated',
                    details={
                        'changes': changes,
                        'timestamp': datetime.utcnow().isoformat()
                    }
                )
                
                return jsonify({
                    'message': 'Profile updated successfully',
                    'user': user.to_dict()
                }), 200
            else:
                return jsonify({'error': 'Failed to update profile'}), 500
        else:
            return jsonify({'message': 'No changes to update'}), 200
            
    except Exception as e:
        current_app.logger.error(f"Update profile error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@auth_bp.route('/change-password', methods=['POST'])
@require_auth
@require_mfa
def change_password():
    """
    Change user password
    
    Expected JSON:
    {
        "current_password": "old_password",
        "new_password": "new_password"
    }
    """
    try:
        data = request.get_json()
        current_password = data.get('current_password', '')
        new_password = data.get('new_password', '')
        
        if not current_password or not new_password:
            return jsonify({'error': 'Current and new passwords are required'}), 400
        
        if len(new_password) < 8:
            return jsonify({'error': 'New password must be at least 8 characters long'}), 400
        
        user = DatabaseService.get_by_id(UserProfile, session['user_id'])
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Get current password hash
        metadata = user.get_decrypted_metadata()
        if not metadata or 'password_hash' not in metadata:
            return jsonify({'error': 'Account configuration error'}), 500
        
        # Verify current password
        if not check_password_hash(metadata['password_hash'], current_password):
            return jsonify({'error': 'Current password is incorrect'}), 401
        
        # Update password hash
        metadata['password_hash'] = generate_password_hash(new_password)
        metadata['password_changed_at'] = datetime.utcnow().isoformat()
        user.set_encrypted_metadata(metadata)
        
        if DatabaseService.safe_update(user, encrypted_metadata=user.encrypted_metadata):
            # Log password change
            AuditService.log_user_action(
                user_id=user.user_id,
                action='password_changed',
                details={
                    'timestamp': datetime.utcnow().isoformat()
                }
            )
            
            return jsonify({'message': 'Password changed successfully'}), 200
        else:
            return jsonify({'error': 'Failed to change password'}), 500
            
    except Exception as e:
        current_app.logger.error(f"Change password error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@auth_bp.route('/logout', methods=['POST'])
@require_auth
def logout():
    """Logout user and clear session"""
    try:
        user_id = session.get('user_id')
        
        # Log logout
        if user_id:
            AuditService.log_user_action(
                user_id=user_id,
                action='logout',
                details={
                    'timestamp': datetime.utcnow().isoformat()
                }
            )
        
        # Clear session
        session.clear()
        
        return jsonify({'message': 'Logged out successfully'}), 200
        
    except Exception as e:
        current_app.logger.error(f"Logout error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@auth_bp.route('/session', methods=['GET'])
def check_session():
    """Check if user has valid session"""
    try:
        if 'user_id' not in session:
            return jsonify({'authenticated': False}), 200
        
        # Verify user still exists and is active
        user = DatabaseService.get_by_id(UserProfile, session['user_id'])
        if not user or user.status != 'active':
            session.clear()
            return jsonify({'authenticated': False}), 200
        
        return jsonify({
            'authenticated': True,
            'user': user.to_dict(),
            'mfa_verified': session.get('mfa_verified', False)
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Session check error: {str(e)}")
        return jsonify({'authenticated': False}), 200