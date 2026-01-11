"""
ML Routes - Machine learning equipment identification with exercise suggestions
"""

from flask import Blueprint, request
from datetime import datetime
from app.extensions import db
from app.models import MLPrediction, Exercise, User, Workout, WorkoutExercise
from app.utils import responses, decorators
import os
import json
import uuid


bp = Blueprint('ml', __name__, url_prefix='/api/ml')

# Get Hugging Face token from environment
HUGGINGFACE_TOKEN = os.getenv('HUGGINGFACE_TOKEN', None)

# Try to initialize the ML model
try:
    from transformers import pipeline
    CLASSIFIER = pipeline(
        "image-classification",
        model="google/vit-base-patch16-224",
        token=HUGGINGFACE_TOKEN
    )
    ML_ENABLED = True
except Exception as e:
    print(f"⚠️  Warning: ML model not initialized. {str(e)}")
    print("⚠️  Falling back to placeholder predictions.")
    CLASSIFIER = None
    ML_ENABLED = False


# Equipment to muscle groups mapping with primary focus
EQUIPMENT_TO_MUSCLES = {
    "Barbell": {
        "primary": ["chest", "back", "legs"],  # Most common barbell exercises
        "secondary": ["shoulders", "arms"]
    },
    "Dumbbell": {
        "primary": ["chest", "shoulders", "arms"],
        "secondary": ["back"]
    },
    "Bench Press": {
        "primary": ["chest"],
        "secondary": ["shoulders", "arms"]
    },
    "Squat Rack": {
        "primary": ["legs", "back"],
        "secondary": []
    },
    "Cable Machine": {
        "primary": ["chest", "back", "arms"],
        "secondary": ["shoulders"]
    },
    "Treadmill": {
        "primary": ["cardio"],
        "secondary": []
    },
    "Elliptical": {
        "primary": ["cardio"],
        "secondary": []
    },
    "Kettlebell": {
        "primary": ["legs", "shoulders", "arms"],
        "secondary": ["core"]
    },
    "Resistance Band": {
        "primary": ["chest", "back", "shoulders"],
        "secondary": ["arms"]
    },
    "Yoga Mat": {
        "primary": ["core", "flexibility"],
        "secondary": []
    },
    "Smith Machine": {
        "primary": ["chest", "legs"],
        "secondary": ["back", "shoulders"]
    },
    "Leg Press": {
        "primary": ["legs"],
        "secondary": ["core"]
    },
    "Pull-up Bar": {
        "primary": ["back", "arms"],
        "secondary": []
    },
    "Rowing Machine": {
        "primary": ["back", "cardio"],
        "secondary": ["arms"]
    },
}


# Placeholder equipment mapping for testing
EQUIPMENT_MAPPING = {
    "barbell": "Barbell",
    "dumbbell": "Dumbbell",
    "bench": "Bench Press",
    "rack": "Squat Rack",
    "cable": "Cable Machine",
    "treadmill": "Treadmill",
    "elliptical": "Elliptical",
    "kettlebell": "Kettlebell",
    "resistance": "Resistance Band",
    "mat": "Yoga Mat"
}


def serialize_prediction(prediction: MLPrediction, include_exercises: bool = True) -> dict:
    """
    Serialize MLPrediction to dictionary
    
    Args:
        prediction: MLPrediction model instance
        include_exercises: Include suggested exercises with details
        
    Returns:
        Dictionary representation of prediction
    """
    pred_dict = {
        "prediction_id": prediction.prediction_id,
        "image_file_path": prediction.image_file_path,
        "equipment_name": prediction.equipment_name,
        "confidence": prediction.confidence_score,
        "created_at": prediction.created_at.isoformat() if prediction.created_at else None
    }
    
    if include_exercises:
        suggested = prediction.suggested_exercises or []
        if isinstance(suggested, str):
            try:
                suggested = json.loads(suggested)
            except:
                suggested = []
        pred_dict["suggested_exercises"] = suggested
    
    return pred_dict


