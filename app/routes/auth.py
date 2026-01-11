from flask import Blueprint, request
from app.extensions import db
from app.models import User
from app.utils.responses import success_response, error_response
from app.utils.validators import validate_required_fields, validate_email, validate_username, validate_password
from app.services.auth_service import AuthService
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

bp = Blueprint('auth', __name__, url_prefix='/api/auth')


@bp.route('/register', methods=['POST'])
def register():
    """Register a new user"""
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
        }, 'User registered successfully', 201), 201
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Registration error: {str(e)}")
        return error_response('SERVER_ERROR', str(e), 'SERVER_ERROR', 500)


@bp.route('/login', methods=['POST'])
def login():
    """Login user and return JWT token"""
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
        
        # Generate token
        token = AuthService.generate_jwt_token(user.user_id)
        
        logger.info(f"User logged in: {user.username}")
        
        return success_response({
            'user_id': user.user_id,
            'username': user.username,
            'token': token,
            'token_expires_in': 86400
        }, 'Login successful', 200)
        
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
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
