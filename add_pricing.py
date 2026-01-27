#!/usr/bin/env python3
"""
Add estimated pricing to all recipes based on ingredients.

Uses ingredient analysis to estimate cost per serving.
"""

import json
import re
from pathlib import Path
from collections import defaultdict

CURATED_RECIPES_JSON = Path(__file__).parent / "curated_recipes.json"

# Ingredient pricing database (per unit, approximate US prices)
INGREDIENT_PRICES = {
    # Proteins (per pound)
    "chicken": 4.50,
    "chicken breast": 5.00,
    "chicken thigh": 3.50,
    "beef": 8.00,
    "ground beef": 6.00,
    "steak": 12.00,
    "sirloin": 10.00,
    "ribeye": 15.00,
    "pork": 5.00,
    "pork shoulder": 4.00,
    "pork chop": 6.00,
    "bacon": 7.00,
    "ham": 5.00,
    "sausage": 5.50,
    "salmon": 12.00,
    "tuna": 8.00,
    "fish": 8.00,
    "cod": 7.00,
    "halibut": 15.00,
    "tilapia": 5.00,
    "shrimp": 10.00,
    "crab": 15.00,
    "lobster": 20.00,
    "scallop": 18.00,
    "turkey": 4.00,
    "lamb": 10.00,
    "egg": 0.25,
    "eggs": 0.25,
    
    # Vegetables (per pound or unit)
    "onion": 1.00,
    "garlic": 0.50,
    "carrot": 1.50,
    "celery": 1.50,
    "potato": 1.00,
    "tomato": 2.00,
    "bell pepper": 2.00,
    "mushroom": 4.00,
    "spinach": 3.00,
    "lettuce": 2.00,
    "broccoli": 2.50,
    "cauliflower": 2.50,
    "zucchini": 2.00,
    "eggplant": 2.00,
    "corn": 1.50,
    "peas": 2.00,
    "green bean": 3.00,
    "asparagus": 4.00,
    "avocado": 1.50,
    
    # Grains & Starches
    "rice": 2.00,
    "pasta": 2.00,
    "noodle": 2.00,
    "bread": 3.00,
    "flour": 1.50,
    "quinoa": 5.00,
    "barley": 2.00,
    "couscous": 3.00,
    
    # Dairy
    "milk": 3.50,
    "cheese": 5.00,
    "butter": 4.00,
    "cream": 4.00,
    "yogurt": 4.00,
    "sour cream": 3.00,
    
    # Oils & Fats
    "olive oil": 8.00,
    "vegetable oil": 3.00,
    "canola oil": 3.00,
    "coconut oil": 6.00,
    
    # Spices & Herbs (per ounce, but used in small amounts)
    "salt": 0.50,
    "pepper": 2.00,
    "paprika": 3.00,
    "cumin": 4.00,
    "coriander": 4.00,
    "turmeric": 4.00,
    "cinnamon": 5.00,
    "nutmeg": 6.00,
    "oregano": 4.00,
    "thyme": 4.00,
    "rosemary": 4.00,
    "basil": 4.00,
    "parsley": 3.00,
    "cilantro": 3.00,
    "ginger": 4.00,
    "bay leaf": 3.00,
    
    # Other common ingredients
    "chicken broth": 2.50,
    "beef broth": 2.50,
    "vegetable broth": 2.50,
    "stock": 2.50,
    "wine": 8.00,
    "vinegar": 3.00,
    "soy sauce": 3.00,
    "worcestershire": 4.00,
    "mustard": 3.00,
    "mayonnaise": 3.00,
    "ketchup": 2.00,
    "sugar": 2.00,
    "honey": 6.00,
    "lemon": 0.50,
    "lime": 0.50,
    "orange": 0.75,
}


def normalize_ingredient(ingredient):
    """Normalize ingredient name for matching."""
    # Remove common prefixes and clean up
    text = ingredient.lower()
    # Remove common measurement words
    text = re.sub(r'\b\d+[\/\d]*\s*(cup|tbsp|tsp|oz|lb|pound|ounce|gram|kg|ml|liter|piece|pieces|clove|cloves|can|cans|bunch|bunches|head|heads|package|packages)\b', '', text)
    # Remove common descriptors
    text = re.sub(r'\b(fresh|dried|ground|chopped|diced|sliced|minced|whole|boneless|skinless|large|small|medium|extra|virgin|organic)\b', '', text)
    # Clean up whitespace
    text = ' '.join(text.split())
    return text.strip()


