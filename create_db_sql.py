import sqlite3
import os

db_path = 'fitness_app.db'

# Delete old empty database
if os.path.exists(db_path):
    os.remove(db_path)
    print("🗑️  Deleted empty database\n")

print("🔨 Creating database with raw SQL...\n")

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Create all tables with exact schema
cursor.executescript('''
CREATE TABLE users (
    user_id VARCHAR(36) PRIMARY KEY,
    username VARCHAR(80) UNIQUE NOT NULL,
    email VARCHAR(120) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    age FLOAT,
    current_weight FLOAT,
    height FLOAT,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL
);

CREATE TABLE goals (
    goal_id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL,
    goal_type VARCHAR(50) NOT NULL,
    target_value FLOAT NOT NULL,
    target_unit VARCHAR(50) NOT NULL,
    current_progress FLOAT DEFAULT 0,
    target_date DATE NOT NULL,
    status VARCHAR(50) DEFAULT 'active',
    description TEXT,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,
    FOREIGN KEY(user_id) REFERENCES users(user_id)
);

CREATE TABLE exercises (
    exercise_id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(120) UNIQUE NOT NULL,
    description TEXT,
    primary_muscle_group VARCHAR(50) NOT NULL,
    secondary_muscle_groups TEXT,
    difficulty_level VARCHAR(50) NOT NULL,
    typical_calories_per_minute FLOAT NOT NULL,
    created_at DATETIME NOT NULL
);

CREATE TABLE workouts (
    workout_id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL,
    workout_date DATE NOT NULL,
    workout_type VARCHAR(50) NOT NULL,
    status VARCHAR(50) DEFAULT 'in_progress',
    total_duration_minutes INTEGER,
    total_calories_burned FLOAT DEFAULT 0,
    notes TEXT,
    created_at DATETIME NOT NULL,
    completed_at DATETIME,
    FOREIGN KEY(user_id) REFERENCES users(user_id)
);

CREATE TABLE workout_exercises (
    workout_exercise_id VARCHAR(36) PRIMARY KEY,
    workout_id VARCHAR(36) NOT NULL,
    exercise_id VARCHAR(36) NOT NULL,
    sets INTEGER,
    reps INTEGER,
    weight_used FLOAT,
    weight_unit VARCHAR(20),
    duration_seconds INTEGER,
    calories_burned FLOAT DEFAULT 0,
    order_in_workout INTEGER,
    created_at DATETIME NOT NULL,
    FOREIGN KEY(workout_id) REFERENCES workouts(workout_id),
    FOREIGN KEY(exercise_id) REFERENCES exercises(exercise_id)
);

CREATE TABLE meals (
    meal_id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL,
    meal_type VARCHAR(50) NOT NULL,
    meal_date DATE NOT NULL,
    total_calories FLOAT DEFAULT 0,
    protein_g FLOAT DEFAULT 0,
    carbs_g FLOAT DEFAULT 0,
    fats_g FLOAT DEFAULT 0,
    notes TEXT,
    created_at DATETIME NOT NULL,
    FOREIGN KEY(user_id) REFERENCES users(user_id)
);

CREATE TABLE meal_items (
    meal_item_id VARCHAR(36) PRIMARY KEY,
    meal_id VARCHAR(36) NOT NULL,
    food_name VARCHAR(120) NOT NULL,
    quantity FLOAT NOT NULL,
    quantity_unit VARCHAR(50) NOT NULL,
    calories FLOAT DEFAULT 0,
    protein_g FLOAT DEFAULT 0,
    carbs_g FLOAT DEFAULT 0,
    fats_g FLOAT DEFAULT 0,
    created_at DATETIME NOT NULL,
    FOREIGN KEY(meal_id) REFERENCES meals(meal_id)
);

CREATE TABLE fitness_programs (
    program_id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL,
    goal_id VARCHAR(36),
    program_name VARCHAR(120) NOT NULL,
    duration_weeks INTEGER NOT NULL,
    focus_muscle_groups TEXT,
    difficulty_level VARCHAR(50) NOT NULL,
    created_at DATETIME NOT NULL,
    FOREIGN KEY(user_id) REFERENCES users(user_id),
    FOREIGN KEY(goal_id) REFERENCES goals(goal_id)
);

CREATE TABLE program_workouts (
    program_workout_id VARCHAR(36) PRIMARY KEY,
    program_id VARCHAR(36) NOT NULL,
    day_of_week INTEGER NOT NULL,
    rest_day BOOLEAN DEFAULT 0,
    suggested_exercises TEXT,
    created_at DATETIME NOT NULL,
    FOREIGN KEY(program_id) REFERENCES fitness_programs(program_id)
);

CREATE TABLE calendar_events (
    event_id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL,
    event_date DATE NOT NULL,
    event_type VARCHAR(50) NOT NULL,
    event_title VARCHAR(120) NOT NULL,
    related_id VARCHAR(36),
    event_details TEXT,
    created_at DATETIME NOT NULL,
    FOREIGN KEY(user_id) REFERENCES users(user_id)
);

CREATE TABLE ml_predictions (
    prediction_id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL,
    image_file_path VARCHAR(255) NOT NULL,
    equipment_name VARCHAR(120),
    confidence_score FLOAT,
    suggested_exercises TEXT,
    created_at DATETIME NOT NULL,
    FOREIGN KEY(user_id) REFERENCES users(user_id)
);
''')

conn.commit()

# Verify
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()

print(f"✅ Created {len(tables)} tables:")
for (table,) in tables:
    print(f"   ✅ {table}")

conn.close()

print("\n🎉 Database created successfully!")
print("✅ Now seed exercises and restart Flask")
