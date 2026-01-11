"""
Database seeding script - Populate exercises in the database
Execute: python scripts/seed_exercises.py
"""
import os
import sys
import json
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import create_app
from app.database import db
from app.models import Exercise

def seed_exercises():
    """Seed the database with exercise data"""
    
    # Create app context
    app = create_app()
    
    with app.app_context():
        # Check if exercises already exist
        existing_count = Exercise.query.count()
        if existing_count > 0:
            print(f"✓ Database already contains {existing_count} exercises. Skipping seed.")
            return
        
        # Exercise data - 50+ exercises across 7 muscle groups
        exercises_data = [
            # Chest (5)
            {
                "name": "Barbell Bench Press",
                "description": "Classic chest exercise with barbell",
                "primary_muscle_group": "chest",
                "secondary_muscle_groups": ["shoulders", "triceps"],
                "difficulty_level": "beginner",
                "typical_calories_per_minute": 7.5
            },
            {
                "name": "Dumbbell Bench Press",
                "description": "Bench press variation using dumbbells",
                "primary_muscle_group": "chest",
                "secondary_muscle_groups": ["shoulders", "triceps"],
                "difficulty_level": "beginner",
                "typical_calories_per_minute": 6.8
            },
            {
                "name": "Incline Bench Press",
                "description": "Bench press on incline angle targeting upper chest",
                "primary_muscle_group": "chest",
                "secondary_muscle_groups": ["shoulders", "triceps"],
                "difficulty_level": "intermediate",
                "typical_calories_per_minute": 6.5
            },
            {
                "name": "Cable Fly",
                "description": "Chest isolation exercise using cable machine",
                "primary_muscle_group": "chest",
                "secondary_muscle_groups": ["shoulders"],
                "difficulty_level": "intermediate",
                "typical_calories_per_minute": 5.2
            },
            {
                "name": "Push-ups",
                "description": "Bodyweight chest exercise",
                "primary_muscle_group": "chest",
                "secondary_muscle_groups": ["shoulders", "triceps"],
                "difficulty_level": "beginner",
                "typical_calories_per_minute": 5.8
            },
            
            # Back (7)
            {
                "name": "Deadlift",
                "description": "Full body lift primarily targeting back",
                "primary_muscle_group": "back",
                "secondary_muscle_groups": ["legs", "core"],
                "difficulty_level": "advanced",
                "typical_calories_per_minute": 9.5
            },
            {
                "name": "Barbell Row",
                "description": "Back strength exercise with barbell",
                "primary_muscle_group": "back",
                "secondary_muscle_groups": ["biceps", "shoulders"],
                "difficulty_level": "intermediate",
                "typical_calories_per_minute": 8.2
            },
            {
                "name": "Lat Pulldown",
                "description": "Cable machine exercise for back width",
                "primary_muscle_group": "back",
                "secondary_muscle_groups": ["biceps", "shoulders"],
                "difficulty_level": "beginner",
                "typical_calories_per_minute": 6.5
            },
            {
                "name": "Pull-ups",
                "description": "Bodyweight back exercise",
                "primary_muscle_group": "back",
                "secondary_muscle_groups": ["biceps", "shoulders"],
                "difficulty_level": "intermediate",
                "typical_calories_per_minute": 8.0
            },
            {
                "name": "Assisted Pull-ups",
                "description": "Pull-ups with machine assistance",
                "primary_muscle_group": "back",
                "secondary_muscle_groups": ["biceps", "shoulders"],
                "difficulty_level": "beginner",
                "typical_calories_per_minute": 6.5
            },
            {
                "name": "Bent-over Row",
                "description": "Back exercise using dumbbells",
                "primary_muscle_group": "back",
                "secondary_muscle_groups": ["biceps", "shoulders"],
                "difficulty_level": "intermediate",
                "typical_calories_per_minute": 7.8
            },
            {
                "name": "Machine Row",
                "description": "Seated row on machine",
                "primary_muscle_group": "back",
                "secondary_muscle_groups": ["biceps"],
                "difficulty_level": "beginner",
                "typical_calories_per_minute": 6.0
            },
            
            # Legs (7)
            {
                "name": "Barbell Squat",
                "description": "Primary leg compound exercise",
                "primary_muscle_group": "legs",
                "secondary_muscle_groups": ["core", "back"],
                "difficulty_level": "intermediate",
                "typical_calories_per_minute": 9.0
            },
            {
                "name": "Leg Press",
                "description": "Machine-based leg exercise",
                "primary_muscle_group": "legs",
                "secondary_muscle_groups": ["glutes"],
                "difficulty_level": "beginner",
                "typical_calories_per_minute": 8.2
            },
            {
                "name": "Leg Curl",
                "description": "Isolation exercise for hamstrings",
                "primary_muscle_group": "legs",
                "secondary_muscle_groups": [],
                "difficulty_level": "beginner",
                "typical_calories_per_minute": 5.5
            },
            {
                "name": "Leg Extension",
                "description": "Isolation exercise for quadriceps",
                "primary_muscle_group": "legs",
                "secondary_muscle_groups": [],
                "difficulty_level": "beginner",
                "typical_calories_per_minute": 5.3
            },
            {
                "name": "Hack Squat",
                "description": "Machine squat variation",
                "primary_muscle_group": "legs",
                "secondary_muscle_groups": ["glutes"],
                "difficulty_level": "intermediate",
                "typical_calories_per_minute": 7.8
            },
            {
                "name": "Lunges",
                "description": "Single leg exercise",
                "primary_muscle_group": "legs",
                "secondary_muscle_groups": ["glutes"],
                "difficulty_level": "intermediate",
                "typical_calories_per_minute": 7.2
            },
            {
                "name": "Calf Raise",
                "description": "Isolation exercise for calves",
                "primary_muscle_group": "legs",
                "secondary_muscle_groups": [],
                "difficulty_level": "beginner",
                "typical_calories_per_minute": 4.5
            },
            
            # Shoulders (5)
            {
                "name": "Overhead Press",
                "description": "Standing shoulder press with barbell",
                "primary_muscle_group": "shoulders",
                "secondary_muscle_groups": ["triceps", "chest"],
                "difficulty_level": "intermediate",
                "typical_calories_per_minute": 7.5
            },
            {
                "name": "Lateral Raise",
                "description": "Isolation exercise for shoulder width",
                "primary_muscle_group": "shoulders",
                "secondary_muscle_groups": [],
                "difficulty_level": "beginner",
                "typical_calories_per_minute": 5.0
            },
            {
                "name": "Face Pull",
                "description": "Cable exercise for rear shoulders",
                "primary_muscle_group": "shoulders",
                "secondary_muscle_groups": ["back"],
                "difficulty_level": "beginner",
                "typical_calories_per_minute": 4.8
            },
            {
                "name": "Dumbbell Shoulder Press",
                "description": "Shoulder press with dumbbells",
                "primary_muscle_group": "shoulders",
                "secondary_muscle_groups": ["triceps", "chest"],
                "difficulty_level": "intermediate",
                "typical_calories_per_minute": 7.0
            },
            {
                "name": "Shrugs",
                "description": "Isolation exercise for trapezius",
                "primary_muscle_group": "shoulders",
                "secondary_muscle_groups": [],
                "difficulty_level": "beginner",
                "typical_calories_per_minute": 5.5
            },
            
            # Arms (6)
            {
                "name": "Barbell Curl",
                "description": "Primary bicep exercise",
                "primary_muscle_group": "arms",
                "secondary_muscle_groups": [],
                "difficulty_level": "beginner",
                "typical_calories_per_minute": 5.2
            },
            {
                "name": "Dumbbell Curl",
                "description": "Bicep isolation with dumbbells",
                "primary_muscle_group": "arms",
                "secondary_muscle_groups": [],
                "difficulty_level": "beginner",
                "typical_calories_per_minute": 5.0
            },
            {
                "name": "Tricep Dips",
                "description": "Bodyweight tricep exercise",
                "primary_muscle_group": "arms",
                "secondary_muscle_groups": ["chest", "shoulders"],
                "difficulty_level": "intermediate",
                "typical_calories_per_minute": 6.8
            },
            {
                "name": "Tricep Rope",
                "description": "Cable tricep exercise",
                "primary_muscle_group": "arms",
                "secondary_muscle_groups": [],
                "difficulty_level": "beginner",
                "typical_calories_per_minute": 5.0
            },
            {
                "name": "Hammer Curl",
                "description": "Bicep variation with neutral grip",
                "primary_muscle_group": "arms",
                "secondary_muscle_groups": [],
                "difficulty_level": "beginner",
                "typical_calories_per_minute": 5.0
            },
            {
                "name": "Close Grip Bench Press",
                "description": "Chest exercise targeting triceps",
                "primary_muscle_group": "arms",
                "secondary_muscle_groups": ["chest", "shoulders"],
                "difficulty_level": "intermediate",
                "typical_calories_per_minute": 7.2
            },
            
            # Cardio (5)
            {
                "name": "Treadmill",
                "description": "Running on treadmill machine",
                "primary_muscle_group": "cardio",
                "secondary_muscle_groups": ["legs"],
                "difficulty_level": "beginner",
                "typical_calories_per_minute": 8.5
            },
            {
                "name": "Elliptical",
                "description": "Low-impact cardio machine",
                "primary_muscle_group": "cardio",
                "secondary_muscle_groups": ["legs", "shoulders"],
                "difficulty_level": "beginner",
                "typical_calories_per_minute": 7.0
            },
            {
                "name": "Rowing Machine",
                "description": "Full body cardio and strength",
                "primary_muscle_group": "cardio",
                "secondary_muscle_groups": ["back", "legs"],
                "difficulty_level": "intermediate",
                "typical_calories_per_minute": 8.8
            },
            {
                "name": "Stationary Bike",
                "description": "Low-impact leg cardio",
                "primary_muscle_group": "cardio",
                "secondary_muscle_groups": ["legs"],
                "difficulty_level": "beginner",
                "typical_calories_per_minute": 7.2
            },
            {
                "name": "Jump Rope",
                "description": "Bodyweight cardio and coordination",
                "primary_muscle_group": "cardio",
                "secondary_muscle_groups": ["legs", "shoulders"],
                "difficulty_level": "intermediate",
                "typical_calories_per_minute": 9.5
            },
            
            # Core (5)
            {
                "name": "Plank",
                "description": "Isometric core exercise",
                "primary_muscle_group": "core",
                "secondary_muscle_groups": ["shoulders", "chest"],
                "difficulty_level": "beginner",
                "typical_calories_per_minute": 5.0
            },
            {
                "name": "Crunches",
                "description": "Abdominal isolation exercise",
                "primary_muscle_group": "core",
                "secondary_muscle_groups": [],
                "difficulty_level": "beginner",
                "typical_calories_per_minute": 4.2
            },
            {
                "name": "Leg Raises",
                "description": "Lower ab isolation exercise",
                "primary_muscle_group": "core",
                "secondary_muscle_groups": [],
                "difficulty_level": "intermediate",
                "typical_calories_per_minute": 5.5
            },
            {
                "name": "Cable Woodchop",
                "description": "Rotational core exercise",
                "primary_muscle_group": "core",
                "secondary_muscle_groups": ["shoulders"],
                "difficulty_level": "intermediate",
                "typical_calories_per_minute": 5.8
            },
            {
                "name": "Ab Wheel",
                "description": "Advanced core exercise",
                "primary_muscle_group": "core",
                "secondary_muscle_groups": ["shoulders", "back"],
                "difficulty_level": "advanced",
                "typical_calories_per_minute": 6.5
            }
        ]
        
        # Insert exercises into database
        print(f"\n{'='*60}")
        print(f"Seeding Exercises into Database")
        print(f"{'='*60}")
        
        import uuid
        for exercise_data in exercises_data:
            exercise = Exercise(
                exercise_id=str(uuid.uuid4()),
                name=exercise_data["name"],
                description=exercise_data["description"],
                primary_muscle_group=exercise_data["primary_muscle_group"],
                secondary_muscle_groups=json.dumps(exercise_data["secondary_muscle_groups"]),
                difficulty_level=exercise_data["difficulty_level"],
                typical_calories_per_minute=exercise_data["typical_calories_per_minute"]
            )
            db.session.add(exercise)
        
        # Commit to database
        try:
            db.session.commit()
            print(f"✓ Successfully seeded {len(exercises_data)} exercises")
            
            # Group by muscle
            muscle_counts = {}
            for ex_data in exercises_data:
                muscle = ex_data["primary_muscle_group"]
                muscle_counts[muscle] = muscle_counts.get(muscle, 0) + 1
            
            print(f"\nBreakdown by muscle group:")
            for muscle, count in sorted(muscle_counts.items()):
                print(f"  • {muscle.capitalize()}: {count} exercises")
            
            print(f"{'='*60}\n")
            
        except Exception as e:
            db.session.rollback()
            print(f"✗ Error seeding exercises: {str(e)}")
            print(f"{'='*60}\n")
            sys.exit(1)


if __name__ == '__main__':
    seed_exercises()
