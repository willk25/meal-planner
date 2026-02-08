#!/usr/bin/env python3
"""
Recipe Upload Tool

Allows users to upload recipes via text, JSON, or interactive input
and automatically adds them to curated_recipes.json with proper formatting
and metadata detection.
"""

import json
import re
import argparse
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple

# Import auto-detection functions from curate_recipes.py
try:
    from curate_recipes import (
        detect_protein_source,
        get_meal_type,
        get_difficulty,
        PROTEIN_SOURCES
    )
except ImportError:
    # Fallback if curate_recipes.py is not available
    PROTEIN_SOURCES = {
        "chicken": ["chicken", "poultry"],
        "beef": ["beef", "steak", "ground beef", "chuck", "sirloin", "ribeye", "brisket"],
        "pork": ["pork", "bacon", "ham", "sausage", "prosciutto"],
        "seafood": ["fish", "salmon", "tuna", "shrimp", "cod", "halibut", "tilapia", "mahi", "trout", "sea bass", "crab", "lobster", "scallop"],
        "turkey": ["turkey"],
        "lamb": ["lamb"],
        "eggs": ["egg", "eggs", "frittata", "omelet", "omelette"],
    }
    
    def detect_protein_source(recipe):
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
    
    def get_meal_type(recipe):
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
    
    def get_difficulty(recipe):
        """Estimate difficulty based on ingredients and steps."""
        num_ingredients = len(recipe.get("ingredients", []))
        num_steps = len(recipe.get("directions", []))
        
        if num_ingredients <= 6 and num_steps <= 4:
            return "easy"
        elif num_ingredients <= 10 and num_steps <= 7:
            return "medium"
        else:
            return "involved"

CURATED_RECIPES_JSON = Path(__file__).parent / "curated_recipes.json"


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


def parse_json_recipe(json_str: str) -> Dict[str, Any]:
    """Parse a JSON format recipe."""
    try:
        recipe = json.loads(json_str)
        return recipe
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON format: {e}")


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


def load_existing_recipes() -> List[Dict[str, Any]]:
    """Load existing recipes from database or JSON file."""
    # MULTI-USER: When enabling user authentication, uncomment this section:
    # try:
    #     from db_layer import get_current_user_id, load_user_recipes
    #     user_id = get_current_user_id()
    #     if user_id:
    #         # User is authenticated, load only their recipes
    #         return load_user_recipes(user_id)
    #     else:
    #         # No user authenticated - either return empty or all recipes
    #         # Option 1: Return empty (require login to see recipes)
    #         # return []
    #         # Option 2: Return all recipes (allow anonymous viewing)
    #         from db_layer import load_recipes
    #         return load_recipes()
    # except ImportError:
    #     pass
    
    try:
        from db_layer import load_recipes
        return load_recipes()
    except ImportError:
        # Fallback to direct JSON if db_layer not available
        if not CURATED_RECIPES_JSON.exists():
            return []
        
        try:
            with open(CURATED_RECIPES_JSON, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"⚠️  Warning: Could not load existing recipes: {e}")
            return []


def check_duplicate(recipe: Dict[str, Any], existing_recipes: List[Dict[str, Any]]) -> bool:
    """Check if recipe title already exists."""
    title = recipe.get('title', '').strip().lower()
    for existing in existing_recipes:
        if existing.get('title', '').strip().lower() == title:
            return True
    return False


def create_backup() -> Path:
    """Create a backup of curated_recipes.json before writing."""
    if not CURATED_RECIPES_JSON.exists():
        return None
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = CURATED_RECIPES_JSON.parent / f"curated_recipes_backup_{timestamp}.json"
    
    try:
        import shutil
        shutil.copy2(CURATED_RECIPES_JSON, backup_path)
        return backup_path
    except Exception as e:
        print(f"⚠️  Warning: Could not create backup: {e}")
        return None


