"""
ML Routes - Machine learning equipment identification
Endpoints: 2 (POST identify-equipment, GET predictions list)
"""
from flask import Blueprint, request
from datetime import datetime
from app.extensions import db

from app.models import MLPrediction, Exercise, User
from app.utils import responses, decorators
import os

bp = Blueprint('ml', __name__, url_prefix='/api/ml')

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
        include_exercises: Include suggested exercises
        
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
        import json
        suggested = prediction.suggested_exercises or []
        if isinstance(suggested, str):
            try:
                suggested = json.loads(suggested)
            except:
                suggested = []
        pred_dict["suggested_exercises"] = suggested
    
    return pred_dict


def get_exercises_for_equipment(equipment_name: str) -> list:
    """
    Get exercises that can be done with identified equipment
    
    Args:
        equipment_name: Name of identified equipment
        
    Returns:
        List of exercise objects with details
    """
    # Simple mapping for now - in production would use more sophisticated matching
    muscle_map = {
        "Barbell": ["chest", "back", "legs", "shoulders", "arms"],
        "Dumbbell": ["chest", "back", "shoulders", "arms"],
        "Bench Press": ["chest", "shoulders", "triceps"],
        "Squat Rack": ["legs", "back"],
        "Cable Machine": ["chest", "back", "shoulders", "arms"],
        "Treadmill": ["cardio", "legs"],
        "Elliptical": ["cardio"],
        "Kettlebell": ["legs", "shoulders", "arms", "core"],
        "Resistance Band": ["chest", "back", "shoulders", "arms"],
        "Yoga Mat": ["core", "flexibility"]
    }
    
    muscles = muscle_map.get(equipment_name, ["cardio"])
    exercises = db.session.query(Exercise).filter(
        Exercise.primary_muscle_group.in_(muscles)
    ).limit(5).all()
    
    return [
        {
            "exercise_id": ex.exercise_id,
            "exercise_name": ex.name,
            "primary_muscle": ex.primary_muscle_group,
            "difficulty": ex.difficulty_level
        }
        for ex in exercises
    ]


@bp.route('/identify-equipment', methods=['POST'])
@decorators.token_required
def identify_equipment(token_user_id):
    """
    Identify fitness equipment from image upload
    
    Request: multipart/form-data with 'image' file
    
    Response (200):
    {
        "prediction_id": "uuid",
        "equipment_name": "Barbell",
        "confidence": 0.94,
        "suggested_exercises": [...]
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
        import uuid
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
        
        # For now: Return placeholder prediction
        # In production: Run actual ML model here
        equipment_name = "Barbell Bench"
        confidence = 0.94
        
        # Get suggested exercises
        suggested_exercises = get_exercises_for_equipment(equipment_name)
        
        # Store prediction in database
        import json
        prediction = MLPrediction(
            prediction_id=str(uuid.uuid4()),
            user_id=token_user_id,
            image_file_path=filename,
            equipment_name=equipment_name,
            confidence_score=confidence,
            suggested_exercises=json.dumps([ex["exercise_id"] for ex in suggested_exercises])
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


@bp.route('/predictions/<user_id>', methods=['GET'])
@decorators.token_required
def list_predictions(token_user_id, user_id):
    """
    List user's ML predictions
    
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
        
        predictions = [serialize_prediction(p, include_exercises=False) for p in pagination.items]
        
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
