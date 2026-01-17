"""
Flask app factory and initialization
"""
from flask import Flask, send_from_directory, jsonify
from flask_cors import CORS
from flasgger import Flasgger
import os
import uuid
from datetime import datetime

from app.extensions import db, jwt
from config import current_config


def _seed_exercises_inline():
    """Seed exercises directly (called from within app context)"""
    from app.models import Exercise
    
    exercises_data = [
        # Chest
        {"name": "Barbell Bench Press", "description": "Classic chest exercise", "primary_muscle_group": "chest", "secondary_muscle_groups": ["shoulders", "triceps"], "difficulty_level": "beginner", "typical_calories_per_minute": 7.5},
        {"name": "Dumbbell Bench Press", "description": "Bench press with dumbbells", "primary_muscle_group": "chest", "secondary_muscle_groups": ["shoulders", "triceps"], "difficulty_level": "beginner", "typical_calories_per_minute": 7.0},
        {"name": "Push-Ups", "description": "Bodyweight chest exercise", "primary_muscle_group": "chest", "secondary_muscle_groups": ["shoulders", "triceps", "core"], "difficulty_level": "beginner", "typical_calories_per_minute": 7.0},
        {"name": "Dumbbell Flyes", "description": "Isolation exercise for chest", "primary_muscle_group": "chest", "secondary_muscle_groups": ["shoulders"], "difficulty_level": "intermediate", "typical_calories_per_minute": 5.5},
        {"name": "Cable Crossover", "description": "Cable chest exercise", "primary_muscle_group": "chest", "secondary_muscle_groups": ["shoulders"], "difficulty_level": "intermediate", "typical_calories_per_minute": 6.0},
        
        # Back
        {"name": "Deadlift", "description": "Compound back exercise", "primary_muscle_group": "back", "secondary_muscle_groups": ["legs", "core"], "difficulty_level": "intermediate", "typical_calories_per_minute": 9.0},
        {"name": "Pull-Ups", "description": "Bodyweight back exercise", "primary_muscle_group": "back", "secondary_muscle_groups": ["biceps", "shoulders"], "difficulty_level": "intermediate", "typical_calories_per_minute": 8.0},
        {"name": "Barbell Row", "description": "Rowing movement for back", "primary_muscle_group": "back", "secondary_muscle_groups": ["biceps"], "difficulty_level": "intermediate", "typical_calories_per_minute": 7.5},
        {"name": "Lat Pulldown", "description": "Machine exercise for lats", "primary_muscle_group": "back", "secondary_muscle_groups": ["biceps"], "difficulty_level": "beginner", "typical_calories_per_minute": 6.5},
        {"name": "Seated Cable Row", "description": "Cable rowing exercise", "primary_muscle_group": "back", "secondary_muscle_groups": ["biceps"], "difficulty_level": "beginner", "typical_calories_per_minute": 6.0},
        
        # Legs
        {"name": "Barbell Squat", "description": "Compound leg exercise", "primary_muscle_group": "legs", "secondary_muscle_groups": ["core"], "difficulty_level": "beginner", "typical_calories_per_minute": 8.5},
        {"name": "Leg Press", "description": "Machine leg exercise", "primary_muscle_group": "legs", "secondary_muscle_groups": [], "difficulty_level": "beginner", "typical_calories_per_minute": 7.5},
        {"name": "Lunges", "description": "Single-leg exercise", "primary_muscle_group": "legs", "secondary_muscle_groups": ["core"], "difficulty_level": "beginner", "typical_calories_per_minute": 7.0},
        {"name": "Leg Extension", "description": "Quadriceps isolation", "primary_muscle_group": "legs", "secondary_muscle_groups": [], "difficulty_level": "beginner", "typical_calories_per_minute": 5.0},
        {"name": "Leg Curl", "description": "Hamstring isolation", "primary_muscle_group": "legs", "secondary_muscle_groups": [], "difficulty_level": "beginner", "typical_calories_per_minute": 5.0},
        
        # Shoulders
        {"name": "Overhead Press", "description": "Shoulder press with barbell", "primary_muscle_group": "shoulders", "secondary_muscle_groups": ["triceps", "core"], "difficulty_level": "beginner", "typical_calories_per_minute": 7.0},
        {"name": "Dumbbell Shoulder Press", "description": "Shoulder press with dumbbells", "primary_muscle_group": "shoulders", "secondary_muscle_groups": ["triceps"], "difficulty_level": "beginner", "typical_calories_per_minute": 6.5},
        {"name": "Lateral Raises", "description": "Side delt isolation", "primary_muscle_group": "shoulders", "secondary_muscle_groups": [], "difficulty_level": "beginner", "typical_calories_per_minute": 4.5},
        {"name": "Front Raises", "description": "Front delt isolation", "primary_muscle_group": "shoulders", "secondary_muscle_groups": [], "difficulty_level": "beginner", "typical_calories_per_minute": 4.5},
        {"name": "Face Pulls", "description": "Rear delt and upper back", "primary_muscle_group": "shoulders", "secondary_muscle_groups": ["back"], "difficulty_level": "intermediate", "typical_calories_per_minute": 5.0},
        
        # Arms
        {"name": "Barbell Curl", "description": "Bicep exercise with barbell", "primary_muscle_group": "arms", "secondary_muscle_groups": [], "difficulty_level": "beginner", "typical_calories_per_minute": 4.5},
        {"name": "Dumbbell Curl", "description": "Bicep exercise with dumbbells", "primary_muscle_group": "arms", "secondary_muscle_groups": [], "difficulty_level": "beginner", "typical_calories_per_minute": 4.5},
        {"name": "Tricep Dips", "description": "Bodyweight tricep exercise", "primary_muscle_group": "arms", "secondary_muscle_groups": ["chest", "shoulders"], "difficulty_level": "intermediate", "typical_calories_per_minute": 6.5},
        {"name": "Tricep Pushdown", "description": "Cable tricep exercise", "primary_muscle_group": "arms", "secondary_muscle_groups": [], "difficulty_level": "beginner", "typical_calories_per_minute": 4.5},
        {"name": "Hammer Curl", "description": "Bicep and forearm exercise", "primary_muscle_group": "arms", "secondary_muscle_groups": [], "difficulty_level": "beginner", "typical_calories_per_minute": 4.5},
        
        # Core
        {"name": "Plank", "description": "Isometric core exercise", "primary_muscle_group": "core", "secondary_muscle_groups": [], "difficulty_level": "beginner", "typical_calories_per_minute": 5.0},
        {"name": "Crunches", "description": "Basic ab exercise", "primary_muscle_group": "core", "secondary_muscle_groups": [], "difficulty_level": "beginner", "typical_calories_per_minute": 5.5},
        {"name": "Russian Twists", "description": "Oblique exercise", "primary_muscle_group": "core", "secondary_muscle_groups": [], "difficulty_level": "intermediate", "typical_calories_per_minute": 6.0},
        {"name": "Hanging Leg Raises", "description": "Advanced ab exercise", "primary_muscle_group": "core", "secondary_muscle_groups": [], "difficulty_level": "advanced", "typical_calories_per_minute": 7.0},
        {"name": "Mountain Climbers", "description": "Dynamic core exercise", "primary_muscle_group": "core", "secondary_muscle_groups": ["cardio"], "difficulty_level": "intermediate", "typical_calories_per_minute": 9.0},
        
        # Cardio
        {"name": "Running", "description": "Outdoor or treadmill running", "primary_muscle_group": "cardio", "secondary_muscle_groups": ["legs"], "difficulty_level": "beginner", "typical_calories_per_minute": 11.0},
        {"name": "Cycling", "description": "Stationary or outdoor cycling", "primary_muscle_group": "cardio", "secondary_muscle_groups": ["legs"], "difficulty_level": "beginner", "typical_calories_per_minute": 9.0},
        {"name": "Jump Rope", "description": "Cardio with jump rope", "primary_muscle_group": "cardio", "secondary_muscle_groups": ["legs", "arms"], "difficulty_level": "intermediate", "typical_calories_per_minute": 12.0},
        {"name": "Burpees", "description": "Full body cardio exercise", "primary_muscle_group": "cardio", "secondary_muscle_groups": ["full_body"], "difficulty_level": "intermediate", "typical_calories_per_minute": 10.0},
        {"name": "Rowing Machine", "description": "Full body cardio", "primary_muscle_group": "cardio", "secondary_muscle_groups": ["back", "legs"], "difficulty_level": "beginner", "typical_calories_per_minute": 10.5}
    ]
    
    for ex_data in exercises_data:
        exercise = Exercise(
            exercise_id=str(uuid.uuid4()),
            name=ex_data["name"],
            description=ex_data["description"],
            primary_muscle_group=ex_data["primary_muscle_group"],
            secondary_muscle_groups=",".join(ex_data["secondary_muscle_groups"]),
            difficulty_level=ex_data["difficulty_level"],
            typical_calories_per_minute=ex_data["typical_calories_per_minute"],
            is_custom=False,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.session.add(exercise)
    
    db.session.commit()
    print(f"✓ Seeded {len(exercises_data)} exercises")


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
                    print("🌱 Seeding exercises into database...")
                    _seed_exercises_inline()
                    print("✓ Exercises seeded successfully")
                except Exception as seed_error:
                    print(f"⚠ Could not auto-seed exercises: {seed_error}")
                    import traceback
                    traceback.print_exc()
                    
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

