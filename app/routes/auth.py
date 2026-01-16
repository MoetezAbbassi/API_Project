from flask import Blueprint, request
from app.extensions import db
from app.models import User, EmailVerificationCode
from app.utils.responses import success_response, error_response
from app.utils.validators import validate_required_fields, validate_email, validate_username, validate_password
from app.services.auth_service import AuthService
from app.services.email_service import generate_verification_code, send_verification_email, create_verification_entry, verify_code
import logging
from datetime import datetime, timezone
import os
import requests as http_requests

logger = logging.getLogger(__name__)

bp = Blueprint('auth', __name__, url_prefix='/api/auth')

# Google OAuth Configuration
GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID', '')
GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET', '')
GOOGLE_TOKEN_URL = 'https://oauth2.googleapis.com/token'
GOOGLE_USERINFO_URL = 'https://www.googleapis.com/oauth2/v2/userinfo'


@bp.route('/google/login', methods=['POST'])
def google_login():
    """
    Login or register with Google OAuth 2.0
    ---
    tags:
      - Authentication
    summary: Google OAuth 2.0 login
    description: Authenticate using Google Sign-In. Creates new account if email not found.
    consumes:
      - application/json
    produces:
      - application/json
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            credential:
              type: string
              description: Google ID token from Sign-In button (alternative format)
            code:
              type: string
              description: Authorization code from OAuth flow
            redirect_uri:
              type: string
              description: Redirect URI used in OAuth flow
    responses:
      200:
        description: Google authentication successful
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            message:
              type: string
              example: Google login successful
            data:
              type: object
              properties:
                token:
                  type: string
                  description: JWT Bearer token
                user:
                  type: object
                is_new_user:
                  type: boolean
                  description: True if new account was created
      400:
        description: Bad request
        schema:
          $ref: '#/definitions/ErrorResponse'
      401:
        description: Invalid Google token
        schema:
          $ref: '#/definitions/ErrorResponse'
    """
    try:
        data = request.get_json()
        
        if not data:
            return error_response('INVALID_INPUT', 'Request body cannot be empty', 'EMPTY_BODY', 400)
        
        google_user_info = None
        
        # Method 1: Using ID token (credential from Google Sign-In button)
        if 'credential' in data:
            # Verify ID token with Google
            try:
                from google.oauth2 import id_token
                from google.auth.transport import requests as google_requests
                
                idinfo = id_token.verify_oauth2_token(
                    data['credential'],
                    google_requests.Request(),
                    GOOGLE_CLIENT_ID
                )
                
                google_user_info = {
                    'id': idinfo['sub'],
                    'email': idinfo['email'],
                    'name': idinfo.get('name', ''),
                    'picture': idinfo.get('picture', '')
                }
            except Exception as e:
                logger.error(f"Google ID token verification failed: {str(e)}")
                return error_response('INVALID_TOKEN', 'Invalid Google credential', 'INVALID_GOOGLE_TOKEN', 401)
        
        # Method 2: Using authorization code (from redirect flow)
        elif 'code' in data:
            redirect_uri = data.get('redirect_uri', 'http://localhost:5000')
            
            # Exchange code for tokens
            token_response = http_requests.post(GOOGLE_TOKEN_URL, data={
                'code': data['code'],
                'client_id': GOOGLE_CLIENT_ID,
                'client_secret': GOOGLE_CLIENT_SECRET,
                'redirect_uri': redirect_uri,
                'grant_type': 'authorization_code'
            })
            
            if token_response.status_code != 200:
                logger.error(f"Google token exchange failed: {token_response.text}")
                return error_response('OAUTH_ERROR', 'Failed to exchange authorization code', 'TOKEN_EXCHANGE_FAILED', 400)
            
            tokens = token_response.json()
            access_token = tokens.get('access_token')
            
            # Get user info with access token
            userinfo_response = http_requests.get(
                GOOGLE_USERINFO_URL,
                headers={'Authorization': f'Bearer {access_token}'}
            )
            
            if userinfo_response.status_code != 200:
                return error_response('OAUTH_ERROR', 'Failed to get user info from Google', 'USERINFO_FAILED', 400)
            
            google_user_info = userinfo_response.json()
        
        else:
            return error_response('INVALID_INPUT', 'Missing credential or authorization code', 'MISSING_OAUTH_DATA', 400)
        
        if not google_user_info or not google_user_info.get('email'):
            return error_response('OAUTH_ERROR', 'Could not retrieve email from Google', 'NO_EMAIL', 400)
        
        # Check if user exists by email
        email = google_user_info['email']
        user = db.session.query(User).filter(User.email == email).first()
        is_new_user = False
        
        if not user:
            # Create new user
            is_new_user = True
            
            # Generate username from email or name
            base_username = google_user_info.get('name', '').replace(' ', '_').lower()
            if not base_username:
                base_username = email.split('@')[0]
            
            # Ensure unique username
            username = base_username
            counter = 1
            while db.session.query(User).filter(User.username == username).first():
                username = f"{base_username}_{counter}"
                counter += 1
            
            # Generate a secure random password that meets validation requirements
            # OAuth users won't use this password, but it needs to be valid
            import secrets
            import string
            random_base = secrets.token_hex(8)  # 16 chars of hex
            random_password = f"Ggl@{random_base}1"  # Ensures uppercase, lowercase, number, special char
            
            user = User(
                username=username,
                email=email,
                password_hash=AuthService.hash_password(random_password),  # Random password for OAuth users
                google_id=google_user_info.get('id'),
                profile_picture=google_user_info.get('picture')
            )
            
            db.session.add(user)
            db.session.commit()
            
            logger.info(f"New user registered via Google OAuth: {user.username}")
        else:
            # Update Google ID if not set
            if not user.google_id:
                user.google_id = google_user_info.get('id')
                db.session.commit()
        
        # Generate JWT token
        token = AuthService.generate_jwt_token(user.user_id)
        
        return success_response({
            'token': token,
            'user': {
                'user_id': user.user_id,
                'username': user.username,
                'email': user.email,
                'profile_picture': google_user_info.get('picture')
            },
            'is_new_user': is_new_user
        }, 'Google login successful', 200)
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Google OAuth error: {str(e)}")
        return error_response('SERVER_ERROR', str(e), 'SERVER_ERROR', 500)