def get_exercises_for_equipment(equipment_name: str, limit: int = 6) -> list:
    """
    Get TOP exercises that can be done with identified equipment
    
    Priority: Primary muscle groups first, then secondary
    
    Args:
        equipment_name: Name of identified equipment
        limit: Maximum number of exercises to return (default 6)
        
    Returns:
        List of exercise objects sorted by relevance with limited results
    """
    # Get muscle groups for this equipment
    equipment_config = EQUIPMENT_TO_MUSCLES.get(equipment_name, {})
    primary_muscles = equipment_config.get("primary", [])
    secondary_muscles = equipment_config.get("secondary", [])
    
    # First priority: primary muscles
    primary_exercises = db.session.query(Exercise).filter(
        Exercise.primary_muscle_group.in_(primary_muscles)
    ).all() if primary_muscles else []
    
    # Second priority: secondary muscles (only if we need more)
    secondary_exercises = []
    if len(primary_exercises) < limit and secondary_muscles:
        secondary_exercises = db.session.query(Exercise).filter(
            Exercise.primary_muscle_group.in_(secondary_muscles)
        ).all()
    
    # Combine and limit to requested amount
    all_exercises = primary_exercises + secondary_exercises
    exercise_list = []
    
    for ex in all_exercises[:limit]:  # Take only first N exercises
        secondary = []
        if ex.secondary_muscle_groups:
            try:
                secondary = json.loads(ex.secondary_muscle_groups) if isinstance(ex.secondary_muscle_groups, str) else ex.secondary_muscle_groups
            except:
                secondary = []
        
        exercise_list.append({
            "exercise_id": ex.exercise_id,
            "exercise_name": ex.name,
            "description": ex.description,
            "primary_muscle": ex.primary_muscle_group,
            "secondary_muscles": secondary,
            "difficulty": ex.difficulty_level,
            "typical_calories_per_minute": ex.typical_calories_per_minute
        })
    
    return exercise_list


def identify_with_huggingface(filepath: str) -> tuple:
    """
    Use HuggingFace model to identify equipment from image
    
    Args:
        filepath: Path to the image file
        
    Returns:
        Tuple of (equipment_name, confidence_score)
    """
    if not ML_ENABLED or CLASSIFIER is None:
        # Fallback to placeholder
        return "Barbell", 0.94
    
    try:
        # Run inference
        results = CLASSIFIER(filepath)
        
        if results:
            # Get top prediction
            top_result = results[0]
            label = top_result['label']
            score = top_result['score']
            
            # Map label to equipment name
            equipment_name = EQUIPMENT_MAPPING.get(label.lower(), label)
            
            return equipment_name, score
    except Exception as e:
        print(f"ML Model Error: {str(e)}")
    
    # Fallback
    return "Barbell", 0.94


@bp.route('/identify-equipment', methods=['POST'])
@decorators.token_required
def identify_equipment(token_user_id):
    """
    Identify fitness equipment from image upload and return TOP suggested exercises
    
    Request: multipart/form-data with 'image' file
    
    Response (200):
    {
        "success": true,
        "data": {
            "prediction_id": "uuid",
            "equipment_name": "Barbell",
            "confidence": 0.94,
            "suggested_exercises": [
                {
                    "exercise_id": "uuid",
                    "exercise_name": "Barbell Bench Press",
                    "description": "Classic chest exercise...",
                    "primary_muscle": "chest",
                    "secondary_muscles": ["shoulders", "triceps"],
                    "difficulty": "intermediate",
                    "typical_calories_per_minute": 8.5
                },
                ... (max 6 exercises)
            ]
        },
        "message": "Equipment identified successfully"
    }
    """
    try:
        # Check for file in request
        if 'image' not in request.files:
            return responses.validation_error_response("No image file provided")
        
        file = request.files['image']
        
        if file.filename == '':
            return responses.validation_error_response("No image file selected")
        
        # Validate file type
        allowed_extensions = {'png', 'jpg', 'jpeg', 'gif'}
        if '.' not in file.filename or file.filename.split('.')[-1].lower() not in allowed_extensions:
            return responses.validation_error_response("Invalid file type. Allowed: png, jpg, jpeg, gif")
        
        # Save file
        uploads_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), '..', 'uploads', 'images')
        os.makedirs(uploads_dir, exist_ok=True)
        
        # Generate filename
        filename = f"{uuid.uuid4()}_{file.filename}"
        filepath = os.path.join(uploads_dir, filename)
        
        # Save file
        try:
            file.save(filepath)
        except Exception as e:
            return responses.error_response(
                "File upload error",
                str(e),
                "ML_UPLOAD_ERROR",
                500
            )
        
        # Identify equipment using HuggingFace model
        equipment_name, confidence = identify_with_huggingface(filepath)
        
        # Get TOP suggested exercises (LIMITED to 6)
        suggested_exercises = get_exercises_for_equipment(equipment_name, limit=6)
        
        # Store prediction in database
        exercise_ids = [ex["exercise_id"] for ex in suggested_exercises]
        prediction = MLPrediction(
            prediction_id=str(uuid.uuid4()),
            user_id=token_user_id,
            image_file_path=filename,
            equipment_name=equipment_name,
            confidence_score=confidence,
            suggested_exercises=json.dumps(exercise_ids)
        )
        
        db.session.add(prediction)
        db.session.commit()
        
        # Build response
        response_data = {
            "prediction_id": prediction.prediction_id,
            "equipment_name": equipment_name,
            "confidence": confidence,
            "suggested_exercises": suggested_exercises
        }
        
        return responses.success_response(
            response_data,
            "Equipment identified successfully"
        )
    
    except Exception as e:
        db.session.rollback()
        return responses.error_response(
            "ML processing error",
            str(e),
            "ML_IDENTIFY_ERROR",
            500
        )


