"""
Workouts Routes - Manage user workouts and exercises
Endpoints: 10 (POST, GET list, GET detail, POST exercise, PUT exercise, PUT complete, DELETE, DELETE exercise, GET recent, GET by-date)
"""
from flask import Blueprint, request
from datetime import datetime, timedelta
from sqlalchemy import func
from app.extensions import db

from app.models import Workout, WorkoutExercise, Exercise, User
from app.utils import validators, responses, decorators
from app.utils.constants import WORKOUT_TYPES, WORKOUT_STATUSES

bp = Blueprint('workouts', __name__, url_prefix='/api/workouts')




def serialize_workout_exercise(workout_exercise: WorkoutExercise, exercise: Exercise = None) -> dict:
    """
    Serialize WorkoutExercise with exercise details
    
    Args:
        workout_exercise: WorkoutExercise model instance
        exercise: Exercise model instance (if not set, will query)
        
    Returns:
        Dictionary representation of workout exercise
    """
    if not exercise:
        exercise = db.session.query(Exercise).filter_by(exercise_id=workout_exercise.exercise_id).first()
    
    return {
        "workout_exercise_id": workout_exercise.workout_exercise_id,
        "exercise_id": workout_exercise.exercise_id,
        "exercise_name": exercise.name if exercise else "Unknown",
        "sets": workout_exercise.sets,
        "reps": workout_exercise.reps,
        "weight_used": workout_exercise.weight_used,
        "weight_unit": workout_exercise.weight_unit,
        "duration_seconds": workout_exercise.duration_seconds,
        "calories_burned": workout_exercise.calories_burned,
        "order_in_workout": workout_exercise.order_in_workout,
        "created_at": workout_exercise.created_at.isoformat() if workout_exercise.created_at else None
    }


def serialize_workout(workout: Workout, include_exercises: bool = False) -> dict:
    """
    Serialize Workout object to dictionary
    
    Args:
        workout: Workout model instance
        include_exercises: Include WorkoutExercise array
        
    Returns:
        Dictionary representation of workout
    """
    workout_dict = {
        "workout_id": workout.workout_id,
        "user_id": workout.user_id,
        "workout_date": workout.workout_date.isoformat() if workout.workout_date else None,
        "workout_type": workout.workout_type,
        "status": workout.status,
        "total_duration_minutes": workout.total_duration_minutes,
        "total_calories_burned": workout.total_calories_burned,
        "notes": workout.notes,
        "created_at": workout.created_at.isoformat() if workout.created_at else None,
        "completed_at": workout.completed_at.isoformat() if workout.completed_at else None
    }
    
    if include_exercises:
        workout_exercises = Workoutdb.session.query(Exercise).filter_by(workout_id=workout.workout_id).order_by(
            WorkoutExercise.order_in_workout
        ).all()
        
        exercises = []
        muscle_groups = set()
        for we in workout_exercises:
            exercise = db.session.query(Exercise).filter_by(exercise_id=we.exercise_id).first()
            exercises.append(serialize_workout_exercise(we, exercise))
            if exercise:
                muscle_groups.add(exercise.primary_muscle_group)
        
        workout_dict["exercises"] = exercises
        workout_dict["muscle_groups_worked"] = list(muscle_groups)
    
    return workout_dict


