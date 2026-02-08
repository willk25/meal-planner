#!/usr/bin/env python3
"""
Database abstraction layer for recipes.
Supports both JSON file storage (fallback) and Supabase (when configured).
Falls back to JSON if Supabase is unavailable or fails.
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime

# Load environment variables from .env file if it exists
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv not installed, that's okay

# Try to import Supabase
try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False

CURATED_RECIPES_JSON = Path(__file__).parent / "curated_recipes.json"

# Environment variable to enable Supabase (defaults to false for safety)
USE_SUPABASE = os.getenv('USE_SUPABASE', 'false').lower() == 'true'
SUPABASE_URL = os.getenv('SUPABASE_URL', '')
SUPABASE_KEY = os.getenv('SUPABASE_KEY', '')

# Initialize Supabase client if available
supabase_client: Optional[Client] = None
if SUPABASE_AVAILABLE and USE_SUPABASE and SUPABASE_URL and SUPABASE_KEY:
    try:
        supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)
        print("✅ Supabase client initialized")
    except Exception as e:
        print(f"⚠️  Warning: Failed to initialize Supabase: {e}")
        print("   Falling back to JSON file storage")
        supabase_client = None
        USE_SUPABASE = False
elif USE_SUPABASE:
    print("⚠️  Warning: Supabase enabled but missing URL or KEY")
    print("   Falling back to JSON file storage")
    USE_SUPABASE = False


def load_recipes() -> List[Dict[str, Any]]:
    """
    Load all recipes from database (Supabase) or JSON file (fallback).
    Returns empty list if no recipes found.
    """
    # Try Supabase first if enabled
    if USE_SUPABASE and supabase_client:
        try:
            response = supabase_client.table('recipes').select('*').execute()
            if response.data:
                # Convert Supabase records to recipe format (remove id, created_at, updated_at)
                recipes = []
                for record in response.data:
                    recipe = {k: v for k, v in record.items() 
                             if k not in ['id', 'created_at', 'updated_at']}
                    recipes.append(recipe)
                return recipes
            return []
        except Exception as e:
            print(f"⚠️  Warning: Supabase load failed: {e}")
            print("   Falling back to JSON file")
    
    # Fallback to JSON
    return _load_from_json()


def save_recipes(recipes: List[Dict[str, Any]]) -> bool:
    """
    Save all recipes to database (Supabase) or JSON file (fallback).
    Returns True if successful.
    """
    # Try Supabase first if enabled
    if USE_SUPABASE and supabase_client:
        try:
            # Delete all existing recipes and insert new ones
            # (Supabase doesn't have a simple "replace all" operation)
            existing = supabase_client.table('recipes').select('id').execute()
            if existing.data:
                ids = [r['id'] for r in existing.data]
                supabase_client.table('recipes').delete().in_('id', ids).execute()
            
            # Insert all recipes in chunks (Supabase has limits)
            if recipes:
                # Filter out unwanted fields before inserting
                # Only keep fields that exist in the database schema
                allowed_fields = {
                    'title', 'ingredients', 'directions', 'protein_source', 'meal_type',
                    'difficulty', 'rating', 'protein', 'desc', 'categories', 'date',
                    'estimated_price', 'num_ingredients', 'num_steps'
                }
                filtered_recipes = []
                for recipe in recipes:
                    # Only include fields that are in the database schema
                    filtered_recipe = {k: v for k, v in recipe.items() 
                                     if k in allowed_fields}
                    filtered_recipes.append(filtered_recipe)
                
                chunk_size = 50  # Smaller chunks to avoid SSL/timeout issues
                total_chunks = (len(filtered_recipes) + chunk_size - 1) // chunk_size
                
                import time
                for i in range(0, len(filtered_recipes), chunk_size):
                    chunk = filtered_recipes[i:i + chunk_size]
                    chunk_num = (i // chunk_size) + 1
                    
                    # Retry logic for SSL/connection errors
                    max_retries = 3
                    retry_delay = 2  # seconds
                    
                    for attempt in range(max_retries):
                        try:
                            print(f"   Uploading chunk {chunk_num}/{total_chunks} ({len(chunk)} recipes)...", end='', flush=True)
                            supabase_client.table('recipes').insert(chunk).execute()
                            print(" ✓")
                            
                            # Small delay between chunks to avoid overwhelming the connection
                            if i + chunk_size < len(filtered_recipes):
                                time.sleep(0.5)
                            break
                        except Exception as e:
                            if attempt < max_retries - 1:
                                print(f" ✗ (retrying in {retry_delay}s...)")
                                time.sleep(retry_delay)
                                retry_delay *= 2  # Exponential backoff
                            else:
                                # Last attempt failed, re-raise the exception
                                print(f" ✗")
                                raise
            
            return True
        except Exception as e:
            print(f"⚠️  Warning: Supabase save failed: {e}")
            print("   Falling back to JSON file")
    
    # Fallback to JSON
    return _save_to_json(recipes)


def add_recipe(recipe: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Add a single recipe to database (Supabase) or JSON file (fallback).
    Returns (success, message).
    """
    # Try Supabase first if enabled
    if USE_SUPABASE and supabase_client:
        try:
            # Check for duplicates by title
            existing = supabase_client.table('recipes').select('id, title').eq('title', recipe['title']).execute()
            if existing.data:
                return (False, f"Duplicate recipe found: '{recipe['title']}' already exists")
            
            # Insert new recipe
            response = supabase_client.table('recipes').insert(recipe).execute()
            if response.data:
                return (True, f"✅ Successfully added recipe: '{recipe['title']}'")
            return (False, "Failed to add recipe to Supabase")
        except Exception as e:
            print(f"⚠️  Warning: Supabase add failed: {e}")
            print("   Falling back to JSON file")
    
    # Fallback to JSON
    return _add_to_json(recipe)