@bp.route('/google/config', methods=['GET'])
def google_config():
    """Get Google OAuth client ID for frontend"""
    return success_response({
        'client_id': GOOGLE_CLIENT_ID,
        'configured': bool(GOOGLE_CLIENT_ID)
    }, 'Google OAuth config', 200)


@bp.route('/register', methods=['POST'])
def register():
    """
    Register a new user
    ---
    tags:
      - Authentication
    summary: Register a new user account
    description: Create a new user account with email, username, and password
    consumes:
      - application/json
    produces:
      - application/json
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - username
            - email
            - password
          properties:
            username:
              type: string
              minLength: 3
              maxLength: 20
              description: Unique username (alphanumeric, 3-20 characters)
            email:
              type: string
              format: email
              description: Valid email address
            password:
              type: string
              minLength: 8
              description: Password (min 8 chars, must contain uppercase, lowercase, numbers)
    responses:
      201:
        description: User successfully registered
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            message:
              type: string
              example: User registered successfully
            user:
              type: object
              properties:
                user_id:
                  type: integer
                username:
                  type: string
                email:
                  type: string
                created_at:
                  type: string
                  format: date-time
      400:
        description: Bad request - validation error
        schema:
          $ref: '#/definitions/ErrorResponse'
      409:
        description: Conflict - username or email already exists
        schema:
          $ref: '#/definitions/ErrorResponse'
    """
    try:
        data = request.get_json()
        
        if not data:
            return error_response('INVALID_INPUT', 'Request body cannot be empty', 'EMPTY_BODY', 400)
        
        # Validate required fields
        required_fields = ['username', 'email', 'password']
        valid, missing_field = validate_required_fields(data, required_fields)
        if not valid:
            return error_response('MISSING_FIELD', f'Missing required field: {missing_field}', 'MISSING_FIELD', 400)
        
        # Validate inputs
        valid, msg = validate_username(data['username'])
        if not valid:
            return error_response('INVALID_USERNAME', msg, 'INVALID_USERNAME', 400)
        
        if not validate_email(data['email']):
            return error_response('INVALID_EMAIL', 'Invalid email format', 'INVALID_EMAIL', 400)
        
        valid, msg = validate_password(data['password'])
        if not valid:
            return error_response('WEAK_PASSWORD', msg, 'WEAK_PASSWORD', 400)
        
        # Check if user already exists
        existing_user = db.session.query(User).filter(
            (User.username == data['username']) | (User.email == data['email'])
        ).first()
        
        if existing_user:
            return error_response('USER_EXISTS', 'Username or email already exists', 'USER_EXISTS', 400)
        
        # Create new user
        user = User(
            username=data['username'],
            email=data['email'],
            password_hash=AuthService.hash_password(data['password'])
        )
        
        db.session.add(user)
        db.session.commit()
        
        logger.info(f"User registered: {user.username}")
        
        return success_response({
            'user_id': user.user_id,
            'username': user.username,
            'email': user.email,
            'created_at': user.created_at.isoformat()
        }, 'User registered successfully', 201)
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Registration error: {str(e)}")
        return error_response('SERVER_ERROR', str(e), 'SERVER_ERROR', 500)


