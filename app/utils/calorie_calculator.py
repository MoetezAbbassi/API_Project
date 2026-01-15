"""
Calorie Calculator - Estimates calories burned based on exercise properties
Uses research-backed values for different exercise types
"""

# Calories per minute for different exercise types and difficulty levels
# Based on research and fitness industry standards
CALORIE_ESTIMATES = {
    # STRENGTH/RESISTANCE TRAINING
    'strength': {
        'beginner': 4.0,      # Light dumbbells, machine weights
        'intermediate': 6.0,  # Moderate weights, compound movements
        'advanced': 8.0       # Heavy weights, explosive movements
    },
    # CARDIO
    'cardio': {
        'beginner': 6.0,      # Walking, light jogging
        'intermediate': 10.0, # Running, moderate pace
        'advanced': 15.0      # Sprinting, high intensity
    },
    # FLEXIBILITY/MOBILITY
    'flexibility': {
        'beginner': 2.5,      # Stretching, light yoga
        'intermediate': 3.5,  # Vinyasa yoga, mobility work
        'advanced': 5.0       # Power yoga, intense flow
    },
    # HIIT (High Intensity Interval Training)
    'hiit': {
        'beginner': 10.0,     # Light intervals
        'intermediate': 14.0, # Moderate intensity intervals
        'advanced': 18.0      # Maximum intensity intervals
    },
    # MIXED/GENERAL
    'mixed': {
        'beginner': 5.0,
        'intermediate': 7.0,
        'advanced': 9.0
    }
}

# Muscle group adjustments (multipliers)
MUSCLE_GROUP_MULTIPLIERS = {
    'chest': 1.0,
    'back': 1.05,
    'legs': 1.2,           # Larger muscle group = more calories
    'shoulders': 0.95,
    'biceps': 0.85,        # Smaller muscle groups
    'triceps': 0.85,
    'forearms': 0.8,
    'core': 1.1,           # Core engagement increases calorie burn
    'glutes': 1.15,        # Large muscle group
    'hamstrings': 1.15,
    'quadriceps': 1.15,
    'calves': 0.9,
    'full_body': 1.3,      # Full body workouts burn more
    'cardio': 1.0
}

def estimate_calories_per_minute(exercise_type: str, difficulty: str, muscle_group: str = None) -> float:
    """
    Estimate calories burned per minute for an exercise
    
    Args:
        exercise_type: 'strength', 'cardio', 'flexibility', 'hiit', 'mixed'
        difficulty: 'beginner', 'intermediate', 'advanced'
        muscle_group: primary muscle group (optional multiplier)
    
    Returns:
        Estimated calories per minute (float)
    """
    # Normalize inputs
    exercise_type = exercise_type.lower().strip()
    difficulty = difficulty.lower().strip()
    
    # Default to 'mixed' if invalid type
    if exercise_type not in CALORIE_ESTIMATES:
        exercise_type = 'mixed'
    
    # Default to 'intermediate' if invalid difficulty
    if difficulty not in CALORIE_ESTIMATES[exercise_type]:
        difficulty = 'intermediate'
    
    # Get base calories per minute
    base_calories = CALORIE_ESTIMATES[exercise_type][difficulty]
    
    # Apply muscle group multiplier if provided
    if muscle_group:
        muscle_group = muscle_group.lower().strip()
        multiplier = MUSCLE_GROUP_MULTIPLIERS.get(muscle_group, 1.0)
        base_calories *= multiplier
    
    # Round to 1 decimal place
    return round(base_calories, 1)


def calculate_calories_burned(calories_per_minute: float, duration_minutes: int) -> float:
    """
    Calculate total calories burned
    
    Args:
        calories_per_minute: Rate of calorie burn
        duration_minutes: Duration of exercise in minutes
    
    Returns:
        Total calories burned (float)
    """
    if duration_minutes <= 0:
        return 0.0
    return round(calories_per_minute * duration_minutes, 1)


