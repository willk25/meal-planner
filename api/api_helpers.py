#!/usr/bin/env python3
"""
Minimal helper functions for API endpoints.
These are self-contained to avoid importing from parent directory,
which would cause Vercel to bundle large files.
"""

import re
from datetime import datetime
from typing import Dict, Any, List, Tuple

# Dummy import to ensure Vercel bundles db_layer.py (wrapped to not crash if it fails)
try:
    import db_layer  # noqa: F401
except ImportError:
    pass  # Will use importlib.util at runtime instead

# Protein source detection (minimal version)
PROTEIN_SOURCES = {
    "chicken": ["chicken", "poultry"],
    "beef": ["beef", "steak", "ground beef", "chuck", "sirloin", "ribeye", "brisket"],
    "pork": ["pork", "bacon", "ham", "sausage", "prosciutto"],
    "seafood": ["fish", "salmon", "tuna", "shrimp", "cod", "halibut", "tilapia", "mahi", "trout", "sea bass", "crab", "lobster", "scallop"],
    "turkey": ["turkey"],
    "lamb": ["lamb"],
    "eggs": ["egg", "eggs", "frittata", "omelet", "omelette"],
}


def detect_protein_source(recipe: Dict[str, Any]) -> str:
    """Detect the main protein source from title/ingredients/categories."""
    title_lower = recipe.get("title", "").lower()
    categories = recipe.get("categories", [])
    cats_lower = [c.lower() for c in categories] if categories else []
    ingredients = recipe.get("ingredients", [])
    ings_lower = " ".join(ingredients).lower() if ingredients else ""
    all_text = f"{title_lower} {' '.join(cats_lower)} {ings_lower}"
    
    for source, keywords in PROTEIN_SOURCES.items():
        for keyword in keywords:
            if keyword in all_text:
                return source
    return "other"


def get_meal_type(recipe: Dict[str, Any]) -> str:
    """Categorize by meal type."""
    categories = recipe.get("categories", [])
    cats_lower = [c.lower() for c in categories] if categories else []
    title_lower = recipe.get("title", "").lower()
    
    if any(k in cats_lower or k in title_lower for k in ["breakfast", "brunch", "egg"]):
        return "breakfast"
    if any(k in cats_lower for k in ["soup", "stew", "chili"]):
        return "soup"
    if any(k in cats_lower for k in ["salad"]):
        return "salad"
    if any(k in cats_lower for k in ["appetizer", "starter"]):
        return "appetizer"
    return "entree"


def get_difficulty(recipe: Dict[str, Any]) -> str:
    """Estimate difficulty based on ingredients and steps."""
    num_ingredients = len(recipe.get("ingredients", []))
    num_steps = len(recipe.get("directions", []))
    
    if num_ingredients <= 6 and num_steps <= 4:
        return "easy"
    elif num_ingredients <= 10 and num_steps <= 7:
        return "medium"
    else:
        return "involved"


def parse_text_recipe(text: str) -> Dict[str, Any]:
    """
    Parse a simple text format recipe.
    
    Expected format:
    Title: Recipe Name
    Ingredients:
    - ingredient 1
    - ingredient 2
    Directions:
    1. Step 1
    2. Step 2
    """
    recipe = {}
    lines = text.strip().split('\n')
    
    current_section = None
    ingredients = []
    directions = []
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if not line:
            i += 1
            continue
        
        # Title
        if line.lower().startswith('title:'):
            recipe['title'] = line.split(':', 1)[1].strip()
            i += 1
            continue
        
        # Ingredients section
        if line.lower().startswith('ingredients:'):
            current_section = 'ingredients'
            i += 1
            continue
        
        # Directions section
        if line.lower().startswith('directions:'):
            current_section = 'directions'
            i += 1
            continue
        
        # Optional fields
        if ':' in line and current_section is None:
            key, value = line.split(':', 1)
            key = key.strip().lower()
            value = value.strip()
            
            # Map common variations
            if key in ['protein source', 'protein_source']:
                recipe['protein_source'] = value.lower()
            elif key in ['meal type', 'meal_type']:
                recipe['meal_type'] = value.lower()
            elif key in ['difficulty']:
                recipe['difficulty'] = value.lower()
            elif key in ['rating']:
                try:
                    recipe['rating'] = float(value)
                except ValueError:
                    pass
            elif key in ['protein', 'protein (g)']:
                try:
                    recipe['protein'] = float(value)
                except ValueError:
                    pass
            elif key in ['calories']:
                try:
                    recipe['calories'] = float(value)
                except ValueError:
                    pass
            elif key in ['description', 'desc']:
                recipe['desc'] = value
            elif key in ['source']:
                recipe['source'] = value
            i += 1
            continue
        
        # Collect ingredients
        if current_section == 'ingredients':
            # Remove bullet points and numbering
            ingredient = re.sub(r'^[-•*]\s*', '', line)
            ingredient = re.sub(r'^\d+\.\s*', '', ingredient)
            if ingredient.strip():
                ingredients.append(ingredient.strip())
        
        # Collect directions
        elif current_section == 'directions':
            # Remove numbering if present
            direction = re.sub(r'^\d+\.\s*', '', line)
            if direction.strip():
                directions.append(direction.strip())
        
        i += 1
    
    if ingredients:
        recipe['ingredients'] = ingredients
    if directions:
        recipe['directions'] = directions
    
    return recipe


