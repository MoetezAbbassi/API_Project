"""
Pytest configuration and fixtures for testing the Fitness API.
"""

import pytest
import os
from datetime import datetime
from app import create_app
from app.database import db
from app.models import User
from app.services.auth_service import AuthService


@pytest.fixture
def test_app():
    """
    Create Flask app with in-memory SQLite database for testing.
    """
    # Set test configuration
    os.environ['FLASK_ENV'] = 'testing'
    os.environ['DATABASE_URL'] = 'sqlite:///:memory:'
    
    app = create_app()
    
    # Create tables
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def test_client(test_app):
    """
    Return Flask test client.
    """
    return test_app.test_client()


@pytest.fixture
def sample_user(test_app):
    """
    Create a sample user in the test database.
    """
    with test_app.app_context():
        user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "TestPassword123"
        }
        
        # Check if user already exists
        existing = User.query.filter_by(username=user_data["username"]).first()
        if existing:
            return existing
        
        # Hash password and create user
        password_hash = AuthService.hash_password(user_data["password"])
        user = User(
            username=user_data["username"],
            email=user_data["email"],
            password_hash=password_hash,
            age=28,
            current_weight=180,
            height=72
        )
        
        db.session.add(user)
        db.session.commit()
        
        return user


@pytest.fixture
def test_user_token(test_app, test_client, sample_user):
    """
    Create a test user and return a valid JWT token.
    """
    with test_app.app_context():
        # Login to get token
        response = test_client.post(
            '/api/auth/login',
            json={
                "username": "testuser",
                "password": "TestPassword123"
            }
        )
        
        if response.status_code == 200:
            data = response.get_json()
            return data['data']['token']
        
        return None


@pytest.fixture
def auth_headers(test_user_token):
    """
    Return authorization headers with valid token.
    """
    return {
        "Authorization": f"Bearer {test_user_token}"
    }