def save_recipes(recipes: List[Dict[str, Any]]) -> bool:
    """Save recipes to database or JSON file."""
    try:
        from db_layer import save_recipes as db_save_recipes
        return db_save_recipes(recipes)
    except ImportError:
        # Fallback to direct JSON if db_layer not available
        try:
            # Create backup
            backup_path = create_backup()
            if backup_path:
                print(f"📦 Backup created: {backup_path.name}")
            
            # Write recipes
            with open(CURATED_RECIPES_JSON, 'w', encoding='utf-8') as f:
                json.dump(recipes, f, indent=2, ensure_ascii=False)
            
            return True
        except Exception as e:
            print(f"❌ Error saving recipes: {e}")
            return False


def add_recipe(recipe: Dict[str, Any], skip_duplicate_check: bool = False) -> Tuple[bool, str]:
    """
    Add a recipe to database or JSON file.
    
    Args:
        recipe: Recipe dictionary
        skip_duplicate_check: If True, skip duplicate checking
    
    Returns:
        (success, message)
    """
    # Validate
    is_valid, errors = validate_recipe(recipe)
    if not is_valid:
        return (False, f"Validation failed: {', '.join(errors)}")
    
    # Enrich with auto-detected metadata
    recipe = enrich_recipe(recipe)
    
    # MULTI-USER: When enabling user authentication, uncomment this section:
    # from db_layer import get_current_user_id, add_user_recipe
    # user_id = get_current_user_id()
    # if user_id:
    #     # User is authenticated, use user-specific function
    #     if skip_duplicate_check:
    #         # For skip_duplicate_check with users, we need special handling
    #         existing_recipes = load_existing_recipes()
    #         recipe['user_id'] = user_id
    #         existing_recipes.append(recipe)
    #         if save_recipes(existing_recipes):
    #             return (True, f"✅ Successfully added recipe: '{recipe['title']}'")
    #         else:
    #             return (False, "Failed to save recipes")
    #     else:
    #         return add_user_recipe(recipe, user_id)
    # else:
    #     # No user authenticated - either allow anonymous or require login
    #     # Option 1: Allow anonymous (current behavior)
    #     # Option 2: Require login (uncomment next line)
    #     # return (False, "Please sign in to add recipes")
    
    # Try using db_layer first (supports Supabase)
    try:
        from db_layer import add_recipe as db_add_recipe
        if skip_duplicate_check:
            # For skip_duplicate_check, we need to use the old method
            # because db_layer.add_recipe doesn't support this flag
            existing_recipes = load_existing_recipes()
            existing_recipes.append(recipe)
            if save_recipes(existing_recipes):
                return (True, f"✅ Successfully added recipe: '{recipe['title']}'")
            else:
                return (False, "Failed to save recipes")
        else:
            return db_add_recipe(recipe)
    except ImportError:
        # Fallback to direct JSON if db_layer not available
        existing_recipes = load_existing_recipes()
        
        # Check for duplicates
        if not skip_duplicate_check and check_duplicate(recipe, existing_recipes):
            return (False, f"Duplicate recipe found: '{recipe['title']}' already exists")
        
        # Add to list
        existing_recipes.append(recipe)
        
        # Save
        if save_recipes(existing_recipes):
            return (True, f"✅ Successfully added recipe: '{recipe['title']}'")
        else:
            return (False, "Failed to save recipes")


def preview_recipe(recipe: Dict[str, Any]) -> None:
    """Print a preview of the recipe."""
    print("\n" + "=" * 60)
    print("📋 RECIPE PREVIEW")
    print("=" * 60)
    print(f"Title: {recipe.get('title', 'N/A')}")
    print(f"Ingredients: {len(recipe.get('ingredients', []))} items")
    print(f"Directions: {len(recipe.get('directions', []))} steps")
    print(f"Protein Source: {recipe.get('protein_source', 'N/A')}")
    print(f"Meal Type: {recipe.get('meal_type', 'N/A')}")
    print(f"Difficulty: {recipe.get('difficulty', 'N/A')}")
    if recipe.get('rating'):
        print(f"Rating: {recipe['rating']} ⭐")
    if recipe.get('protein'):
        print(f"Protein: {recipe['protein']}g")
    print("=" * 60)


