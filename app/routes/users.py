"""User profile and statistics routes."""
from flask import Blueprint, request
from datetime import datetime, timedelta, timezone, date
from sqlalchemy import func, and_
from app.extensions import db

from app.models import User, Workout, Meal, Goal, WeightEntry
from app.services.auth_service import AuthService
from app.utils import validators
from app.utils.responses import (
    success_response, error_response, validation_error_response,
    unauthorized_response, not_found_response, forbidden_response
)
from app.utils.decorators import token_required, validate_json

bp = Blueprint('users', __name__, url_prefix='/api/users')


def serialize_user(user: User) -> dict:
    """Convert User model to dictionary.
    
    Args:
        user: User model instance
        
    Returns:
        Dictionary representation of user
    """
    return {
        "user_id": user.user_id,
        "username": user.username,
        "email": user.email,
        "age": user.age,
        "current_weight": user.current_weight,
        "target_weight": user.target_weight,
        "height": user.height,
        "created_at": user.created_at.isoformat() + 'Z',
        "updated_at": user.updated_at.isoformat() + 'Z'
    }


@bp.route('/<user_id>', methods=['GET'])
@token_required
def get_user(token_user_id, user_id):
    """Get user profile information.
    
    Args:
        user_id: User ID to retrieve
    
    Returns:
        200: User profile data
        401: Unauthorized
        404: User not found
    """
    try:
        # Security check: User can only access their own profile
        if token_user_id != user_id:
            return forbidden_response("You can only access your own profile")
        
        user = db.session.query(User).filter_by(user_id=user_id).first()
        if not user:
            return not_found_response("User")
        
        return success_response(serialize_user(user))
    
    except Exception as e:
        return error_response(
            "Retrieval Error",
            "An error occurred while retrieving user profile",
            "USER_RETRIEVAL_ERROR",
            500
        )


@bp.route('/<user_id>', methods=['PUT'])
@token_required
@validate_json
def update_user(token_user_id, user_id):
    """Update user profile information.
    
    Request JSON (all optional):
        - age (float): Age in years
        - current_weight (float): Weight in pounds
        - height (float): Height in inches
    
    Returns:
        200: Updated user profile
        400: Validation error
        401: Unauthorized
        404: User not found
    """
    try:
        # Security check: User can only update their own profile
        if token_user_id != user_id:
            return forbidden_response("You can only update your own profile")
        
        user = db.session.query(User).filter_by(user_id=user_id).first()
        if not user:
            return not_found_response("User")
        
        data = request.get_json()
        
        # Update age if provided
        if 'age' in data:
            if data['age'] is not None:
                is_valid, error_msg = validators.validate_positive_number(data['age'], 'age')
                if not is_valid:
                    return validation_error_response(error_msg)
            user.age = data['age']
        
        # Update current_weight if provided
        if 'current_weight' in data:
            if data['current_weight'] is not None:
                is_valid, error_msg = validators.validate_positive_number(data['current_weight'], 'current_weight')
                if not is_valid:
                    return validation_error_response(error_msg)
            user.current_weight = data['current_weight']
        
        # Update target_weight if provided
        if 'target_weight' in data:
            if data['target_weight'] is not None:
                is_valid, error_msg = validators.validate_positive_number(data['target_weight'], 'target_weight')
                if not is_valid:
                    return validation_error_response(error_msg)
            user.target_weight = data['target_weight']
        
        # Update height if provided
        if 'height' in data:
            if data['height'] is not None:
                is_valid, error_msg = validators.validate_positive_number(data['height'], 'height')
                if not is_valid:
                    return validation_error_response(error_msg)
            user.height = data['height']
        
        user.updated_at = datetime.now(timezone.utc)
        db.session.commit()
        
        return success_response(serialize_user(user), "User profile updated successfully")
    
    except Exception as e:
        db.session.rollback()
        return error_response(
            "Update Error",
            "An error occurred while updating user profile",
            "USER_UPDATE_ERROR",
            500
        )


