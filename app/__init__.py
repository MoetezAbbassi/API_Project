from flask_cors import CORS
import logging
import os
from datetime import timedelta

# Import extensions from separate module to avoid circular imports
from app.extensions import db, jwt


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_app():
    """Application factory function"""
    from flask import Flask
    
    app = Flask(__name__)
    
    # Configure Flask
    app.config['FLASK_ENV'] = os.getenv('FLASK_ENV', 'development')
    
    # Configure SQLAlchemy
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///fitness_app.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'connect_args': {'check_same_thread': False} if 'sqlite' in app.config['SQLALCHEMY_DATABASE_URI'] else {}
    }
    
    # Configure JWT
    app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'change-me-in-production')
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)
    
    # Initialize extensions with app
    db.init_app(app)
    jwt.init_app(app)
    CORS(app, resources={r"/api/*": {"origins": "*", "allow_headers": ["Content-Type", "Authorization"], "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"]}})
    
    # Create uploads directory
    uploads_dir = os.path.join(os.getcwd(), 'uploads', 'images')
    os.makedirs(uploads_dir, exist_ok=True)
    
    # Register blueprints and create tables
    with app.app_context():
    # Import all models explicitly to register them with SQLAlchemy
        from app.models import (
        User, Goal, Exercise, Workout, WorkoutExercise,
        Meal, MealItem, FitnessProgram, ProgramWorkout,
        CalendarEvent, MLPrediction
    )
    
    # Don't create tables - database already exists
        logger.info("✅ Database connected successfully")
        
        # Import and register blueprints
        from app.routes import auth, users, goals, exercises, workouts, meals, calendar, programs, dashboard, ml, nutrition
        
        app.register_blueprint(auth.bp)
        app.register_blueprint(users.bp)
        app.register_blueprint(goals.bp)
        app.register_blueprint(exercises.bp)
        app.register_blueprint(workouts.bp)
        app.register_blueprint(meals.bp)
        app.register_blueprint(calendar.bp)
        app.register_blueprint(programs.bp)
        app.register_blueprint(dashboard.bp)
        app.register_blueprint(ml.bp)
        app.register_blueprint(nutrition.bp)
        
        logger.info("✅ All blueprints registered successfully")
        
        # Welcome endpoint at root
        @app.route('/', methods=['GET'])
        def welcome():
            return {
                'message': 'Fitness Trainer API',
                'version': '1.0.0',
                'status': 'running',
                'health_endpoint': '/api/health',
                'register_endpoint': 'POST /api/auth/register'
            }, 200
        
        # Health check endpoint
        @app.route('/api/health', methods=['GET'])
        def health_check():
            return {
                'service': 'Fitness API',
                'status': 'healthy',
                'version': '1.0.0'
            }, 200
        
        # Error handlers
        @app.errorhandler(404)
        def not_found(error):
            from app.utils.responses import error_response
            return error_response('NOT_FOUND', 'Resource not found', 'NOT_FOUND', 404)
        
        @app.errorhandler(500)
        def internal_error(error):
            from app.utils.responses import error_response
            logger.error(f"Internal server error: {str(error)}")
            return error_response('INTERNAL_ERROR', 'Internal server error', 'INTERNAL_ERROR', 500)
    
    return app
