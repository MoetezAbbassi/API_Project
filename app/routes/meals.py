"""
Meals Routes - Manage user nutrition and meal logging
Endpoints: 
- POST /api/meals - Create meal manually
- POST /api/meals/analyze-image - ML-based meal recognition from photo
- POST /api/meals/analyze-text - Analyze food items from text description
- GET /api/meals - List current user's meals
- GET /api/meals/nutrition/summary - Get nutrition summary
- GET /api/meals/<meal_id> - Get single meal with items
- PUT /api/meals/<meal_id> - Update meal
- DELETE /api/meals/<meal_id> - Delete meal
"""
from flask import Blueprint, request
from datetime import datetime
from sqlalchemy import func
from werkzeug.utils import secure_filename
import os
import uuid as uuid_module
from app.extensions import db

from app.models import Meal, MealItem, User
from app.utils import validators, responses, decorators
from app.utils.constants import MEAL_TYPES
from app.services.meal_service import get_meal_service

bp = Blueprint('meals', __name__, url_prefix='/api/meals')

# Allowed image extensions
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS




def serialize_meal(meal: Meal, include_items: bool = True) -> dict:
    """
    Serialize Meal object to dictionary
    
    Args:
        meal: Meal model instance
        include_items: Whether to include meal items
        
    Returns:
        Dictionary representation of meal
    """
    result = {
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
    
    if include_items and hasattr(meal, 'meal_items'):
        result["items"] = [serialize_meal_item(item) for item in meal.meal_items]
        result["item_count"] = len(meal.meal_items)
    
    return result


def serialize_meal_item(item: MealItem) -> dict:
    """
    Serialize MealItem object to dictionary
    """
    return {
        "meal_item_id": item.meal_item_id,
        "food_name": item.food_name,
        "quantity": item.quantity,
        "quantity_unit": item.quantity_unit,
        "calories": item.calories,
        "protein_g": item.protein_g,
        "carbs_g": item.carbs_g,
        "fats_g": item.fats_g
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


@bp.route('', methods=['GET'])
@decorators.token_required
def list_meals_current_user(token_user_id):
    """
    List current user's meals with optional date filtering
    
    Query params:
    - date: Filter meals by date (YYYY-MM-DD)
    - page: Page number (default 1)
    - per_page: Items per page (default 20)
    """
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        date_filter = request.args.get('date', type=str)
        
        # Validate pagination parameters
        if page < 1:
            return responses.validation_error_response("Page number must be positive")
        if per_page < 1 or per_page > 100:
            return responses.validation_error_response("Items per page must be between 1 and 100")
        
        query = db.session.query(Meal).filter_by(user_id=token_user_id)
        
        # Filter by date if provided
        if date_filter:
            is_valid, error_msg = validators.validate_date(date_filter)
            if not is_valid:
                return responses.validation_error_response(f"Invalid date format: {error_msg}")
            
            try:
                filter_date = datetime.strptime(date_filter, '%Y-%m-%d').date()
                query = query.filter(Meal.meal_date == filter_date)
            except ValueError as e:
                return responses.validation_error_response(f"Invalid date format: {str(e)}")
        
        # Order by date descending
        query = query.order_by(Meal.meal_date.desc())
        
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


@bp.route('/nutrition/summary', methods=['GET'])
@decorators.token_required
def get_nutrition_summary(token_user_id):
    """
    Get nutrition summary for current user
    
    Query params:
    - date: Filter by date (YYYY-MM-DD), defaults to today
    """
    try:
        from datetime import date as date_type
        date_filter = request.args.get('date', type=str)
        
        if date_filter:
            is_valid, _ = validators.validate_date(date_filter)
            if is_valid:
                filter_date = datetime.strptime(date_filter, '%Y-%m-%d').date()
            else:
                filter_date = date_type.today()
        else:
            filter_date = date_type.today()
        
        # Get meals for date
        meals = db.session.query(Meal).filter(
            Meal.user_id == token_user_id,
            Meal.meal_date == filter_date
        ).all()
        
        total_calories = sum(m.total_calories for m in meals)
        total_protein = sum(m.protein_g or 0 for m in meals)
        total_carbs = sum(m.carbs_g or 0 for m in meals)
        total_fats = sum(m.fats_g or 0 for m in meals)
        
        macro_percentages = calculate_macro_percentages(total_protein, total_carbs, total_fats)
        
        return responses.success_response({
            "date": filter_date.isoformat(),
            "total_calories": round(total_calories, 2),
            "total_protein_g": round(total_protein, 2),
            "total_carbs_g": round(total_carbs, 2),
            "total_fats_g": round(total_fats, 2),
            "macro_percentages": macro_percentages,
            "meal_count": len(meals)
        }, "Nutrition summary retrieved successfully")
    
    except Exception as e:
        return responses.error_response(
            "Database error",
            str(e),
            "NUTRITION_SUMMARY_ERROR",
            500
        )


@bp.route('', methods=['POST'])
@decorators.validate_json
@decorators.token_required
def create_meal(token_user_id):
    """
    Log a meal with optional food items
    
    Request body:
    {
        "meal_type": "breakfast|lunch|dinner|snack",
        "meal_date": "2026-01-11",
        "notes": "My healthy breakfast",
        "items": [
            {
                "food_name": "Scrambled Eggs",
                "quantity": 150,
                "quantity_unit": "g"
            },
            {
                "food_name": "Toast",
                "quantity": 2,
                "quantity_unit": "slices"
            }
        ]
    }
    
    The calories and macros will be calculated automatically from items.
    If no items provided, you can manually specify totals.
    """
    try:
        data = request.get_json()
        meal_service = get_meal_service()
        
        # Validate required fields
        is_valid, error_msg = validators.validate_required_fields(
            data, ['meal_type', 'meal_date']
        )
        if not is_valid:
            return responses.validation_error_response(error_msg)
        
        # Validate meal type - allow custom meal types
        meal_type = data['meal_type'].lower()
        
        # Validate date
        is_valid, error_msg = validators.validate_date(data['meal_date'])
        if not is_valid:
            return responses.validation_error_response(error_msg)
        
        # Parse date
        meal_date = datetime.strptime(data['meal_date'], '%Y-%m-%d').date()
        
        # Get items if provided
        items_data = data.get('items', [])
        
        # Calculate nutrition from items or use provided values
        total_calories = 0
        total_protein = 0
        total_carbs = 0
        total_fats = 0
        
        meal_items = []
        
        if items_data:
            # Analyze items and calculate nutrition
            for item in items_data:
                food_name = item.get('food_name', '')
                quantity = item.get('quantity', 100)
                quantity_unit = item.get('quantity_unit', 'g')
                
                if not food_name:
                    continue
                
                # Use provided nutrition values if available, otherwise look up
                if item.get('calories') and item.get('protein_g'):
                    # Nutrition data already provided (e.g., from scanned meal)
                    nutrition = {
                        "food_name": food_name,
                        "quantity": quantity,
                        "unit": quantity_unit,
                        "calories": item.get('calories', 0),
                        "protein_g": item.get('protein_g', 0),
                        "carbs_g": item.get('carbs_g', 0),
                        "fats_g": item.get('fats_g', 0)
                    }
                else:
                    # Look up nutrition from database
                    nutrition = meal_service.get_nutrition_for_food(food_name, quantity, quantity_unit)
                
                meal_items.append({
                    "food_name": food_name,
                    "quantity": quantity,
                    "quantity_unit": quantity_unit,
                    "calories": nutrition["calories"],
                    "protein_g": nutrition["protein_g"],
                    "carbs_g": nutrition["carbs_g"],
                    "fats_g": nutrition["fats_g"]
                })
                
                total_calories += nutrition["calories"]
                total_protein += nutrition["protein_g"]
                total_carbs += nutrition["carbs_g"]
                total_fats += nutrition["fats_g"]
        else:
            # Use manually provided values if no items
            total_calories = float(data.get('total_calories', 0))
            total_protein = float(data.get('protein_g', 0))
            total_carbs = float(data.get('carbs_g', 0))
            total_fats = float(data.get('fats_g', 0))
        
        # Create meal
        meal = Meal(
            meal_id=str(uuid_module.uuid4()),
            user_id=token_user_id,
            meal_type=meal_type,
            meal_date=meal_date,
            total_calories=round(total_calories, 1),
            protein_g=round(total_protein, 1),
            carbs_g=round(total_carbs, 1),
            fats_g=round(total_fats, 1),
            notes=data.get('notes', '')
        )
        
        db.session.add(meal)
        db.session.flush()  # Get meal_id
        
        # Create meal items
        for item in meal_items:
            meal_item = MealItem(
                meal_item_id=str(uuid_module.uuid4()),
                meal_id=meal.meal_id,
                food_name=item["food_name"],
                quantity=item["quantity"],
                quantity_unit=item["quantity_unit"],
                calories=item["calories"],
                protein_g=item["protein_g"],
                carbs_g=item["carbs_g"],
                fats_g=item["fats_g"]
            )
            db.session.add(meal_item)
        
        db.session.commit()
        
        # Reload meal with items
        meal = db.session.query(Meal).filter_by(meal_id=meal.meal_id).first()
        
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


@bp.route('/analyze-image', methods=['POST'])
@decorators.token_required
def analyze_meal_image(token_user_id):
    """
    Analyze a meal image using ML to identify foods and calculate calories
    
    Request: multipart/form-data with 'image' file
    
    Returns:
    {
        "recognized_foods": [...],
        "totals": {
            "calories": 650,
            "protein_g": 45,
            "carbs_g": 65,
            "fats_g": 20
        }
    }
    """
    try:
        if 'image' not in request.files:
            return responses.validation_error_response("No image file provided")
        
        file = request.files['image']
        
        if file.filename == '':
            return responses.validation_error_response("No file selected")
        
        if not allowed_file(file.filename):
            return responses.validation_error_response(
                f"Invalid file type. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
            )
        
        # Save file temporarily
        filename = secure_filename(file.filename)
        unique_filename = f"{uuid_module.uuid4()}_{filename}"
        
        # Get uploads directory from Flask app config or use default
        from flask import current_app
        upload_folder = current_app.config.get('UPLOAD_FOLDER', 'uploads/images')
        os.makedirs(upload_folder, exist_ok=True)
        
        file_path = os.path.join(upload_folder, unique_filename)
        file.save(file_path)
        
        try:
            # Analyze image with ML service
            meal_service = get_meal_service()
            result = meal_service.recognize_and_analyze_meal(file_path)
            
            if not result.get("success"):
                return responses.error_response(
                    "Analysis failed",
                    result.get("error", "Failed to analyze image"),
                    "ML_ANALYSIS_ERROR",
                    400
                )
            
            return responses.success_response({
                "recognized_foods": result.get("recognized_foods", []),
                "description": result.get("description", ""),
                "totals": result.get("totals", {}),
                "provider": result.get("provider", "unknown"),
                "count": result.get("count", 0),
                "image_path": unique_filename
            }, "Meal image analyzed successfully")
            
        finally:
            # Clean up temp file
            if os.path.exists(file_path):
                os.remove(file_path)
    
    except Exception as e:
        return responses.error_response(
            "Analysis error",
            str(e),
            "MEAL_ANALYZE_ERROR",
            500
        )


@bp.route('/analyze-text', methods=['POST'])
@decorators.validate_json
@decorators.token_required
def analyze_meal_text(token_user_id):
    """
    Analyze food items from text description
    
    Request body:
    {
        "items": [
            {"food_name": "chicken breast", "quantity": 200, "quantity_unit": "g"},
            {"food_name": "rice", "quantity": 150, "quantity_unit": "g"}
        ]
    }
    
    Or simple text:
    {
        "description": "chicken breast 200g, rice 150g, broccoli 100g"
    }
    """
    try:
        data = request.get_json()
        meal_service = get_meal_service()
        
        items = data.get('items', [])
        
        # Parse text description if provided
        if not items and 'description' in data:
            description = data['description']
            # Simple parsing - split by comma and try to extract food + quantity
            items = parse_food_description(description)
        
        if not items:
            return responses.validation_error_response(
                "Please provide 'items' array or 'description' text"
            )
        
        # Analyze the items
        result = meal_service.analyze_meal(items)
        
        return responses.success_response({
            "foods": result.get("items", []),
            "totals": result.get("totals", {}),
            "item_count": result.get("item_count", 0)
        }, "Food items analyzed successfully")
    
    except Exception as e:
        return responses.error_response(
            "Analysis error",
            str(e),
            "MEAL_TEXT_ANALYZE_ERROR",
            500
        )


def parse_food_description(description: str) -> list:
    """
    Parse a text description into food items
    Example: "chicken breast 200g, rice 150g, salad"
    """
    import re
    
    items = []
    # Split by comma or 'and'
    parts = re.split(r',|\band\b', description)
    
    for part in parts:
        part = part.strip()
        if not part:
            continue
        
        # Try to extract quantity and unit
        # Pattern: food_name quantity unit
        match = re.match(r'^(.+?)\s+(\d+(?:\.\d+)?)\s*(g|kg|ml|l|oz|cup|cups|slice|slices|piece|pieces)?$', part, re.IGNORECASE)
        
        if match:
            food_name = match.group(1).strip()
            quantity = float(match.group(2))
            unit = match.group(3) or 'g'
        else:
            # No quantity found, use default
            food_name = part
            quantity = 100
            unit = 'g'
        
        items.append({
            "food_name": food_name,
            "quantity": quantity,
            "quantity_unit": unit.lower()
        })
    
    return items


@bp.route('/search', methods=['GET'])
@decorators.token_required
def search_foods(token_user_id):
    """
    Search for foods in the database
    
    Query params:
    - q: Search query
    """
    try:
        query = request.args.get('q', '', type=str).lower().strip()
        
        if not query or len(query) < 2:
            return responses.validation_error_response("Query must be at least 2 characters")
        
        meal_service = get_meal_service()
        
        # Search in local database
        from app.services.meal_service import FOOD_DATABASE
        
        results = []
        for food_name, nutrition in FOOD_DATABASE.items():
            if query in food_name.lower():
                results.append({
                    "food_name": food_name.title(),
                    "calories_per_100g": nutrition["calories"],
                    "protein_per_100g": nutrition["protein"],
                    "carbs_per_100g": nutrition["carbs"],
                    "fats_per_100g": nutrition["fats"],
                    "default_serving": nutrition["serving_size"],
                    "default_unit": nutrition["unit"]
                })
        
        # Sort by relevance (exact match first, then by name)
        results.sort(key=lambda x: (0 if x["food_name"].lower().startswith(query) else 1, x["food_name"]))
        
        return responses.success_response({
            "foods": results[:20],  # Limit to 20 results
            "count": len(results)
        }, "Foods found")
    
    except Exception as e:
        return responses.error_response(
            "Search error",
            str(e),
            "FOOD_SEARCH_ERROR",
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
        
        # Delete meal (cascade will handle meal_items)
        db.session.delete(meal)
        db.session.flush()  # Flush to detect any errors before commit
        db.session.commit()
        
        return responses.deleted_response("Meal deleted successfully")
    
    except Exception as e:
        db.session.rollback()
        import traceback
        traceback.print_exc()
        return responses.error_response(
            "Database error",
            f"{str(e)} - Check server logs for details",
            "MEAL_DELETE_ERROR",
            500
        )

@bp.route('/<meal_id>/add-item', methods=['POST'])
@decorators.token_required
def add_item_to_meal(token_user_id, meal_id):
    """
    Add a food item to an existing meal (manual input only)
    
    Path params:
    - meal_id: Meal ID (UUID)
    
    Request body (JSON):
    {
      "food_name": "chicken",
      "quantity": 100,
      "quantity_unit": "g"
    }
    """
    try:
        # Verify meal exists
        meal = db.session.query(Meal).filter_by(meal_id=meal_id).first()
        if not meal:
            return responses.not_found_response("Meal not found")
        
        # Security: verify user owns meal
        if meal.user_id != token_user_id:
            return responses.forbidden_response("You can only modify your own meals")
        
        # Get request data
        data = request.get_json() or {}
        food_name = data.get('food_name', '').strip()
        quantity = data.get('quantity', 100)
        quantity_unit = data.get('quantity_unit', 'g')
        
        # Validate food name
        if not food_name:
            return responses.bad_request_response("Food name is required")
        
        # Get nutrition info for the food
        meal_service = get_meal_service()
        nutrition = meal_service.get_nutrition_for_food(food_name, quantity, quantity_unit)
        
        if not nutrition:
            return responses.not_found_response(f"Food '{food_name}' not found in database")
        
        # Create meal item
        meal_item = MealItem(
            meal_item_id=str(uuid_module.uuid4()),
            meal_id=meal_id,
            food_name=food_name,
            quantity=quantity,
            quantity_unit=quantity_unit,
            calories=nutrition.get('calories', 0),
            protein_g=nutrition.get('protein', 0),
            carbs_g=nutrition.get('carbs', 0),
            fats_g=nutrition.get('fats', 0),
            recognition_method='manual'
        )
        
        db.session.add(meal_item)
        db.session.commit()
        
        return responses.success_response(
            "Item added successfully",
            {
                "meal_item_id": meal_item.meal_item_id,
                "food_name": meal_item.food_name,
                "nutrition": nutrition
            },
            201
        )
    
    except Exception as e:
        db.session.rollback()
        import traceback
        traceback.print_exc()
        return responses.error_response(
            "Error adding item",
            str(e),
            "MEAL_ADD_ITEM_ERROR",
            500
        )