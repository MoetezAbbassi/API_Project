"""
Meals Routes - Manage user nutrition and meal logging
Endpoints: 5 (POST create, GET list, GET daily, PUT update, DELETE)
"""
from flask import Blueprint, request
from datetime import datetime
from sqlalchemy import func
from app.extensions import db

from app.models import Meal, User
from app.utils import validators, responses, decorators
from app.utils.constants import MEAL_TYPES

bp = Blueprint('meals', __name__, url_prefix='/api/meals')




def serialize_meal(meal: Meal) -> dict:
    """
    Serialize Meal object to dictionary
    
    Args:
        meal: Meal model instance
        
    Returns:
        Dictionary representation of meal
    """
    return {
        "meal_id": meal.meal_id,
        "user_id": meal.user_id,
        "meal_type": meal.meal_type,
        "meal_date": meal.meal_date.isoformat() if meal.meal_date else None,
        "total_calories": meal.total_calories,
        "protein_g": meal.protein_g,
        "carbs_g": meal.carbs_g,
        "fats_g": meal.fats_g,
        "notes": meal.notes,
        "created_at": meal.created_at.isoformat() if meal.created_at else None
    }


def calculate_macro_percentages(protein: float, carbs: float, fats: float) -> dict:
    """
    Calculate macro percentages based on gram amounts
    
    Args:
        protein: Protein in grams
        carbs: Carbohydrates in grams
        fats: Fats in grams
        
    Returns:
        Dictionary with macro percentages
    """
    # Calories per gram: protein=4, carbs=4, fats=9
    protein_cal = protein * 4
    carbs_cal = carbs * 4
    fats_cal = fats * 9
    
    total_cal = protein_cal + carbs_cal + fats_cal
    
    if total_cal == 0:
        return {"protein_percentage": 0, "carbs_percentage": 0, "fats_percentage": 0}
    
    return {
        "protein_percentage": round((protein_cal / total_cal) * 100, 2),
        "carbs_percentage": round((carbs_cal / total_cal) * 100, 2),
        "fats_percentage": round((fats_cal / total_cal) * 100, 2)
    }


