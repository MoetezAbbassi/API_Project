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


def serialize_exercise(exercise: Exercise, include_user_info=False) -> dict:
    """
    Serialize Exercise object to dictionary
    
    Args:
        exercise: Exercise model instance
        include_user_info: Whether to include user information for custom exercises
        
    Returns:
        Dictionary representation of exercise
    """
    result = {
        "exercise_id": exercise.exercise_id,
        "name": exercise.name,
        "description": exercise.description,
        "primary_muscle_group": exercise.primary_muscle_group,
        "secondary_muscle_groups": exercise.secondary_muscle_groups or [],
        "difficulty_level": exercise.difficulty_level,
        "typical_calories_per_minute": exercise.typical_calories_per_minute,
        "is_custom": exercise.is_custom if hasattr(exercise, 'is_custom') else False,
        "created_at": exercise.created_at.isoformat() if exercise.created_at else None
    }
    
    if include_user_info and exercise.user_id:
        result["user_id"] = exercise.user_id
    
    return result


@bp.route('', methods=['GET'])
def list_exercises():
    """
    List exercises with optional filtering by muscle group and difficulty
    
    Returns system exercises + user's custom exercises if authenticated
    
    Query params:
    - muscle: Filter by muscle group (chest, back, legs, shoulders, arms, core, cardio)
    - muscle_group: Alias for muscle
    - difficulty: Filter by difficulty level (beginner, intermediate, advanced)
    - page: Page number (default 1)
    - per_page: Items per page (default 50)
    """
    try:
        # Get token if available (optional authentication)
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        user_id = None
        if token:
            try:
                from flask_jwt_extended import decode_token
                decoded = decode_token(token)
                user_id = decoded.get('sub')
            except:
                pass  # No valid token, just show system exercises
        
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)
        muscle = request.args.get('muscle', type=str) or request.args.get('muscle_group', type=str)
        difficulty = request.args.get('difficulty', type=str)
        
        # Query system exercises (is_custom = False OR is_custom is NULL for backward compatibility)
        query = db.session.query(Exercise).filter(
            db.or_(
                Exercise.is_custom == False,
                Exercise.is_custom == None
            )
        )
        
        # Add user's custom exercises if authenticated
        if user_id:
            custom_query = db.session.query(Exercise).filter(
                Exercise.is_custom == True,
                Exercise.user_id == user_id
            )
            
            # Apply filters to custom query
            if muscle:
                is_valid, _ = validators.validate_enum(muscle, MUSCLE_GROUPS)
                if is_valid:
                    custom_query = custom_query.filter_by(primary_muscle_group=muscle)
            
            if difficulty:
                is_valid, _ = validators.validate_enum(difficulty, DIFFICULTY_LEVELS)
                if is_valid:
                    custom_query = custom_query.filter_by(difficulty_level=difficulty)
            
            # Combine queries
            if muscle or difficulty:
                # Apply same filters to system query
                if muscle:
                    is_valid, _ = validators.validate_enum(muscle, MUSCLE_GROUPS)
                    if is_valid:
                        query = query.filter_by(primary_muscle_group=muscle)
                
                if difficulty:
                    is_valid, _ = validators.validate_enum(difficulty, DIFFICULTY_LEVELS)
                    if is_valid:
                        query = query.filter_by(difficulty_level=difficulty)
            
            query = query.union(custom_query)
        else:
            # Filter system exercises only
            if muscle:
                is_valid, _ = validators.validate_enum(muscle, MUSCLE_GROUPS)
                if is_valid:
                    query = query.filter_by(primary_muscle_group=muscle)
            
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
        import traceback
        traceback.print_exc()
        return responses.error_response(
            "Database error",
            str(e),
            "EXERCISE_LIST_ERROR",
            500
        )


@bp.route('/muscle-groups', methods=['GET'])
def get_muscle_groups():
    """
    Get list of available muscle groups
    """
    try:
        return responses.success_response(
            {"muscle_groups": list(MUSCLE_GROUPS)},
            "Muscle groups retrieved successfully"
        )
    except Exception as e:
        return responses.error_response(
            "Error",
            str(e),
            "MUSCLE_GROUPS_ERROR",
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
        # Validate UUID format
        import uuid
        try:
            uuid.UUID(exercise_id)
        except ValueError:
            return responses.validation_error_response("Invalid exercise ID format")
        
        exercise = db.session.query(Exercise).filter_by(exercise_id=exercise_id).first()
        if not exercise:
            return responses.not_found_response("Exercise not found")
        
        return responses.success_response(
            serialize_exercise(exercise),
            "Exercise retrieved successfully"
        )
    
    except Exception as e:
        import traceback
        traceback.print_exc()
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
        "typical_calories_per_minute": 7.5  // Optional - will be estimated if not provided
    }
    """
    try:
        from app.utils.calorie_calculator import estimate_calories_per_minute
        
        data = request.get_json()
        
        # Validate required fields
        is_valid, error_msg = validators.validate_required_fields(
            data, ['name', 'description', 'primary_muscle_group', 'difficulty_level']
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
        
        # Get or estimate calories per minute
        if 'typical_calories_per_minute' in data and data['typical_calories_per_minute']:
            # Validate if provided
            is_valid, error_msg = validators.validate_positive_number(data['typical_calories_per_minute'], 'typical_calories_per_minute')
            if not is_valid:
                return responses.validation_error_response(error_msg)
            calories_per_min = float(data['typical_calories_per_minute'])
        else:
            # Estimate based on difficulty, type (inferred from muscle group), and muscle group
            exercise_type = 'strength'  # Default - could be inferred from muscle group
            if data['primary_muscle_group'] == 'cardio':
                exercise_type = 'cardio'
            
            calories_per_min = estimate_calories_per_minute(
                exercise_type,
                data['difficulty_level'],
                data['primary_muscle_group']
            )
        
        # Check for duplicate exercise name (only for user's own custom exercises and system exercises)
        existing = db.session.query(Exercise).filter(
            Exercise.name == data['name'],
            db.or_(
                Exercise.is_custom == False,
                db.and_(Exercise.is_custom == True, Exercise.user_id == token_user_id)
            )
        ).first()
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
            typical_calories_per_minute=calories_per_min,
            is_custom=True,  # User-created exercise
            user_id=token_user_id  # Associate with user
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


@bp.route('/<exercise_id>', methods=['DELETE'])
@decorators.token_required
def delete_exercise(token_user_id, exercise_id):
    """
    Delete an exercise by ID
    
    Path params:
    - exercise_id: Exercise ID (UUID)
    
    Response (204): Exercise deleted successfully
    Response (404): Exercise not found
    Response (409): Cannot delete - used in workouts
    """
    try:
        from app.models import WorkoutExercise
        
        # Find the exercise
        exercise = db.session.query(Exercise).filter_by(exercise_id=exercise_id).first()
        if not exercise:
            return responses.not_found_response("Exercise not found")
        
        # Check if exercise is used in any workouts
        workout_count = db.session.query(WorkoutExercise).filter_by(
            exercise_id=exercise_id
        ).count()
        
        if workout_count > 0:
            return responses.conflict_response(
                f"Cannot delete - used in {workout_count} workout(s). Delete workout records first."
            )
        
        # Delete the exercise
        db.session.delete(exercise)
        db.session.commit()
        
        return responses.success_response(
            {"exercise_id": exercise_id},
            "Exercise deleted successfully",
            204
        )
    
    except Exception as e:
        db.session.rollback()
        return responses.error_response(
            "Database error",
            str(e),
            "EXERCISE_DELETE_ERROR",
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
