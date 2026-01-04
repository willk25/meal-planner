#!/usr/bin/env python3
"""
Curate recipes from the full Epicurious dataset.

Filters for:
- High protein (muscle building)
- Good ratings (4+ stars)
- Simple recipes (≤15 ingredients)
- Has complete data (ingredients + directions)

Categorizes by protein source for easy browsing.
"""

import json
from pathlib import Path
from collections import Counter

FULL_RECIPES_JSON = Path(__file__).parent / "full_format_recipes.json"
CURATED_RECIPES_JSON = Path(__file__).parent / "curated_recipes.json"

# Filtering criteria
MIN_PROTEIN = 25  # grams per serving
MAX_PROTEIN = 100  # grams per serving (cap outliers - data errors)
MIN_RATING = 4.0  # out of 5 (4 stars minimum)
MAX_INGREDIENTS = 15  # keep it simple
MIN_INGREDIENTS = 3  # need real recipes, not just "toast"

# Protein source detection
PROTEIN_SOURCES = {
    "chicken": ["chicken", "poultry"],
    "beef": ["beef", "steak", "ground beef", "chuck", "sirloin", "ribeye", "brisket"],
    "pork": ["pork", "bacon", "ham", "sausage", "prosciutto"],
    "seafood": ["fish", "salmon", "tuna", "shrimp", "cod", "halibut", "tilapia", "mahi", "trout", "sea bass", "crab", "lobster", "scallop"],
    "turkey": ["turkey"],
    "lamb": ["lamb"],
    "eggs": ["egg", "eggs", "frittata", "omelet", "omelette"],
}

# Categories to EXCLUDE (desserts, drinks, etc.)
EXCLUDE_CATEGORIES = [
    "dessert", "cake", "cookie", "pie", "chocolate", "candy", "brownie",
    "cocktail", "drink", "beverage", "smoothie", "juice",
    "bread", "muffin", "pancake", "waffle",  # carb-heavy breakfast items
]


def load_full_recipes():
    """Load the full recipe dataset."""
    with open(FULL_RECIPES_JSON, "r") as f:
        return json.load(f)


def detect_protein_source(recipe):
    """Detect the main protein source from title/ingredients/categories."""
    # Check title first (most reliable)
    title_lower = recipe.get("title", "").lower()
    
    # Check categories
    categories = recipe.get("categories", [])
    cats_lower = [c.lower() for c in categories] if categories else []
    
    # Check ingredients
    ingredients = recipe.get("ingredients", [])
    ings_lower = " ".join(ingredients).lower() if ingredients else ""
    
    # Combined text for searching
    all_text = f"{title_lower} {' '.join(cats_lower)} {ings_lower}"
    
    for source, keywords in PROTEIN_SOURCES.items():
        for keyword in keywords:
            if keyword in all_text:
                return source
    
    return "other"


def should_exclude(recipe):
    """Check if recipe should be excluded (desserts, drinks, etc.)."""
    categories = recipe.get("categories", [])
    if not categories:
        return False
    
    cats_lower = [c.lower() for c in categories]
    title_lower = recipe.get("title", "").lower()
    
    for exclude in EXCLUDE_CATEGORIES:
        if exclude in cats_lower or exclude in title_lower:
            return True
    
    return False


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