@bp.route('', methods=['POST'])
@decorators.validate_json
@decorators.token_required
def create_workout(token_user_id):
    """
    Create a new workout
    
    Request body:
    {
        "workout_type": "strength|cardio|flexibility|mixed",
        "notes": "Upper body day"
    }
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        is_valid, error_msg = validators.validate_required_fields(data, ['workout_type'])
        if not is_valid:
            return responses.validation_error_response(error_msg)
        
        # Validate workout type
        is_valid, error_msg = validators.validate_enum(data['workout_type'], WORKOUT_TYPES)
        if not is_valid:
            return responses.validation_error_response(f"Invalid workout_type. Must be one of: {', '.join(WORKOUT_TYPES)}")
        
        # Create workout
        import uuid
        workout = Workout(
            workout_id=str(uuid.uuid4()),
            user_id=token_user_id,
            workout_date=datetime.now().date(),
            workout_type=data['workout_type'],
            status='in_progress',
            total_duration_minutes=0,
            total_calories_burned=0.0,
            notes=data.get('notes', '')
        )
        
        db.session.add(workout)
        db.session.commit()
        
        return responses.created_response(
            serialize_workout(workout, include_exercises=True),
            "Workout created successfully"
        )
    
    except Exception as e:
        db.session.rollback()
        return responses.error_response(
            "Database error",
            str(e),
            "WORKOUT_CREATE_ERROR",
            500
        )


@bp.route('/<user_id>', methods=['GET'])
@decorators.token_required
def list_workouts(token_user_id, user_id):
    """
    List user's workouts with optional date range filtering
    
    Query params:
    - start_date: Filter workouts from date (YYYY-MM-DD)
    - end_date: Filter workouts to date (YYYY-MM-DD)
    - page: Page number (default 1)
    - per_page: Items per page (default 10)
    """
    try:
        # Verify user exists
        user = db.session.query(User).filter_by(user_id=user_id).first()
        if not user:
            return responses.not_found_response("User not found")
        
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        start_date = request.args.get('start_date', type=str)
        end_date = request.args.get('end_date', type=str)
        
        query = db.session.query(Workout).filter_by(user_id=user_id)
        
        # Filter by date range if provided
        if start_date:
            is_valid, error_msg = validators.validate_date(start_date)
            if is_valid:
                start = datetime.strptime(start_date, '%Y-%m-%d').date()
                query = query.filter(Workout.workout_date >= start)
        
        if end_date:
            is_valid, error_msg = validators.validate_date(end_date)
            if is_valid:
                end = datetime.strptime(end_date, '%Y-%m-%d').date()
                query = query.filter(Workout.workout_date <= end)
        
        # Order by date descending
        query = query.order_by(Workout.workout_date.desc())
        
        # Paginate
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        workouts = [serialize_workout(w) for w in pagination.items]
        
        return responses.paginated_response(
            workouts,
            pagination.total,
            page,
            per_page,
            "Workouts retrieved successfully"
        )
    
    except Exception as e:
        return responses.error_response(
            "Database error",
            str(e),
            "WORKOUT_LIST_ERROR",
            500
        )


@bp.route('/<workout_id>', methods=['GET'])
def get_workout(workout_id):
    """
    Get workout detail with all exercises and muscle groups worked
    
    Path params:
    - workout_id: Workout ID (UUID)
    """
    try:
        workout = db.session.query(Workout).filter_by(workout_id=workout_id).first()
        if not workout:
            return responses.not_found_response("Workout not found")
        
        return responses.success_response(
            serialize_workout(workout, include_exercises=True),
            "Workout retrieved successfully"
        )
    
    except Exception as e:
        return responses.error_response(
            "Database error",
            str(e),
            "WORKOUT_GET_ERROR",
            500
        )


@bp.route('/<workout_id>/exercises', methods=['POST'])
@decorators.validate_json
@decorators.token_required
def add_exercise_to_workout(token_user_id, workout_id):
    """
    Add exercise to workout
    
    Request body:
    {
        "exercise_id": "uuid",
        "sets": 3,
        "reps": 10,
        "weight_used": 185,
        "weight_unit": "lbs"
    }
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        is_valid, error_msg = validators.validate_required_fields(
            data, ['exercise_id', 'sets', 'reps', 'weight_used', 'weight_unit']
        )
        if not is_valid:
            return responses.validation_error_response(error_msg)
        
        # Verify workout exists
        workout = db.session.query(Workout).filter_by(workout_id=workout_id).first()
        if not workout:
            return responses.not_found_response("Workout not found")
        
        # Security: verify user owns workout
        if workout.user_id != token_user_id:
            return responses.forbidden_response("You can only add exercises to your own workouts")
        
        # Verify exercise exists
        exercise = db.session.query(Exercise).filter_by(exercise_id=data['exercise_id']).first()
        if not exercise:
            return responses.not_found_response("Exercise not found")
        
        # Validate sets, reps
        is_valid, error_msg = validators.validate_positive_number(data['sets'], 'sets')
        if not is_valid:
            return responses.validation_error_response(error_msg)
        
        is_valid, error_msg = validators.validate_positive_number(data['reps'], 'reps')
        if not is_valid:
            return responses.validation_error_response(error_msg)
        
        is_valid, error_msg = validators.validate_positive_number(data['weight_used'], 'weight_used')
        if not is_valid:
            return responses.validation_error_response(error_msg)
        
        # Get next order
        last_order = db.session.query(func.max(WorkoutExercise.order_in_workout)).filter_by(
            workout_id=workout_id
        ).scalar() or 0
        
        # Calculate calories burned
        # Formula: calories = sets * reps * exercise.typical_calories_per_minute / 10
        calories_burned = (int(data['sets']) * int(data['reps']) * exercise.typical_calories_per_minute) / 10
        
        # Create workout exercise
        import uuid
        workout_exercise = WorkoutExercise(
            workout_exercise_id=str(uuid.uuid4()),
            workout_id=workout_id,
            exercise_id=data['exercise_id'],
            sets=int(data['sets']),
            reps=int(data['reps']),
            weight_used=float(data['weight_used']),
            weight_unit=data['weight_unit'],
            duration_seconds=0,
            calories_burned=round(calories_burned, 2),
            order_in_workout=last_order + 1
        )
        
        db.session.add(workout_exercise)
        db.session.commit()
        
        return responses.created_response(
            serialize_workout_exercise(workout_exercise, exercise),
            "Exercise added to workout successfully"
        )
    
    except Exception as e:
        db.session.rollback()
        return responses.error_response(
            "Database error",
            str(e),
            "WORKOUT_ADD_EXERCISE_ERROR",
            500
        )


