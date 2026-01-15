"""Decorators for route protection and validation."""
from functools import wraps
from flask import request
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
from app.utils.responses import error_response, unauthorized_response, validation_error_response
import inspect
import logging

logger = logging.getLogger(__name__)


def token_required(fn):
    """Decorator to require JWT token in Authorization header.
    
    Verifies the JWT token and extracts user_id to pass to the decorated function.
    If token is invalid or missing, returns 401 Unauthorized.
    
    The decorated function can accept token_user_id as a parameter, which will be
    populated from the JWT token.
    
    Usage:
        @bp.route('/api/endpoint')
        @token_required
        def my_endpoint(token_user_id):
            # token_user_id is automatically extracted from token
            pass
            
        @bp.route('/api/endpoint/<user_id>')
        @token_required
        def my_endpoint(token_user_id, user_id):
            # token_user_id from JWT, user_id from URL
            pass
    """
    @wraps(fn)
    def decorator(*args, **kwargs):
        try:
            # Debug: Check what's in the Authorization header
            auth_header = request.headers.get('Authorization')
            logger.info(f"🔐 @token_required - Authorization header: {auth_header[:50] if auth_header else 'MISSING'}...")
            
            if not auth_header:
                logger.error("❌ NO AUTHORIZATION HEADER!")
                return unauthorized_response("Missing Authorization header")
            
            # Verify JWT
            verify_jwt_in_request()
            token_user_id = get_jwt_identity()
            logger.info(f"✅ Token valid! user_id: {token_user_id}")
            
            # Get function signature
            sig = inspect.signature(fn)
            params = list(sig.parameters.keys())
            
            logger.info(f"Function: {fn.__name__}, params: {params}")
            logger.info(f"Decorator received - args: {len(args)} items, kwargs keys: {list(kwargs.keys())}")
            
            # If function expects token_user_id, inject it
            if 'token_user_id' in params:
                # Check if token_user_id is already passed as first positional arg
                if len(args) > 0 and args[0] == token_user_id:
                    logger.info(f"  → token_user_id already in args[0], skipping")
                elif 'token_user_id' not in kwargs:
                    logger.info(f"  → Adding token_user_id to kwargs")
                    kwargs['token_user_id'] = token_user_id
                else:
                    logger.info(f"  → token_user_id already in kwargs, skipping")
            
            logger.info(f"Calling {fn.__name__} with {len(args)} args and {len(kwargs)} kwargs")
            return fn(*args, **kwargs)
                
        except Exception as e:
            import traceback
            logger.error(f"❌ Token verification failed: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            return unauthorized_response("Invalid or expired token")
    
    return decorator


def validate_json(fn):
    """Decorator to validate that request has JSON body.
    
    Ensures the request contains valid JSON and returns 400 Bad Request if empty.
    
    Usage:
        @bp.route('/api/endpoint', methods=['POST'])
        @validate_json
        def my_endpoint():
            data = request.get_json()
            pass
    """
    @wraps(fn)
    def decorator(*args, **kwargs):
        if not request.is_json:
            return validation_error_response("Request must contain valid JSON")
        
        data = request.get_json()
        if not data:
            return validation_error_response("Request body cannot be empty")
        
        return fn(*args, **kwargs)
    
    return decorator


def handle_errors(fn):
    """Decorator for general error handling in route handlers.
    
    Catches unexpected exceptions and returns 500 Internal Server Error.
    
    Usage:
        @bp.route('/api/endpoint')
        @handle_errors
        def my_endpoint():
            # Any unhandled exceptions will return 500
            pass
    """
    @wraps(fn)
    def decorator(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except Exception as e:
            # Log the error in production
            return error_response(
                "Internal Server Error",
                "An unexpected error occurred",
                "INTERNAL_ERROR",
                500
            )
    
    return decorator
