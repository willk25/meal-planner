#!/usr/bin/env python3
"""
Recipe Bot - Picks random recipes and writes to Google Sheets + Google Docs.
Triggers Apps Script to send email with recipe options.

Uses curated_recipes.json (1,295 high-protein, well-rated, simple recipes)
or falls back to full_format_recipes.json (20k+ recipes).

Run manually or schedule with cron/Task Scheduler every 2 days.
"""

import os
import json
from pathlib import Path
from datetime import datetime

import requests
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# ===== CONFIG =====
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/documents",
    "https://www.googleapis.com/auth/drive.file",
]
SERVICE_ACCOUNT_FILE = Path(__file__).parent / "service_account.json"
SPREADSHEET_ID = os.environ.get("GOOGLE_SHEET_ID", "YOUR_SHEET_ID_HERE")
GOOGLE_DOC_ID = os.environ.get("GOOGLE_DOC_ID", "")  # Optional: existing doc to update

# Dataset paths - prefer curated, fall back to full
CURATED_RECIPES_JSON = Path(__file__).parent / "curated_recipes.json"
FULL_RECIPES_JSON = Path(__file__).parent / "full_format_recipes.json"

NUM_RECIPES = int(os.environ.get("NUM_RECIPES", 5))
MIN_RATING = float(os.environ.get("MIN_RATING", 3.5))  # Minimum rating (0-5)

# Meal type filter: "entree", "dessert", "appetizer", "breakfast", "any"
MEAL_TYPE = os.environ.get("MEAL_TYPE", "entree")

# Protein source filter (for curated recipes): "chicken", "beef", "pork", "seafood", "any"
PROTEIN_SOURCE = os.environ.get("PROTEIN_SOURCE", "any")

# Apps Script Web App URL (triggers email)
APPS_SCRIPT_URL = os.environ.get("APPS_SCRIPT_URL", "")

# Category mappings for meal types
MEAL_TYPE_CATEGORIES = {
    "entree": [
        "Main Course", "Dinner", "Lunch", "Entrée",
        "Chicken", "Beef", "Pork", "Fish", "Seafood", "Pasta", "Rice",
        "Stew", "Roast", "Grill/Barbecue", "Meat", "Poultry"
    ],
    "dessert": [
        "Dessert", "Cake", "Cookie", "Pie", "Chocolate", "Ice Cream",
        "Pudding", "Brownie", "Tart", "Candy", "Cheesecake", "Fruit Dessert"
    ],
    "appetizer": [
        "Appetizer", "Starter", "Hors d'Oeuvre", "Dip", "Snack",
        "Finger Food", "Canapé"
    ],
    "breakfast": [
        "Breakfast", "Brunch", "Pancake", "Waffle", "Egg",
        "Morning", "Cereal"
    ],
    "side": [
        "Side", "Salad", "Vegetable", "Potato", "Rice"
    ],
    "soup": [
        "Soup", "Stew", "Chili", "Broth"
    ],
}


def get_credentials():
    """Get Google credentials from service account."""
    return Credentials.from_service_account_file(
        str(SERVICE_ACCOUNT_FILE),
        scopes=SCOPES,
    )


def get_sheets_client():
    """Authenticate with Google Sheets using service account."""
    creds = get_credentials()
    return gspread.authorize(creds)


def get_docs_service():
    """Get Google Docs API service."""
    creds = get_credentials()
    return build('docs', 'v1', credentials=creds)


def get_drive_service():
    """Get Google Drive API service (for creating docs)."""
    creds = get_credentials()
    return build('drive', 'v3', credentials=creds)


def load_recipes():
    """Load recipes from JSON file (curated preferred, full as fallback)."""
    # Try curated recipes first
    if CURATED_RECIPES_JSON.exists():
        with open(CURATED_RECIPES_JSON, "r") as f:
            recipes = json.load(f)
        print(f"  Loaded {len(recipes)} curated recipes (high-protein, simple, well-rated)")
        df = pd.DataFrame(recipes)
        return df, True  # True = using curated
    
    # Fall back to full recipes
    if not FULL_RECIPES_JSON.exists():
        raise FileNotFoundError(f"No recipe file found!")
    
    with open(FULL_RECIPES_JSON, "r") as f:
        recipes = json.load(f)
    
    print(f"  Loaded {len(recipes)} recipes from Epicurious")
    df = pd.DataFrame(recipes)
    df = df.dropna(subset=["title", "ingredients"])
    df = df[df["ingredients"].apply(lambda x: len(x) > 0)]
    
    return df, False  # False = using full


def filter_by_rating(df):
    """Filter recipes by minimum rating."""
    if "rating" not in df.columns:
        return df
    
    df = df[(df["rating"] >= MIN_RATING) | (df["rating"].isna())]
    print(f"  After rating filter (>= {MIN_RATING}⭐): {len(df)} recipes")
    
    return df