def extract_quantity(ingredient):
    """Extract quantity from ingredient string."""
    # Look for common patterns: "1 cup", "2 lbs", "3/4 cup", etc.
    match = re.search(r'(\d+[\/\d]*)\s*(cup|cups|tbsp|tsp|oz|lb|pound|pounds|ounce|ounces|gram|grams|kg|ml|liter|piece|pieces|clove|cloves|can|cans|bunch|bunches|head|heads|package|packages)?', ingredient.lower())
    if match:
        qty_str = match.group(1)
        unit = match.group(2) or ''
        
        # Convert fraction to decimal
        if '/' in qty_str:
            parts = qty_str.split()
            if len(parts) == 2:
                try:
                    whole = float(parts[0])
                    frac = parts[1]
                except ValueError:
                    whole = 0
                    frac = qty_str
            else:
                whole = 0
                frac = qty_str
            if '/' in frac:
                try:
                    num_str, den_str = frac.split('/')
                    if num_str.strip() and den_str.strip():
                        num, den = float(num_str), float(den_str)
                        if den != 0:
                            qty = whole + (num / den)
                        else:
                            qty = whole if whole > 0 else 1.0
                    else:
                        qty = whole if whole > 0 else 1.0
                except (ValueError, ZeroDivisionError):
                    qty = whole if whole > 0 else 1.0
            else:
                qty = whole if whole > 0 else 1.0
        else:
            try:
                qty = float(qty_str)
            except ValueError:
                qty = 1.0
        
        # Convert to pounds for proteins, cups for others
        if unit in ['lb', 'pound', 'pounds']:
            return qty, 'lb'
        elif unit in ['oz', 'ounce', 'ounces']:
            return qty / 16, 'lb'  # Convert oz to lbs
        elif unit in ['cup', 'cups']:
            return qty, 'cup'
        elif unit in ['tbsp', 'tablespoon', 'tablespoons']:
            return qty / 16, 'cup'  # 16 tbsp = 1 cup
        elif unit in ['tsp', 'teaspoon', 'teaspoons']:
            return qty / 48, 'cup'  # 48 tsp = 1 cup
        else:
            # Assume it's a count (e.g., "2 eggs")
            return qty, 'count'
    
    return 1.0, 'count'  # Default


def estimate_ingredient_cost(ingredient):
    """Estimate cost of a single ingredient."""
    normalized = normalize_ingredient(ingredient)
    quantity, unit = extract_quantity(ingredient)
    
    # Try to find matching ingredient
    best_match = None
    best_score = 0
    
    for key, price in INGREDIENT_PRICES.items():
        if key in normalized:
            # Score based on how much of the ingredient name matches
            score = len(key) / len(normalized) if normalized else 0
            if score > best_score:
                best_score = score
                best_match = (key, price)
    
    if not best_match:
        # Default pricing for unknown ingredients
        return 1.50  # Average cost for miscellaneous ingredients
    
    key, base_price = best_match
    
    # Adjust for quantity
    if unit == 'lb':
        cost = quantity * base_price
    elif unit == 'cup':
        # Assume 1 cup ≈ 0.5 lb for most ingredients
        cost = quantity * base_price * 0.5
    else:
        # For count-based items (eggs, etc.)
        cost = quantity * base_price
    
    return cost


def estimate_recipe_price(recipe):
    """Estimate total price for a recipe."""
    if not recipe.get('ingredients'):
        return None
    
    total_cost = 0.0
    ingredient_costs = []
    
    for ingredient in recipe['ingredients']:
        cost = estimate_ingredient_cost(ingredient)
        ingredient_costs.append(cost)
        total_cost += cost
    
    # Estimate servings (default to 4 if not specified)
    # Could be improved by analyzing recipe descriptions or typical serving sizes
    servings = 4
    
    # Some recipes might serve more (soups, stews) or less (appetizers)
    if recipe.get('meal_type') == 'soup':
        servings = 6
    elif recipe.get('meal_type') == 'appetizer':
        servings = 8
    elif recipe.get('meal_type') == 'salad':
        servings = 4
    
    # Price per serving
    price_per_serving = total_cost / servings if servings > 0 else total_cost
    
    # Round to 2 decimal places
    return round(price_per_serving, 2)


def add_pricing_to_recipes():
    """Add estimated pricing to all recipes."""
    print("💰 Adding Estimated Pricing to Recipes\n")
    
    # Load recipes
    print("Loading recipes...")
    with open(CURATED_RECIPES_JSON, 'r') as f:
        recipes = json.load(f)
    
    print(f"  Found {len(recipes)} recipes\n")
    
    # Process each recipe
    print("Estimating prices...")
    priced_count = 0
    skipped_count = 0
    
    for i, recipe in enumerate(recipes):
        if i % 100 == 0:
            print(f"  Processing recipe {i+1}/{len(recipes)}...")
        
        # Skip if already has pricing
        if 'estimated_price' in recipe and recipe['estimated_price'] is not None:
            skipped_count += 1
            continue
        
        estimated_price = estimate_recipe_price(recipe)
        recipe['estimated_price'] = estimated_price
        
        if estimated_price:
            priced_count += 1
    
    print(f"\n✅ Pricing complete!")
    print(f"  Added pricing to {priced_count} recipes")
    if skipped_count > 0:
        print(f"  Skipped {skipped_count} recipes (already had pricing)")
    
    # Save updated recipes
    print("\nSaving updated recipes...")
    with open(CURATED_RECIPES_JSON, 'w') as f:
        json.dump(recipes, f, indent=2)
    
    print("✅ Saved to curated_recipes.json")
    
    # Show some statistics
    prices = [r['estimated_price'] for r in recipes if r.get('estimated_price')]
    if prices:
        print(f"\n📊 Price Statistics:")
        print(f"  Average: ${sum(prices) / len(prices):.2f}")
        print(f"  Minimum: ${min(prices):.2f}")
        print(f"  Maximum: ${max(prices):.2f}")


if __name__ == "__main__":
    add_pricing_to_recipes()
