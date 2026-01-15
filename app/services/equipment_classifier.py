"""
Equipment Classifier Service - Accurate gym equipment identification using ML
Uses a combination of image classification and keyword detection for robust predictions
"""

import os
import logging
from typing import Tuple, List, Dict, Optional
import json

logger = logging.getLogger(__name__)

# Try to import ML libraries
ML_AVAILABLE = False
CLASSIFIER = None
CLIP_MODEL = None
CLIP_PROCESSOR = None

try:
    from transformers import CLIPProcessor, CLIPModel
    from PIL import Image
    import torch
    ML_AVAILABLE = True
    logger.info("✅ ML libraries loaded successfully")
except ImportError as e:
    logger.warning(f"⚠️ ML libraries not available: {e}")
    logger.warning("⚠️ Will use fallback classification based on filename/metadata")


# Comprehensive gym equipment database with exercises
GYM_EQUIPMENT_DATABASE = {
    "barbell": {
        "display_name": "Barbell",
        "keywords": ["barbell", "bar", "olympic", "weight bar", "straight bar"],
        "primary_muscles": ["chest", "back", "legs", "shoulders"],
        "secondary_muscles": ["arms", "core"],
        "exercises": [
            {"name": "Barbell Bench Press", "muscle": "chest", "difficulty": "intermediate"},
            {"name": "Barbell Squat", "muscle": "legs", "difficulty": "intermediate"},
            {"name": "Barbell Deadlift", "muscle": "back", "difficulty": "advanced"},
            {"name": "Barbell Row", "muscle": "back", "difficulty": "intermediate"},
            {"name": "Overhead Press", "muscle": "shoulders", "difficulty": "intermediate"},
            {"name": "Barbell Curl", "muscle": "arms", "difficulty": "beginner"}
        ]
    },
    "dumbbell": {
        "display_name": "Dumbbell",
        "keywords": ["dumbbell", "dumbell", "db", "free weight", "hand weight"],
        "primary_muscles": ["chest", "shoulders", "arms"],
        "secondary_muscles": ["back", "core"],
        "exercises": [
            {"name": "Dumbbell Bench Press", "muscle": "chest", "difficulty": "beginner"},
            {"name": "Dumbbell Shoulder Press", "muscle": "shoulders", "difficulty": "beginner"},
            {"name": "Dumbbell Curl", "muscle": "arms", "difficulty": "beginner"},
            {"name": "Dumbbell Row", "muscle": "back", "difficulty": "beginner"},
            {"name": "Dumbbell Fly", "muscle": "chest", "difficulty": "intermediate"},
            {"name": "Lateral Raise", "muscle": "shoulders", "difficulty": "beginner"}
        ]
    },
    "bench": {
        "display_name": "Bench Press Station",
        "keywords": ["bench", "bench press", "flat bench", "incline", "decline"],
        "primary_muscles": ["chest"],
        "secondary_muscles": ["shoulders", "arms"],
        "exercises": [
            {"name": "Flat Bench Press", "muscle": "chest", "difficulty": "intermediate"},
            {"name": "Incline Bench Press", "muscle": "chest", "difficulty": "intermediate"},
            {"name": "Decline Bench Press", "muscle": "chest", "difficulty": "intermediate"},
            {"name": "Close-Grip Bench Press", "muscle": "arms", "difficulty": "intermediate"},
            {"name": "Dumbbell Pullover", "muscle": "chest", "difficulty": "intermediate"}
        ]
    },
    "squat_rack": {
        "display_name": "Squat Rack / Power Rack",
        "keywords": ["squat rack", "power rack", "cage", "squat", "rack"],
        "primary_muscles": ["legs", "back"],
        "secondary_muscles": ["core", "shoulders"],
        "exercises": [
            {"name": "Barbell Squat", "muscle": "legs", "difficulty": "intermediate"},
            {"name": "Front Squat", "muscle": "legs", "difficulty": "advanced"},
            {"name": "Rack Pull", "muscle": "back", "difficulty": "intermediate"},
            {"name": "Standing Calf Raise", "muscle": "legs", "difficulty": "beginner"},
            {"name": "Overhead Press", "muscle": "shoulders", "difficulty": "intermediate"}
        ]
    },
    "cable_machine": {
        "display_name": "Cable Machine",
        "keywords": ["cable", "pulley", "cable crossover", "functional trainer"],
        "primary_muscles": ["chest", "back", "arms"],
        "secondary_muscles": ["shoulders", "core"],
        "exercises": [
            {"name": "Cable Fly", "muscle": "chest", "difficulty": "beginner"},
            {"name": "Lat Pulldown", "muscle": "back", "difficulty": "beginner"},
            {"name": "Tricep Pushdown", "muscle": "arms", "difficulty": "beginner"},
            {"name": "Cable Curl", "muscle": "arms", "difficulty": "beginner"},
            {"name": "Face Pull", "muscle": "shoulders", "difficulty": "beginner"},
            {"name": "Cable Row", "muscle": "back", "difficulty": "beginner"}
        ]
    },
    "treadmill": {
        "display_name": "Treadmill",
        "keywords": ["treadmill", "running machine", "cardio", "run"],
        "primary_muscles": ["cardio", "legs"],
        "secondary_muscles": [],
        "exercises": [
            {"name": "Steady State Running", "muscle": "cardio", "difficulty": "beginner"},
            {"name": "HIIT Intervals", "muscle": "cardio", "difficulty": "intermediate"},
            {"name": "Incline Walking", "muscle": "legs", "difficulty": "beginner"},
            {"name": "Sprint Intervals", "muscle": "cardio", "difficulty": "advanced"}
        ]
    },
    "elliptical": {
        "display_name": "Elliptical Machine",
        "keywords": ["elliptical", "cross trainer", "elliptical trainer"],
        "primary_muscles": ["cardio", "legs"],
        "secondary_muscles": ["arms"],
        "exercises": [
            {"name": "Elliptical Cardio", "muscle": "cardio", "difficulty": "beginner"},
            {"name": "Reverse Elliptical", "muscle": "legs", "difficulty": "beginner"},
            {"name": "High Resistance Intervals", "muscle": "legs", "difficulty": "intermediate"}
        ]
    },
    "rowing_machine": {
        "display_name": "Rowing Machine",
        "keywords": ["rowing", "rower", "erg", "ergometer", "row machine"],
        "primary_muscles": ["back", "cardio"],
        "secondary_muscles": ["arms", "legs"],
        "exercises": [
            {"name": "Steady State Rowing", "muscle": "cardio", "difficulty": "beginner"},
            {"name": "Power Rowing", "muscle": "back", "difficulty": "intermediate"},
            {"name": "HIIT Rowing", "muscle": "cardio", "difficulty": "advanced"}
        ]
    },
    "stationary_bike": {
        "display_name": "Stationary Bike",
        "keywords": ["bike", "cycle", "stationary bike", "spin", "cycling"],
        "primary_muscles": ["cardio", "legs"],
        "secondary_muscles": [],
        "exercises": [
            {"name": "Steady State Cycling", "muscle": "cardio", "difficulty": "beginner"},
            {"name": "Spin Class", "muscle": "cardio", "difficulty": "intermediate"},
            {"name": "Hill Climbs", "muscle": "legs", "difficulty": "intermediate"}
        ]
    },
    "kettlebell": {
        "display_name": "Kettlebell",
        "keywords": ["kettlebell", "kb", "kettle bell"],
        "primary_muscles": ["legs", "shoulders", "core"],
        "secondary_muscles": ["back", "arms"],
        "exercises": [
            {"name": "Kettlebell Swing", "muscle": "legs", "difficulty": "beginner"},
            {"name": "Goblet Squat", "muscle": "legs", "difficulty": "beginner"},
            {"name": "Turkish Get-Up", "muscle": "core", "difficulty": "advanced"},
            {"name": "Kettlebell Clean & Press", "muscle": "shoulders", "difficulty": "intermediate"},
            {"name": "Kettlebell Snatch", "muscle": "shoulders", "difficulty": "advanced"}
        ]
    },
    "pull_up_bar": {
        "display_name": "Pull-up Bar",
        "keywords": ["pull up", "pullup", "chin up", "chinup", "bar", "horizontal bar"],
        "primary_muscles": ["back", "arms"],
        "secondary_muscles": ["core"],
        "exercises": [
            {"name": "Pull-ups", "muscle": "back", "difficulty": "intermediate"},
            {"name": "Chin-ups", "muscle": "arms", "difficulty": "intermediate"},
            {"name": "Hanging Leg Raise", "muscle": "core", "difficulty": "intermediate"},
            {"name": "Muscle-ups", "muscle": "back", "difficulty": "advanced"}
        ]
    },
    "dip_bars": {
        "display_name": "Dip Bars / Parallel Bars",
        "keywords": ["dip", "dips", "parallel bars", "dip station", "dip bar"],
        "primary_muscles": ["chest", "triceps"],
        "secondary_muscles": ["shoulders", "core"],
        "exercises": [
            {"name": "Tricep Dips", "muscle": "triceps", "difficulty": "intermediate"},
            {"name": "Chest Dips", "muscle": "chest", "difficulty": "intermediate"},
            {"name": "Assisted Dips", "muscle": "triceps", "difficulty": "beginner"},
            {"name": "L-Sit", "muscle": "core", "difficulty": "advanced"},
            {"name": "Knee Raises", "muscle": "core", "difficulty": "beginner"}
        ]
    },
    "leg_press": {
        "display_name": "Leg Press Machine",
        "keywords": ["leg press", "press", "leg machine"],
        "primary_muscles": ["legs"],
        "secondary_muscles": ["core"],
        "exercises": [
            {"name": "Leg Press", "muscle": "legs", "difficulty": "beginner"},
            {"name": "Single Leg Press", "muscle": "legs", "difficulty": "intermediate"},
            {"name": "Calf Press", "muscle": "legs", "difficulty": "beginner"}
        ]
    },
    "smith_machine": {
        "display_name": "Smith Machine",
        "keywords": ["smith", "smith machine", "guided barbell"],
        "primary_muscles": ["chest", "legs", "shoulders"],
        "secondary_muscles": ["back", "arms"],
        "exercises": [
            {"name": "Smith Machine Squat", "muscle": "legs", "difficulty": "beginner"},
            {"name": "Smith Machine Bench Press", "muscle": "chest", "difficulty": "beginner"},
            {"name": "Smith Machine Shoulder Press", "muscle": "shoulders", "difficulty": "beginner"},
            {"name": "Smith Machine Lunges", "muscle": "legs", "difficulty": "beginner"}
        ]
    },
    "resistance_band": {
        "display_name": "Resistance Bands",
        "keywords": ["resistance band", "band", "elastic", "tube"],
        "primary_muscles": ["chest", "back", "shoulders"],
        "secondary_muscles": ["arms", "legs"],
        "exercises": [
            {"name": "Band Pull-apart", "muscle": "back", "difficulty": "beginner"},
            {"name": "Band Chest Press", "muscle": "chest", "difficulty": "beginner"},
            {"name": "Band Rows", "muscle": "back", "difficulty": "beginner"},
            {"name": "Band Bicep Curl", "muscle": "arms", "difficulty": "beginner"}
        ]
    },
    "yoga_mat": {
        "display_name": "Yoga Mat / Floor Exercises",
        "keywords": ["mat", "yoga", "floor", "bodyweight"],
        "primary_muscles": ["core", "flexibility"],
        "secondary_muscles": ["legs", "arms"],
        "exercises": [
            {"name": "Plank", "muscle": "core", "difficulty": "beginner"},
            {"name": "Push-ups", "muscle": "chest", "difficulty": "beginner"},
            {"name": "Crunches", "muscle": "core", "difficulty": "beginner"},
            {"name": "Yoga Flow", "muscle": "flexibility", "difficulty": "beginner"},
            {"name": "Mountain Climbers", "muscle": "cardio", "difficulty": "intermediate"}
        ]
    },
    "medicine_ball": {
        "display_name": "Medicine Ball",
        "keywords": ["medicine ball", "med ball", "slam ball", "wall ball"],
        "primary_muscles": ["core", "arms"],
        "secondary_muscles": ["legs", "shoulders"],
        "exercises": [
            {"name": "Medicine Ball Slam", "muscle": "core", "difficulty": "intermediate"},
            {"name": "Wall Ball Shots", "muscle": "legs", "difficulty": "intermediate"},
            {"name": "Russian Twist", "muscle": "core", "difficulty": "beginner"},
            {"name": "Medicine Ball Throw", "muscle": "core", "difficulty": "beginner"}
        ]
    },
    "lat_pulldown": {
        "display_name": "Lat Pulldown Machine",
        "keywords": ["lat", "pulldown", "lat pulldown", "lat machine"],
        "primary_muscles": ["back"],
        "secondary_muscles": ["arms"],
        "exercises": [
            {"name": "Wide Grip Lat Pulldown", "muscle": "back", "difficulty": "beginner"},
            {"name": "Close Grip Lat Pulldown", "muscle": "back", "difficulty": "beginner"},
            {"name": "Behind Neck Pulldown", "muscle": "back", "difficulty": "intermediate"},
            {"name": "V-Bar Pulldown", "muscle": "back", "difficulty": "beginner"}
        ]
    }
}