def curate_recipes():
    """Main curation logic."""
    print("🍽️  Recipe Curation Tool\n")
    print("Loading full recipe dataset...")
    
    recipes = load_full_recipes()
    print(f"  Total recipes: {len(recipes)}")
    
    # Step 1: Filter for complete data
    print("\nFiltering for complete data...")
    filtered = [r for r in recipes 
                if r.get("ingredients") and len(r.get("ingredients", [])) >= MIN_INGREDIENTS
                and r.get("directions") and len(r.get("directions", [])) > 0
                and r.get("title")]
    print(f"  With ingredients + directions: {len(filtered)}")
    
    # Step 2: Filter for protein (with reasonable cap to exclude data errors)
    print(f"\nFiltering for protein {MIN_PROTEIN}-{MAX_PROTEIN}g...")
    filtered = [r for r in filtered 
                if r.get("protein") and MIN_PROTEIN <= r["protein"] <= MAX_PROTEIN]
    print(f"  High protein: {len(filtered)}")
    
    # Step 3: Filter for rating
    print(f"\nFiltering for rating >= {MIN_RATING}...")
    filtered = [r for r in filtered 
                if r.get("rating") and r["rating"] >= MIN_RATING]
    print(f"  Well-rated: {len(filtered)}")
    
    # Step 4: Filter for simplicity
    print(f"\nFiltering for <= {MAX_INGREDIENTS} ingredients...")
    filtered = [r for r in filtered 
                if len(r.get("ingredients", [])) <= MAX_INGREDIENTS]
    print(f"  Simple recipes: {len(filtered)}")
    
    # Step 5: Exclude desserts/drinks
    print("\nExcluding desserts, drinks, breads...")
    filtered = [r for r in filtered if not should_exclude(r)]
    print(f"  After exclusions: {len(filtered)}")
    
    # Step 6: Add metadata
    print("\nAdding metadata (protein source, meal type, difficulty)...")
    for recipe in filtered:
        recipe["protein_source"] = detect_protein_source(recipe)
        recipe["meal_type"] = get_meal_type(recipe)
        recipe["difficulty"] = get_difficulty(recipe)
        recipe["num_ingredients"] = len(recipe.get("ingredients", []))
        recipe["num_steps"] = len(recipe.get("directions", []))
    
    # Stats
    print("\n" + "=" * 50)
    print("📊 CURATED RECIPE STATS")
    print("=" * 50)
    
    protein_counts = Counter(r["protein_source"] for r in filtered)
    print("\nBy Protein Source:")
    for source, count in protein_counts.most_common():
        print(f"  {source.capitalize():12} {count:4}")
    
    meal_counts = Counter(r["meal_type"] for r in filtered)
    print("\nBy Meal Type:")
    for meal, count in meal_counts.most_common():
        print(f"  {meal.capitalize():12} {count:4}")
    
    difficulty_counts = Counter(r["difficulty"] for r in filtered)
    print("\nBy Difficulty:")
    for diff, count in difficulty_counts.most_common():
        print(f"  {diff.capitalize():12} {count:4}")
    
    # Protein stats
    proteins = [r["protein"] for r in filtered if r.get("protein")]
    avg_protein = sum(proteins) / len(proteins) if proteins else 0
    print(f"\nAverage Protein: {avg_protein:.1f}g")
    
    ratings = [r["rating"] for r in filtered if r.get("rating")]
    avg_rating = sum(ratings) / len(ratings) if ratings else 0
    print(f"Average Rating: {avg_rating:.2f} ⭐")
    
    # Save
    print(f"\n💾 Saving {len(filtered)} curated recipes to curated_recipes.json...")
    with open(CURATED_RECIPES_JSON, "w") as f:
        json.dump(filtered, f, indent=2)
    
    print("\n✅ Done! Your curated recipes are ready.")
    print(f"\n📁 File: {CURATED_RECIPES_JSON}")
    print(f"📊 Total: {len(filtered)} recipes")
    
    # Sample recipes
    print("\n" + "=" * 50)
    print("🍳 SAMPLE RECIPES")
    print("=" * 50)
    
    # Show top rated from each protein source
    for source in ["chicken", "beef", "seafood", "pork"]:
        source_recipes = [r for r in filtered if r["protein_source"] == source]
        if source_recipes:
            top = sorted(source_recipes, key=lambda x: (x.get("rating", 0), x.get("protein", 0)), reverse=True)[:2]
            print(f"\n{source.upper()}:")
            for r in top:
                print(f"  • {r['title']}")
                print(f"    {r['protein']:.0f}g protein | {r['rating']:.1f}⭐ | {r['difficulty']} | {r['num_ingredients']} ingredients")


if __name__ == "__main__":
    curate_recipes()

