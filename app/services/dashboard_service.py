"""
Dashboard Service - Business logic for dashboard analytics and aggregations.
"""

import logging
from typing import Dict, List, Any
from datetime import datetime, timedelta
from collections import defaultdict
from sqlalchemy import func
from app.database import db
from app.models import Workout, Meal, Goal, WorkoutExercise, Exercise

logger = logging.getLogger(__name__)


def get_dashboard_summary(user_id: str, period: str = "week") -> Dict[str, Any]:
    """
    Get comprehensive dashboard summary.
    
    Args:
        user_id: User ID
        period: 'week', 'month', or 'year'
    
    Returns:
        Dictionary with aggregated stats
    """
    try:
        start_date, end_date = get_date_range(period)
        
        # Query workouts
        workouts = Workout.query.filter(
            Workout.user_id == user_id,
            Workout.status == "completed",
            func.date(Workout.workout_date) >= start_date,
            func.date(Workout.workout_date) <= end_date
        ).all()
        
        # Query meals
        meals = Meal.query.filter(
            Meal.user_id == user_id,
            func.date(Meal.meal_date) >= start_date,
            func.date(Meal.meal_date) <= end_date
        ).all()
        
        # Calculate totals
        calories_burned = sum(w.total_calories_burned or 0 for w in workouts)
        calories_consumed = sum(m.total_calories or 0 for m in meals)
        average_duration = (sum(w.total_duration_minutes or 0 for w in workouts) / len(workouts)) if workouts else 0
        
        return {
            "workouts_count": len(workouts),
            "calories_burned": round(calories_burned, 1),
            "calories_consumed": round(calories_consumed, 1),
            "calorie_deficit": round(calories_consumed - calories_burned, 1),
            "average_workout_duration": round(average_duration, 1),
            "period": period
        }
    except Exception as e:
        logger.error(f"Error getting dashboard summary: {str(e)}")
        return {
            "workouts_count": 0,
            "calories_burned": 0,
            "calories_consumed": 0,
            "calorie_deficit": 0,
            "average_workout_duration": 0,
            "period": period
        }


def get_calorie_graph_data(user_id: str, period: str = "week") -> List[Dict[str, Any]]:
    """
    Get daily calorie data for graph.
    
    Args:
        user_id: User ID
        period: 'week', 'month', or 'year'
    
    Returns:
        Array of daily calorie data
    """
    try:
        start_date, end_date = get_date_range(period)
        daily_data = defaultdict(lambda: {"burned": 0, "consumed": 0})
        
        # Get workouts
        workouts = Workout.query.filter(
            Workout.user_id == user_id,
            Workout.status == "completed",
            func.date(Workout.workout_date) >= start_date,
            func.date(Workout.workout_date) <= end_date
        ).all()
        
        for w in workouts:
            date_key = w.workout_date.strftime("%Y-%m-%d") if isinstance(w.workout_date, datetime) else str(w.workout_date)
            daily_data[date_key]["burned"] += w.total_calories_burned or 0
        
        # Get meals
        meals = Meal.query.filter(
            Meal.user_id == user_id,
            func.date(Meal.meal_date) >= start_date,
            func.date(Meal.meal_date) <= end_date
        ).all()
        
        for m in meals:
            date_key = m.meal_date.strftime("%Y-%m-%d") if isinstance(m.meal_date, datetime) else str(m.meal_date)
            daily_data[date_key]["consumed"] += m.total_calories or 0
        
        # Format for graph
        result = []
        current = start_date
        while current <= end_date:
            date_key = current.strftime("%Y-%m-%d")
            day_name = current.strftime("%a")
            data = daily_data.get(date_key, {"burned": 0, "consumed": 0})
            
            result.append({
                "day": day_name,
                "date": date_key,
                "burned": round(data["burned"], 1),
                "consumed": round(data["consumed"], 1),
                "net": round(data["consumed"] - data["burned"], 1)
            })
            
            current += timedelta(days=1)
        
        return result
    except Exception as e:
        logger.error(f"Error getting calorie graph data: {str(e)}")
        return []


def get_muscle_focus_distribution(user_id: str, period: str = "week") -> Dict[str, float]:
    """
    Get muscle group distribution percentages.
    
    Args:
        user_id: User ID
        period: 'week', 'month', or 'year'
    
    Returns:
        Dictionary with muscle groups and percentages
    """
    try:
        start_date, end_date = get_date_range(period)
        muscle_counts = defaultdict(int)
        total_exercises = 0
        
        # Get workouts
        workouts = Workout.query.filter(
            Workout.user_id == user_id,
            Workout.status == "completed",
            func.date(Workout.workout_date) >= start_date,
            func.date(Workout.workout_date) <= end_date
        ).all()
        
        # Count exercises per muscle group
        for w in workouts:
            for we in w.workout_exercises:
                if we.exercise and we.exercise.primary_muscle_group:
                    muscle_counts[we.exercise.primary_muscle_group] += 1
                    total_exercises += 1
        
        # Convert to percentages
        result = {}
        if total_exercises > 0:
            for muscle, count in muscle_counts.items():
                result[muscle] = round(count / total_exercises * 100, 1)
        
        return result
    except Exception as e:
        logger.error(f"Error getting muscle focus distribution: {str(e)}")
        return {}


def get_goal_progress_data(user_id: str) -> List[Dict[str, Any]]:
    """
    Get all goals with progress data.
    
    Args:
        user_id: User ID
    
    Returns:
        Array of goals with progress info
    """
    try:
        goals = Goal.query.filter(
            Goal.user_id == user_id,
            Goal.status == "active"
        ).all()
        
        result = []
        for goal in goals:
            target_date = goal.target_date
            days_remaining = (target_date - datetime.now().date()).days if target_date else 0
            
            progress_pct = (goal.current_progress or 0) / (goal.target_value or 1) * 100
            
            result.append({
                "goal_id": goal.goal_id,
                "type": goal.goal_type,
                "target_value": goal.target_value,
                "current_progress": goal.current_progress or 0,
                "progress_percentage": round(min(progress_pct, 100), 2),
                "target_date": goal.target_date.strftime("%Y-%m-%d") if goal.target_date else None,
                "days_remaining": days_remaining,
                "status": goal.status
            })
        
        return result
    except Exception as e:
        logger.error(f"Error getting goal progress data: {str(e)}")
        return []


def get_date_range(period: str) -> tuple:
    """
    Calculate date range for period.
    
    Args:
        period: 'week', 'month', or 'year'
    
    Returns:
        Tuple of (start_date, end_date)
    """
    today = datetime.now().date()
    
    if period == "week":
        start_date = today - timedelta(days=today.weekday())
        end_date = start_date + timedelta(days=6)
    elif period == "month":
        start_date = today.replace(day=1)
        if today.month == 12:
            end_date = today.replace(year=today.year + 1, month=1, day=1) - timedelta(days=1)
        else:
            end_date = today.replace(month=today.month + 1, day=1) - timedelta(days=1)
    elif period == "year":
        start_date = today.replace(month=1, day=1)
        end_date = today.replace(month=12, day=31)
    else:
        start_date = today
        end_date = today
    
    return start_date, end_date