# ImageNet labels that map to gym equipment
IMAGENET_TO_EQUIPMENT = {
    "barbell": "barbell",
    "dumbbell": "dumbbell",
    "weight": "dumbbell",
    "gym": "cable_machine",
    "bench": "bench",
    "treadmill": "treadmill",
    "bicycle": "stationary_bike",
    "bike": "stationary_bike",
    "rowing": "rowing_machine",
    "mattress": "yoga_mat",
    "mat": "yoga_mat",
    "horizontal bar": "pull_up_bar",
    "parallel bars": "pull_up_bar",
    "punching bag": "cable_machine",
    "exercise equipment": "cable_machine",
}


def init_classifier():
    """
    Initialize the CLIP model for zero-shot image classification.
    Models are cached locally after first download (~2-5 minutes first run).
    Subsequent runs use cached version (< 5 seconds startup).
    """
    global CLIP_MODEL, CLIP_PROCESSOR, ML_AVAILABLE
    
    if not ML_AVAILABLE:
        return None
    
    try:
        logger.info("📦 Loading CLIP model from Hugging Face (uses local cache if available)...")
        # Use CLIP model which is excellent for zero-shot classification
        # It can match images to text descriptions of gym equipment
        CLIP_MODEL = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
        CLIP_PROCESSOR = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
        logger.info("✅ CLIP classifier initialized successfully (from cache if available)")
        return CLIP_MODEL
    except Exception as e:
        logger.error(f"❌ Failed to initialize CLIP classifier: {e}")
        ML_AVAILABLE = False
        return None


