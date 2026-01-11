"""
Programs Routes - Manage fitness training programs
Endpoints: 3 (POST create, GET list, GET detail)
"""
from flask import Blueprint, request
from datetime import datetime
from app.extensions import db

from app.models import FitnessProgram, ProgramWorkout, Exercise, Goal, User
from app.utils import validators, responses, decorators
from app.utils.constants import DIFFICULTY_LEVELS, MUSCLE_GROUPS

bp = Blueprint('programs', __name__, url_prefix='/api/programs')


def serialize_program_workout(program_workout: ProgramWorkout, exercises: list = None) -> dict:
    """
    Serialize ProgramWorkout to dictionary
    
    Args:
        program_workout: ProgramWorkout model instance
        exercises: Optional pre-loaded exercises
        
    Returns:
        Dictionary representation of program workout
    """
    return {
        "program_workout_id": program_workout.program_workout_id,
        "day_of_week": program_workout.day_of_week,
        "rest_day": program_workout.rest_day,
        "suggested_exercises": program_workout.suggested_exercises or [],
        "created_at": program_workout.created_at.isoformat() if program_workout.created_at else None
    }


def serialize_program(program: FitnessProgram, include_workouts: bool = False) -> dict:
    """
    Serialize FitnessProgram to dictionary
    
    Args:
        program: FitnessProgram model instance
        include_workouts: Include weekly workouts
        
    Returns:
        Dictionary representation of program
    """
    program_dict = {
        "program_id": program.program_id,
        "user_id": program.user_id,
        "goal_id": program.goal_id,
        "program_name": program.program_name,
        "duration_weeks": program.duration_weeks,
        "focus_muscle_groups": program.focus_muscle_groups or [],
        "difficulty_level": program.difficulty_level,
        "created_at": program.created_at.isoformat() if program.created_at else None
    }
    
    if include_workouts:
        program_workouts = db.session.query(ProgramWorkout).filter_by(program_id=program.program_id).order_by(
            ProgramWorkout.day_of_week
        ).all()
        program_dict["weekly_workouts"] = [serialize_program_workout(pw) for pw in program_workouts]
    
    return program_dict


def generate_weekly_schedule(focus_muscles: list, difficulty: str, program_id: str):
    """
    Generate weekly workout schedule with rest days
    
    Args:
        focus_muscles: List of muscle groups to focus on
        difficulty: Difficulty level
        program_id: Program ID for association
    """
    import uuid
    import json
    
    # Pattern: Rest on days 0, 3, 6 (Sunday, Wednesday, Saturday)
    rest_days = [0, 3, 6]
    
    program_workouts = []
    for day in range(7):
        is_rest = day in rest_days
        
        # Get suggested exercises for focus muscles and difficulty
        suggested_exercises = []
        if not is_rest:
            exercises = db.session.query(Exercise).filter(
                Exercise.primary_muscle_group.in_(focus_muscles),
                Exercise.difficulty_level == difficulty
            ).limit(5).all()
            suggested_exercises = [ex.exercise_id for ex in exercises]
        
        pw = ProgramWorkout(
            program_workout_id=str(uuid.uuid4()),
            program_id=program_id,
            day_of_week=day,
            rest_day=is_rest,
            suggested_exercises=json.dumps(suggested_exercises)
        )
        program_workouts.append(pw)
    
    return program_workouts


@bp.route('', methods=['POST'])
@decorators.validate_json
@decorators.token_required
def create_program(token_user_id):
    """
    Create fitness program with weekly schedule
    
    Request body:
    {
        "program_name": "Summer Strength",
        "goal_id": "uuid_or_null",
        "duration_weeks": 12,
        "focus_muscle_groups": ["chest", "legs"],
        "difficulty_level": "beginner|intermediate|advanced"
    }
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        is_valid, error_msg = validators.validate_required_fields(
            data, ['program_name', 'duration_weeks', 'focus_muscle_groups', 'difficulty_level']
        )
        if not is_valid:
            return responses.validation_error_response(error_msg)
        
        # Validate duration
        is_valid, error_msg = validators.validate_positive_number(data['duration_weeks'], 'duration_weeks')
        if not is_valid:
            return responses.validation_error_response(error_msg)
        
        # Validate difficulty
        is_valid, _ = validators.validate_enum(data['difficulty_level'], DIFFICULTY_LEVELS)
        if not is_valid:
            return responses.validation_error_response(f"Invalid difficulty_level. Must be one of: {', '.join(DIFFICULTY_LEVELS)}")
        
        # Validate focus muscles
        focus_muscles = data.get('focus_muscle_groups', [])
        for muscle in focus_muscles:
            is_valid, _ = validators.validate_enum(muscle, MUSCLE_GROUPS)
            if not is_valid:
                return responses.validation_error_response(f"Invalid muscle group: {muscle}")
        
        # Verify goal exists if provided
        if data.get('goal_id'):
            goal = db.session.query(Goal).filter_by(goal_id=data['goal_id']).first()
            if not goal:
                return responses.not_found_response("Goal not found")
        
        # Create program
        import uuid
        import json
        program = FitnessProgram(
            program_id=str(uuid.uuid4()),
            user_id=token_user_id,
            goal_id=data.get('goal_id'),
            program_name=data['program_name'],
            duration_weeks=int(data['duration_weeks']),
            focus_muscle_groups=json.dumps(focus_muscles),
            difficulty_level=data['difficulty_level']
        )
        
        db.session.add(program)
        db.session.flush()
        
        # Generate weekly schedule
        program_workouts = generate_weekly_schedule(focus_muscles, data['difficulty_level'], program.program_id)
        db.session.add_all(program_workouts)
        
        db.session.commit()
        
        return responses.created_response(
            serialize_program(program, include_workouts=True),
            "Program created successfully with weekly schedule"
        )
    
    except Exception as e:
        db.session.rollback()
        return responses.error_response(
            "Database error",
            str(e),
            "PROGRAM_CREATE_ERROR",
            500
        )


@bp.route('/<user_id>', methods=['GET'])
@decorators.token_required
def list_programs(token_user_id, user_id):
    """
    List user's programs
    
    Path params:
    - user_id: User ID (UUID)
    """
    try:
        # Verify user exists
        user = db.session.query(User).filter_by(user_id=user_id).first()
        if not user:
            return responses.not_found_response("User not found")
        
        programs = db.session.query(FitnessProgram).filter_by(user_id=user_id).order_by(
            FitnessProgram.created_at.desc()
        ).all()
        
        return responses.success_response(
            [serialize_program(p) for p in programs],
            "Programs retrieved successfully"
        )
    
    except Exception as e:
        return responses.error_response(
            "Database error",
            str(e),
            "PROGRAM_LIST_ERROR",
            500
        )


@bp.route('/<program_id>', methods=['GET'])
@decorators.token_required
def get_program(token_user_id, program_id):
    """
    Get program detail with weekly schedule
    
    Path params:
    - program_id: Program ID (UUID)
    """
    try:
        program = db.session.query(FitnessProgram).filter_by(program_id=program_id).first()
        if not program:
            return responses.not_found_response("Program not found")
        
        # Security: verify user owns program
        if program.user_id != token_user_id:
            return responses.forbidden_response("You can only view your own programs")
        
        return responses.success_response(
            serialize_program(program, include_workouts=True),
            "Program retrieved successfully"
        )
    
    except Exception as e:
        return responses.error_response(
            "Database error",
            str(e),
            "PROGRAM_GET_ERROR",
            500
        )
