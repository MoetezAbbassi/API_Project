import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Step 1: Delete old database
db_path = 'fitness_app.db'
if os.path.exists(db_path):
    os.remove(db_path)
    print(f"🗑️  Deleted old database\n")

# Step 2: Import Flask and create app
from flask import Flask
from app.extensions import db

print("📦 Creating app...\n")

# Create minimal app config
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///fitness_app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize db
db.init_app(app)

print("✅ App created\n")

# Step 3: Now import ALL models
print("📥 Importing models...\n")
with app.app_context():
    from app.models import (
        User, Goal, Exercise, Workout, WorkoutExercise,
        Meal, MealItem, FitnessProgram, ProgramWorkout,
        CalendarEvent, MLPrediction
    )
    
    print("✅ Models imported\n")
    
    # Step 4: Create all tables
    print("🔨 Creating tables...\n")
    db.create_all()
    
    # Step 5: Verify
    import sqlite3
    conn = sqlite3.connect('fitness_app.db')
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    
    print(f"✅ Created {len(tables)} tables:")
    for (table,) in tables:
        print(f"   ✅ {table}")
    
    conn.close()
    
    print("\n🎉 Database initialized successfully!")
    print("\n✅ Now run: python run.py")