def analyze_filename(filename: str) -> Tuple[Optional[str], float]:
    """
    Analyze filename for equipment keywords
    
    Args:
        filename: Name of the uploaded file
        
    Returns:
        Tuple of (equipment_key, confidence) or (None, 0)
    """
    filename_lower = filename.lower()
    
    for equip_key, equip_data in GYM_EQUIPMENT_DATABASE.items():
        for keyword in equip_data["keywords"]:
            if keyword in filename_lower:
                return equip_key, 0.75  # Medium-high confidence for filename match
    
    return None, 0.0


def analyze_image_with_ml(filepath: str) -> Tuple[Optional[str], float]:
    """
    Use CLIP model to classify the image against gym equipment descriptions
    
    Args:
        filepath: Path to the image file
        
    Returns:
        Tuple of (equipment_key, confidence)
    """
    global CLIP_MODEL, CLIP_PROCESSOR
    
    if not ML_AVAILABLE:
        logger.warning("ML not available, skipping image analysis")
        return None, 0.0
    
    if CLIP_MODEL is None:
        logger.info("Initializing CLIP model...")
        init_classifier()
        if CLIP_MODEL is None:
            logger.error("Failed to initialize CLIP model")
            return None, 0.0
    
    try:
        logger.info(f"Loading image from: {filepath}")
        # Load image
        image = Image.open(filepath).convert("RGB")
        logger.info(f"Image loaded successfully: {image.size}")
        
        # Create text descriptions for each equipment type
        equipment_descriptions = []
        equipment_keys = []
        
        for equip_key, equip_data in GYM_EQUIPMENT_DATABASE.items():
            # Create a descriptive text for this equipment
            display_name = equip_data["display_name"]
            equipment_descriptions.append(f"a photo of {display_name}")
            equipment_descriptions.append(f"gym equipment: {display_name}")
            equipment_keys.append(equip_key)
            equipment_keys.append(equip_key)
        
        logger.info(f"Created {len(equipment_descriptions)} text descriptions for {len(set(equipment_keys))} equipment types")
        
        logger.info("Running CLIP processor...")
        inputs = CLIP_PROCESSOR(
            text=equipment_descriptions,
            images=image,
            return_tensors="pt",
            padding=True
        )
        
        # Move inputs to the same device as the model
        device = next(CLIP_MODEL.parameters()).device
        logger.info(f"CLIP model device: {device}")
        inputs = {k: v.to(device) if hasattr(v, 'to') else v for k, v in inputs.items()}
        
        logger.info("Running CLIP model inference...")
        
        # Get similarity scores
        with torch.no_grad():
            outputs = CLIP_MODEL(**inputs)
            logits_per_image = outputs.logits_per_image
            probs = logits_per_image.softmax(dim=1)
        
        # Get the best match
        best_idx = probs[0].argmax().item()
        best_confidence = probs[0][best_idx].item()
        best_equipment = equipment_keys[best_idx]
        
        logger.info(f"✅ CLIP classification result: {best_equipment} with confidence {best_confidence:.2%}")
        
        # Log top 3 predictions for debugging
        top_indices = probs[0].argsort(descending=True)[:6]
        logger.info("🎯 Top predictions:")
        for idx in top_indices:
            equip = equipment_keys[idx.item()]
            conf = probs[0][idx].item()
            logger.info(f"  - {equip}: {conf:.2%}")
        
        return best_equipment, best_confidence
        
    except Exception as e:
        logger.error(f"❌ CLIP classification error: {e}")
        import traceback
        logger.error(traceback.format_exc())
    
    return None, 0.0