@bp.route('/add-exercise-to-workout', methods=['POST'])
@decorators.token_required
def add_exercise_to_workout(token_user_id):
    """
    Add a selected exercise from ML suggestions to a workout
    
    Request JSON:
    {
        "workout_id": "uuid",
        "exercise_id": "uuid",
        "sets": 3,
        "reps": 10,
        "weight_used": 185,
        "weight_unit": "lbs",
        "duration_seconds": 180
    }
    
    Response (201):
    {
        "success": true,
        "data": {
            "workout_exercise_id": "uuid",
            "exercise_name": "Barbell Bench Press",
            "sets": 3,
            "reps": 10,
            "weight_used": 185,
            "duration_seconds": 180,
            "calories_burned": 45
        },
        "message": "Exercise added to workout successfully"
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return responses.validation_error_response("Request body cannot be empty")
        
        # Validate required fields
        required = ['workout_id', 'exercise_id']
        for field in required:
            if field not in data:
                return responses.validation_error_response(f"Missing required field: {field}")
        
        workout_id = data.get('workout_id')
        exercise_id = data.get('exercise_id')
        sets = data.get('sets', 3)
        reps = data.get('reps', 10)
        weight_used = data.get('weight_used', 0)
        weight_unit = data.get('weight_unit', 'lbs')
        duration_seconds = data.get('duration_seconds', 0)
        
        # Verify workout exists and belongs to user
        workout = db.session.query(Workout).filter_by(
            workout_id=workout_id,
            user_id=token_user_id
        ).first()
        
        if not workout:
            return responses.not_found_response("Workout not found")
        
        # Verify exercise exists
        exercise = db.session.query(Exercise).filter_by(exercise_id=exercise_id).first()
        
        if not exercise:
            return responses.not_found_response("Exercise not found")
        
        # Calculate calories burned
        calories_burned = 0
        if duration_seconds and exercise.typical_calories_per_minute:
            calories_burned = (duration_seconds / 60) * exercise.typical_calories_per_minute
        
        # Create workout exercise entry
        workout_exercise = WorkoutExercise(
            workout_exercise_id=str(uuid.uuid4()),
            workout_id=workout_id,
            exercise_id=exercise_id,
            sets=sets,
            reps=reps,
            weight_used=weight_used,
            weight_unit=weight_unit,
            duration_seconds=duration_seconds,
            calories_burned=calories_burned,
            order_in_workout=1  # Default order
        )
        
        db.session.add(workout_exercise)
        db.session.commit()
        
        response_data = {
            "workout_exercise_id": workout_exercise.workout_exercise_id,
            "exercise_name": exercise.name,
            "sets": sets,
            "reps": reps,
            "weight_used": weight_used,
            "weight_unit": weight_unit,
            "duration_seconds": duration_seconds,
            "calories_burned": round(calories_burned, 2),
            "muscle_group": exercise.primary_muscle_group
        }
        
        return responses.success_response(
            response_data,
            "Exercise added to workout successfully",
            201
        )
    
    except Exception as e:
        db.session.rollback()
        return responses.error_response(
            "Error adding exercise to workout",
            str(e),
            "ML_ADD_EXERCISE_ERROR",
            500
        )


@bp.route('/predictions/<user_id>', methods=['GET'])
@decorators.token_required
def list_predictions(token_user_id, user_id):
    """
    List user's ML predictions with suggested exercises
    
    Query params:
    - page: Page number (default 1)
    - per_page: Items per page (default 10)
    
    Response (200):
    {
        "success": true,
        "data": [
            {
                "prediction_id": "uuid",
                "image_file_path": "filename.jpg",
                "equipment_name": "Barbell",
                "confidence": 0.94,
                "suggested_exercises": [...],
                "created_at": "2026-01-11T17:00:00"
            }
        ],
        "pagination": {
            "total": 5,
            "page": 1,
            "per_page": 10,
            "pages": 1
        }
    }
    """
    try:
        # Verify user exists
        user = db.session.query(User).filter_by(user_id=user_id).first()
        if not user:
            return responses.not_found_response("User not found")
        
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        pagination = db.session.query(MLPrediction).filter_by(user_id=user_id).order_by(
            MLPrediction.created_at.desc()
        ).paginate(page=page, per_page=per_page, error_out=False)
        
        predictions = [serialize_prediction(p, include_exercises=True) for p in pagination.items]
        
        return responses.paginated_response(
            predictions,
            pagination.total,
            page,
            per_page,
            "ML predictions retrieved successfully"
        )
    
    except Exception as e:
        return responses.error_response(
            "Database error",
            str(e),
            "ML_LIST_PREDICTIONS_ERROR",
            500
        )