@bp.route('/login', methods=['POST'])
def login():
    """
    Step 1 of login: Verify credentials and send verification code to email
    ---
    tags:
      - Authentication
    summary: Login with email and password
    description: Initiate login flow. Sends 6-digit verification code to registered email.
    consumes:
      - application/json
    produces:
      - application/json
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - username
            - password
          properties:
            username:
              type: string
              description: Username
            password:
              type: string
              description: Password
    responses:
      200:
        description: Verification code sent to email
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            message:
              type: string
              example: Verification code sent to your email
            data:
              type: object
              properties:
                user_id:
                  type: string
                email_hint:
                  type: string
                  example: a***@gmail.com
                verification_required:
                  type: boolean
                expires_in_seconds:
                  type: integer
      400:
        description: Bad request - validation or invalid credentials
        schema:
          $ref: '#/definitions/ErrorResponse'
      404:
        description: User not found
        schema:
          $ref: '#/definitions/ErrorResponse'
    """
    try:
        data = request.get_json()
        
        if not data:
            return error_response('INVALID_INPUT', 'Request body cannot be empty', 'EMPTY_BODY', 400)
        
        # Validate required fields
        required_fields = ['username', 'password']
        valid, missing_field = validate_required_fields(data, required_fields)
        if not valid:
            return error_response('MISSING_FIELD', f'Missing required field: {missing_field}', 'MISSING_FIELD', 400)
        
        # Find user
        user = db.session.query(User).filter(User.username == data['username']).first()
        
        if not user:
            return error_response('USER_NOT_FOUND', 'User not found', 'USER_NOT_FOUND', 404)
        
        # Verify password
        if not AuthService.verify_password(data['password'], user.password_hash):
            return error_response('INVALID_PASSWORD', 'Invalid password', 'INVALID_PASSWORD', 400)
        
        # Generate and send verification code
        code = generate_verification_code()
        
        # Create verification entry in database
        verification_info = create_verification_entry(user.user_id, code)
        
        # Send email with code
        email_sent, email_msg = send_verification_email(user.email, code, user.username)
        
        if not email_sent:
            logger.warning(f"Failed to send verification email: {email_msg}")
            # Still continue - code is stored in database
        
        # Create email hint (hide most of the email)
        email_parts = user.email.split('@')
        email_hint = f"{email_parts[0][:2]}***@{email_parts[1]}" if len(email_parts) == 2 else "***"
        
        logger.info(f"Verification code sent for user: {user.username}")
        
        return success_response({
            'user_id': user.user_id,
            'email_hint': email_hint,
            'verification_required': True,
            'expires_in_seconds': verification_info['expires_in_seconds']
        }, 'Verification code sent to your email', 200)
        
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        return error_response('SERVER_ERROR', str(e), 'SERVER_ERROR', 500)


