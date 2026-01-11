"""
Dashboard Routes - User fitness dashboard with aggregated data
Endpoints: 1 (GET dashboard summary with graphs)
"""
from flask import Blueprint, request
from datetime import datetime, timedelta
from collections import defaultdict
from sqlalchemy import func
from app.extensions import db

from app.models import User, Workout, Meal, Goal, WorkoutExercise, Exercise
from app.utils import validators, responses, decorators

bp = Blueprint('dashboard', __name__, url_prefix='/api/dashboard')


def get_date_range(period: str) -> tuple:
    """
    Get start and end dates based on period
    
    Args:
        period: 'week', 'month', or 'year'
        
    Returns:
        Tuple of (start_date, end_date)
    """
    today = datetime.now().date()
    
    if period == 'week':
        # Last 7 days
        start_date = today - timedelta(days=7)
        end_date = today
    elif period == 'month':
        # Last 30 days
        start_date = today - timedelta(days=30)
        end_date = today
    elif period == 'year':
        # Last 365 days
        start_date = today - timedelta(days=365)
        end_date = today
    else:
        # Default to week
        start_date = today - timedelta(days=7)
        end_date = today
    
    return start_date, end_date


@bp.route('/<user_id>', methods=['GET'])
@decorators.token_required
def get_dashboard(token_user_id, user_id):
    """
    Get comprehensive dashboard with aggregated fitness data
    
    Query params:
    - period: Time period (week, month, year - default: week)
    """
    try:
        # Verify user exists
        user = db.session.query(User).filter_by(user_id=user_id).first()
        if not user:
            return responses.not_found_response("User not found")
        
        period = request.args.get('period', 'week', type=str)
        start_date, end_date = get_date_range(period)
        
        # Get workouts for period
        workouts = db.session.query(Workout).filter(
            Workout.user_id == user_id,
            Workout.workout_date >= start_date,
            Workout.workout_date <= end_date,
            Workout.status == 'completed'
        ).all()
        
        # Get meals for period
        meals = db.session.query(Meal).filter(
            Meal.user_id == user_id,
            Meal.meal_date >= start_date,
            Meal.meal_date <= end_date
        ).all()
        
        # Get active goals
        goals = db.session.query(Goal).filter_by(user_id=user_id, status='active').all()
        
        # Calculate summary statistics
        total_calories_burned = sum(w.total_calories_burned or 0 for w in workouts)
        total_calories_consumed = sum(m.total_calories for m in meals)
        calorie_deficit = total_calories_consumed - total_calories_burned
        
        avg_workout_duration = 0
        if workouts:
            avg_workout_duration = sum(w.total_duration_minutes or 0 for w in workouts) / len(workouts)
        
        summary = {
            "workouts_this_period": len(workouts),
            "total_calories_burned": round(total_calories_burned, 2),
            "total_calories_consumed": round(total_calories_consumed, 2),
            "calorie_deficit": round(calorie_deficit, 2),
            "average_workout_duration": round(avg_workout_duration, 2)
        }
        
        # Get goal progress data
        goals_data = []
        for goal in goals:
            progress_percentage = 0.0
            if goal.target_value and goal.target_value > 0:
                progress_percentage = round((goal.current_progress / goal.target_value) * 100, 2)
            
            goals_data.append({
                "goal_id": goal.goal_id,
                "type": goal.goal_type,
                "progress_percentage": progress_percentage,
                "target_date": goal.target_date.isoformat() if goal.target_date else None
            })
        
        # Get daily calorie breakdown
        daily_breakdown = defaultdict(lambda: {"burned": 0, "consumed": 0})
        
        for workout in workouts:
            day_key = workout.workout_date.strftime('%a')
            daily_breakdown[day_key]["burned"] += workout.total_calories_burned or 0
        
        for meal in meals:
            day_key = meal.meal_date.strftime('%a')
            daily_breakdown[day_key]["consumed"] += meal.total_calories
        
        # Format daily calories
        days_order = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        daily_calories = []
        for day in days_order:
            if day in daily_breakdown:
                burned = daily_breakdown[day]["burned"]
                consumed = daily_breakdown[day]["consumed"]
                daily_calories.append({
                    "day": day,
                    "burned": round(burned, 2),
                    "consumed": round(consumed, 2),
                    "net": round(consumed - burned, 2)
                })
        
        # Get muscle groups focus distribution
        muscle_groups_focus = defaultdict(int)
        for workout in workouts:
            workout_exercises = db.session.query(WorkoutExercise).filter_by(workout_id=workout.workout_id).all()
            for we in workout_exercises:
                exercise = db.session.query(Exercise).filter_by(exercise_id=we.exercise_id).first()
                if exercise:
                    muscle_groups_focus[exercise.primary_muscle_group] += 1
        
        # Convert to percentages
        total_exercises = sum(muscle_groups_focus.values())
        if total_exercises > 0:
            muscle_groups_focus = {
                k: round((v / total_exercises) * 100, 2) 
                for k, v in muscle_groups_focus.items()
            }
        
        # Get recent workouts
        recent_workouts = db.session.query(Workout).filter_by(user_id=user_id).order_by(
            Workout.workout_date.desc()
        ).limit(5).all()
        
        recent_workouts_data = [
            {
                "workout_id": w.workout_id,
                "date": w.workout_date.isoformat() if w.workout_date else None,
                "duration": w.total_duration_minutes,
                "calories": round(w.total_calories_burned or 0, 2)
            }
            for w in recent_workouts
        ]
        
        # Build response
        dashboard_data = {
            "user_id": user_id,
            "username": user.username,
            "current_weight": user.current_weight,
            "summary": summary,
            "goals": goals_data,
            "graphs": {
                "daily_calories": daily_calories,
                "muscle_groups_focus": dict(muscle_groups_focus)
            },
            "recent_workouts": recent_workouts_data
        }
        
        return responses.success_response(
            dashboard_data,
            "Dashboard retrieved successfully"
        )
    
    except Exception as e:
        return responses.error_response(
            "Database error",
            str(e),
            "DASHBOARD_GET_ERROR",
            500
        )