@bp.route('/<user_id>/stats', methods=['GET'])
@token_required
def get_user_stats(token_user_id, user_id):
    """Get user fitness statistics.
    
    Returns:
        200: User statistics
        401: Unauthorized
        404: User not found
    """
    try:
        # Security check: User can only access their own stats
        if token_user_id != user_id:
            return forbidden_response("You can only view your own stats")
        
        user = db.session.query(User).filter_by(user_id=user_id).first()
        if not user:
            return not_found_response("User")
        
        today = datetime.now(timezone.utc).date()
        month_ago = today - timedelta(days=30)
        week_ago = today - timedelta(days=7)
        
        # Total workouts
        total_workouts = db.session.query(func.count(Workout.workout_id)).filter(
            and_(Workout.user_id == user_id, Workout.status == 'completed')
        ).scalar() or 0
        
        # Total calories burned
        total_calories_burned = db.session.query(func.sum(Workout.total_calories_burned)).filter(
            and_(Workout.user_id == user_id, Workout.status == 'completed')
        ).scalar() or 0
        
        # Workouts this month
        workouts_this_month = db.session.query(func.count(Workout.workout_id)).filter(
            and_(
                Workout.user_id == user_id,
                Workout.status == 'completed',
                Workout.workout_date >= month_ago
            )
        ).scalar() or 0
        
        # Workouts this week
        workouts_this_week = db.session.query(func.count(Workout.workout_id)).filter(
            and_(
                Workout.user_id == user_id,
                Workout.status == 'completed',
                Workout.workout_date >= week_ago
            )
        ).scalar() or 0
        
        # Active goals
        active_goals = db.session.query(func.count(Goal.goal_id)).filter(
            and_(Goal.user_id == user_id, Goal.status == 'active')
        ).scalar() or 0
        
        # Completed goals
        completed_goals = db.session.query(func.count(Goal.goal_id)).filter(
            and_(Goal.user_id == user_id, Goal.status == 'completed')
        ).scalar() or 0
        
        # Weight lost (approximate)
        weight_lost = 0
        if user.current_weight:
            # This is a placeholder - in production, you'd track starting weight
            weight_lost = 0
        
        # Streak days (consecutive days with workouts)
        # This is a simplified calculation
        streak_days = 0
        current_date = today
        for i in range(1, 100):  # Check up to 100 days
            check_date = today - timedelta(days=i)
            workout_on_date = db.session.query(func.count(Workout.workout_id)).filter(
                and_(
                    Workout.user_id == user_id,
                    Workout.status == 'completed',
                    Workout.workout_date == check_date
                )
            ).scalar()
            if workout_on_date:
                streak_days = i
            else:
                break
        
        return success_response({
            "total_workouts": total_workouts,
            "total_calories_burned": float(total_calories_burned) if total_calories_burned else 0,
            "workouts_this_month": workouts_this_month,
            "workouts_this_week": workouts_this_week,
            "active_goals": active_goals,
            "completed_goals": completed_goals,
            "current_weight": user.current_weight,
            "weight_lost": weight_lost,
            "streak_days": streak_days
        })
    
    except Exception as e:
        return error_response(
            "Stats Error",
            "An error occurred while retrieving user statistics",
            "STATS_ERROR",
            500
        )


@bp.route('/<user_id>', methods=['DELETE'])
@token_required
@validate_json
def delete_user(token_user_id, user_id):
    """Delete user account.
    
    Request JSON:
        - password (str): User password for verification
    
    Returns:
        200: Account deleted successfully
        400: Validation error
        401: Invalid password or unauthorized
        404: User not found
    """
    try:
        # Security check: User can only delete their own account
        if token_user_id != user_id:
            return forbidden_response("You can only delete your own account")
        
        user = db.session.query(User).filter_by(user_id=user_id).first()
        if not user:
            return not_found_response("User")
        
        data = request.get_json()
        
        # Verify password
        if 'password' not in data or not data['password']:
            return validation_error_response("Password is required to delete account")
        
        if not AuthService.verify_password(data['password'], user.password_hash):
            return unauthorized_response("Invalid password")
        
        # Delete user (cascades to related records)
        db.delete(user)
        db.commit()
        
        return success_response(None, "Account deleted successfully")
    
    except Exception as e:
        db.rollback()
        return error_response(
            "Delete Error",
            "An error occurred while deleting user account",
            "USER_DELETE_ERROR",
            500
        )


