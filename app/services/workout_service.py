"""
Workout Service - Business logic for workout calculations and aggregations.
"""

import logging
from typing import List, Dict, Any
from datetime import datetime
from sqlalchemy import func
from app.database import db
from app.models import Workout, WorkoutExercise, Exercise, Goal

logger = logging.getLogger(__name__)


def calculate_calories_burned(exercise: Exercise, sets: int, reps: int, duration_seconds: int = 0) -> float:
    """
    Calculate calories burned for an exercise.
    
    Args:
        exercise: Exercise model instance
        sets: Number of sets performed
        reps: Number of reps per set
        duration_seconds: Alternative duration-based calculation
    
    Returns:
        Calories burned (rounded to 1 decimal place)
    """
    try:
        if duration_seconds > 0:
            # Alternative: duration-based calculation
            calories = (exercise.typical_calories_per_minute / 60) * duration_seconds
        else:
            # Primary: sets and reps calculation
            calories = sets * reps * exercise.typical_calories_per_minute / 10
        
        return round(calories, 1)
    except Exception as e:
        logger.error(f"Error calculating calories: {str(e)}")
        return 0.0


def get_workout_summary(workout: Workout) -> Dict[str, Any]:
    """
    Get summary statistics for a workout.
    
    Args:
        workout: Workout model instance
    
    Returns:
        Dictionary with duration, calories, muscle_groups, exercise_count
    """
    try:
        # Calculate duration in minutes
        if workout.created_at and workout.completed_at:
            duration_minutes = int((workout.completed_at - workout.created_at).total_seconds() / 60)
        elif workout.total_duration_minutes:
            duration_minutes = workout.total_duration_minutes
        else:
            duration_minutes = 0
        
        # Get unique muscle groups
        muscle_groups = get_muscle_groups_worked(workout)
        
        return {
            "duration": duration_minutes,
            "calories": workout.total_calories_burned or 0,
            "muscle_groups": muscle_groups,
            "exercise_count": len(workout.workout_exercises)
        }
    except Exception as e:
        logger.error(f"Error getting workout summary: {str(e)}")
        return {
            "duration": 0,
            "calories": 0,
            "muscle_groups": [],
            "exercise_count": 0
        }


def calculate_goal_progress(goal: Goal, user: Any) -> float:
    """
    Calculate progress percentage for a goal.
    
    Args:
        goal: Goal model instance
        user: User model instance
    
    Returns:
        Progress percentage (0-100+)
    """
    try:
        if goal.goal_type == "weight_loss":
            # Weight loss: how much weight lost towards target
            if goal.target_value <= 0:
                return 0.0
            weight_lost = (user.current_weight or 0) - (goal.current_progress or user.current_weight or 0)
            progress = abs(weight_lost) / goal.target_value * 100
        
        elif goal.goal_type == "muscle_gain":
            # Muscle gain: how much weight gained towards target
            if goal.target_value <= 0:
                return 0.0
            weight_gained = (goal.current_progress or user.current_weight or 0) - (user.current_weight or 0)
            progress = weight_gained / goal.target_value * 100
        
        elif goal.goal_type == "endurance":
            # Endurance: based on workouts completed
            if goal.target_value <= 0:
                return 0.0
            progress = (goal.current_progress or 0) / goal.target_value * 100
        
        else:
            progress = (goal.current_progress or 0) / (goal.target_value or 1) * 100
        
        return round(min(progress, 100), 2)
    except Exception as e:
        logger.error(f"Error calculating goal progress: {str(e)}")
        return 0.0


def get_muscle_groups_worked(workout: Workout) -> List[str]:
    """
    Get unique primary muscle groups worked in a workout.
    
    Args:
        workout: Workout model instance
    
    Returns:
        List of unique primary muscle groups
    """
    try:
        muscle_groups = set()
        
        for we in workout.workout_exercises:
            if we.exercise and we.exercise.primary_muscle_group:
                muscle_groups.add(we.exercise.primary_muscle_group)
        
        return sorted(list(muscle_groups))
    except Exception as e:
        logger.error(f"Error getting muscle groups: {str(e)}")
        return []