@bp.route('', methods=['POST'])
@decorators.validate_json
@decorators.token_required
def create_meal(token_user_id):
    """
    Log a meal
    
    Request body:
    {
        "meal_type": "breakfast|lunch|dinner|snack",
        "meal_date": "2026-01-11",
        "total_calories": 650,
        "protein_g": 45,
        "carbs_g": 65,
        "fats_g": 20,
        "notes": "Grilled chicken with rice"
    }
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        is_valid, error_msg = validators.validate_required_fields(
            data, ['meal_type', 'meal_date', 'total_calories', 'protein_g', 'carbs_g', 'fats_g']
        )
        if not is_valid:
            return responses.validation_error_response(error_msg)
        
        # Validate meal type
        is_valid, error_msg = validators.validate_enum(data['meal_type'], MEAL_TYPES)
        if not is_valid:
            return responses.validation_error_response(f"Invalid meal_type. Must be one of: {', '.join(MEAL_TYPES)}")
        
        # Validate date
        is_valid, error_msg = validators.validate_date(data['meal_date'])
        if not is_valid:
            return responses.validation_error_response(error_msg)
        
        # Validate numeric fields
        is_valid, error_msg = validators.validate_positive_number(data['total_calories'], 'total_calories')
        if not is_valid:
            return responses.validation_error_response(error_msg)
        
        is_valid, error_msg = validators.validate_positive_number(data['protein_g'], 'protein_g')
        if not is_valid:
            return responses.validation_error_response(error_msg)
        
        is_valid, error_msg = validators.validate_positive_number(data['carbs_g'], 'carbs_g')
        if not is_valid:
            return responses.validation_error_response(error_msg)
        
        is_valid, error_msg = validators.validate_positive_number(data['fats_g'], 'fats_g')
        if not is_valid:
            return responses.validation_error_response(error_msg)
        
        # Parse date
        meal_date = datetime.strptime(data['meal_date'], '%Y-%m-%d').date()
        
        # Create meal
        import uuid
        meal = Meal(
            meal_id=str(uuid.uuid4()),
            user_id=token_user_id,
            meal_type=data['meal_type'],
            meal_date=meal_date,
            total_calories=float(data['total_calories']),
            protein_g=float(data['protein_g']),
            carbs_g=float(data['carbs_g']),
            fats_g=float(data['fats_g']),
            notes=data.get('notes', '')
        )
        
        db.session.add(meal)
        db.session.commit()
        
        return responses.created_response(
            serialize_meal(meal),
            "Meal logged successfully"
        )
    
    except Exception as e:
        db.session.rollback()
        return responses.error_response(
            "Database error",
            str(e),
            "MEAL_CREATE_ERROR",
            500
        )


@bp.route('/<user_id>', methods=['GET'])
@decorators.token_required
def list_meals(token_user_id, user_id):
    """
    List user's meals with optional date range filtering
    
    Query params:
    - start_date: Filter meals from date (YYYY-MM-DD)
    - end_date: Filter meals to date (YYYY-MM-DD)
    - page: Page number (default 1)
    - per_page: Items per page (default 20)
    """
    try:
        # Verify user exists
        user = db.session.query(User).filter_by(user_id=user_id).first()
        if not user:
            return responses.not_found_response("User not found")
        
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        start_date = request.args.get('start_date', type=str)
        end_date = request.args.get('end_date', type=str)
        
        query = db.session.query(Meal).filter_by(user_id=user_id)
        
        # Filter by date range if provided
        if start_date:
            is_valid, error_msg = validators.validate_date(start_date)
            if is_valid:
                start = datetime.strptime(start_date, '%Y-%m-%d').date()
                query = query.filter(Meal.meal_date >= start)
        
        if end_date:
            is_valid, error_msg = validators.validate_date(end_date)
            if is_valid:
                end = datetime.strptime(end_date, '%Y-%m-%d').date()
                query = query.filter(Meal.meal_date <= end)
        
        # Order by date descending
        query = query.order_by(Meal.meal_date.desc(), Meal.created_at.desc())
        
        # Paginate
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        meals = [serialize_meal(m) for m in pagination.items]
        
        return responses.paginated_response(
            meals,
            pagination.total,
            page,
            per_page,
            "Meals retrieved successfully"
        )
    
    except Exception as e:
        return responses.error_response(
            "Database error",
            str(e),
            "MEAL_LIST_ERROR",
            500
        )


@bp.route('/<user_id>/daily', methods=['GET'])
@decorators.token_required
def get_daily_nutrition(token_user_id, user_id):
    """
    Get daily nutrition summary - all meals for a specific date with totals
    
    Query params:
    - date: Date (YYYY-MM-DD format, defaults to today)
    """
    try:
        # Verify user exists
        user = db.session.query(User).filter_by(user_id=user_id).first()
        if not user:
            return responses.not_found_response("User not found")
        
        date_str = request.args.get('date', datetime.now().date().isoformat(), type=str)
        
        # Validate date
        is_valid, error_msg = validators.validate_date(date_str)
        if not is_valid:
            return responses.validation_error_response(error_msg)
        
        # Parse date
        meal_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        
        # Query meals for the day
        meals = db.session.query(Meal).filter_by(user_id=user_id, meal_date=meal_date).all()
        
        # Calculate daily totals
        total_calories = sum(m.total_calories for m in meals)
        total_protein = sum(m.protein_g for m in meals)
        total_carbs = sum(m.carbs_g for m in meals)
        total_fats = sum(m.fats_g for m in meals)
        
        # Calculate macro percentages
        macro_percentages = calculate_macro_percentages(total_protein, total_carbs, total_fats)
        
        response_data = {
            "date": meal_date.isoformat(),
            "total_calories": total_calories,
            "total_protein_g": total_protein,
            "total_carbs_g": total_carbs,
            "total_fats_g": total_fats,
            "meals_count": len(meals),
            "meals": [serialize_meal(m) for m in meals],
            "macros_breakdown": macro_percentages
        }
        
        return responses.success_response(
            response_data,
            "Daily nutrition summary retrieved successfully"
        )
    
    except Exception as e:
        return responses.error_response(
            "Database error",
            str(e),
            "MEAL_DAILY_ERROR",
            500
        )


@bp.route('/<meal_id>', methods=['PUT'])
@decorators.validate_json
@decorators.token_required
def update_meal(token_user_id, meal_id):
    """
    Update meal
    
    Request body (all optional):
    {
        "meal_type": "lunch",
        "total_calories": 700,
        "protein_g": 50,
        "carbs_g": 70,
        "fats_g": 22
    }
    """
    try:
        # Verify meal exists
        meal = db.session.query(Meal).filter_by(meal_id=meal_id).first()
        if not meal:
            return responses.not_found_response("Meal not found")
        
        # Security: verify user owns meal
        if meal.user_id != token_user_id:
            return responses.forbidden_response("You can only update your own meals")
        
        data = request.get_json()
        
        # Update fields if provided
        if 'meal_type' in data:
            is_valid, error_msg = validators.validate_enum(data['meal_type'], MEAL_TYPES)
            if not is_valid:
                return responses.validation_error_response(f"Invalid meal_type. Must be one of: {', '.join(MEAL_TYPES)}")
            meal.meal_type = data['meal_type']
        
        if 'total_calories' in data:
            is_valid, error_msg = validators.validate_positive_number(data['total_calories'], 'total_calories')
            if not is_valid:
                return responses.validation_error_response(error_msg)
            meal.total_calories = float(data['total_calories'])
        
        if 'protein_g' in data:
            is_valid, error_msg = validators.validate_positive_number(data['protein_g'], 'protein_g')
            if not is_valid:
                return responses.validation_error_response(error_msg)
            meal.protein_g = float(data['protein_g'])
        
        if 'carbs_g' in data:
            is_valid, error_msg = validators.validate_positive_number(data['carbs_g'], 'carbs_g')
            if not is_valid:
                return responses.validation_error_response(error_msg)
            meal.carbs_g = float(data['carbs_g'])
        
        if 'fats_g' in data:
            is_valid, error_msg = validators.validate_positive_number(data['fats_g'], 'fats_g')
            if not is_valid:
                return responses.validation_error_response(error_msg)
            meal.fats_g = float(data['fats_g'])
        
        db.session.commit()
        
        return responses.success_response(
            serialize_meal(meal),
            "Meal updated successfully"
        )
    
    except Exception as e:
        db.session.rollback()
        return responses.error_response(
            "Database error",
            str(e),
            "MEAL_UPDATE_ERROR",
            500
        )


@bp.route('/<meal_id>', methods=['DELETE'])
@decorators.token_required
def delete_meal(token_user_id, meal_id):
    """
    Delete a meal
    
    Path params:
    - meal_id: Meal ID (UUID)
    """
    try:
        # Verify meal exists
        meal = db.session.query(Meal).filter_by(meal_id=meal_id).first()
        if not meal:
            return responses.not_found_response("Meal not found")
        
        # Security: verify user owns meal
        if meal.user_id != token_user_id:
            return responses.forbidden_response("You can only delete your own meals")
        
        db.session.delete(meal)
        db.session.commit()
        
        return responses.deleted_response("Meal deleted successfully")
    
    except Exception as e:
        db.session.rollback()
        return responses.error_response(
            "Database error",
            str(e),
            "MEAL_DELETE_ERROR",
            500
        )
