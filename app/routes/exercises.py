"""
Exercises Routes - Manage exercise reference data
Endpoints: 5 (GET list, GET detail, GET by-muscle, POST create, GET by-difficulty)
No authentication required for GET endpoints (public reference data)
"""
from flask import Blueprint, request
from datetime import datetime
from sqlalchemy import func
from app.extensions import db

from app.models import Exercise
from app.utils import validators, responses, decorators
from app.utils.constants import MUSCLE_GROUPS, DIFFICULTY_LEVELS

bp = Blueprint('exercises', __name__, url_prefix='/api/exercises')


def serialize_exercise(exercise: Exercise) -> dict:
    """
    Serialize Exercise object to dictionary
    
    Args:
        exercise: Exercise model instance
        
    Returns:
        Dictionary representation of exercise
    """
    return {
        "exercise_id": exercise.exercise_id,
        "name": exercise.name,
        "description": exercise.description,
        "primary_muscle_group": exercise.primary_muscle_group,
        "secondary_muscle_groups": exercise.secondary_muscle_groups or [],
        "difficulty_level": exercise.difficulty_level,
        "typical_calories_per_minute": exercise.typical_calories_per_minute,
        "created_at": exercise.created_at.isoformat() if exercise.created_at else None
    }


@bp.route('', methods=['GET'])
def list_exercises():
    """
    List exercises with optional filtering by muscle group and difficulty
    
    Query params:
    - muscle: Filter by muscle group (chest, back, legs, shoulders, arms, core, cardio)
    - difficulty: Filter by difficulty level (beginner, intermediate, advanced)
    - page: Page number (default 1)
    - per_page: Items per page (default 10)
    """
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        muscle = request.args.get('muscle', type=str)
        difficulty = request.args.get('difficulty', type=str)
        
        query = db.session.query(Exercise)
        
        # Filter by muscle group if provided
        if muscle:
            is_valid, _ = validators.validate_enum(muscle, MUSCLE_GROUPS)
            if is_valid:
                query = query.filter_by(primary_muscle_group=muscle)
        
        # Filter by difficulty if provided
        if difficulty:
            is_valid, _ = validators.validate_enum(difficulty, DIFFICULTY_LEVELS)
            if is_valid:
                query = query.filter_by(difficulty_level=difficulty)
        
        # Paginate
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        exercises = [serialize_exercise(ex) for ex in pagination.items]
        
        return responses.paginated_response(
            exercises,
            pagination.total,
            page,
            per_page,
            "Exercises retrieved successfully"
        )
    
    except Exception as e:
        return responses.error_response(
            "Database error",
            str(e),
            "EXERCISE_LIST_ERROR",
            500
        )


@bp.route('/<exercise_id>', methods=['GET'])
def get_exercise(exercise_id):
    """
    Get single exercise detail
    
    Path params:
    - exercise_id: Exercise ID (UUID)
    """
    try:
        exercise = db.session.query(Exercise).filter_by(exercise_id=exercise_id).first()
        if not exercise:
            return responses.not_found_response("Exercise not found")
        
        return responses.success_response(
            serialize_exercise(exercise),
            "Exercise retrieved successfully"
        )
    
    except Exception as e:
        return responses.error_response(
            "Database error",
            str(e),
            "EXERCISE_GET_ERROR",
            500
        )


@bp.route('/muscle/<muscle_group>', methods=['GET'])
def get_exercises_by_muscle(muscle_group):
    """
    List exercises filtered by muscle group
    
    Path params:
    - muscle_group: Muscle group name (chest, back, legs, shoulders, arms, core, cardio)
    
    Query params:
    - page: Page number (default 1)
    - per_page: Items per page (default 15)
    """
    try:
        # Validate muscle group
        is_valid, error_msg = validators.validate_enum(muscle_group, MUSCLE_GROUPS)
        if not is_valid:
            return responses.validation_error_response(
                f"Invalid muscle group. Must be one of: {', '.join(MUSCLE_GROUPS)}"
            )
        
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 15, type=int)
        
        pagination = db.session.query(Exercise).filter_by(
            primary_muscle_group=muscle_group
        ).paginate(page=page, per_page=per_page, error_out=False)
        
        exercises = [serialize_exercise(ex) for ex in pagination.items]
        
        return responses.paginated_response(
            exercises,
            pagination.total,
            page,
            per_page,
            f"Exercises for {muscle_group} retrieved successfully"
        )
    
    except Exception as e:
        return responses.error_response(
            "Database error",
            str(e),
            "EXERCISE_BY_MUSCLE_ERROR",
            500
        )