def classify_equipment(filepath: str, filename: str) -> Tuple[str, float, str]:
    """
    Main classification function - combines multiple methods for accuracy
    
    Args:
        filepath: Full path to the image file
        filename: Original filename
        
    Returns:
        Tuple of (equipment_key, confidence, display_name)
    """
    best_match = None
    best_confidence = 0.0
    
    # Method 1: Analyze filename
    filename_match, filename_conf = analyze_filename(filename)
    if filename_match and filename_conf > best_confidence:
        best_match = filename_match
        best_confidence = filename_conf
    
    # Method 2: ML-based image classification
    ml_match, ml_conf = analyze_image_with_ml(filepath)
    if ml_match and ml_conf > best_confidence:
        best_match = ml_match
        best_confidence = ml_conf
    
    # If still no match, default to dumbbell with low confidence
    if not best_match:
        best_match = "dumbbell"
        best_confidence = 0.5
    
    # Get display name
    equipment_data = GYM_EQUIPMENT_DATABASE.get(best_match, {})
    display_name = equipment_data.get("display_name", "Unknown Equipment")
    
    return best_match, best_confidence, display_name


def get_exercises_for_equipment(equipment_key: str, limit: int = 6) -> List[Dict]:
    """
    Get recommended exercises for the identified equipment
    
    Args:
        equipment_key: Key in GYM_EQUIPMENT_DATABASE
        limit: Maximum number of exercises to return
        
    Returns:
        List of exercise dictionaries
    """
    equipment_data = GYM_EQUIPMENT_DATABASE.get(equipment_key)
    
    if not equipment_data:
        # Fallback to dumbbell exercises
        equipment_data = GYM_EQUIPMENT_DATABASE.get("dumbbell", {})
    
    exercises = equipment_data.get("exercises", [])[:limit]
    
    # Add estimated calories and format for frontend
    result = []
    for ex in exercises:
        result.append({
            "name": ex["name"],
            "primary_muscle": ex["muscle"],
            "difficulty": ex["difficulty"],
            "estimated_calories_per_set": 8 if ex["difficulty"] == "beginner" else (12 if ex["difficulty"] == "intermediate" else 15),
            "recommended_sets": 3,
            "recommended_reps": 10 if ex["muscle"] != "cardio" else None,
            "recommended_duration": 300 if ex["muscle"] == "cardio" else None  # 5 minutes for cardio
        })
    
    return result


def get_equipment_info(equipment_key: str) -> Dict:
    """
    Get detailed information about equipment
    
    Args:
        equipment_key: Key in GYM_EQUIPMENT_DATABASE
        
    Returns:
        Equipment info dictionary
    """
    equipment_data = GYM_EQUIPMENT_DATABASE.get(equipment_key, {})
    
    return {
        "key": equipment_key,
        "display_name": equipment_data.get("display_name", "Unknown"),
        "primary_muscles": equipment_data.get("primary_muscles", []),
        "secondary_muscles": equipment_data.get("secondary_muscles", []),
        "total_exercises": len(equipment_data.get("exercises", []))
    }