@bp.route('/verify-login', methods=['POST'])
def verify_login():
    """
    Step 2 of login: Verify the code sent to email and get JWT token
    ---
    tags:
      - Authentication
    summary: Verify 2FA code and get JWT token
    description: Complete login flow by verifying the 6-digit code from email
    consumes:
      - application/json
    produces:
      - application/json
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - user_id
            - code
          properties:
            user_id:
              type: string
              description: User ID from login endpoint
            code:
              type: string
              pattern: '^\\d{6}$'
              description: 6-digit verification code from email
    responses:
      200:
        description: Login successful, JWT token issued
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            message:
              type: string
              example: Login successful
            data:
              type: object
              properties:
                user_id:
                  type: string
                username:
                  type: string
                email:
                  type: string
                token:
                  type: string
                  description: JWT Bearer token for authenticated requests
                token_expires_in:
                  type: integer
                  example: 86400
      400:
        description: Bad request or invalid code
        schema:
          $ref: '#/definitions/ErrorResponse'
      404:
        description: User not found
        schema:
          $ref: '#/definitions/ErrorResponse'
    """
    try:
        data = request.get_json()
        
        if not data:
            return error_response('INVALID_INPUT', 'Request body cannot be empty', 'EMPTY_BODY', 400)
        
        # Validate required fields
        required_fields = ['user_id', 'code']
        valid, missing_field = validate_required_fields(data, required_fields)
        if not valid:
            return error_response('MISSING_FIELD', f'Missing required field: {missing_field}', 'MISSING_FIELD', 400)
        
        user_id = data['user_id']
        code = data['code']
        
        # Find user
        user = db.session.query(User).filter(User.user_id == user_id).first()
        
        if not user:
            return error_response('USER_NOT_FOUND', 'User not found', 'USER_NOT_FOUND', 404)
        
        # Verify the code
        is_valid, msg = verify_code(user_id, code)
        
        if not is_valid:
            return error_response('INVALID_CODE', msg, 'INVALID_CODE', 400)
        
        # Generate JWT token
        token = AuthService.generate_jwt_token(user.user_id)
        
        logger.info(f"User logged in with 2FA: {user.username}")
        
        return success_response({
            'user_id': user.user_id,
            'username': user.username,
            'email': user.email,
            'token': token,
            'token_expires_in': 86400
        }, 'Login successful', 200)
        
    except Exception as e:
        logger.error(f"Verify login error: {str(e)}")
        return error_response('SERVER_ERROR', str(e), 'SERVER_ERROR', 500)