@bp.route('', methods=['POST'])
@decorators.validate_json
@decorators.token_required
def create_exercise(token_user_id):
    """
    Create a new exercise (admin use)
    
    Request body:
    {
        "name": "Barbell Bench Press",
        "description": "Classic chest exercise",
        "primary_muscle_group": "chest",
        "secondary_muscle_groups": ["shoulders", "triceps"],
        "difficulty_level": "intermediate",
        "typical_calories_per_minute": 7.5
    }
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        is_valid, error_msg = validators.validate_required_fields(
            data, ['name', 'description', 'primary_muscle_group', 'difficulty_level', 'typical_calories_per_minute']
        )
        if not is_valid:
            return responses.validation_error_response(error_msg)
        
        # Validate primary muscle group
        is_valid, error_msg = validators.validate_enum(data['primary_muscle_group'], MUSCLE_GROUPS)
        if not is_valid:
            return responses.validation_error_response(f"Invalid primary_muscle_group. Must be one of: {', '.join(MUSCLE_GROUPS)}")
        
        # Validate difficulty level
        is_valid, error_msg = validators.validate_enum(data['difficulty_level'], DIFFICULTY_LEVELS)
        if not is_valid:
            return responses.validation_error_response(f"Invalid difficulty_level. Must be one of: {', '.join(DIFFICULTY_LEVELS)}")
        
        # Validate calories per minute
        is_valid, error_msg = validators.validate_positive_number(data['typical_calories_per_minute'], 'typical_calories_per_minute')
        if not is_valid:
            return responses.validation_error_response(error_msg)
        
        # Check for duplicate exercise name
        existing = db.session.query(Exercise).filter_by(name=data['name']).first()
        if existing:
            return responses.conflict_response("Exercise with this name already exists")
        
        # Create exercise
        import uuid
        import json
        secondary_muscles = data.get('secondary_muscle_groups', [])
        
        exercise = Exercise(
            exercise_id=str(uuid.uuid4()),
            name=data['name'],
            description=data['description'],
            primary_muscle_group=data['primary_muscle_group'],
            secondary_muscle_groups=json.dumps(secondary_muscles),
            difficulty_level=data['difficulty_level'],
            typical_calories_per_minute=float(data['typical_calories_per_minute'])
        )
        
        db.session.add(exercise)
        db.session.commit()
        
        return responses.created_response(
            serialize_exercise(exercise),
            "Exercise created successfully"
        )
    
    except Exception as e:
        db.session.rollback()
        return responses.error_response(
            "Database error",
            str(e),
            "EXERCISE_CREATE_ERROR",
            500
        )


@bp.route('/difficulty/<difficulty_level>', methods=['GET'])
def get_exercises_by_difficulty(difficulty_level):
    """
    List exercises filtered by difficulty level
    
    Path params:
    - difficulty_level: Difficulty level (beginner, intermediate, advanced)
    
    Query params:
    - page: Page number (default 1)
    - per_page: Items per page (default 10)
    """
    try:
        # Validate difficulty level
        is_valid, error_msg = validators.validate_enum(difficulty_level, DIFFICULTY_LEVELS)
        if not is_valid:
            return responses.validation_error_response(
                f"Invalid difficulty level. Must be one of: {', '.join(DIFFICULTY_LEVELS)}"
            )
        
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        pagination = db.session.query(Exercise).filter_by(
            difficulty_level=difficulty_level
        ).paginate(page=page, per_page=per_page, error_out=False)
        
        exercises = [serialize_exercise(ex) for ex in pagination.items]
        
        return responses.paginated_response(
            exercises,
            pagination.total,
            page,
            per_page,
            f"Exercises with {difficulty_level} difficulty retrieved successfully"
        )
    
    except Exception as e:
        return responses.error_response(
            "Database error",
            str(e),
            "EXERCISE_BY_DIFFICULTY_ERROR",
            500
        )