def filter_by_protein_source(df):
    """Filter curated recipes by protein source."""
    if PROTEIN_SOURCE == "any" or "protein_source" not in df.columns:
        return df
    
    df = df[df["protein_source"].str.lower() == PROTEIN_SOURCE.lower()]
    print(f"  After protein source filter ({PROTEIN_SOURCE}): {len(df)} recipes")
    
    return df


def filter_by_meal_type(df):
    """Filter recipes by meal type using categories."""
    if MEAL_TYPE == "any":
        return df
    
    categories_to_match = MEAL_TYPE_CATEGORIES.get(MEAL_TYPE, [])
    if not categories_to_match:
        return df
    
    def has_matching_category(cats):
        if not isinstance(cats, list):
            return False
        cats_lower = [c.lower() for c in cats]
        for target in categories_to_match:
            if target.lower() in cats_lower:
                return True
        return False
    
    df = df[df["categories"].apply(has_matching_category)]
    print(f"  After meal type filter ({MEAL_TYPE}): {len(df)} recipes")
    
    if len(df) < NUM_RECIPES:
        print(f"  ⚠ Only {len(df)} recipes match - consider using MEAL_TYPE=any")
    
    return df


def pick_recipes(df, n=None):
    """Randomly select n recipes, weighted by rating."""
    if n is None:
        n = NUM_RECIPES
    if len(df) < n:
        n = len(df)
    
    # Weight selection toward higher ratings
    if "rating" in df.columns and df["rating"].notna().any():
        weights = df["rating"].fillna(df["rating"].mean())
        weights = weights - weights.min() + 1
        weights = weights / weights.sum()
        return df.sample(n, weights=weights, random_state=None)
    
    return df.sample(n, random_state=None)


def format_ingredients(ingredients):
    """Format ingredients list for display."""
    if not isinstance(ingredients, list):
        return str(ingredients)
    return "\n".join(f"• {ing}" for ing in ingredients)


def format_directions(directions):
    """Format directions list for display."""
    if not isinstance(directions, list):
        return str(directions) if directions else "See recipe source"
    return "\n".join(f"{i+1}. {step}" for i, step in enumerate(directions))


def write_to_google_sheet(client, recipes_df):
    """Write recipes to Google Sheet."""
    sh = client.open_by_key(SPREADSHEET_ID)
    
    try:
        recipes_ws = sh.worksheet("Selected Recipes")
    except gspread.WorksheetNotFound:
        recipes_ws = sh.add_worksheet(title="Selected Recipes", rows=200, cols=6)
    
    recipes_ws.clear()
    
    headers = ["Title", "Ingredients", "Rating", "Calories", "Categories", "Directions"]
    recipe_rows = [headers]
    
    for _, row in recipes_df.iterrows():
        title = str(row.get("title", ""))
        ingredients = format_ingredients(row.get("ingredients", []))
        directions = format_directions(row.get("directions", []))
        
        rating = row.get("rating")
        rating_str = f"⭐ {rating:.1f}" if pd.notna(rating) else "N/A"
        
        calories = row.get("calories")
        calories_str = f"{calories:.0f} cal" if pd.notna(calories) else "N/A"
        
        categories = row.get("categories", [])
        categories_str = ", ".join(categories) if isinstance(categories, list) else str(categories)
        
        recipe_rows.append([
            title,
            ingredients,
            rating_str,
            calories_str,
            categories_str,
            directions,
        ])
    
    recipes_ws.update(range_name="A1", values=recipe_rows)
    
    print(f"✓ Updated Google Sheet with {len(recipes_df)} recipes")


