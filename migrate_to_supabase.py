#!/usr/bin/env python3
"""
Migration script to upload curated_recipes.json to Supabase.
Run this once after setting up Supabase to migrate your existing recipes.
"""

import json
import sys
from pathlib import Path

# Load environment variables
try:
    from dotenv import load_dotenv
    try:
        load_dotenv()
    except (PermissionError, FileNotFoundError):
        # .env file doesn't exist or can't be read - that's okay, use system env vars
        pass
except ImportError:
    pass

# Import db_layer from root (has full functionality)
sys.path.insert(0, str(Path(__file__).parent))
from db_layer import save_recipes, get_storage_type

CURATED_RECIPES_JSON = Path(__file__).parent / "curated_recipes.json"


def main():
    print("🔄 Recipe Migration to Supabase")
    print("=" * 60)
    
    # Check if Supabase is configured
    storage_type = get_storage_type()
    print(f"Current storage type: {storage_type}")
    
    if storage_type != "Supabase":
        print("\n❌ Error: Supabase is not configured!")
        print("\nPlease:")
        print("1. Set up Supabase (see SUPABASE_SETUP.md)")
        print("2. Add to .env file:")
        print("   USE_SUPABASE=true")
        print("   SUPABASE_URL=your-url")
        print("   SUPABASE_KEY=your-key")
        print("\nThen run this script again.")
        sys.exit(1)
    
    # Check if JSON file exists
    if not CURATED_RECIPES_JSON.exists():
        print(f"\n❌ Error: {CURATED_RECIPES_JSON} not found!")
        sys.exit(1)
    
    # Load recipes from JSON
    print(f"\n📖 Loading recipes from {CURATED_RECIPES_JSON.name}...")
    try:
        with open(CURATED_RECIPES_JSON, 'r', encoding='utf-8') as f:
            recipes = json.load(f)
        print(f"   Found {len(recipes)} recipes")
    except Exception as e:
        print(f"❌ Error loading JSON: {e}")
        sys.exit(1)
    
    # Save to Supabase
    print(f"\n💾 Uploading {len(recipes)} recipes to Supabase...")
    print("   This may take a few minutes for large datasets...")
    
    success = save_recipes(recipes)
    
    if success:
        print(f"\n✅ Successfully migrated {len(recipes)} recipes to Supabase!")
        print("\n🎉 Your recipes are now in Supabase!")
        print("   The meal planner will now load from Supabase.")
    else:
        print("\n❌ Migration failed. Check the error messages above.")
        sys.exit(1)


if __name__ == "__main__":
    main()
