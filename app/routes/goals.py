"""
Goals Routes - Manage fitness goals and progress tracking
Endpoints: 5 (POST, GET list, GET detail, PUT, DELETE)
"""
from flask import Blueprint, request
from datetime import datetime, timedelta
from sqlalchemy import func
from app.extensions import db

from app.models import Goal, User, Workout
from app.utils import validators, responses, decorators
from app.utils.constants import GOAL_TYPES

bp = Blueprint('goals', __name__, url_prefix='/api/goals')




def serialize_goal(goal: Goal, include_workouts: bool = False) -> dict:
    """
    Serialize Goal object to dictionary with calculated fields
    
    Args:
        goal: Goal model instance
        include_workouts: Include related workouts data
        
    Returns:
        Dictionary representation of goal with progress calculations
    """
    progress_percentage = 0.0
    if goal.target_value and goal.target_value > 0:
        progress_percentage = round((goal.current_progress / goal.target_value) * 100, 2)
    
    target_date = goal.target_date
    days_remaining = 0
    if target_date:
        days_remaining = (target_date - datetime.now().date()).days
    
    goal_dict = {
        "goal_id": goal.goal_id,
        "user_id": goal.user_id,
        "goal_type": goal.goal_type,
        "target_value": goal.target_value,
        "target_unit": goal.target_unit,
        "current_progress": goal.current_progress,
        "target_date": goal.target_date.isoformat() if goal.target_date else None,
        "status": goal.status,
        "description": goal.description,
        "progress_percentage": progress_percentage,
        "days_remaining": days_remaining,
        "created_at": goal.created_at.isoformat() if goal.created_at else None,
        "updated_at": goal.updated_at.isoformat() if goal.updated_at else None
    }
    
    if include_workouts:
        related_workouts = db.session.query(Workout).filter_by(user_id=goal.user_id).all()
        goal_dict["related_workouts"] = len(related_workouts)
        
        # Calculate total calories deficit for goal period
        total_calories_burned = db.session.query(func.sum(Workout.total_calories_burned)).filter(
            Workout.user_id == goal.user_id,
            Workout.status == 'completed',
            Workout.created_at >= goal.created_at
        ).scalar()
        goal_dict["total_calories_deficit"] = float(total_calories_burned or 0)
    
    return goal_dict


@bp.route('', methods=['GET'])
@decorators.token_required
def list_goals_current_user(token_user_id):
    """
    List current user's goals with optional status filter
    
    Query params:
    - status: Filter by goal status (active, completed, abandoned)
    - page: Page number (default 1)
    - per_page: Items per page (default 10)
    """
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        status_filter = request.args.get('status', type=str)
        
        query = db.session.query(Goal).filter_by(user_id=token_user_id)
        
        # Filter by status if provided
        if status_filter:
            query = query.filter_by(status=status_filter)
        
        # Order by target_date
        query = query.order_by(Goal.target_date.asc())
        
        # Paginate
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        goals = [serialize_goal(g) for g in pagination.items]
        
        return responses.paginated_response(
            goals,
            pagination.total,
            page,
            per_page,
            "Goals retrieved successfully"
        )
    
    except Exception as e:
        return responses.error_response(
            "Database error",
            str(e),
            "GOAL_LIST_ERROR",
            500
        )


