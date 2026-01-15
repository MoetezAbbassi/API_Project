"""
Flask app factory and initialization
"""
from flask import Flask, send_from_directory
from flask_cors import CORS
import os

from app.extensions import db, jwt
from config import current_config


def create_app(config=None):
    """
    Application factory function.
    Creates and configures the Flask application.
    
    Args:
        config: Configuration object (defaults to current_config)
    
    Returns:
        Flask application instance
    """
    app = Flask(__name__, static_folder='../frontend', static_url_path='')
    
    # Load configuration
    if config:
        app.config.from_object(config)
    else:
        app.config.from_object(current_config)
    
    # Initialize extensions
    db.init_app(app)
    jwt.init_app(app)
    
    # Configure CORS
    CORS(
        app,
        origins=app.config.get('CORS_ORIGINS', '*'),
        allow_headers=app.config.get('CORS_ALLOW_HEADERS', ['Content-Type', 'Authorization']),
        methods=app.config.get('CORS_METHODS', ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'])
    )
    
    # Create uploads directory if it doesn't exist
    upload_folder = app.config.get('UPLOAD_FOLDER')
    if upload_folder and not os.path.exists(upload_folder):
        try:
            os.makedirs(upload_folder, exist_ok=True)
        except Exception as e:
            print(f"Warning: Could not create upload folder: {e}")
    
    # Create application context and initialize database
    with app.app_context():
        # Import models to ensure they're registered with SQLAlchemy
        from app import models
        try:
            db.create_all()
        except Exception as e:
            print(f"Warning: Could not create database tables: {e}")
    
    # Register blueprints
    from app.routes import auth, users, exercises, workouts, calendar, programs, dashboard, ml, nutrition, meals
    app.register_blueprint(auth.bp)
    app.register_blueprint(users.bp)
    app.register_blueprint(exercises.bp)
    app.register_blueprint(workouts.bp)
    app.register_blueprint(calendar.bp)
    app.register_blueprint(programs.bp)
    app.register_blueprint(dashboard.bp)
    app.register_blueprint(ml.bp)
    app.register_blueprint(nutrition.bp)
    app.register_blueprint(meals.bp)
    
    # Register error handlers
    register_error_handlers(app)
    
    # Register health check endpoint
    @app.route('/api/health', methods=['GET'])
    def health_check():
        """Health check endpoint"""
        return {
            'status': 'healthy',
            'service': 'Fitness API',
            'version': '1.0.0'
        }, 200
    
    # Serve frontend files
    @app.route('/')
    def serve_index():
        """Serve the main index page"""
        return send_from_directory(app.static_folder, 'index.html')
    
    @app.route('/app')
    def serve_app():
        """Serve the app dashboard page"""
        return send_from_directory(app.static_folder, 'app.html')
    
    @app.route('/<path:filename>')
    def serve_static(filename):
        """Serve static frontend files"""
        # Don't serve API routes as static files
        if filename.startswith('api/'):
            return {'error': 'Not Found'}, 404
        
        # Check if file exists, otherwise return index.html for SPA routing
        file_path = os.path.join(app.static_folder, filename)
        if os.path.isfile(file_path):
            return send_from_directory(app.static_folder, filename)
        # For HTML files without extension
        if not '.' in filename:
            html_file = filename + '.html'
            html_path = os.path.join(app.static_folder, html_file)
            if os.path.isfile(html_path):
                return send_from_directory(app.static_folder, html_file)
        return send_from_directory(app.static_folder, 'index.html')
    
    return app


def register_error_handlers(app):
    """Register global error handlers"""
    from flask import jsonify
    
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            'success': False,
            'error': 'NOT_FOUND',
            'message': 'The requested resource does not exist'
        }), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({
            'success': False,
            'error': 'INTERNAL_SERVER_ERROR',
            'message': 'An internal server error occurred'
        }), 500
    
    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({
            'success': False,
            'error': 'BAD_REQUEST',
            'message': 'Bad request'
        }), 400