def create_google_doc(recipes_df):
    """Create a Google Doc with the recipes (shopping list + directions)."""
    try:
        drive_service = get_drive_service()
        docs_service = get_docs_service()
    except Exception as e:
        print(f"⚠ Could not connect to Google Docs API: {e}")
        return None
    
    # Create a new document
    date_str = datetime.now().strftime("%B %d, %Y")
    doc_title = f"Meal Plan - {date_str}"
    
    try:
        # Create the document
        doc_metadata = {
            'name': doc_title,
            'mimeType': 'application/vnd.google-apps.document'
        }
        doc = drive_service.files().create(body=doc_metadata).execute()
        doc_id = doc['id']
        
        print(f"✓ Created Google Doc: {doc_title}")
        
        # Build the document content
        requests_list = []
        
        # Title
        requests_list.append({
            'insertText': {
                'location': {'index': 1},
                'text': f"🍽️ Meal Plan\n{date_str}\n\n"
            }
        })
        
        # For each recipe
        current_index = 1 + len(f"🍽️ Meal Plan\n{date_str}\n\n")
        
        for idx, (_, row) in enumerate(recipes_df.iterrows(), 1):
            title = str(row.get("title", "")).strip()
            ingredients = row.get("ingredients", [])
            directions = row.get("directions", [])
            
            # Nutrition info
            protein = row.get("protein")
            calories = row.get("calories")
            rating = row.get("rating")
            
            nutrition_parts = []
            if pd.notna(protein):
                nutrition_parts.append(f"{protein:.0f}g protein")
            if pd.notna(calories):
                nutrition_parts.append(f"{calories:.0f} cal")
            if pd.notna(rating):
                nutrition_parts.append(f"{rating:.1f}⭐")
            nutrition_str = " | ".join(nutrition_parts) if nutrition_parts else ""
            
            # Recipe header
            recipe_header = f"{'═' * 50}\n"
            recipe_header += f"RECIPE {idx}: {title.upper()}\n"
            if nutrition_str:
                recipe_header += f"{nutrition_str}\n"
            recipe_header += f"{'═' * 50}\n\n"
            
            # Shopping list
            shopping_list = "📋 SHOPPING LIST\n"
            shopping_list += "─" * 30 + "\n"
            if isinstance(ingredients, list):
                for ing in ingredients:
                    shopping_list += f"☐ {ing}\n"
            shopping_list += "\n"
            
            # Directions
            directions_text = "👨‍🍳 DIRECTIONS\n"
            directions_text += "─" * 30 + "\n"
            if isinstance(directions, list):
                for i, step in enumerate(directions, 1):
                    directions_text += f"{i}. {step}\n\n"
            else:
                directions_text += "See recipe source.\n"
            
            directions_text += "\n\n"
            
            # Combine
            full_recipe_text = recipe_header + shopping_list + directions_text
            
            requests_list.append({
                'insertText': {
                    'location': {'index': current_index},
                    'text': full_recipe_text
                }
            })
            current_index += len(full_recipe_text)
        
        # Execute all updates
        docs_service.documents().batchUpdate(
            documentId=doc_id,
            body={'requests': requests_list}
        ).execute()
        
        doc_url = f"https://docs.google.com/document/d/{doc_id}/edit"
        print(f"✓ Google Doc URL: {doc_url}")
        
        return doc_url
        
    except Exception as e:
        print(f"⚠ Error creating Google Doc: {e}")
        return None


def trigger_email():
    """Call the Apps Script web app to send the email."""
    if not APPS_SCRIPT_URL:
        print("⚠ APPS_SCRIPT_URL not set - skipping email trigger")
        print("  See README.md for Apps Script setup instructions\n")
        return
    
    try:
        response = requests.get(APPS_SCRIPT_URL)
        if response.status_code == 200:
            print("✓ Email triggered via Apps Script")
        else:
            print(f"⚠ Apps Script returned status {response.status_code}")
    except Exception as e:
        print(f"⚠ Failed to trigger email: {e}")


def main():
    """Main entry point."""
    print("🍽️  Recipe Bot Starting...\n")
    
    # Load recipes
    print("Loading recipes...")
    df, is_curated = load_recipes()
    
    # Apply filters
    df = filter_by_rating(df)
    
    if is_curated:
        df = filter_by_protein_source(df)
    
    df = filter_by_meal_type(df)
    
    if len(df) == 0:
        print("❌ No recipes match your filters! Try adjusting MIN_RATING or MEAL_TYPE")
        return
    
    # Pick recipes
    chosen = pick_recipes(df)
    print(f"\n📋 Selected {len(chosen)} recipes:\n")
    
    for _, row in chosen.iterrows():
        title = row.get("title", "Unknown")
        rating = row.get("rating")
        calories = row.get("calories")
        protein = row.get("protein")
        
        info_parts = []
        if pd.notna(protein):
            info_parts.append(f"{protein:.0f}g protein")
        if pd.notna(rating):
            info_parts.append(f"⭐ {rating:.1f}")
        if pd.notna(calories):
            info_parts.append(f"{calories:.0f} cal")
        
        info_str = f" ({', '.join(info_parts)})" if info_parts else ""
        print(f"    • {title}{info_str}")
    print()
    
    # Write to Google Sheets
    try:
        client = get_sheets_client()
        write_to_google_sheet(client, chosen)
    except FileNotFoundError:
        print("⚠ service_account.json not found - skipping Google Sheets update")
        print("  See README.md for setup instructions\n")
        return
    except Exception as e:
        print(f"⚠ Google Sheets error: {e}\n")
        return
    
    # Create Google Doc with shopping list + directions
    create_google_doc(chosen)
    
    # Trigger email via Apps Script
    trigger_email()
    
    print("\n✅ Recipe Bot Complete!")


if __name__ == "__main__":
    main()
