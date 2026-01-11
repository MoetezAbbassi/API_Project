import sqlite3
import uuid
from datetime import datetime

db_path = 'fitness_app.db'

print("🌱 Seeding exercises directly into SQLite...\n")

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

exercises = [
    # Chest
    ("Bench Press", "Classic chest exercise", "chest", '["shoulders", "triceps"]', "beginner", 8.5),
    ("Incline Bench Press", "Targets upper chest", "chest", '["shoulders"]', "intermediate", 8.0),
    ("Dumbbell Flyes", "Chest isolation exercise", "chest", '["shoulders"]', "intermediate", 6.5),
    ("Push-ups", "Bodyweight chest exercise", "chest", '["shoulders", "triceps"]', "beginner", 7.0),
    
    # Back
    ("Deadlift", "Full body compound lift", "back", '["legs", "core"]', "intermediate", 9.5),
    ("Bent Over Rows", "Back strengthening exercise", "back", '["biceps"]', "intermediate", 8.0),
    ("Pull-ups", "Bodyweight back exercise", "back", '["biceps"]', "intermediate", 9.0),
    ("Lat Pulldowns", "Machine back exercise", "back", '["biceps"]', "beginner", 6.5),
    
    # Legs
    ("Squat", "Fundamental leg exercise", "legs", '["core", "glutes"]', "beginner", 9.0),
    ("Leg Press", "Machine leg exercise", "legs", '["glutes"]', "beginner", 7.5),
    ("Lunges", "Single leg exercise", "legs", '["glutes", "core"]', "intermediate", 7.0),
    ("Leg Curls", "Hamstring isolation", "legs", '[]', "beginner", 5.5),
    
    # Shoulders
    ("Shoulder Press", "Standing overhead press", "shoulders", '["triceps", "chest"]', "intermediate", 8.5),
    ("Lateral Raises", "Shoulder isolation", "shoulders", '[]', "beginner", 4.5),
    ("Shrugs", "Trap exercise", "shoulders", '[]', "beginner", 3.5),
    
    # Arms
    ("Barbell Curls", "Bicep exercise", "biceps", '[]', "beginner", 5.0),
    ("Tricep Dips", "Tricep bodyweight exercise", "triceps", '["chest"]', "intermediate", 7.0),
    ("Tricep Extensions", "Tricep isolation", "triceps", '[]', "beginner", 4.5),
    
    # Core
    ("Planks", "Core stability", "core", '[]', "beginner", 4.0),
    ("Crunches", "Core exercise", "core", '[]', "beginner", 3.5),
    
    # Cardio
    ("Running", "Cardio exercise", "cardio", '["legs"]', "beginner", 12.0),
    ("Cycling", "Low impact cardio", "cardio", '["legs"]', "beginner", 10.0),
]

now = datetime.utcnow().isoformat()

for name, desc, muscle, secondary, difficulty, calories in exercises:
    exercise_id = str(uuid.uuid4())
    cursor.execute('''
        INSERT INTO exercises (exercise_id, name, description, primary_muscle_group, secondary_muscle_groups, difficulty_level, typical_calories_per_minute, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (exercise_id, name, desc, muscle, secondary, difficulty, calories, now))

conn.commit()

# Verify
cursor.execute("SELECT COUNT(*) FROM exercises")
count = cursor.fetchone()[0]

print(f"✅ Seeded {count} exercises!\n")

# Show by muscle group
cursor.execute('''
    SELECT primary_muscle_group, COUNT(*) as count 
    FROM exercises 
    GROUP BY primary_muscle_group 
    ORDER BY count DESC
''')

print("📊 Exercises by muscle group:")
for muscle, cnt in cursor.fetchall():
    print(f"   {muscle.capitalize()}: {cnt}")

conn.close()

print("\n✅ Seeding complete! Restart Flask and test.")
