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
        
        # Insert new recipe
        response = supabase_client.table('recipes').insert(recipe).execute()
        if response.data:
            return (True, f"✅ Successfully added recipe: '{recipe['title']}'")
        return (False, "Failed to add recipe to Supabase")
    except Exception as e:
        return (False, f"Error adding recipe: {str(e)}")