@bp.route('/resend-code', methods=['POST'])
def resend_verification_code():
    """
    Resend verification code to user's email
    
    Request body:
    {
        "user_id": "uuid"
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return error_response('INVALID_INPUT', 'Request body cannot be empty', 'EMPTY_BODY', 400)
        
        user_id = data.get('user_id')
        if not user_id:
            return error_response('MISSING_FIELD', 'Missing required field: user_id', 'MISSING_FIELD', 400)
        
        # Find user
        user = db.session.query(User).filter(User.user_id == user_id).first()
        
        if not user:
            return error_response('USER_NOT_FOUND', 'User not found', 'USER_NOT_FOUND', 404)
        
        # Generate new code
        code = generate_verification_code()
        verification_info = create_verification_entry(user.user_id, code)
        
        # Send email
        email_sent, email_msg = send_verification_email(user.email, code, user.username)
        
        # Create email hint
        email_parts = user.email.split('@')
        email_hint = f"{email_parts[0][:2]}***@{email_parts[1]}" if len(email_parts) == 2 else "***"
        
        return success_response({
            'email_hint': email_hint,
            'expires_in_seconds': verification_info['expires_in_seconds']
        }, 'Verification code resent', 200)
        
    except Exception as e:
        logger.error(f"Resend code error: {str(e)}")
        return error_response('SERVER_ERROR', str(e), 'SERVER_ERROR', 500)


@bp.route('/logout', methods=['POST'])
def logout():
    """Logout user (token invalidation would happen on client side)"""
    try:
        # In a real app, you might blacklist the token here
        return success_response({}, 'Logged out successfully', 200)
        
    except Exception as e:
        logger.error(f"Logout error: {str(e)}")
        return error_response('SERVER_ERROR', str(e), 'SERVER_ERROR', 500)


@bp.route('/verify', methods=['GET'])
def verify():
    """Verify JWT token"""
    try:
        from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
        
        verify_jwt_in_request()
        user_id = get_jwt_identity()
        
        user = db.session.query(User).filter(User.user_id == user_id).first()
        
        if not user:
            return error_response('USER_NOT_FOUND', 'User not found', 'USER_NOT_FOUND', 404)
        
        return success_response({
            'user_id': user.user_id,
            'username': user.username
        }, 'Token is valid', 200)
        
    except Exception as e:
        logger.error(f"Token verification error: {str(e)}")
        return error_response('INVALID_TOKEN', 'Invalid or expired token', 'INVALID_TOKEN', 401)


@bp.route('/profile', methods=['GET'])
def get_profile():
    """Get user profile"""
    try:
        from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
        
        verify_jwt_in_request()
        user_id = get_jwt_identity()
        
        user = db.session.query(User).filter(User.user_id == user_id).first()
        
        if not user:
            return error_response('USER_NOT_FOUND', 'User not found', 'USER_NOT_FOUND', 404)
        
        return success_response({
            'user_id': user.user_id,
            'username': user.username,
            'email': user.email,
            'age': user.age,
            'height': user.height,
            'current_weight': user.current_weight,
            'target_weight': user.target_weight,
            'created_at': user.created_at.isoformat() if user.created_at else None
        }, 'Profile retrieved', 200)
        
    except Exception as e:
        logger.error(f"Profile retrieval error: {str(e)}")
        return error_response('SERVER_ERROR', str(e), 'SERVER_ERROR', 500)


@bp.route('/profile', methods=['PUT'])
def update_profile():
    """Update user profile"""
    try:
        from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
        
        verify_jwt_in_request()
        user_id = get_jwt_identity()
        
        user = db.session.query(User).filter(User.user_id == user_id).first()
        
        if not user:
            return error_response('USER_NOT_FOUND', 'User not found', 'USER_NOT_FOUND', 404)
        
        data = request.get_json()
        
        if 'height' in data:
            user.height = data['height']
        if 'current_weight' in data:
            user.current_weight = data['current_weight']
        if 'target_weight' in data:
            user.target_weight = data['target_weight']
        if 'age' in data:
            user.age = data['age']
        
        db.session.commit()
        
        logger.info(f"Profile updated for user: {user.username}")
        
        return success_response({
            'user_id': user.user_id,
            'username': user.username,
            'email': user.email,
            'age': user.age,
            'height': user.height,
            'current_weight': user.current_weight,
            'target_weight': user.target_weight
        }, 'Profile updated', 200)
        
    except Exception as e:
        logger.error(f"Profile update error: {str(e)}")
        return error_response('SERVER_ERROR', str(e), 'SERVER_ERROR', 500)


@bp.route('/change-password', methods=['POST'])
def change_password():
    """Change user password"""
    try:
        from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
        
        verify_jwt_in_request()
        user_id = get_jwt_identity()
        
        user = db.session.query(User).filter(User.user_id == user_id).first()
        
        if not user:
            return error_response('USER_NOT_FOUND', 'User not found', 'USER_NOT_FOUND', 404)
        
        data = request.get_json()
        current_password = data.get('current_password')
        new_password = data.get('new_password')
        
        if not current_password or not new_password:
            return error_response('MISSING_FIELDS', 'Current and new password required', 'MISSING_FIELDS', 400)
        
        # Verify current password
        if not AuthService.verify_password(current_password, user.password_hash):
            return error_response('INVALID_PASSWORD', 'Current password is incorrect', 'INVALID_PASSWORD', 401)
        
        # Hash and set new password
        user.password_hash = AuthService.hash_password(new_password)
        db.session.commit()
        
        logger.info(f"Password changed for user: {user.username}")
        
        return success_response({}, 'Password changed successfully', 200)
        
    except Exception as e:
        logger.error(f"Password change error: {str(e)}")
        return error_response('SERVER_ERROR', str(e), 'SERVER_ERROR', 500)


@bp.route('/refresh-token', methods=['POST'])
def refresh_token():
    """Refresh JWT token"""
    try:
        from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
        
        verify_jwt_in_request()
        user_id = get_jwt_identity()
        
        user = db.session.query(User).filter(User.user_id == user_id).first()
        
        if not user:
            return error_response('USER_NOT_FOUND', 'User not found', 'USER_NOT_FOUND', 404)
        
        # Generate new token
        new_token = AuthService.generate_jwt_token(user.user_id)
        
        logger.info(f"Token refreshed for user: {user.username}")
        
        return success_response({
            'token': new_token,
            'token_expires_in': 86400
        }, 'Token refreshed', 200)
        
    except Exception as e:
        logger.error(f"Token refresh error: {str(e)}")
        return error_response('INVALID_TOKEN', 'Invalid or expired token', 'INVALID_TOKEN', 401)
