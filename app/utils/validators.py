"""Validation functions for input data."""
import re
from datetime import datetime
from typing import Tuple


def validate_email(email: str) -> bool:
    """Validate email format.
    
    Args:
        email: Email address to validate
        
    Returns:
        True if valid email format, False otherwise
    """
    if not email:
        return False
    
    # Basic email regex pattern
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_username(username: str) -> Tuple[bool, str]:
    """Validate username format.
    
    Rules:
    - 3-20 characters
    - Alphanumeric and underscore only
    
    Args:
        username: Username to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not username:
        return False, "Username is required"
    
    if len(username) < 3:
        return False, "Username must be at least 3 characters"
    
    if len(username) > 20:
        return False, "Username must be at most 20 characters"
    
    if not re.match(r'^[a-zA-Z0-9_]+$', username):
        return False, "Username can only contain letters, numbers, and underscores"
    
    return True, ""


def validate_password(password: str) -> Tuple[bool, str]:
    """Validate password strength.
    
    Rules:
    - Minimum 8 characters
    - At least 1 uppercase letter
    - At least 1 number
    
    Args:
        password: Password to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not password:
        return False, "Password is required"
    
    if len(password) < 8:
        return False, "Password must be at least 8 characters"
    
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"
    
    if not re.search(r'\d', password):
        return False, "Password must contain at least one number"
    
    return True, ""


def validate_required_fields(data: dict, required: list) -> Tuple[bool, str]:
    """Validate that all required fields are present.
    
    Args:
        data: Dictionary to validate
        required: List of required field names
        
    Returns:
        Tuple of (is_valid, missing_field_name)
    """
    if not data:
        return False, "Request body is required"
    
    for field in required:
        if field not in data or data[field] is None:
            return False, f"{field} is required"
    
    return True, ""


def validate_positive_number(value, field_name: str) -> Tuple[bool, str]:
    """Validate that a value is a positive number.
    
    Args:
        value: Value to validate
        field_name: Name of field (for error message)
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if value is None:
        return False, f"{field_name} is required"
    
    try:
        num_value = float(value)
        if num_value <= 0:
            return False, f"{field_name} must be a positive number"
        return True, ""
    except (ValueError, TypeError):
        return False, f"{field_name} must be a valid number"


def validate_date(date_string: str) -> Tuple[bool, str]:
    """Validate date string in YYYY-MM-DD format.
    
    Args:
        date_string: Date string to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not date_string:
        return False, "Date is required"
    
    try:
        datetime.strptime(date_string, '%Y-%m-%d')
        return True, ""
    except ValueError:
        return False, "Date must be in YYYY-MM-DD format"


def validate_enum(value: str, allowed_values: list) -> Tuple[bool, str]:
    """Validate that value is in allowed list.
    
    Args:
        value: Value to validate
        allowed_values: List of allowed values
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not value:
        return False, "Value is required"
    
    if value not in allowed_values:
        return False, f"Value must be one of: {', '.join(allowed_values)}"
    
    return True, ""


def validate_int(value, field_name: str, min_value: int = None, max_value: int = None) -> Tuple[bool, str]:
    """Validate that value is an integer within range.
    
    Args:
        value: Value to validate
        field_name: Name of field (for error message)
        min_value: Minimum allowed value (optional)
        max_value: Maximum allowed value (optional)
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if value is None:
        return False, f"{field_name} is required"
    
    try:
        int_value = int(value)
        
        if min_value is not None and int_value < min_value:
            return False, f"{field_name} must be at least {min_value}"
        
        if max_value is not None and int_value > max_value:
            return False, f"{field_name} must be at most {max_value}"
        
        return True, ""
    except (ValueError, TypeError):
        return False, f"{field_name} must be a valid integer"
