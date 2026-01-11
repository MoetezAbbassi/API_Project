"""
Nutrition Routes - Daily and weekly nutrition tracking
Endpoints: 2 (GET daily, GET weekly)
"""
from flask import Blueprint, request
from datetime import datetime, timedelta
from sqlalchemy import func
from app.extensions import db

from app.models import Meal, User
from app.utils import validators, responses, decorators

bp = Blueprint('nutrition', __name__, url_prefix='/api/nutrition')


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


def get_iso_week(date: datetime.date) -> tuple:
    """
    Get ISO week number and year
    
    Args:
        date: Date object
        
    Returns:
        Tuple of (week_number, year)
    """
    return date.isocalendar()[:2]


@bp.route('/daily/<user_id>', methods=['GET'])
@decorators.token_required
def get_daily_nutrition(token_user_id, user_id):
    """
    Get daily nutrition summary for specific date
    
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
        
        # Serialize meals
        meals_data = []
        for meal in meals:
            meals_data.append({
                "meal_id": meal.meal_id,
                "meal_type": meal.meal_type,
                "total_calories": meal.total_calories,
                "protein_g": meal.protein_g,
                "carbs_g": meal.carbs_g,
                "fats_g": meal.fats_g,
                "notes": meal.notes,
                "created_at": meal.created_at.isoformat() if meal.created_at else None
            })
        
        response_data = {
            "date": meal_date.isoformat(),
            "total_calories": round(total_calories, 2),
            "total_protein_g": round(total_protein, 2),
            "total_carbs_g": round(total_carbs, 2),
            "total_fats_g": round(total_fats, 2),
            "meals_count": len(meals),
            "meals": meals_data,
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
            "NUTRITION_DAILY_ERROR",
            500
        )


@bp.route('/weekly/<user_id>', methods=['GET'])
@decorators.token_required
def get_weekly_nutrition(token_user_id, user_id):
    """
    Get weekly nutrition summary
    
    Query params:
    - week: ISO week number (1-53, default: current week)
    - year: Year (default: current year)
    """
    try:
        # Verify user exists
        user = db.session.query(User).filter_by(user_id=user_id).first()
        if not user:
            return responses.not_found_response("User not found")
        
        # Get current week/year as defaults
        today = datetime.now().date()
        current_week, current_year = get_iso_week(today)
        
        week = request.args.get('week', current_week, type=int)
        year = request.args.get('year', current_year, type=int)
        
        # Validate week and year
        if week < 1 or week > 53:
            return responses.validation_error_response("Week must be between 1 and 53")
        
        if year < 2000 or year > 2100:
            return responses.validation_error_response("Year must be between 2000 and 2100")
        
        # Calculate date range for ISO week
        # ISO week 1 is the week with January 4th
        jan_4 = datetime(year, 1, 4).date()
        week_1_monday = jan_4 - timedelta(days=jan_4.weekday())
        start_date = week_1_monday + timedelta(weeks=week - 1)
        end_date = start_date + timedelta(days=6)
        
        # Query meals for the week
        meals = db.session.query(Meal).filter(
            Meal.user_id == user_id,
            Meal.meal_date >= start_date,
            Meal.meal_date <= end_date
        ).all()
        
        # Group meals by date
        daily_breakdown = {}
        for meal_date in [start_date + timedelta(days=i) for i in range(7)]:
            daily_breakdown[meal_date] = {
                "date": meal_date.isoformat(),
                "calories": 0,
                "protein_g": 0,
                "carbs_g": 0,
                "fats_g": 0
            }
        
        # Accumulate meal data
        for meal in meals:
            if meal.meal_date in daily_breakdown:
                daily_breakdown[meal.meal_date]["calories"] += meal.total_calories
                daily_breakdown[meal.meal_date]["protein_g"] += meal.protein_g
                daily_breakdown[meal.meal_date]["carbs_g"] += meal.carbs_g
                daily_breakdown[meal.meal_date]["fats_g"] += meal.fats_g
        
        # Build daily breakdown array
        daily_breakdown_array = []
        weekly_totals = {
            "total_calories": 0,
            "total_protein": 0,
            "total_carbs": 0,
            "total_fats": 0
        }
        
        for date_obj in sorted(daily_breakdown.keys()):
            day_data = daily_breakdown[date_obj]
            daily_breakdown_array.append({
                "date": day_data["date"],
                "calories": round(day_data["calories"], 2),
                "protein_g": round(day_data["protein_g"], 2),
                "carbs_g": round(day_data["carbs_g"], 2),
                "fats_g": round(day_data["fats_g"], 2)
            })
            
            weekly_totals["total_calories"] += day_data["calories"]
            weekly_totals["total_protein"] += day_data["protein_g"]
            weekly_totals["total_carbs"] += day_data["carbs_g"]
            weekly_totals["total_fats"] += day_data["fats_g"]
        
        # Round totals
        for key in weekly_totals:
            weekly_totals[key] = round(weekly_totals[key], 2)
        
        # Calculate average daily calories
        avg_daily_calories = round(weekly_totals["total_calories"] / 7, 2) if weekly_totals["total_calories"] > 0 else 0
        
        response_data = {
            "week": week,
            "year": year,
            "week_range": f"{start_date.isoformat()} to {end_date.isoformat()}",
            "daily_breakdown": daily_breakdown_array,
            "weekly_totals": {
                **weekly_totals,
                "average_daily_calories": avg_daily_calories
            }
        }
        
        return responses.success_response(
            response_data,
            "Weekly nutrition summary retrieved successfully"
        )
    
    except Exception as e:
        return responses.error_response(
            "Database error",
            str(e),
            "NUTRITION_WEEKLY_ERROR",
            500
        )
