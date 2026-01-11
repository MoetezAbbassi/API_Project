"""Decorators for route protection and validation."""
from functools import wraps
from flask import request
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
from app.utils.responses import error_response, unauthorized_response, validation_error_response


def token_required(fn):
    """Decorator to require JWT token in Authorization header.
    
    Verifies the JWT token and extracts user_id to pass to the decorated function.
    If token is invalid or missing, returns 401 Unauthorized.
    
    Usage:
        @bp.route('/api/endpoint')
        @token_required
        def my_endpoint(user_id):
            # user_id is automatically extracted from token
            pass
    """
    @wraps(fn)
    def decorator(*args, **kwargs):
        try:
            verify_jwt_in_request()
            user_id = get_jwt_identity()
            return fn(user_id, *args, **kwargs)
        except Exception as e:
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