@bp.route('/<workout_id>/exercises/<exercise_id>', methods=['PUT'])
@decorators.validate_json
@decorators.token_required
def update_workout_exercise(token_user_id, workout_id, exercise_id):
    """
    Update exercise in workout with recalculated calories
    
    Request body (at least one required):
    {
        "sets": 4,
        "reps": 12,
        "weight_used": 195
    }
    """
    try:
        data = request.get_json()
        
        # Verify workout exists
        workout = db.session.query(Workout).filter_by(workout_id=workout_id).first()
        if not workout:
            return responses.not_found_response("Workout not found")
        
        # Security: verify user owns workout
        if workout.user_id != token_user_id:
            return responses.forbidden_response("You can only update exercises in your own workouts")
        
        # Verify workout exercise exists
        workout_exercise = Workoutdb.session.query(Exercise).filter_by(
            workout_id=workout_id,
            exercise_id=exercise_id
        ).first()
        if not workout_exercise:
            return responses.not_found_response("Exercise not found in this workout")
        
        # Get exercise
        exercise = db.session.query(Exercise).filter_by(exercise_id=exercise_id).first()
        if not exercise:
            return responses.not_found_response("Exercise not found")
        
        # Update fields
        if 'sets' in data:
            is_valid, error_msg = validators.validate_positive_number(data['sets'], 'sets')
            if not is_valid:
                return responses.validation_error_response(error_msg)
            workout_exercise.sets = int(data['sets'])
        
        if 'reps' in data:
            is_valid, error_msg = validators.validate_positive_number(data['reps'], 'reps')
            if not is_valid:
                return responses.validation_error_response(error_msg)
            workout_exercise.reps = int(data['reps'])
        
        if 'weight_used' in data:
            is_valid, error_msg = validators.validate_positive_number(data['weight_used'], 'weight_used')
            if not is_valid:
                return responses.validation_error_response(error_msg)
            workout_exercise.weight_used = float(data['weight_used'])
        
        # Recalculate calories
        calories_burned = (workout_exercise.sets * workout_exercise.reps * exercise.typical_calories_per_minute) / 10
        workout_exercise.calories_burned = round(calories_burned, 2)
        
        db.session.commit()
        
        return responses.success_response(
            serialize_workout_exercise(workout_exercise, exercise),
            "Exercise updated successfully"
        )
    
    except Exception as e:
        db.session.rollback()
        return responses.error_response(
            "Database error",
            str(e),
            "WORKOUT_UPDATE_EXERCISE_ERROR",
            500
        )


@bp.route('/<workout_id>', methods=['PUT'])
@decorators.validate_json
@decorators.token_required
def update_workout(token_user_id, workout_id):
    """
    Update workout status and notes
    
    Request body:
    {
        "status": "in_progress|completed|cancelled",
        "notes": "Updated notes"
    }
    """
    try:
        data = request.get_json()
        
        # Verify workout exists
        workout = db.session.query(Workout).filter_by(workout_id=workout_id).first()
        if not workout:
            return responses.not_found_response("Workout not found")
        
        # Security: verify user owns workout
        if workout.user_id != token_user_id:
            return responses.forbidden_response("You can only update your own workouts")
        
        # Update status if provided
        if 'status' in data:
            is_valid, error_msg = validators.validate_enum(data['status'], WORKOUT_STATUSES)
            if not is_valid:
                return responses.validation_error_response(f"Invalid status. Must be one of: {', '.join(WORKOUT_STATUSES)}")
            
            workout.status = data['status']
            
            # If completing, set timestamp and calculate totals
            if data['status'] == 'completed':
                workout.completed_at = datetime.utcnow()
                
                # Calculate total duration and calories
                workout_exercises = Workoutdb.session.query(Exercise).filter_by(workout_id=workout_id).all()
                total_calories = sum(we.calories_burned for we in workout_exercises)
                workout.total_calories_burned = round(total_calories, 2)
                
                # Estimate duration (assume ~2 minutes per exercise on average)
                workout.total_duration_minutes = len(workout_exercises) * 2
        
        # Update notes if provided
        if 'notes' in data:
            workout.notes = data['notes']
        
        db.session.commit()
        
        return responses.success_response(
            serialize_workout(workout, include_exercises=True),
            "Workout updated successfully"
        )
    
    except Exception as e:
        db.session.rollback()
        return responses.error_response(
            "Database error",
            str(e),
            "WORKOUT_UPDATE_ERROR",
            500
        )


