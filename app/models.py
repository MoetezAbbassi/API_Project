from app.extensions import db
from datetime import datetime, timezone
from uuid import uuid4
import json


class User(db.Model):
    __tablename__ = 'users'
    
    user_id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid4()))
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    age = db.Column(db.Float, nullable=True)
    current_weight = db.Column(db.Float, nullable=True)
    height = db.Column(db.Float, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    goals = db.relationship('Goal', back_populates='user', cascade='all, delete-orphan')
    workouts = db.relationship('Workout', back_populates='user', cascade='all, delete-orphan')
    meals = db.relationship('Meal', back_populates='user', cascade='all, delete-orphan')
    programs = db.relationship('FitnessProgram', back_populates='user', cascade='all, delete-orphan')
    calendar_events = db.relationship('CalendarEvent', back_populates='user', cascade='all, delete-orphan')
    ml_predictions = db.relationship('MLPrediction', back_populates='user', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<User {self.username}>'


class Goal(db.Model):
    __tablename__ = 'goals'
    
    goal_id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.user_id'), nullable=False)
    goal_type = db.Column(db.String(50), nullable=False)  # weight_loss, muscle_gain, endurance
    target_value = db.Column(db.Float, nullable=False)
    target_unit = db.Column(db.String(50), nullable=False)
    current_progress = db.Column(db.Float, default=0)
    target_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(50), default='active')  # active, completed, abandoned
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    user = db.relationship('User', back_populates='goals')
    
    def __repr__(self):
        return f'<Goal {self.goal_type}>'


class Exercise(db.Model):
    __tablename__ = 'exercises'
    
    exercise_id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid4()))
    name = db.Column(db.String(120), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=True)
    primary_muscle_group = db.Column(db.String(50), nullable=False)
    secondary_muscle_groups = db.Column(db.Text, nullable=True)  # JSON string
    difficulty_level = db.Column(db.String(50), nullable=False)  # beginner, intermediate, advanced
    typical_calories_per_minute = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    
    # Relationships
    workout_exercises = db.relationship('WorkoutExercise', back_populates='exercise', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Exercise {self.name}>'


class Workout(db.Model):
    __tablename__ = 'workouts'
    
    workout_id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.user_id'), nullable=False)
    workout_date = db.Column(db.Date, nullable=False, default=lambda: datetime.now(timezone.utc).date())
    workout_type = db.Column(db.String(50), nullable=False)  # strength, cardio, flexibility, mixed
    status = db.Column(db.String(50), default='in_progress')  # in_progress, completed, cancelled
    total_duration_minutes = db.Column(db.Integer, nullable=True)
    total_calories_burned = db.Column(db.Float, default=0)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    completed_at = db.Column(db.DateTime, nullable=True)
    
    # Relationships
    user = db.relationship('User', back_populates='workouts')
    workout_exercises = db.relationship('WorkoutExercise', back_populates='workout', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Workout {self.workout_id}>'


class WorkoutExercise(db.Model):
    __tablename__ = 'workout_exercises'
    
    workout_exercise_id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid4()))
    workout_id = db.Column(db.String(36), db.ForeignKey('workouts.workout_id'), nullable=False)
    exercise_id = db.Column(db.String(36), db.ForeignKey('exercises.exercise_id'), nullable=False)
    sets = db.Column(db.Integer, nullable=True)
    reps = db.Column(db.Integer, nullable=True)
    weight_used = db.Column(db.Float, nullable=True)
    weight_unit = db.Column(db.String(20), nullable=True)  # kg, lbs
    duration_seconds = db.Column(db.Integer, nullable=True)
    calories_burned = db.Column(db.Float, default=0)
    order_in_workout = db.Column(db.Integer, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    
    # Relationships
    workout = db.relationship('Workout', back_populates='workout_exercises')
    exercise = db.relationship('Exercise', back_populates='workout_exercises')
    
    def __repr__(self):
        return f'<WorkoutExercise {self.exercise_id}>'


class Meal(db.Model):
    __tablename__ = 'meals'
    
    meal_id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.user_id'), nullable=False)
    meal_type = db.Column(db.String(50), nullable=False)  # breakfast, lunch, dinner, snack
    meal_date = db.Column(db.Date, nullable=False, default=lambda: datetime.now(timezone.utc).date())
    total_calories = db.Column(db.Float, default=0)
    protein_g = db.Column(db.Float, default=0)
    carbs_g = db.Column(db.Float, default=0)
    fats_g = db.Column(db.Float, default=0)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    
    # Relationships
    user = db.relationship('User', back_populates='meals')
    meal_items = db.relationship('MealItem', back_populates='meal', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Meal {self.meal_type}>'


class MealItem(db.Model):
    __tablename__ = 'meal_items'
    
    meal_item_id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid4()))
    meal_id = db.Column(db.String(36), db.ForeignKey('meals.meal_id'), nullable=False)
    food_name = db.Column(db.String(120), nullable=False)
    quantity = db.Column(db.Float, nullable=False)
    quantity_unit = db.Column(db.String(50), nullable=False)
    calories = db.Column(db.Float, default=0)
    protein_g = db.Column(db.Float, default=0)
    carbs_g = db.Column(db.Float, default=0)
    fats_g = db.Column(db.Float, default=0)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    
    # Relationships
    meal = db.relationship('Meal', back_populates='meal_items')
    
    def __repr__(self):
        return f'<MealItem {self.food_name}>'


