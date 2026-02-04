# Recipe Upload Tool

The `upload_recipe.py` script allows you to easily add new recipes to your `curated_recipes.json` file in multiple formats.

## Quick Start

```bash
# Upload from a text file
python upload_recipe.py recipe.txt

# Upload from a JSON file
python upload_recipe.py recipe.json --format json

# Interactive mode (type recipe directly)
python upload_recipe.py --interactive
```

## Supported Input Formats

### Format 1: Simple Text (Recommended for Manual Entry)

The easiest format for typing recipes manually:

```
Title: Recipe Name Here
Ingredients:
- 1 cup ingredient one
- 2 tablespoons ingredient two
- 3 cloves ingredient three
Directions:
1. First step here
2. Second step here
3. Third step here
Protein Source: chicken (optional)
Meal Type: entree (optional)
Difficulty: medium (optional)
Rating: 4.5 (optional)
Protein (g): 35 (optional)
```

**Notes:**
- Ingredients can use `-`, `•`, or `*` as bullet points
- Directions can be numbered (1., 2., etc.) or plain text
- Optional fields can be in any order
- Case-insensitive field names

### Format 2: JSON (For Programmatic Uploads)

Structured format perfect for scripts or APIs:

```json
{
  "title": "Recipe Name Here",
  "ingredients": [
    "1 cup ingredient one",
    "2 tablespoons ingredient two",
    "3 cloves ingredient three"
  ],
  "directions": [
    "First step here",
    "Second step here",
    "Third step here"
  ],
  "protein_source": "chicken",
  "meal_type": "entree",
  "difficulty": "medium",
  "rating": 4.5,
  "protein": 35
}
```

## Field Reference

### Required Fields

- **title** (string): Recipe name
- **ingredients** (array): List of ingredient strings, one per line/item
- **directions** (array): List of cooking steps, one per step

### Optional Fields (Auto-Detected if Missing)

- **protein_source**: `"chicken"`, `"beef"`, `"pork"`, `"seafood"`, `"turkey"`, `"lamb"`, `"eggs"`, or `"other"`
- **meal_type**: `"entree"`, `"appetizer"`, `"dessert"`, `"breakfast"`, `"soup"`, `"salad"`, or `"side"`
- **difficulty**: `"easy"`, `"medium"`, or `"involved"` (auto-calculated from ingredient/step count)

### Optional Fields (Manual Entry)

- **rating** (number): 0-5 star rating
- **protein** (number): Protein in grams
- **calories** (number): Calories per serving
- **estimated_price** (number): Estimated cost
- **desc** or **description** (string): Recipe description
- **source** (string): Recipe source/attribution
- **categories** (array): List of category tags

### Auto-Calculated Fields

These are automatically added:
- **num_ingredients**: Count of ingredients
- **num_steps**: Count of directions
- **date**: ISO timestamp when added

## Usage Examples

### Single File Upload

```bash
python upload_recipe.py my_recipe.txt
```

### JSON Upload

```bash
python upload_recipe.py recipe.json --format json
```

### Interactive Mode

```bash
python upload_recipe.py --interactive
```

Then type your recipe and end with `DONE` on a new line.

### Batch Upload

```bash
python upload_recipe.py recipes/*.txt
```

### Skip Preview (For Scripts)

```bash
python upload_recipe.py recipe.txt --no-preview --skip-duplicate-check
```

## Command Line Options

- `--format {auto,text,json}`: Specify input format (default: auto-detect)
- `--interactive, -i`: Enter recipe interactively
- `--skip-duplicate-check`: Skip checking for duplicate recipe titles
- `--no-preview`: Skip preview and confirmation (useful for batch processing)

## Auto-Detection

The tool automatically detects missing metadata:

- **Protein Source**: Scans title and ingredients for keywords (chicken, beef, etc.)
- **Meal Type**: Analyzes title and categories for meal type indicators
- **Difficulty**: Calculated from number of ingredients and steps:
  - Easy: ≤6 ingredients, ≤4 steps
  - Medium: ≤10 ingredients, ≤7 steps
  - Involved: More than above

## Validation

The tool validates:
- ✅ Title is present and non-empty
- ✅ At least 1 ingredient provided
- ✅ At least 1 direction provided
- ✅ Ingredients and directions are arrays (not strings)
- ✅ No duplicate recipe titles (unless `--skip-duplicate-check` is used)

## Safety Features

- **Automatic Backup**: Creates a timestamped backup before modifying `curated_recipes.json`
- **Preview Before Adding**: Shows recipe preview and asks for confirmation
- **Duplicate Detection**: Warns if recipe title already exists
- **Error Handling**: Graceful error messages with helpful feedback

## Python API

You can also use the upload tool programmatically:

```python
from upload_recipe import add_recipe

recipe = {
    "title": "My Recipe",
    "ingredients": ["1 cup flour", "2 eggs"],
    "directions": ["Mix ingredients", "Bake at 350°F"]
}

success, message = add_recipe(recipe)
print(message)
```

## Tips

1. **Ingredient Formatting**: Include quantities in ingredient strings (e.g., "1 cup flour" not just "flour")
2. **One Step Per Direction**: Each direction should be a separate step, not combined
3. **Meal Type**: If your recipe is a salad, explicitly set `Meal Type: salad` in text format
4. **Batch Processing**: Use `--no-preview` and `--skip-duplicate-check` for automated scripts

## Troubleshooting

**"Validation failed: Missing required field: title"**
- Make sure your recipe has a title field

**"Duplicate recipe found"**
- A recipe with the same title already exists
- Use `--skip-duplicate-check` to override (not recommended)

**"Error parsing recipe"**
- Check your JSON syntax if using JSON format
- For text format, ensure proper section headers (Title:, Ingredients:, Directions:)

## Integration with Meal Planner

Uploaded recipes are immediately available in:
- `meal_planner.html` web interface
- Recipe search functionality
- Weekly meal generation
- All existing meal planner features
