"""
Swagger/OpenAPI configuration for Flasgger
"""

SWAGGER_CONFIG = {
    "headers": [],
    "specs": [
        {
            "endpoint": 'apispec',
            "route": '/apispec.json',
            "rule_filter": lambda rule: True,
            "model_filter": lambda tag: True,
        }
    ],
    "static_url_path": "/flasgger_static",
    "swagger_ui": True,
    "specs_route": "/api/docs"
}

SWAGGER_TEMPLATE = {
    "swagger": "2.0",
    "info": {
        "title": "Fitness Tracker API",
        "description": "A comprehensive RESTful API for fitness tracking, nutrition logging, goal management, and personal training",
        "contact": {
            "email": "support@fitnessapi.com",
            "name": "API Support"
        },
        "version": "1.0.1"
    },
    "host": "localhost:5000",
    "basePath": "/api",
    "schemes": ["http"],
    "securityDefinitions": {
        "Bearer": {
            "type": "apiKey",
            "name": "Authorization",
            "in": "header",
            "description": "JWT authentication token. Format: Bearer <token>"
        },
        "GoogleOAuth": {
            "type": "oauth2",
            "authorizationUrl": "https://accounts.google.com/o/oauth2/v2/auth",
            "tokenUrl": "https://oauth2.googleapis.com/token",
            "flow": "implicit",
            "scopes": {
                "openid": "OpenID authentication",
                "profile": "User profile information",
                "email": "User email address"
            }
        }
    },
    "definitions": {
        "User": {
            "type": "object",
            "properties": {
                "user_id": {"type": "string", "description": "UUID identifier"},
                "username": {"type": "string", "description": "Unique username"},
                "email": {"type": "string", "description": "User email"},
                "age": {"type": "number", "description": "User age"},
                "current_weight": {"type": "number", "description": "Current weight in kg"},
                "target_weight": {"type": "number", "description": "Target weight in kg"},
                "height": {"type": "number", "description": "Height in cm"},
                "profile_picture": {"type": "string", "description": "Profile picture URL"}
            }
        },
        "Workout": {
            "type": "object",
            "properties": {
                "workout_id": {"type": "string"},
                "user_id": {"type": "string"},
                "workout_date": {"type": "string", "format": "date"},
                "workout_type": {"type": "string", "enum": ["strength", "cardio", "flexibility", "mixed"]},
                "status": {"type": "string", "enum": ["in_progress", "completed", "cancelled"]},
                "total_duration_minutes": {"type": "integer"},
                "total_calories_burned": {"type": "number"}
            }
        },
        "Meal": {
            "type": "object",
            "properties": {
                "meal_id": {"type": "string"},
                "user_id": {"type": "string"},
                "meal_type": {"type": "string", "enum": ["breakfast", "lunch", "dinner", "snack"]},
                "meal_date": {"type": "string", "format": "date"},
                "total_calories": {"type": "number"},
                "protein_g": {"type": "number"},
                "carbs_g": {"type": "number"},
                "fats_g": {"type": "number"}
            }
        },
        "Goal": {
            "type": "object",
            "properties": {
                "goal_id": {"type": "string"},
                "user_id": {"type": "string"},
                "goal_type": {"type": "string", "enum": ["weight_loss", "muscle_gain", "endurance"]},
                "target_value": {"type": "number"},
                "current_progress": {"type": "number"},
                "target_date": {"type": "string", "format": "date"},
                "status": {"type": "string", "enum": ["active", "completed", "abandoned"]}
            }
        },
        "ErrorResponse": {
            "type": "object",
            "properties": {
                "success": {"type": "boolean"},
                "error": {
                    "type": "object",
                    "properties": {
                        "type": {"type": "string"},
                        "message": {"type": "string"},
                        "code": {"type": "string"}
                    }
                }
            }
        },
        "SuccessResponse": {
            "type": "object",
            "properties": {
                "success": {"type": "boolean"},
                "message": {"type": "string"},
                "data": {"type": "object"}
            }
        }
    }
}