# Exercise database with realistic calorie values
EXERCISE_DATABASE = {
    # STRENGTH - Chest
    'Barbell Bench Press': {'type': 'strength', 'difficulty': 'intermediate', 'muscle': 'chest', 'calories': 6.5},
    'Dumbbell Bench Press': {'type': 'strength', 'difficulty': 'intermediate', 'muscle': 'chest', 'calories': 6.0},
    'Push-ups': {'type': 'strength', 'difficulty': 'beginner', 'muscle': 'chest', 'calories': 4.5},
    'Chest Fly Machine': {'type': 'strength', 'difficulty': 'beginner', 'muscle': 'chest', 'calories': 3.5},
    'Incline Bench Press': {'type': 'strength', 'difficulty': 'intermediate', 'muscle': 'chest', 'calories': 6.0},
    
    # STRENGTH - Back
    'Barbell Rows': {'type': 'strength', 'difficulty': 'intermediate', 'muscle': 'back', 'calories': 7.0},
    'Pull-ups': {'type': 'strength', 'difficulty': 'advanced', 'muscle': 'back', 'calories': 8.5},
    'Lat Pulldown': {'type': 'strength', 'difficulty': 'beginner', 'muscle': 'back', 'calories': 4.5},
    'Deadlifts': {'type': 'strength', 'difficulty': 'advanced', 'muscle': 'back', 'calories': 9.0},
    'Rowing Machine': {'type': 'cardio', 'difficulty': 'intermediate', 'muscle': 'back', 'calories': 10.0},
    
    # STRENGTH - Legs
    'Squats': {'type': 'strength', 'difficulty': 'intermediate', 'muscle': 'legs', 'calories': 8.0},
    'Leg Press': {'type': 'strength', 'difficulty': 'beginner', 'muscle': 'legs', 'calories': 6.5},
    'Lunges': {'type': 'strength', 'difficulty': 'intermediate', 'muscle': 'legs', 'calories': 7.5},
    'Leg Curl': {'type': 'strength', 'difficulty': 'beginner', 'muscle': 'legs', 'calories': 4.0},
    'Leg Extension': {'type': 'strength', 'difficulty': 'beginner', 'muscle': 'legs', 'calories': 4.0},
    'Calf Raises': {'type': 'strength', 'difficulty': 'beginner', 'muscle': 'calves', 'calories': 2.5},
    
    # STRENGTH - Shoulders
    'Shoulder Press': {'type': 'strength', 'difficulty': 'intermediate', 'muscle': 'shoulders', 'calories': 6.0},
    'Lateral Raises': {'type': 'strength', 'difficulty': 'beginner', 'muscle': 'shoulders', 'calories': 3.5},
    'Military Press': {'type': 'strength', 'difficulty': 'advanced', 'muscle': 'shoulders', 'calories': 7.5},
    
    # STRENGTH - Arms
    'Barbell Curls': {'type': 'strength', 'difficulty': 'intermediate', 'muscle': 'biceps', 'calories': 4.5},
    'Dumbbell Curls': {'type': 'strength', 'difficulty': 'beginner', 'muscle': 'biceps', 'calories': 3.5},
    'Tricep Dips': {'type': 'strength', 'difficulty': 'intermediate', 'muscle': 'triceps', 'calories': 5.0},
    'Tricep Pushdown': {'type': 'strength', 'difficulty': 'beginner', 'muscle': 'triceps', 'calories': 3.0},
    
    # STRENGTH - Core
    'Plank': {'type': 'strength', 'difficulty': 'intermediate', 'muscle': 'core', 'calories': 3.5},
    'Crunches': {'type': 'strength', 'difficulty': 'beginner', 'muscle': 'core', 'calories': 2.5},
    'Russian Twists': {'type': 'strength', 'difficulty': 'intermediate', 'muscle': 'core', 'calories': 4.0},
    'Ab Wheel': {'type': 'strength', 'difficulty': 'advanced', 'muscle': 'core', 'calories': 5.5},
    
    # CARDIO
    'Running': {'type': 'cardio', 'difficulty': 'intermediate', 'muscle': 'cardio', 'calories': 12.0},
    'Sprinting': {'type': 'cardio', 'difficulty': 'advanced', 'muscle': 'cardio', 'calories': 18.0},
    'Jogging': {'type': 'cardio', 'difficulty': 'beginner', 'muscle': 'cardio', 'calories': 8.0},
    'Walking': {'type': 'cardio', 'difficulty': 'beginner', 'muscle': 'cardio', 'calories': 4.0},
    'Cycling': {'type': 'cardio', 'difficulty': 'intermediate', 'muscle': 'cardio', 'calories': 10.0},
    'Stationary Bike': {'type': 'cardio', 'difficulty': 'intermediate', 'muscle': 'cardio', 'calories': 9.0},
    'Treadmill': {'type': 'cardio', 'difficulty': 'beginner', 'muscle': 'cardio', 'calories': 9.0},
    'Jump Rope': {'type': 'cardio', 'difficulty': 'intermediate', 'muscle': 'cardio', 'calories': 12.0},
    'Swimming': {'type': 'cardio', 'difficulty': 'intermediate', 'muscle': 'full_body', 'calories': 11.0},
    'Elliptical': {'type': 'cardio', 'difficulty': 'beginner', 'muscle': 'cardio', 'calories': 7.0},
    
    # HIIT
    'Burpees': {'type': 'hiit', 'difficulty': 'advanced', 'muscle': 'full_body', 'calories': 16.0},
    'Mountain Climbers': {'type': 'hiit', 'difficulty': 'intermediate', 'muscle': 'core', 'calories': 10.0},
    'Jump Squats': {'type': 'hiit', 'difficulty': 'intermediate', 'muscle': 'legs', 'calories': 12.0},
    'Jumping Jacks': {'type': 'hiit', 'difficulty': 'beginner', 'muscle': 'cardio', 'calories': 8.0},
    'Box Jumps': {'type': 'hiit', 'difficulty': 'advanced', 'muscle': 'legs', 'calories': 14.0},
    
    # FLEXIBILITY
    'Yoga': {'type': 'flexibility', 'difficulty': 'intermediate', 'muscle': 'full_body', 'calories': 3.5},
    'Stretching': {'type': 'flexibility', 'difficulty': 'beginner', 'muscle': 'full_body', 'calories': 2.5},
    'Pilates': {'type': 'flexibility', 'difficulty': 'intermediate', 'muscle': 'core', 'calories': 4.0},
}


def get_calories_for_exercise(exercise_name: str) -> float:
    """
    Get calories per minute for a known exercise
    
    Args:
        exercise_name: Name of the exercise
    
    Returns:
        Calories per minute if found, else None
    """
    if exercise_name in EXERCISE_DATABASE:
        return EXERCISE_DATABASE[exercise_name]['calories']
    return None
