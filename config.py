import os
from datetime import timedelta
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Ensure database directory exists
db_dir = os.path.join(os.path.expanduser('~'), 'site', 'wwwroot', 'data') if os.getenv('WEBSITE_INSTANCE_ID') else os.path.dirname(os.path.abspath(__file__))
os.makedirs(db_dir, exist_ok=True)


class Config:
    """Base configuration class"""
    
    # Flask Configuration
    FLASK_ENV = os.getenv('FLASK_ENV', 'production')
    DEBUG = FLASK_ENV == 'development'
    TESTING = False
    
    # Database Configuration - Use persistent storage on Azure
    _db_path = os.path.join(db_dir, 'fitness_app.db')
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', f'sqlite:///{_db_path}')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'connect_args': {'check_same_thread': False} if 'sqlite' in SQLALCHEMY_DATABASE_URI else {}
    }
    
    # Security Configuration
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    
    # JWT Configuration
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'jwt-secret-key-change-in-production')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)
    JWT_TOKEN_LOCATION = ['headers']
    JWT_HEADER_NAME = 'Authorization'
    JWT_HEADER_TYPE = 'Bearer'
    
    # Upload Configuration
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'uploads', 'images')
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 5MB max file size
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    
    # CORS Configuration
    CORS_ORIGINS = '*'
    CORS_ALLOW_HEADERS = ['Content-Type', 'Authorization']
    CORS_METHODS = ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS']
    
    # Pagination
    ITEMS_PER_PAGE = 10


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    TESTING = False


class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    JWT_SECRET_KEY = 'test-jwt-secret-key'
    SECRET_KEY = 'test-secret-key'


class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    TESTING = False


# Select configuration based on FLASK_ENV
config_by_name = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}

CURRENT_ENV = os.getenv('FLASK_ENV', 'development')
current_config = config_by_name.get(CURRENT_ENV, DevelopmentConfig)