@bp.route('/<workout_id>', methods=['DELETE'])
@decorators.token_required
def delete_workout(token_user_id, workout_id):
    """
    Delete workout and all associated exercises
    
    Path params:
    - workout_id: Workout ID (UUID)
    """
    try:
        # Verify workout exists
        workout = db.session.query(Workout).filter_by(workout_id=workout_id).first()
        if not workout:
            return responses.not_found_response("Workout not found")
        
        # Security: verify user owns workout
        if workout.user_id != token_user_id:
            return responses.forbidden_response("You can only delete your own workouts")
        
        # Delete associated workout exercises
        Workoutdb.session.query(Exercise).filter_by(workout_id=workout_id).delete()
        
        # Delete workout
        db.session.delete(workout)
        db.session.commit()
        
        return responses.deleted_response("Workout deleted successfully")
    
    except Exception as e:
        db.session.rollback()
        return responses.error_response(
            "Database error",
            str(e),
            "WORKOUT_DELETE_ERROR",
            500
        )


@bp.route('/<workout_id>/exercises/<exercise_id>', methods=['DELETE'])
@decorators.token_required
def remove_exercise_from_workout(token_user_id, workout_id, exercise_id):
    """
    Remove exercise from workout
    
    Path params:
    - workout_id: Workout ID (UUID)
    - exercise_id: Exercise ID (UUID)
    """
    try:
        # Verify workout exists
        workout = db.session.query(Workout).filter_by(workout_id=workout_id).first()
        if not workout:
            return responses.not_found_response("Workout not found")
        
        # Security: verify user owns workout
        if workout.user_id != token_user_id:
            return responses.forbidden_response("You can only modify your own workouts")
        
        # Verify workout exercise exists
        workout_exercise = Workoutdb.session.query(Exercise).filter_by(
            workout_id=workout_id,
            exercise_id=exercise_id
        ).first()
        if not workout_exercise:
            return responses.not_found_response("Exercise not found in this workout")
        
        db.session.delete(workout_exercise)
        db.session.commit()
        
        return responses.deleted_response("Exercise removed from workout successfully")
    
    except Exception as e:
        db.session.rollback()
        return responses.error_response(
            "Database error",
            str(e),
            "WORKOUT_REMOVE_EXERCISE_ERROR",
            500
        )


@bp.route('/<user_id>/recent', methods=['GET'])
@decorators.token_required
def get_recent_workouts(token_user_id, user_id):
    """
    Get recent workouts for user
    
    Query params:
    - limit: Number of recent workouts (default 5)
    """
    try:
        # Verify user exists
        user = db.session.query(User).filter_by(user_id=user_id).first()
        if not user:
            return responses.not_found_response("User not found")
        
        limit = request.args.get('limit', 5, type=int)
        
        workouts = db.session.query(Workout).filter_by(user_id=user_id).order_by(
            Workout.workout_date.desc()
        ).limit(limit).all()
        
        return responses.success_response(
            [serialize_workout(w) for w in workouts],
            "Recent workouts retrieved successfully"
        )
    
    except Exception as e:
        return responses.error_response(
            "Database error",
            str(e),
            "WORKOUT_RECENT_ERROR",
            500
        )


@bp.route('/<user_id>/by-date/<date>', methods=['GET'])
@decorators.token_required
def get_workouts_by_date(token_user_id, user_id, date):
    """
    Get workouts for specific date
    
    Path params:
    - user_id: User ID (UUID)
    - date: Date (YYYY-MM-DD format)
    """
    try:
        # Verify user exists
        user = db.session.query(User).filter_by(user_id=user_id).first()
        if not user:
            return responses.not_found_response("User not found")
        
        # Validate date format
        is_valid, error_msg = validators.validate_date(date)
        if not is_valid:
            return responses.validation_error_response(error_msg)
        
        # Parse date
        workout_date = datetime.strptime(date, '%Y-%m-%d').date()
        
        # Query workouts
        workouts = db.session.query(Workout).filter_by(
            user_id=user_id,
            workout_date=workout_date
        ).all()
        
        return responses.success_response(
            [serialize_workout(w, include_exercises=True) for w in workouts],
            "Workouts for date retrieved successfully"
        )
    
    except Exception as e:
        return responses.error_response(
            "Database error",
            str(e),
            "WORKOUT_BY_DATE_ERROR",
            500
        )
