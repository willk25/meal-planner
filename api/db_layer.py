#!/usr/bin/env python3
"""
Minimal database layer for Vercel serverless functions.
Only supports Supabase - no JSON fallback to avoid bundling large files.
"""

import os
from typing import Dict, List, Optional, Any, Tuple

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

# Environment variable to enable Supabase (defaults to false for safety)
USE_SUPABASE = os.getenv('USE_SUPABASE', 'false').lower() == 'true'
SUPABASE_URL = os.getenv('SUPABASE_URL', '')
SUPABASE_KEY = os.getenv('SUPABASE_KEY', '')

# Initialize Supabase client if available
supabase_client: Optional[Client] = None
if SUPABASE_AVAILABLE and USE_SUPABASE and SUPABASE_URL and SUPABASE_KEY:
    try:
        supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as e:
        print(f"⚠️  Warning: Failed to initialize Supabase: {e}")
        supabase_client = None
        USE_SUPABASE = False
elif USE_SUPABASE:
    print("⚠️  Warning: Supabase enabled but missing URL or KEY")
    USE_SUPABASE = False


def load_recipes() -> List[Dict[str, Any]]:
    """
    Load all recipes from Supabase.
    Returns empty list if no recipes found or Supabase not configured.
    
    Note: This is the Vercel API version - it only supports Supabase.
    For local development with JSON fallback, use the root db_layer.py
    """
    # Debug logging
    print(f"DEBUG load_recipes: USE_SUPABASE={USE_SUPABASE}, SUPABASE_AVAILABLE={SUPABASE_AVAILABLE}")
    print(f"DEBUG load_recipes: supabase_client={supabase_client is not None}")
    print(f"DEBUG load_recipes: SUPABASE_URL set={bool(SUPABASE_URL)}, SUPABASE_KEY set={bool(SUPABASE_KEY)}")
    
    if not USE_SUPABASE:
        print("⚠️  Warning: USE_SUPABASE is False - check environment variables")
        return []
    
    if not supabase_client:
        print("⚠️  Warning: Supabase client not initialized")
        print(f"   SUPABASE_AVAILABLE={SUPABASE_AVAILABLE}, USE_SUPABASE={USE_SUPABASE}")
        print(f"   SUPABASE_URL={'set' if SUPABASE_URL else 'NOT SET'}")
        print(f"   SUPABASE_KEY={'set' if SUPABASE_KEY else 'NOT SET'}")
        return []
    
    try:
        print("DEBUG: Querying Supabase for recipes...")
        # Supabase/PostgREST defaults to 1000 rows per request, so paginate.
        page_size = 1000
        offset = 0
        all_records = []
        
        while True:
            response = supabase_client.table('recipes').select('*').range(offset, offset + page_size - 1).execute()
            batch = response.data or []
            print(f"DEBUG: Fetched batch offset={offset}, size={len(batch)}")
            
            if not batch:
                break
            
            all_records.extend(batch)
            
            # If we got less than a full page, we're done.
            if len(batch) < page_size:
                break
            
            offset += page_size
        
        print(f"DEBUG: Supabase response received, total rows: {len(all_records)}")
        
        if all_records:
            # Convert Supabase records to recipe format (remove id, created_at, updated_at)
            recipes = []
            for record in all_records:
                recipe = {k: v for k, v in record.items() 
                         if k not in ['id', 'created_at', 'updated_at']}
                recipes.append(recipe)
            print(f"DEBUG: Returning {len(recipes)} recipes")
            return recipes
        print("DEBUG: No recipes found in Supabase")
        return []
    except Exception as e:
        import traceback
        print(f"⚠️  Warning: Supabase load failed: {e}")
        print(f"Traceback: {traceback.format_exc()}")
        return []


def add_recipe(recipe: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Add a single recipe to Supabase.
    Returns (success, message).
    """
    if not USE_SUPABASE or not supabase_client:
        return (False, "Supabase not configured. Please set USE_SUPABASE=true and provide SUPABASE_URL and SUPABASE_KEY environment variables.")
    
    try:
        # Check for duplicates by title
        existing = supabase_client.table('recipes').select('id, title').eq('title', recipe['title']).execute()
        if existing.data:
            return (False, f"Duplicate recipe found: '{recipe['title']}' already exists")
        
        # Filter out unwanted fields - only keep fields that exist in database schema
        allowed_fields = {
            'title', 'ingredients', 'directions', 'protein_source', 'meal_type',
            'difficulty', 'rating', 'protein', 'desc', 'categories', 'date',
            'estimated_price', 'num_ingredients', 'num_steps'
        }
        filtered_recipe = {k: v for k, v in recipe.items() 
                          if k in allowed_fields}
        
        # Insert new recipe
        response = supabase_client.table('recipes').insert(filtered_recipe).execute()
        if response.data:
            return (True, f"✅ Successfully added recipe: '{filtered_recipe['title']}'")
        return (False, "Failed to add recipe to Supabase")
    except Exception as e:
        return (False, f"Error adding recipe: {str(e)}")
