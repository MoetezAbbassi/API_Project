"""
Program Service - Business logic for fitness program generation and management.
"""

import logging
import random
from typing import Dict, List, Any
from app.database import db
from app.models import Exercise, FitnessProgram, ProgramWorkout
from app.utils.constants import MUSCLE_GROUPS

logger = logging.getLogger(__name__)


def generate_program(goal_type: str, difficulty: str, focus_muscles: List[str]) -> Dict[str, Any]:
    """
    Generate a fitness program with weekly schedule.
    
    Args:
        goal_type: Type of goal (weight_loss, muscle_gain, endurance)
        difficulty: Difficulty level (beginner, intermediate, advanced)
        focus_muscles: List of primary muscle groups to focus on
    
    Returns:
        Dictionary with program structure
    """
    try:
        days = []
        
        for day_of_week in range(7):
            # Rest days: 0 (Monday), 3 (Thursday), 6 (Sunday)
            if day_of_week in [0, 3, 6]:
                days.append({
                    "day_of_week": day_of_week,
                    "rest_day": True,
                    "suggested_exercises": []
                })
            else:
                # Select exercises for this day
                selected_muscles = [focus_muscles[day_of_week % len(focus_muscles)]] if focus_muscles else ["chest"]
                exercises = get_suggested_exercises(selected_muscles[0], difficulty, count=5)
                
                days.append({
                    "day_of_week": day_of_week,
                    "rest_day": False,
                    "suggested_exercises": [
                        {
                            "exercise_id": e.exercise_id,
                            "name": e.name,
                            "primary_muscle": e.primary_muscle_group,
                            "difficulty": e.difficulty_level
                        }
                        for e in exercises
                    ]
                })
        
        return {"days": days}
    except Exception as e:
        logger.error(f"Error generating program: {str(e)}")
        return {"days": []}


def get_suggested_exercises(muscle_group: str, difficulty: str, count: int = 5) -> List[Exercise]:
    """
    Get suggested exercises for a muscle group and difficulty.
    
    Args:
        muscle_group: Primary muscle group
        difficulty: Difficulty level
        count: Number of exercises to return
    
    Returns:
        List of Exercise objects
    """
    try:
        exercises = Exercise.query.filter(
            Exercise.primary_muscle_group == muscle_group,
            Exercise.difficulty_level == difficulty
        ).limit(count).all()
        
        return exercises
    except Exception as e:
        logger.error(f"Error getting suggested exercises: {str(e)}")
        return []


def create_weekly_schedule(program: FitnessProgram) -> List[Dict[str, Any]]:
    """
    Create weekly schedule for a program.
    
    Args:
        program: FitnessProgram instance
    
    Returns:
        List of daily workout configurations
    """
    try:
        schedule = []
        focus_muscles = program.focus_muscle_groups or ["chest", "back", "legs"]
        difficulty = program.difficulty_level or "beginner"
        
        for day_of_week in range(7):
            # Rest days: 0 (Monday), 3 (Thursday), 6 (Sunday)
            if day_of_week in [0, 3, 6]:
                schedule.append({
                    "day_of_week": day_of_week,
                    "rest_day": True,
                    "suggested_exercises": []
                })
            else:
                # Select muscle group for this day
                if isinstance(focus_muscles, str):
                    # Handle JSON string
                    import json
                    try:
                        focus_muscles = json.loads(focus_muscles)
                    except:
                        focus_muscles = focus_muscles.split(",")
                
                selected_muscle = focus_muscles[day_of_week % len(focus_muscles)]
                exercises = get_suggested_exercises(selected_muscle, difficulty, count=5)
                
                schedule.append({
                    "day_of_week": day_of_week,
                    "rest_day": False,
                    "suggested_exercises": [
                        {
                            "exercise_id": e.exercise_id,
                            "name": e.name,
                            "primary_muscle": e.primary_muscle_group
                        }
                        for e in exercises
                    ]
                })
        
        return schedule
    except Exception as e:
        logger.error(f"Error creating weekly schedule: {str(e)}")
        return []


def balance_muscle_groups(focus_muscles: List[str], num_days: int = 7) -> List[str]:
    """
    Balance muscle groups across workout days.
    
    Args:
        focus_muscles: List of muscle groups
        num_days: Number of workout days
    
    Returns:
        List of muscle groups balanced across days
    """
    try:
        if not focus_muscles:
            focus_muscles = ["chest", "back", "legs"]
        
        balanced = []
        muscle_index = 0
        
        for _ in range(num_days):
            balanced.append(focus_muscles[muscle_index % len(focus_muscles)])
            muscle_index += 1
        
        return balanced
    except Exception as e:
        logger.error(f"Error balancing muscle groups: {str(e)}")
        return []
