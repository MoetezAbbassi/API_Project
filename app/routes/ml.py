"""
ML Routes - Machine learning equipment identification with exercise suggestions
Enhanced version with accurate equipment classification and workout integration
"""

from flask import Blueprint, request
from datetime import datetime
from app.extensions import db
from app.models import MLPrediction, Exercise, User, Workout, WorkoutExercise
from app.utils import responses, decorators
from app.services.equipment_classifier import (
    classify_equipment,
    get_exercises_for_equipment as get_classifier_exercises,
    get_equipment_info,
    GYM_EQUIPMENT_DATABASE
)
import os
import json
import uuid
import logging

logger = logging.getLogger(__name__)


bp = Blueprint('ml', __name__, url_prefix='/api/ml')


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


def get_exercises_from_database(equipment_key: str, limit: int = 6) -> list:
    """
    Get exercises from database that match the equipment's target muscles
    
    Args:
        equipment_key: Key in GYM_EQUIPMENT_DATABASE
        limit: Maximum number of exercises to return
        
    Returns:
        List of exercise dictionaries from database
    """
    equipment_data = GYM_EQUIPMENT_DATABASE.get(equipment_key, {})
    primary_muscles = equipment_data.get("primary_muscles", ["chest", "back"])
    secondary_muscles = equipment_data.get("secondary_muscles", [])
    
    # Query database for matching exercises
    primary_exercises = db.session.query(Exercise).filter(
        Exercise.primary_muscle_group.in_(primary_muscles)
    ).all() if primary_muscles else []
    
    secondary_exercises = []
    if len(primary_exercises) < limit and secondary_muscles:
        secondary_exercises = db.session.query(Exercise).filter(
            Exercise.primary_muscle_group.in_(secondary_muscles)
        ).all()
    
    # Combine and format
    all_exercises = primary_exercises + secondary_exercises
    exercise_list = []
    
    for ex in all_exercises[:limit]:
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
            "typical_calories_per_minute": ex.typical_calories_per_minute,
            "from_database": True
        })
    
    return exercise_list