@bp.route('', methods=['POST'])
@decorators.validate_json
@decorators.token_required
def create_goal(token_user_id):
    """
    Create a new fitness goal
    
    Request body:
    {
        "goal_type": "weight_loss|muscle_gain|endurance",
        "target_value": 20,
        "target_unit": "lbs|kg|miles",
        "target_date": "2026-06-11",
        "description": "Lose 20 pounds by summer"
    }
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        is_valid, error_msg = validators.validate_required_fields(
            data, ['goal_type', 'target_value', 'target_unit', 'target_date']
        )
        if not is_valid:
            return responses.validation_error_response(error_msg)
        
        # Validate goal_type
        is_valid, error_msg = validators.validate_enum(data['goal_type'], GOAL_TYPES)
        if not is_valid:
            return responses.validation_error_response(f"Invalid goal_type. Must be one of: {', '.join(GOAL_TYPES)}")
        
        # Validate target_value
        is_valid, error_msg = validators.validate_positive_number(data['target_value'], 'target_value')
        if not is_valid:
            return responses.validation_error_response(error_msg)
        
        # Validate target_date
        is_valid, error_msg = validators.validate_date(data['target_date'])
        if not is_valid:
            return responses.validation_error_response(error_msg)
        
        # Parse target_date
        target_date = datetime.strptime(data['target_date'], '%Y-%m-%d').date()
        
        # Create goal
        import uuid
        goal = Goal(
            goal_id=str(uuid.uuid4()),
            user_id=token_user_id,
            goal_type=data['goal_type'],
            target_value=float(data['target_value']),
            target_unit=data['target_unit'],
            current_progress=0.0,
            target_date=target_date,
            status='active',
            description=data.get('description', '')
        )
        
        db.session.add(goal)
        db.session.commit()
        
        return responses.created_response(
            serialize_goal(goal),
            "Goal created successfully"
        )
    
    except Exception as e:
        db.session.rollback()
        return responses.error_response(
            "Database error",
            str(e),
            "GOAL_CREATE_ERROR",
            500
        )


@bp.route('/<user_id>', methods=['GET'])
@decorators.token_required
def list_goals(token_user_id, user_id):
    """
    List user's goals with optional status filter
    
    Query params:
    - status: Filter by goal status (active, completed, abandoned)
    - page: Page number (default 1)
    - per_page: Items per page (default 10)
    """
    try:
        # Verify user owns the goals
        user = db.session.query(User).filter_by(user_id=user_id).first()
        if not user:
            return responses.not_found_response("User not found")
        
        # Get pagination params
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        status = request.args.get('status', type=str)
        
        # Build query
        query = db.session.query(Goal).filter_by(user_id=user_id)
        
        if status:
            is_valid, _ = validators.validate_enum(status, ['active', 'completed', 'abandoned'])
            if is_valid:
                query = query.filter_by(status=status)
        
        # Paginate
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        goals = [serialize_goal(goal) for goal in pagination.items]
        
        return responses.paginated_response(
            goals,
            pagination.total,
            page,
            per_page,
            "Goals retrieved successfully"
        )
    
    except Exception as e:
        return responses.error_response(
            "Database error",
            str(e),
            "GOAL_LIST_ERROR",
            500
        )


@bp.route('/<goal_id>', methods=['GET'])
def get_goal(goal_id):
    """
    Get single goal detail with related workouts and calories deficit
    
    Path params:
    - goal_id: Goal ID (UUID)
    """
    try:
        goal = db.session.query(Goal).filter_by(goal_id=goal_id).first()
        if not goal:
            return responses.not_found_response("Goal not found")
        
        return responses.success_response(
            serialize_goal(goal, include_workouts=True),
            "Goal retrieved successfully"
        )
    
    except Exception as e:
        return responses.error_response(
            "Database error",
            str(e),
            "GOAL_GET_ERROR",
            500
        )


@bp.route('/<goal_id>', methods=['PUT'])
@decorators.validate_json
@decorators.token_required
def update_goal(token_user_id, goal_id):
    """
    Update goal
    
    Request body (all optional):
    {
        "target_value": 25,
        "target_date": "2026-07-11",
        "current_progress": 10,
        "status": "active|completed|abandoned",
        "description": "New description"
    }
    """
    try:
        goal = db.session.query(Goal).filter_by(goal_id=goal_id).first()
        if not goal:
            return responses.not_found_response("Goal not found")
        
        # Security: verify user owns goal
        if goal.user_id != token_user_id:
            return responses.forbidden_response("You can only update your own goals")
        
        data = request.get_json()
        
        # Update fields if provided
        if 'target_value' in data:
            is_valid, error_msg = validators.validate_positive_number(data['target_value'], 'target_value')
            if not is_valid:
                return responses.validation_error_response(error_msg)
            goal.target_value = float(data['target_value'])
        
        if 'target_date' in data:
            is_valid, error_msg = validators.validate_date(data['target_date'])
            if not is_valid:
                return responses.validation_error_response(error_msg)
            goal.target_date = datetime.strptime(data['target_date'], '%Y-%m-%d').date()
        
        if 'current_progress' in data:
            is_valid, error_msg = validators.validate_positive_number(data['current_progress'], 'current_progress')
            if not is_valid:
                return responses.validation_error_response(error_msg)
            goal.current_progress = float(data['current_progress'])
        
        if 'status' in data:
            is_valid, error_msg = validators.validate_enum(data['status'], ['active', 'completed', 'abandoned'])
            if not is_valid:
                return responses.validation_error_response("Invalid status")
            goal.status = data['status']
        
        if 'description' in data:
            goal.description = data['description']
        
        goal.updated_at = datetime.utcnow()
        db.session.commit()
        
        return responses.success_response(
            serialize_goal(goal),
            "Goal updated successfully"
        )
    
    except Exception as e:
        db.session.rollback()
        return responses.error_response(
            "Database error",
            str(e),
            "GOAL_UPDATE_ERROR",
            500
        )


@bp.route('/<goal_id>', methods=['DELETE'])
@decorators.token_required
def delete_goal(token_user_id, goal_id):
    """
    Delete a goal
    
    Path params:
    - goal_id: Goal ID (UUID)
    """
    try:
        goal = db.session.query(Goal).filter_by(goal_id=goal_id).first()
        if not goal:
            return responses.not_found_response("Goal not found")
        
        # Security: verify user owns goal
        if goal.user_id != token_user_id:
            return responses.forbidden_response("You can only delete your own goals")
        
        db.session.delete(goal)
        db.session.commit()
        
        return responses.deleted_response("Goal deleted successfully")
    
    except Exception as e:
        db.session.rollback()
        return responses.error_response(
            "Database error",
            str(e),
            "GOAL_DELETE_ERROR",
            500
        )