def interactive_mode():
    """Interactive mode for entering recipes."""
    print("\n🍽️  Interactive Recipe Upload")
    print("=" * 60)
    print("Enter your recipe. Type 'DONE' on a new line when finished.\n")
    
    lines = []
    while True:
        try:
            line = input()
            if line.strip().upper() == 'DONE':
                break
            lines.append(line)
        except EOFError:
            break
    
    text = '\n'.join(lines)
    recipe = parse_text_recipe(text)
    
    # Enrich with metadata
    recipe = enrich_recipe(recipe)
    
    # Preview
    preview_recipe(recipe)
    
    # Confirm
    response = input("\nAdd this recipe? (y/n): ").strip().lower()
    if response == 'y':
        success, message = add_recipe(recipe)
        print(f"\n{message}")
        return success
    else:
        print("\n❌ Recipe upload cancelled.")
        return False


def process_file(file_path: Path, format_type: str = 'auto', skip_preview: bool = False, skip_duplicate_check: bool = False) -> bool:
    """Process a recipe file."""
    if not file_path.exists():
        print(f"❌ File not found: {file_path}")
        return False
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"❌ Error reading file: {e}")
        return False
    
    # Auto-detect format
    if format_type == 'auto':
        if file_path.suffix.lower() == '.json':
            format_type = 'json'
        else:
            format_type = 'text'
    
    # Parse
    try:
        if format_type == 'json':
            recipe = parse_json_recipe(content)
        else:
            recipe = parse_text_recipe(content)
    except Exception as e:
        print(f"❌ Error parsing recipe: {e}")
        return False
    
    # Enrich
    recipe = enrich_recipe(recipe)
    
    # Preview (unless skipped)
    if not skip_preview:
        preview_recipe(recipe)
        # Confirm
        response = input("\nAdd this recipe? (y/n): ").strip().lower()
        if response != 'y':
            print("\n❌ Recipe upload cancelled.")
            return False
    
    # Add recipe
    success, message = add_recipe(recipe, skip_duplicate_check=skip_duplicate_check)
    if not skip_preview:
        print(f"\n{message}")
    return success


def main():
    """Main CLI interface."""
    parser = argparse.ArgumentParser(
        description='Upload recipes to curated_recipes.json',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Upload from text file
  python upload_recipe.py recipe.txt
  
  # Upload from JSON file
  python upload_recipe.py recipe.json --format json
  
  # Interactive mode
  python upload_recipe.py --interactive
  
  # Batch upload (multiple files)
  python upload_recipe.py recipes/*.txt
  
  # Skip duplicate check
  python upload_recipe.py recipe.txt --skip-duplicate-check
        """
    )
    
    parser.add_argument(
        'files',
        nargs='*',
        type=Path,
        help='Recipe file(s) to upload (text or JSON format)'
    )
    
    parser.add_argument(
        '--format',
        choices=['auto', 'text', 'json'],
        default='auto',
        help='Input format (default: auto-detect from file extension)'
    )
    
    parser.add_argument(
        '--interactive',
        '-i',
        action='store_true',
        help='Enter recipe interactively'
    )
    
    parser.add_argument(
        '--skip-duplicate-check',
        action='store_true',
        help='Skip duplicate checking (not recommended)'
    )
    
    parser.add_argument(
        '--no-preview',
        action='store_true',
        help='Skip preview and confirmation (for batch processing)'
    )
    
    args = parser.parse_args()
    
    # Interactive mode
    if args.interactive:
        interactive_mode()
        return
    
    # File mode
    if not args.files:
        parser.print_help()
        print("\n❌ No files specified. Use --interactive for interactive mode.")
        sys.exit(1)
    
    success_count = 0
    for file_path in args.files:
        print(f"\n📄 Processing: {file_path.name}")
        if process_file(file_path, args.format, skip_preview=args.no_preview, skip_duplicate_check=args.skip_duplicate_check):
            success_count += 1
    
    print(f"\n✅ Successfully uploaded {success_count}/{len(args.files)} recipe(s)")


if __name__ == "__main__":
    main()
