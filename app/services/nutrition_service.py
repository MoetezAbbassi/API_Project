"""
Nutrition Service - Business logic for nutrition calculations and aggregations.
"""

import logging
from typing import Dict, Any
from datetime import datetime, timedelta
from sqlalchemy import func
from app.database import db
from app.models import Meal, Workout, User

logger = logging.getLogger(__name__)


def calculate_daily_nutrition(user_id: str, date: str) -> Dict[str, Any]:
    """
    Calculate daily nutrition summary.
    
    Args:
        user_id: User ID
        date: Date in YYYY-MM-DD format
    
    Returns:
        Dictionary with total_calories, macros, and percentages
    """
    try:
        target_date = datetime.strptime(date, "%Y-%m-%d").date()
        
        # Query all meals for the day
        meals = Meal.query.filter(
            Meal.user_id == user_id,
            func.date(Meal.meal_date) == target_date
        ).all()
        
        # Sum totals
        total_calories = sum(m.total_calories or 0 for m in meals)
        total_protein = sum(m.protein_g or 0 for m in meals)
        total_carbs = sum(m.carbs_g or 0 for m in meals)
        total_fats = sum(m.fats_g or 0 for m in meals)
        
        # Calculate macro percentages
        percentages = calculate_macro_percentages(total_protein, total_carbs, total_fats)
        
        return {
            "date": date,
            "total_calories": total_calories,
            "protein_g": total_protein,
            "carbs_g": total_carbs,
            "fats_g": total_fats,
            "meals_count": len(meals),
            "protein_percentage": percentages["protein"],
            "carbs_percentage": percentages["carbs"],
            "fats_percentage": percentages["fats"]
        }
    except Exception as e:
        logger.error(f"Error calculating daily nutrition: {str(e)}")
        return {
            "date": date,
            "total_calories": 0,
            "protein_g": 0,
            "carbs_g": 0,
            "fats_g": 0,
            "meals_count": 0,
            "protein_percentage": 0,
            "carbs_percentage": 0,
            "fats_percentage": 0
        }


def calculate_weekly_nutrition(user_id: str, week: int, year: int) -> Dict[str, Any]:
    """
    Calculate weekly nutrition summary.
    
    Args:
        user_id: User ID
        week: Week number (1-53)
        year: Year
    
    Returns:
        Dictionary with daily_breakdown and weekly_totals
    """
    try:
        # Calculate week start date (ISO week)
        jan_4 = datetime(year, 1, 4)
        week_1_monday = jan_4 - timedelta(days=jan_4.weekday())
        week_start = week_1_monday + timedelta(weeks=week - 1)
        
        daily_breakdown = []
        total_calories = 0
        total_protein = 0
        total_carbs = 0
        total_fats = 0
        
        # Iterate through 7 days
        for i in range(7):
            day_date = week_start + timedelta(days=i)
            daily = calculate_daily_nutrition(user_id, day_date.strftime("%Y-%m-%d"))
            
            daily_breakdown.append(daily)
            total_calories += daily["total_calories"]
            total_protein += daily["protein_g"]
            total_carbs += daily["carbs_g"]
            total_fats += daily["fats_g"]
        
        # Calculate percentages
        percentages = calculate_macro_percentages(total_protein, total_carbs, total_fats)
        
        return {
            "week": week,
            "year": year,
            "daily_breakdown": daily_breakdown,
            "weekly_totals": {
                "total_calories": total_calories,
                "total_protein": total_protein,
                "total_carbs": total_carbs,
                "total_fats": total_fats,
                "protein_percentage": percentages["protein"],
                "carbs_percentage": percentages["carbs"],
                "fats_percentage": percentages["fats"]
            },
            "average_daily_calories": round(total_calories / 7, 1) if total_calories > 0 else 0
        }
    except Exception as e:
        logger.error(f"Error calculating weekly nutrition: {str(e)}")
        return {
            "week": week,
            "year": year,
            "daily_breakdown": [],
            "weekly_totals": {},
            "average_daily_calories": 0
        }


def calculate_calorie_deficit(user_id: str, date: str) -> float:
    """
    Calculate calorie deficit for a day.
    
    Args:
        user_id: User ID
        date: Date in YYYY-MM-DD format
    
    Returns:
        Calorie deficit (negative = deficit, positive = surplus)
    """
    try:
        target_date = datetime.strptime(date, "%Y-%m-%d").date()
        
        # Get burned calories from workouts
        burned = db.session.query(func.sum(Workout.total_calories_burned)).filter(
            Workout.user_id == user_id,
            func.date(Workout.workout_date) == target_date,
            Workout.status == "completed"
        ).scalar() or 0
        
        # Get consumed calories from meals
        consumed = db.session.query(func.sum(Meal.total_calories)).filter(
            Meal.user_id == user_id,
            func.date(Meal.meal_date) == target_date
        ).scalar() or 0
        
        # Deficit = consumed - burned (negative = deficit)
        deficit = consumed - burned
        return round(deficit, 1)
    except Exception as e:
        logger.error(f"Error calculating calorie deficit: {str(e)}")
        return 0.0


def calculate_macro_percentages(protein_g: float, carbs_g: float, fats_g: float) -> Dict[str, float]:
    """
    Calculate macro percentages from gram amounts.
    
    Args:
        protein_g: Protein in grams
        carbs_g: Carbs in grams
        fats_g: Fats in grams
    
    Returns:
        Dictionary with protein, carbs, fats percentages
    """
    try:
        # Convert grams to calories
        protein_cal = protein_g * 4
        carbs_cal = carbs_g * 4
        fats_cal = fats_g * 9
        
        total_cal = protein_cal + carbs_cal + fats_cal
        
        if total_cal == 0:
            return {"protein": 0, "carbs": 0, "fats": 0}
        
        return {
            "protein": round(protein_cal / total_cal * 100, 1),
            "carbs": round(carbs_cal / total_cal * 100, 1),
            "fats": round(fats_cal / total_cal * 100, 1)
        }
    except Exception as e:
        logger.error(f"Error calculating macro percentages: {str(e)}")
        return {"protein": 0, "carbs": 0, "fats": 0}