@bp.route('/identify-equipment', methods=['POST'])
@decorators.token_required
def identify_equipment(token_user_id):
    """
    Identify fitness equipment from image upload and return suggested exercises
    
    Request: multipart/form-data with 'image' file
    
    Response (200):
    {
        "success": true,
        "data": {
            "prediction_id": "uuid",
            "equipment_name": "Barbell",
            "equipment_key": "barbell",
            "confidence": 0.94,
            "equipment_info": {
                "primary_muscles": ["chest", "back", "legs"],
                "secondary_muscles": ["arms", "core"],
                "total_exercises": 6
            },
            "suggested_exercises": [
                {
                    "exercise_id": "uuid",
                    "exercise_name": "Barbell Bench Press",
                    "description": "Classic chest exercise...",
                    "primary_muscle": "chest",
                    "difficulty": "intermediate",
                    "typical_calories_per_minute": 8.5
                }
            ],
            "quick_exercises": [
                {
                    "name": "Barbell Bench Press",
                    "primary_muscle": "chest",
                    "difficulty": "intermediate",
                    "recommended_sets": 3,
                    "recommended_reps": 10
                }
            ]
        },
        "message": "Equipment identified successfully"
    }
    """
    try:
        logger.info(f"🎯 Starting identify_equipment request...")
        # Check for file in request
        if 'image' not in request.files:
            logger.warning("No image file in request")
            return responses.validation_error_response("No image file provided")
        
        file = request.files['image']
        logger.info(f"File received: {file.filename}")
        
        if file.filename == '':
            logger.warning("Empty filename")
            return responses.validation_error_response("No image file selected")
        
        # Validate file type
        allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
        if '.' not in file.filename or file.filename.split('.')[-1].lower() not in allowed_extensions:
            logger.warning(f"Invalid file type: {file.filename}")
            return responses.validation_error_response("Invalid file type. Allowed: png, jpg, jpeg, gif, webp")
        
        # Save file
        uploads_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), '..', 'uploads', 'images')
        os.makedirs(uploads_dir, exist_ok=True)
        logger.info(f"Upload directory: {uploads_dir}")
        
        # Generate filename
        original_filename = file.filename
        filename = f"{uuid.uuid4()}_{original_filename}"
        filepath = os.path.join(uploads_dir, filename)
        
        # Save file
        try:
            file.save(filepath)
            logger.info(f"✅ File saved to: {filepath}")
        except Exception as e:
            logger.error(f"❌ File save error: {e}")
            return responses.error_response(
                "File upload error",
                str(e),
                "ML_UPLOAD_ERROR",
                500
            )
        
        # Classify equipment using our improved classifier
        try:
            logger.info(f"🔍 Starting equipment classification for: {original_filename}")
            equipment_key, confidence, display_name = classify_equipment(filepath, original_filename)
            logger.info(f"✅ Classification result: key={equipment_key}, confidence={confidence}, display={display_name}")
        except Exception as e:
            logger.error(f"❌ Classification error: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return responses.error_response(
                "Equipment classification failed",
                str(e),
                "ML_CLASSIFY_ERROR",
                500
            )
        
        # Get exercises from database
        try:
            logger.info(f"Getting exercises for equipment: {equipment_key}")
            db_exercises = get_exercises_from_database(equipment_key, limit=6)
            logger.info(f"Found {len(db_exercises)} exercises from database")
        except Exception as e:
            logger.error(f"Database exercises error: {e}")
            db_exercises = []
        
        # Also get quick exercise suggestions from classifier
        try:
            quick_exercises = get_classifier_exercises(equipment_key, limit=4)
            logger.info(f"Found {len(quick_exercises)} quick exercises")
        except Exception as e:
            logger.error(f"Quick exercises error: {e}")
            quick_exercises = []
        
        # Get equipment info
        try:
            equip_info = get_equipment_info(equipment_key)
            logger.info(f"Equipment info: {equip_info}")
        except Exception as e:
            logger.error(f"Equipment info error: {e}")
            equip_info = {}
        
        # Store prediction in database
        try:
            exercise_ids = [ex.get("exercise_id") for ex in db_exercises if ex.get("exercise_id")]
            prediction = MLPrediction(
                prediction_id=str(uuid.uuid4()),
                user_id=token_user_id,
                image_file_path=filename,
                equipment_name=display_name,
                confidence_score=confidence,
                suggested_exercises=json.dumps(exercise_ids)
            )
            
            db.session.add(prediction)
            db.session.commit()
            logger.info(f"✅ Prediction saved: {prediction.prediction_id}")
        except Exception as e:
            logger.error(f"❌ Database save error: {e}")
            db.session.rollback()
            return responses.error_response(
                "Database save error",
                str(e),
                "ML_DB_ERROR",
                500
            )
        
        # Build response with flattened structure for frontend
        response_data = {
            "prediction_id": prediction.prediction_id,
            "equipment_name": display_name,
            "equipment_key": equipment_key,
            "confidence": round(confidence, 2),
            # Flatten for easier frontend access
            "primary_muscles": equip_info.get("primary_muscles", []),
            "secondary_muscles": equip_info.get("secondary_muscles", []),
            # Keep nested for backward compatibility
            "equipment_info": equip_info,
            "suggested_exercises": db_exercises,
            "quick_exercises": quick_exercises
        }
        
        logger.info(f"✅ Sending response: equipment={equipment_key}, confidence={confidence}, exercises={len(db_exercises)}")
        
        return responses.success_response(
            response_data,
            "Equipment identified successfully"
        )
    
    except Exception as e:
        logger.error(f"❌ Unhandled exception in identify_equipment: {e}")
        import traceback
        logger.error(traceback.format_exc())
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
    
    Request: POST /api/ml/add-exercise-to-workout
    Content-Type: application/json
    Body:
    {
        "workout_id": "uuid",
        "exercise_id": "uuid",  // Optional - if from database
        "exercise_name": "Barbell Bench Press",  // Required if no exercise_id
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
        # Validate JSON
        if not request.is_json:
            return responses.validation_error_response("Request must contain valid JSON")
        
        data = request.get_json()
        if not data:
            return responses.validation_error_response("Request body cannot be empty")
        
        # Validate required fields
        workout_id = data.get('workout_id')
        if not workout_id:
            return responses.validation_error_response("Missing required field: workout_id")
        
        exercise_id = data.get('exercise_id')
        exercise_name = data.get('exercise_name')
        
        if not exercise_id and not exercise_name:
            return responses.validation_error_response("Either exercise_id or exercise_name is required")
        
        sets = data.get('sets', 3)
        reps = data.get('reps', 10)
        weight_used = data.get('weight_used', 0)
        weight_unit = data.get('weight_unit', 'lbs')
        duration_seconds = data.get('duration_seconds', 0)
        primary_muscle_group = data.get('primary_muscle_group', 'chest')  # From ML suggestion if available
        
        # Verify workout exists and belongs to user
        workout = db.session.query(Workout).filter_by(
            workout_id=workout_id,
            user_id=token_user_id
        ).first()
        
        if not workout:
            return responses.not_found_response("Workout not found or doesn't belong to you")
        
        # Get or find exercise
        exercise = None
        exercise_created = False
        
        if exercise_id:
            exercise = db.session.query(Exercise).filter_by(exercise_id=exercise_id).first()
        
        if not exercise and exercise_name:
            # Try to find by name (case-insensitive)
            exercise = db.session.query(Exercise).filter(
                Exercise.name.ilike(f"%{exercise_name}%")
            ).first()
        
        # If exercise doesn't exist, create it automatically
        if not exercise:
            try:
                from app.utils.calorie_calculator import estimate_calories_per_minute
                
                # Infer exercise type from muscle group
                exercise_type = 'cardio' if primary_muscle_group == 'cardio' else 'strength'
                
                # Estimate difficulty from context (default to intermediate)
                difficulty = 'intermediate'
                
                # Estimate calories per minute
                estimated_calories = estimate_calories_per_minute(
                    exercise_type,
                    difficulty,
                    primary_muscle_group
                )
                
                new_exercise = Exercise(
                    exercise_id=str(uuid.uuid4()),
                    name=exercise_name or "Unknown Exercise",
                    description=f"Auto-created from ML detection: {exercise_name or 'Unknown'} - {primary_muscle_group}",
                    primary_muscle_group=primary_muscle_group,
                    secondary_muscle_groups=json.dumps([]),  # Empty array
                    difficulty_level=difficulty,
                    typical_calories_per_minute=estimated_calories
                )
                db.session.add(new_exercise)
                db.session.flush()  # Flush to get the exercise_id without committing
                exercise = new_exercise
                exercise_created = True
            except Exception as e:
                db.session.rollback()
                return responses.error_response(
                    "Exercise creation failed",
                    f"Could not create exercise: {str(e)}",
                    "EXERCISE_CREATION_ERROR",
                    400
                )
        
        exercise_id = exercise.exercise_id
        exercise_name = exercise.name
        calories_per_minute = exercise.typical_calories_per_minute or 8.0
        
        # Calculate calories burned
        if duration_seconds and duration_seconds > 0:
            calories_burned = (duration_seconds / 60) * calories_per_minute
        else:
            # Estimate based on sets/reps
            calories_burned = (sets * reps * calories_per_minute) / 10
        
        # Get order for this workout
        from sqlalchemy import func
        last_order = db.session.query(func.max(WorkoutExercise.order_in_workout)).filter_by(
            workout_id=workout_id
        ).scalar() or 0
        
        # Create workout exercise entry
        try:
            workout_exercise = WorkoutExercise(
                workout_exercise_id=str(uuid.uuid4()),
                workout_id=workout_id,
                exercise_id=exercise_id,
                sets=sets,
                reps=reps,
                weight_used=weight_used,
                weight_unit=weight_unit,
                duration_seconds=duration_seconds,
                calories_burned=round(calories_burned, 2),
                order_in_workout=last_order + 1
            )
            
            db.session.add(workout_exercise)
            db.session.commit()  # Commit both exercise and workout_exercise
            
            response_data = {
                "workout_exercise_id": workout_exercise.workout_exercise_id,
                "exercise_id": exercise_id,
                "exercise_name": exercise_name,
                "exercise_created": exercise_created,  # Flag to indicate if exercise was auto-created
                "sets": sets,
                "reps": reps,
                "weight_used": weight_used,
                "weight_unit": weight_unit,
                "duration_seconds": duration_seconds,
                "calories_burned": round(calories_burned, 2),
                "order_in_workout": last_order + 1
            }
        except Exception as e:
            db.session.rollback()
            return responses.error_response(
                "Workout exercise creation failed",
                f"Could not add exercise to workout: {str(e)}",
                "WORKOUT_EXERCISE_ERROR",
                400
            )
        
        return responses.created_response(
            response_data,
            "Exercise added to workout successfully"
        )
    
    except Exception as e:
        db.session.rollback()
        return responses.error_response(
            "Error adding exercise to workout",
            str(e),
            "ML_ADD_EXERCISE_ERROR",
            500
        )


@bp.route('/equipment-list', methods=['GET'])
def get_equipment_list():
    """
    Get list of all recognizable equipment with their exercises
    
    Response (200):
    {
        "success": true,
        "data": [
            {
                "key": "barbell",
                "display_name": "Barbell",
                "primary_muscles": ["chest", "back", "legs"],
                "exercise_count": 6
            }
        ]
    }
    """
    equipment_list = []
    
    for key, data in GYM_EQUIPMENT_DATABASE.items():
        equipment_list.append({
            "key": key,
            "display_name": data.get("display_name", key),
            "primary_muscles": data.get("primary_muscles", []),
            "secondary_muscles": data.get("secondary_muscles", []),
            "exercise_count": len(data.get("exercises", []))
        })
    
    return responses.success_response(
        equipment_list,
        "Equipment list retrieved successfully"
    )


@bp.route('/equipment/<equipment_key>/exercises', methods=['GET'])
def get_equipment_exercises(equipment_key):
    """
    Get exercises for a specific equipment type
    
    Path params:
    - equipment_key: Equipment identifier (e.g., "barbell", "dumbbell")
    
    Response (200):
    {
        "success": true,
        "data": {
            "equipment": {...},
            "exercises": [...]
        }
    }
    """
    if equipment_key not in GYM_EQUIPMENT_DATABASE:
        return responses.not_found_response(f"Equipment '{equipment_key}' not found")
    
    equip_info = get_equipment_info(equipment_key)
    exercises = get_classifier_exercises(equipment_key, limit=10)
    
    # Also get from database
    db_exercises = get_exercises_from_database(equipment_key, limit=10)
    
    return responses.success_response({
        "equipment": equip_info,
        "quick_exercises": exercises,
        "database_exercises": db_exercises
    }, "Equipment exercises retrieved successfully")


@bp.route('/predictions/<user_id>', methods=['GET'])
@decorators.token_required
def list_predictions(token_user_id, user_id):
    """
    List user's ML predictions with suggested exercises
    
    Query params:
    - page: Page number (default 1)
    - per_page: Items per page (default 10)
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


@bp.route('/predictions/<prediction_id>', methods=['GET'])
@decorators.token_required  
def get_prediction(token_user_id, prediction_id):
    """
    Get a specific ML prediction with full exercise details
    """
    try:
        prediction = db.session.query(MLPrediction).filter_by(
            prediction_id=prediction_id
        ).first()
        
        if not prediction:
            return responses.not_found_response("Prediction not found")
        
        # Security check
        if prediction.user_id != token_user_id:
            return responses.forbidden_response("Access denied")
        
        # Get full exercise details from database
        exercise_ids = []
        if prediction.suggested_exercises:
            try:
                exercise_ids = json.loads(prediction.suggested_exercises)
            except:
                exercise_ids = []
        
        exercises = []
        for ex_id in exercise_ids:
            exercise = db.session.query(Exercise).filter_by(exercise_id=ex_id).first()
            if exercise:
                exercises.append({
                    "exercise_id": exercise.exercise_id,
                    "name": exercise.name,
                    "description": exercise.description,
                    "primary_muscle": exercise.primary_muscle_group,
                    "difficulty": exercise.difficulty_level,
                    "calories_per_minute": exercise.typical_calories_per_minute
                })
        
        result = serialize_prediction(prediction, include_exercises=False)
        result["exercises"] = exercises
        
        return responses.success_response(result, "Prediction retrieved successfully")
        
    except Exception as e:
        return responses.error_response(
            "Database error",
            str(e),
            "ML_GET_PREDICTION_ERROR", 
            500
        )