def _load_from_json() -> List[Dict[str, Any]]:
    """Load recipes from JSON file."""
    if not CURATED_RECIPES_JSON.exists():
        return []
    
    try:
        with open(CURATED_RECIPES_JSON, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        print(f"⚠️  Warning: Could not load recipes from JSON: {e}")
        return []


def _save_to_json(recipes: List[Dict[str, Any]]) -> bool:
    """Save recipes to JSON file."""
    try:
        # Create backup
        if CURATED_RECIPES_JSON.exists():
            backup_path = CURATED_RECIPES_JSON.parent / f"curated_recipes_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            import shutil
            shutil.copy2(CURATED_RECIPES_JSON, backup_path)
        
        # Write recipes
        with open(CURATED_RECIPES_JSON, 'w', encoding='utf-8') as f:
            json.dump(recipes, f, indent=2, ensure_ascii=False)
        
        return True
    except Exception as e:
        print(f"❌ Error saving recipes to JSON: {e}")
        return False


def _add_to_json(recipe: Dict[str, Any]) -> Tuple[bool, str]:
    """Add recipe to JSON file."""
    existing_recipes = _load_from_json()
    
    # Check for duplicates
    for existing in existing_recipes:
        if existing.get('title', '').lower() == recipe.get('title', '').lower():
            return (False, f"Duplicate recipe found: '{recipe['title']}' already exists")
    
    # Add to list
    existing_recipes.append(recipe)
    
    # Save
    if _save_to_json(existing_recipes):
        return (True, f"✅ Successfully added recipe: '{recipe['title']}'")
    else:
        return (False, "Failed to save recipes to JSON")


def get_storage_type() -> str:
    """Return the current storage type being used."""
    if USE_SUPABASE and supabase_client:
        return "Supabase"
    return "JSON file"


# ============================================================================
# MULTI-USER FEATURES (COMMENTED OUT - Enable when ready
# ============================================================================
# Uncomment these functions and update load_recipes/add_recipe to use them
# when you're ready to add user authentication and personal recipe collections.
# See MULTI_USER_SETUP.md for implementation guide.
"""

# Get current user ID from Supabase auth
def get_current_user_id() -> Optional[str]:
    \"\"\"Get the current authenticated user's ID.\"\"\"
    if not USE_SUPABASE or not supabase_client:
        return None
    try:
        # Get user from Supabase auth session
        user = supabase_client.auth.get_user()
        if user and user.user:
            return user.user.id
    except Exception:
        pass
    return None

# Load recipes for current user only
def load_user_recipes(user_id: Optional[str] = None) -> List[Dict[str, Any]]:
    \"\"\"
    Load recipes for a specific user (or current user if user_id is None).
    Returns empty list if no recipes found.
    \"\"\"
    if not user_id:
        user_id = get_current_user_id()
    
    if not user_id:
        # No user logged in, return empty or all recipes (depending on your needs)
        return []
    
    if USE_SUPABASE and supabase_client:
        try:
            response = supabase_client.table('recipes').select('*').eq('user_id', user_id).execute()
            if response.data:
                recipes = []
                for record in response.data:
                    recipe = {k: v for k, v in record.items() 
                             if k not in ['id', 'created_at', 'updated_at', 'user_id']}
                    recipes.append(recipe)
                return recipes
            return []
        except Exception as e:
            print(f"⚠️  Warning: Supabase load failed: {e}")
            return []
    
    # Fallback to JSON (no user filtering in JSON mode)
    return _load_from_json()

# Add recipe for current user
def add_user_recipe(recipe: Dict[str, Any], user_id: Optional[str] = None) -> Tuple[bool, str]:
    \"\"\"
    Add a recipe for a specific user (or current user if user_id is None).
    Returns (success, message).
    \"\"\"
    if not user_id:
        user_id = get_current_user_id()
    
    if not user_id:
        return (False, "User not authenticated")
    
    # Add user_id to recipe
    recipe['user_id'] = user_id
    
    if USE_SUPABASE and supabase_client:
        try:
            # Check for duplicates by title AND user_id
            existing = supabase_client.table('recipes').select('id, title').eq('title', recipe['title']).eq('user_id', user_id).execute()
            if existing.data:
                return (False, f"Duplicate recipe found: '{recipe['title']}' already exists")
            
            response = supabase_client.table('recipes').insert(recipe).execute()
            if response.data:
                return (True, f"✅ Successfully added recipe: '{recipe['title']}'")
            return (False, "Failed to add recipe to Supabase")
        except Exception as e:
            print(f"⚠️  Warning: Supabase add failed: {e}")
            return (False, f"Error: {str(e)}")
    
    # Fallback to JSON (no user filtering)
    return _add_to_json(recipe)

# Authentication helpers
def sign_up(email: str, password: str, full_name: str = "") -> Tuple[bool, str, Optional[str]]:
    \"\"\"
    Sign up a new user.
    Returns (success, message, user_id).
    \"\"\"
    if not USE_SUPABASE or not supabase_client:
        return (False, "Supabase not configured", None)
    
    try:
        response = supabase_client.auth.sign_up({
            "email": email,
            "password": password
        })
        
        if response.user:
            # Create profile
            supabase_client.table('profiles').insert({
                'id': response.user.id,
                'email': email,
                'full_name': full_name
            }).execute()
            
            return (True, "Account created successfully", response.user.id)
        return (False, "Failed to create account", None)
    except Exception as e:
        return (False, f"Error: {str(e)}", None)

def sign_in(email: str, password: str) -> Tuple[bool, str, Optional[str]]:
    \"\"\"
    Sign in a user.
    Returns (success, message, user_id).
    \"\"\"
    if not USE_SUPABASE or not supabase_client:
        return (False, "Supabase not configured", None)
    
    try:
        response = supabase_client.auth.sign_in_with_password({
            "email": email,
            "password": password
        })
        
        if response.user:
            return (True, "Signed in successfully", response.user.id)
        return (False, "Invalid credentials", None)
    except Exception as e:
        return (False, f"Error: {str(e)}", None)

def sign_out() -> bool:
    \"\"\"Sign out current user.\"\"\"
    if not USE_SUPABASE or not supabase_client:
        return False
    
    try:
        supabase_client.auth.sign_out()
        return True
    except Exception:
        return False

def get_current_user() -> Optional[Dict[str, Any]]:
    \"\"\"Get current user's profile information.\"\"\"
    user_id = get_current_user_id()
    if not user_id:
        return None
    
    try:
        response = supabase_client.table('profiles').select('*').eq('id', user_id).execute()
        if response.data:
            return response.data[0]
    except Exception:
        pass
    return None
"""
