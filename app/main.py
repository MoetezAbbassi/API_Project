"""
Flask app factory and initialization
"""
from flask import Flask, send_from_directory, jsonify
from flask_cors import CORS
from flasgger import Flasgger
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
    
    # Configure Swagger/OpenAPI documentation
    from app.swagger_config import SWAGGER_CONFIG, SWAGGER_TEMPLATE
    Flasgger(app, config=SWAGGER_CONFIG, template=SWAGGER_TEMPLATE)
    
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
            
            # Auto-seed exercises if database is empty
            if models.Exercise.query.count() == 0:
                try:
                    from scripts.seed_exercises import seed_exercises
                    print("🌱 Seeding exercises into database...")
                    seed_exercises()
                    print("✓ Exercises seeded successfully")
                except Exception as seed_error:
                    print(f"⚠ Could not auto-seed exercises: {seed_error}")
                    
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
    
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            'success': False,
            'error': {
                'type': 'Not Found',
                'message': 'The requested resource does not exist',
                'code': 'NOT_FOUND'
            }
        }), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({
            'success': False,
            'error': {
                'type': 'Internal Server Error',
                'message': 'An internal server error occurred',
                'code': 'INTERNAL_SERVER_ERROR'
            }
        }), 500
    
    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({
            'success': False,
            'error': {
                'type': 'Bad Request',
                'message': 'Bad request',
                'code': 'BAD_REQUEST'
            }
        }), 400
    
    @app.errorhandler(401)
    def unauthorized(error):
        return jsonify({
            'success': False,
            'error': {
                'type': 'Unauthorized',
                'message': 'Authentication required or credentials invalid',
                'code': 'UNAUTHORIZED'
            }
        }), 401
    
    @app.errorhandler(403)
    def forbidden(error):
        return jsonify({
            'success': False,
            'error': {
                'type': 'Forbidden',
                'message': 'You do not have permission to access this resource',
                'code': 'FORBIDDEN'
            }
        }), 403

