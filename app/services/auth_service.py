"""Authentication service for password hashing and JWT token management."""
from typing import Tuple, Optional, Dict
import bcrypt
from flask_jwt_extended import create_access_token, decode_token
from datetime import datetime, timedelta, timezone
from config import Config
from app.utils import validators


class AuthService:
    """Service for handling authentication operations."""
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password using bcrypt.
        
        Args:
            password: Plain text password to hash
            
        Returns:
            Hashed password string
            
        Raises:
            ValueError: If password is invalid
        """
        # Validate password first
        is_valid, error_msg = validators.validate_password(password)
        if not is_valid:
            raise ValueError(error_msg)
        
        # Hash the password with bcrypt
        salt = bcrypt.gensalt(rounds=12)
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')
    
    @staticmethod
    def verify_password(password: str, password_hash: str) -> bool:
        """Verify a password against its hash.
        
        Args:
            password: Plain text password to verify
            password_hash: Hashed password to compare against
            
        Returns:
            True if password matches hash, False otherwise
        """
        try:
            return bcrypt.checkpw(
                password.encode('utf-8'),
                password_hash.encode('utf-8')
            )
        except Exception:
            return False
    
    @staticmethod
    def generate_jwt_token(user_id: str) -> str:
        """Generate a JWT access token.
        
        Args:
            user_id: User ID to encode in token
            
        Returns:
            JWT token string
        """
        return create_access_token(
            identity=user_id,
            expires_delta=timedelta(hours=24)
        )
    
    @staticmethod
    def decode_jwt_token(token: str) -> Optional[Dict]:
        """Decode and verify a JWT token.
        
        Args:
            token: JWT token string to decode
            
        Returns:
            Dictionary with user_id if valid, None if invalid/expired
        """
        try:
            decoded = decode_token(token)
            user_id = decoded.get('sub')  # 'sub' is the identity claim
            
            if user_id:
                return {"user_id": user_id}
            return None
        except Exception:
            # Token is expired, invalid, or malformed
            return None
    
    @staticmethod
    def validate_registration_input(username: str, email: str, password: str) -> Tuple[bool, str]:
        """Validate all registration input fields.
        
        Args:
            username: Username to validate
            email: Email to validate
            password: Password to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Validate username
        is_valid_username, username_error = validators.validate_username(username)
        if not is_valid_username:
            return False, username_error
        
        # Validate email
        if not validators.validate_email(email):
            return False, "Invalid email format"
        
        # Validate password
        is_valid_password, password_error = validators.validate_password(password)
        if not is_valid_password:
            return False, password_error
        
        return True, ""
    
    @staticmethod
    def generate_refresh_token(user_id: str) -> str:
        """Generate a refresh token (same as access token for now).
        
        In a more advanced implementation, you'd have shorter-lived access tokens
        and longer-lived refresh tokens.
        
        Args:
            user_id: User ID to encode in token
            
        Returns:
            JWT refresh token string
        """
        return create_access_token(
            identity=user_id,
            expires_delta=timedelta(days=7)  # Longer expiry for refresh
        )