class FitnessProgram(db.Model):
    __tablename__ = 'fitness_programs'
    
    program_id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.user_id'), nullable=False)
    goal_id = db.Column(db.String(36), db.ForeignKey('goals.goal_id'), nullable=True)
    program_name = db.Column(db.String(120), nullable=False)
    duration_weeks = db.Column(db.Integer, nullable=False)
    focus_muscle_groups = db.Column(db.Text, nullable=True)  # JSON string
    difficulty_level = db.Column(db.String(50), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    
    # Relationships
    user = db.relationship('User', back_populates='programs')
    program_workouts = db.relationship('ProgramWorkout', back_populates='program', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<FitnessProgram {self.program_name}>'


class ProgramWorkout(db.Model):
    __tablename__ = 'program_workouts'
    
    program_workout_id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid4()))
    program_id = db.Column(db.String(36), db.ForeignKey('fitness_programs.program_id'), nullable=False)
    day_of_week = db.Column(db.Integer, nullable=False)  # 0-6
    rest_day = db.Column(db.Boolean, default=False)
    suggested_exercises = db.Column(db.Text, nullable=True)  # JSON string
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    
    # Relationships
    program = db.relationship('FitnessProgram', back_populates='program_workouts')
    
    def __repr__(self):
        return f'<ProgramWorkout day_{self.day_of_week}>'


class CalendarEvent(db.Model):
    __tablename__ = 'calendar_events'
    
    event_id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.user_id'), nullable=False)
    event_date = db.Column(db.Date, nullable=False)
    event_type = db.Column(db.String(50), nullable=False)
    event_title = db.Column(db.String(120), nullable=False)
    related_id = db.Column(db.String(36), nullable=True)
    event_details = db.Column(db.Text, nullable=True)  # JSON string
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    
    # Relationships
    user = db.relationship('User', back_populates='calendar_events')
    
    def __repr__(self):
        return f'<CalendarEvent {self.event_type}>'


class MLPrediction(db.Model):
    __tablename__ = 'ml_predictions'
    
    prediction_id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.user_id'), nullable=False)
    image_file_path = db.Column(db.String(255), nullable=False)
    equipment_name = db.Column(db.String(120), nullable=True)
    confidence_score = db.Column(db.Float, nullable=True)
    suggested_exercises = db.Column(db.Text, nullable=True)  # JSON string
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    
    # Relationships
    user = db.relationship('User', back_populates='ml_predictions')
    
    def __repr__(self):
        return f'<MLPrediction {self.equipment_name}>'