@bp.route('/<user_id>/progress', methods=['GET'])
@token_required
def get_user_progress(token_user_id, user_id):
    """Get user progress for a date range.
    
    Query Parameters:
        - start_date (str): Start date in YYYY-MM-DD format
        - end_date (str): End date in YYYY-MM-DD format
    
    Returns:
        200: Progress data for the period
        400: Invalid date format
        401: Unauthorized
        404: User not found
    """
    try:
        # Security check: User can only access their own progress
        if token_user_id != user_id:
            return forbidden_response("You can only view your own progress")
        
        user = db.session.query(User).filter_by(user_id=user_id).first()
        if not user:
            return not_found_response("User")
        
        # Get date parameters
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')
        
        if not start_date_str or not end_date_str:
            return validation_error_response("start_date and end_date parameters are required")
        
        # Validate dates
        is_valid, error_msg = validators.validate_date(start_date_str)
        if not is_valid:
            return validation_error_response(f"start_date: {error_msg}")
        
        is_valid, error_msg = validators.validate_date(end_date_str)
        if not is_valid:
            return validation_error_response(f"end_date: {error_msg}")
        
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        
        # Get workouts in range
        workouts = db.session.query(Workout).filter(
            and_(
                Workout.user_id == user_id,
                Workout.status == 'completed',
                Workout.workout_date >= start_date,
                Workout.workout_date <= end_date
            )
        ).all()
        
        # Get meals in range
        meals = db.session.query(Meal).filter(
            and_(
                Meal.user_id == user_id,
                Meal.meal_date >= start_date,
                Meal.meal_date <= end_date
            )
        ).all()
        
        # Calculate totals
        total_workouts = len(workouts)
        total_calories_burned = sum(w.total_calories_burned or 0 for w in workouts)
        total_calories_consumed = sum(m.total_calories or 0 for m in meals)
        
        # Average workout duration
        total_duration = sum(w.total_duration_minutes or 0 for w in workouts)
        average_duration = total_duration / total_workouts if total_workouts > 0 else 0
        
        # Weight change (simplified - would need historical data)
        weight_change = 0
        
        return success_response({
            "period": f"{start_date_str} to {end_date_str}",
            "workouts": total_workouts,
            "calories_burned": total_calories_burned,
            "calories_consumed": total_calories_consumed,
            "net_deficit": total_calories_consumed - total_calories_burned,
            "weight_change": weight_change,
            "average_workout_duration": round(average_duration, 1)
        })
    
    except Exception as e:
        return error_response(
            "Progress Error",
            "An error occurred while retrieving user progress",
            "PROGRESS_ERROR",
            500
        )

# Weight Tracking Endpoints
@bp.route('/<user_id>/weight', methods=['POST'])
@token_required
@validate_json
def add_weight_entry(token_user_id, user_id):
    """Add a weight entry for the user.
    
    Request JSON:
        - weight (float, required): Weight in kg
        - entry_date (string, optional): Date in YYYY-MM-DD format (default: today)
        - notes (string, optional): Notes about the entry
    
    Returns:
        201: Weight entry created
        400: Validation error
        401: Unauthorized
        404: User not found
    """
    try:
        # Security check
        if token_user_id != user_id:
            return forbidden_response("You can only add weight entries to your own profile")
        
        user = db.session.query(User).filter_by(user_id=user_id).first()
        if not user:
            return not_found_response("User")
        
        data = request.get_json()
        
        # Validate weight
        if 'weight' not in data or data['weight'] is None:
            return validation_error_response("weight is required")
        
        is_valid, error_msg = validators.validate_positive_number(data['weight'], 'weight')
        if not is_valid:
            return validation_error_response(error_msg)
        
        # Parse entry date (default to today)
        entry_date = date.today()
        if 'entry_date' in data and data['entry_date']:
            try:
                entry_date = datetime.strptime(data['entry_date'], '%Y-%m-%d').date()
            except ValueError:
                return validation_error_response("entry_date must be in YYYY-MM-DD format")
        
        # Create weight entry
        weight_entry = WeightEntry(
            user_id=user_id,
            weight=float(data['weight']),
            entry_date=entry_date,
            notes=data.get('notes')
        )
        
        # Update user's current weight
        user.current_weight = float(data['weight'])
        user.updated_at = datetime.now(timezone.utc)
        
        db.session.add(weight_entry)
        db.session.commit()
        
        return success_response({
            "entry_id": weight_entry.entry_id,
            "weight": weight_entry.weight,
            "entry_date": weight_entry.entry_date.isoformat(),
            "notes": weight_entry.notes,
            "created_at": weight_entry.created_at.isoformat() + 'Z'
        }, "Weight entry added successfully", 201)
    
    except Exception as e:
        db.rollback()
        return error_response(
            "Weight Entry Error",
            "An error occurred while adding weight entry",
            "WEIGHT_ENTRY_ERROR",
            500
        )