def enrich_recipe(recipe: Dict[str, Any]) -> Dict[str, Any]:
    """
    Add auto-detected metadata to recipe.
    """
    # Ensure ingredients and directions are lists
    if isinstance(recipe.get('ingredients'), str):
        recipe['ingredients'] = [i.strip() for i in recipe['ingredients'].split('\n') if i.strip()]
    if isinstance(recipe.get('directions'), str):
        recipe['directions'] = [d.strip() for d in recipe['directions'].split('\n') if d.strip()]
    
    # Auto-detect protein_source if not provided
    if 'protein_source' not in recipe or not recipe['protein_source']:
        recipe['protein_source'] = detect_protein_source(recipe)
    
    # Auto-detect meal_type if not provided
    if 'meal_type' not in recipe or not recipe['meal_type']:
        recipe['meal_type'] = get_meal_type(recipe)
    
    # Auto-calculate num_ingredients and num_steps
    recipe['num_ingredients'] = len(recipe.get('ingredients', []))
    recipe['num_steps'] = len(recipe.get('directions', []))
    
    # Auto-detect difficulty if not provided
    if 'difficulty' not in recipe or not recipe['difficulty']:
        recipe['difficulty'] = get_difficulty(recipe)
    
    # Add date if not present
    if 'date' not in recipe:
        recipe['date'] = datetime.now().isoformat() + 'Z'
    
    return recipe


def validate_recipe(recipe: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate recipe has required fields.
    Returns (is_valid, list_of_errors).
    """
    errors = []
    
    if not recipe.get('title') or not recipe['title'].strip():
        errors.append("Missing required field: title")
    
    ingredients = recipe.get('ingredients', [])
    if not ingredients or len(ingredients) == 0:
        errors.append("Missing required field: ingredients (must have at least 1)")
    elif isinstance(ingredients, str):
        errors.append("Ingredients must be a list/array, not a string")
    
    directions = recipe.get('directions', [])
    if not directions or len(directions) == 0:
        errors.append("Missing required field: directions (must have at least 1)")
    elif isinstance(directions, str):
        errors.append("Directions must be a list/array, not a string")
    
    return (len(errors) == 0, errors)


def add_recipe_to_db(recipe: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Add a recipe to the database using db_layer.
    Uses importlib to load db_layer directly from file path (reliable in Vercel).
    """
    try:
        import importlib.util
        import sys
        from pathlib import Path
        
        # Get the api directory (where this file and db_layer.py are located)
        api_dir = Path(__file__).parent
        
        # Load db_layer using importlib (more reliable in Vercel)
        db_layer_path = api_dir / 'db_layer.py'
        if not db_layer_path.exists():
            return (False, f"Database layer not found at {db_layer_path}")
        
        spec = importlib.util.spec_from_file_location("db_layer", db_layer_path)
        if spec is None or spec.loader is None:
            return (False, f"Failed to create spec for db_layer at {db_layer_path}")
        
        db_layer = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(db_layer)
        db_add_recipe = db_layer.add_recipe
        
        return db_add_recipe(recipe)
    except ImportError as e:
        return (False, f"Database layer not available: {str(e)}")
    except Exception as e:
        return (False, f"Error adding recipe: {str(e)}")
