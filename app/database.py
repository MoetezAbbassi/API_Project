"""
Database module - simplified for Flask-SQLAlchemy
The 'db' object is now initialized in app/__init__.py
"""
import logging

logger = logging.getLogger(__name__)

# Note: Do NOT import db here to avoid circular imports
# Import db from 'app' when needed: from app import db