@bp.route('/<user_id>/weight', methods=['GET'])
@token_required
def get_weight_history(token_user_id, user_id):
    """Get user's weight history.
    
    Query Parameters:
        - days (int, optional): Get weight entries from last N days (default: 90)
    
    Returns:
        200: List of weight entries sorted by date
        401: Unauthorized
        404: User not found
    """
    try:
        # Security check
        if token_user_id != user_id:
            return forbidden_response("You can only view your own weight history")
        
        user = db.session.query(User).filter_by(user_id=user_id).first()
        if not user:
            return not_found_response("User")
        
        # Get number of days to retrieve (default 90)
        days = request.args.get('days', default=90, type=int)
        if days < 1:
            days = 90
        
        # Calculate start date
        start_date = date.today() - timedelta(days=days)
        
        # Get weight entries
        entries = db.session.query(WeightEntry).filter(
            and_(
                WeightEntry.user_id == user_id,
                WeightEntry.entry_date >= start_date
            )
        ).order_by(WeightEntry.entry_date.asc()).all()
        
        return success_response({
            "user_id": user_id,
            "target_weight": user.target_weight,
            "current_weight": user.current_weight,
            "entries": [
                {
                    "entry_id": e.entry_id,
                    "weight": e.weight,
                    "entry_date": e.entry_date.isoformat(),
                    "notes": e.notes
                }
                for e in entries
            ]
        })
    
    except Exception as e:
        return error_response(
            "Weight History Error",
            "An error occurred while retrieving weight history",
            "WEIGHT_HISTORY_ERROR",
            500
        )


@bp.route('/<user_id>/weight/<entry_id>', methods=['PUT'])
@token_required
@validate_json
def update_weight_entry(token_user_id, user_id, entry_id):
    """Update a weight entry.
    
    Request JSON (at least one required):
        - weight (float): New weight in kg
        - entry_date (string): Date in YYYY-MM-DD format
        - notes (string): Updated notes
    
    Returns:
        200: Updated weight entry
        400: Validation error
        401: Unauthorized
        404: Entry or user not found
    """
    try:
        # Security check
        if token_user_id != user_id:
            return forbidden_response("You can only update your own weight entries")
        
        user = db.session.query(User).filter_by(user_id=user_id).first()
        if not user:
            return not_found_response("User")
        
        entry = db.session.query(WeightEntry).filter(
            and_(
                WeightEntry.entry_id == entry_id,
                WeightEntry.user_id == user_id
            )
        ).first()
        if not entry:
            return not_found_response("Weight entry")
        
        data = request.get_json()
        
        # Update weight if provided
        if 'weight' in data and data['weight'] is not None:
            is_valid, error_msg = validators.validate_positive_number(data['weight'], 'weight')
            if not is_valid:
                return validation_error_response(error_msg)
            entry.weight = float(data['weight'])
            user.current_weight = float(data['weight'])
        
        # Update entry date if provided
        if 'entry_date' in data and data['entry_date']:
            try:
                entry.entry_date = datetime.strptime(data['entry_date'], '%Y-%m-%d').date()
            except ValueError:
                return validation_error_response("entry_date must be in YYYY-MM-DD format")
        
        # Update notes if provided
        if 'notes' in data:
            entry.notes = data['notes']
        
        user.updated_at = datetime.now(timezone.utc)
        db.commit()
        
        return success_response({
            "entry_id": entry.entry_id,
            "weight": entry.weight,
            "entry_date": entry.entry_date.isoformat(),
            "notes": entry.notes,
            "created_at": entry.created_at.isoformat() + 'Z'
        }, "Weight entry updated successfully")
    
    except Exception as e:
        db.session.rollback()
        return error_response(
            "Weight Entry Update Error",
            "An error occurred while updating weight entry",
            "WEIGHT_ENTRY_UPDATE_ERROR",
            500
        )


@bp.route('/<user_id>/weight/<entry_id>', methods=['DELETE'])
@token_required
def delete_weight_entry(token_user_id, user_id, entry_id):
    """Delete a weight entry.
    
    Returns:
        200: Deletion success
        401: Unauthorized
        404: Entry or user not found
    """
    try:
        # Security check
        if token_user_id != user_id:
            return forbidden_response("You can only delete your own weight entries")
        
        user = db.session.query(User).filter_by(user_id=user_id).first()
        if not user:
            return not_found_response("User")
        
        entry = db.session.query(WeightEntry).filter(
            and_(
                WeightEntry.entry_id == entry_id,
                WeightEntry.user_id == user_id
            )
        ).first()
        if not entry:
            return not_found_response("Weight entry")
        
        db.session.delete(entry)
        db.session.commit()
        
        return success_response(None, "Weight entry deleted successfully")
    
    except Exception as e:
        db.rollback()
        return error_response(
            "Weight Entry Delete Error",
            "An error occurred while deleting weight entry",
            "WEIGHT_ENTRY_DELETE_ERROR",
            500
        )