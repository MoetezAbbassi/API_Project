# app/utils/responses.py - Fixed Version
"""
Standardized response handlers for Flask endpoints
Ensures all responses return valid Flask response format
"""
from flask import jsonify

def success_response(data=None, message="Success", status_code=200):
    """
    Return a successful response
    
    Args:
        data: Response data (dict or list)
        message: Success message
        status_code: HTTP status code
        
    Returns:
        Tuple of (dict, status_code) - Flask compatible
    """
    response = {
        "success": True,
        "message": message
    }
    if data is not None:
        response["data"] = data
    
    return response, status_code


def error_response(error_type="Error", error_message="An error occurred", error_code="GENERIC_ERROR", status_code=400):
    """
    Return an error response
    
    Args:
        error_type: Type of error (e.g., "Validation Error")
        error_message: Detailed error message
        error_code: Error code for client handling
        status_code: HTTP status code
        
    Returns:
        Tuple of (dict, status_code) - Flask compatible
    """
    return {
        "success": False,
        "error": {
            "type": error_type,
            "message": error_message,
            "code": error_code
        }
    }, status_code


def validation_error_response(message="Validation failed", status_code=422):
    """
    Return a validation error response
    
    Args:
        message: Validation error message
        status_code: HTTP status code (default 422 Unprocessable Entity)
        
    Returns:
        Tuple of (dict, status_code) - Flask compatible
    """
    return {
        "success": False,
        "error": {
            "type": "Validation Error",
            "message": message,
            "code": "VALIDATION_ERROR"
        }
    }, status_code


def not_found_response(message="Resource not found", status_code=404):
    """
    Return a not found response
    
    Args:
        message: Not found message
        status_code: HTTP status code (default 404)
        
    Returns:
        Tuple of (dict, status_code) - Flask compatible
    """
    return {
        "success": False,
        "error": {
            "type": "Not Found",
            "message": message,
            "code": "NOT_FOUND"
        }
    }, status_code


def unauthorized_response(message="Unauthorized access", status_code=401):
    """
    Return an unauthorized response
    
    Args:
        message: Unauthorized message
        status_code: HTTP status code (default 401)
        
    Returns:
        Tuple of (dict, status_code) - Flask compatible
    """
    return {
        "success": False,
        "error": {
            "type": "Unauthorized",
            "message": message,
            "code": "UNAUTHORIZED"
        }
    }, status_code


def forbidden_response(message="Forbidden access", status_code=403):
    """
    Return a forbidden response
    
    Args:
        message: Forbidden message
        status_code: HTTP status code (default 403)
        
    Returns:
        Tuple of (dict, status_code) - Flask compatible
    """
    return {
        "success": False,
        "error": {
            "type": "Forbidden",
            "message": message,
            "code": "FORBIDDEN"
        }
    }, status_code


def paginated_response(data, total, page, per_page, message="Success", status_code=200):
    """
    Return a paginated response
    
    Args:
        data: List of items
        total: Total count of items
        page: Current page number
        per_page: Items per page
        message: Success message
        status_code: HTTP status code
        
    Returns:
        Tuple of (dict, status_code) - Flask compatible
    """
    import math
    
    response = {
        "success": True,
        "message": message,
        "data": data,
        "pagination": {
            "total": total,
            "page": page,
            "per_page": per_page,
            "pages": math.ceil(total / per_page) if per_page > 0 else 0
        }
    }
    
    return response, status_code


def created_response(data=None, message="Created successfully", status_code=201):
    """
    Return a created response (201)
    
    Args:
        data: Created resource data
        message: Success message
        status_code: HTTP status code (default 201)
        
    Returns:
        Tuple of (dict, status_code) - Flask compatible
    """
    response = {
        "success": True,
        "message": message
    }
    if data is not None:
        response["data"] = data
    
    return response, status_code