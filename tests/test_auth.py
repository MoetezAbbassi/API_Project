"""
Authentication endpoint tests.
"""

import pytest
import json


class TestAuthRegister:
    """Test user registration endpoint."""
    
    def test_register_success(self, test_client):
        """Test successful user registration."""
        response = test_client.post(
            '/api/auth/register',
            json={
                "username": "newuser",
                "email": "new@example.com",
                "password": "SecurePass123"
            }
        )
        
        assert response.status_code == 201
        data = response.get_json()
        assert data['success'] is True
        assert 'user_id' in data['data']
        assert data['data']['username'] == "newuser"
        assert data['data']['email'] == "new@example.com"
    
    def test_register_duplicate_username(self, test_client, sample_user):
        """Test registration with duplicate username."""
        response = test_client.post(
            '/api/auth/register',
            json={
                "username": "testuser",  # Already exists
                "email": "another@example.com",
                "password": "SecurePass123"
            }
        )
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['success'] is False
        assert "username already exists" in data['message'].lower()
    
    def test_register_duplicate_email(self, test_client, sample_user):
        """Test registration with duplicate email."""
        response = test_client.post(
            '/api/auth/register',
            json={
                "username": "anotheruser",
                "email": "test@example.com",  # Already exists
                "password": "SecurePass123"
            }
        )
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['success'] is False
    
    def test_register_weak_password(self, test_client):
        """Test registration with weak password."""
        response = test_client.post(
            '/api/auth/register',
            json={
                "username": "weakuser",
                "email": "weak@example.com",
                "password": "weak"  # Too weak
            }
        )
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['success'] is False
        assert "password" in data['message'].lower()
    
    def test_register_missing_fields(self, test_client):
        """Test registration with missing required fields."""
        response = test_client.post(
            '/api/auth/register',
            json={
                "username": "user"
                # Missing email and password
            }
        )
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['success'] is False


class TestAuthLogin:
    """Test user login endpoint."""
    
    def test_login_success(self, test_client, sample_user):
        """Test successful login."""
        response = test_client.post(
            '/api/auth/login',
            json={
                "username": "testuser",
                "password": "TestPassword123"
            }
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert 'token' in data['data']
        assert data['data']['username'] == "testuser"
    
    def test_login_invalid_password(self, test_client, sample_user):
        """Test login with wrong password."""
        response = test_client.post(
            '/api/auth/login',
            json={
                "username": "testuser",
                "password": "WrongPassword123"
            }
        )
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['success'] is False
    
    def test_login_user_not_found(self, test_client):
        """Test login with nonexistent user."""
        response = test_client.post(
            '/api/auth/login',
            json={
                "username": "nonexistentuser",
                "password": "SomePassword123"
            }
        )
        
        assert response.status_code == 404
        data = response.get_json()
        assert data['success'] is False
    
    def test_login_missing_fields(self, test_client):
        """Test login with missing fields."""
        response = test_client.post(
            '/api/auth/login',
            json={
                "username": "testuser"
                # Missing password
            }
        )
        
        assert response.status_code == 400


class TestAuthVerify:
    """Test token verification endpoint."""
    
    def test_verify_token_valid(self, test_client, auth_headers):
        """Test verification with valid token."""
        response = test_client.get(
            '/api/auth/verify',
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert 'user_id' in data['data']
    
    def test_verify_token_invalid(self, test_client):
        """Test verification with invalid token."""
        response = test_client.get(
            '/api/auth/verify',
            headers={"Authorization": "Bearer invalid.token.here"}
        )
        
        assert response.status_code == 401
        data = response.get_json()
        assert data['success'] is False
    
    def test_verify_token_missing(self, test_client):
        """Test verification without token."""
        response = test_client.get('/api/auth/verify')
        
        assert response.status_code == 401
        data = response.get_json()
        assert data['success'] is False


class TestAuthRefreshToken:
    """Test token refresh endpoint."""
    
    def test_refresh_token_success(self, test_client, auth_headers):
        """Test successful token refresh."""
        response = test_client.post(
            '/api/auth/refresh-token',
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert 'token' in data['data']
        assert data['data']['token'] != auth_headers['Authorization'].split(' ')[1]
    
    def test_refresh_token_invalid(self, test_client):
        """Test token refresh with invalid token."""
        response = test_client.post(
            '/api/auth/refresh-token',
            headers={"Authorization": "Bearer invalid.token"}
        )
        
        assert response.status_code == 401
        data = response.get_json()
        assert data['success'] is False
