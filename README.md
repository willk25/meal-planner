# 🍽️ Recipe Bot

A Python bot that picks random recipes from Epicurious, writes to Google Sheets & Google Docs, and emails you the options with full ingredients and directions. Runs every 2 days.

## Features

- **2,500+ Curated Recipes** - High-protein, well-rated, simple to make
- **Smart Filtering**: By meal type, protein source, and rating
- **Muscle-Building Focus**: 25-100g protein per serving
- **Complete Info**: Ingredients, directions, calories, ratings
- **Google Sheets**: Updates a sheet with your recipe options
- **Google Docs**: Creates a meal plan doc with shopping lists + directions
- **Email**: Sends formatted email when new recipes are picked

---

## Dataset

**Curated Dataset** (`curated_recipes.json`): 2,567 recipes filtered for:
- ✅ High protein (25-100g per serving)
- ✅ Well-rated (3.75+ stars)
- ✅ Simple (≤15 ingredients)
- ✅ Complete directions
- ❌ No desserts, drinks, or breads

**By Protein Source:**
| Source | Count |
|--------|-------|
| Chicken | 835 |
| Seafood | 491 |
| Beef | 468 |
| Pork | 395 |
| Lamb | 123 |
| Eggs | 65 |
| Turkey | 30 |

**Original Dataset** (`full_format_recipes.json`): 20k recipes from [Epicurious Kaggle](https://www.kaggle.com/datasets/hugodarwood/epirecipes).

Each recipe includes:
| Field | Example |
|-------|---------|
| `title` | "Lentil, Apple, and Turkey Wrap" |
| `ingredients` | ["4 cups stock", "1 cup lentils", ...] |
| `directions` | ["Place stock in pan...", "Fold in tomato..."] |
| `rating` | 4.5 |
| `protein` | 30 |
| `calories` | 426 |
| `protein_source` | "chicken" (curated only) |
| `difficulty` | "easy" / "medium" / "involved" |

---

## Quick Start

### 1. Install Dependencies

```bash
cd /Users/willkannegieser/projects/Recipes
pip install -r requirements.txt
```

### 2. Set Up Google APIs (One-Time)

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create/select a project
3. **APIs & Services → Enable APIs** → Enable:
   - "Google Sheets API"
   - "Google Docs API"
   - "Google Drive API"
4. **APIs & Services → Credentials → Create credentials → Service account**
5. Create account → **Keys → Add Key → JSON**
6. Save as `service_account.json` in this folder

### 3. Create Your Google Sheet

1. Create a new Google Sheet
2. Copy the **spreadsheet ID** from the URL:
   ```
   https://docs.google.com/spreadsheets/d/SPREADSHEET_ID_HERE/edit
   ```
3. **Share** with your service account email (Editor access)

### 4. Configure `.env`

```bash
# Google Sheets & Docs
GOOGLE_SHEET_ID=your_spreadsheet_id_here
GOOGLE_DOC_ID=                           # Optional: leave blank to create new docs

# Apps Script (set up in next section)
APPS_SCRIPT_URL=https://script.google.com/macros/s/.../exec

# Recipe Filters
NUM_RECIPES=5          # Recipes per run
MIN_RATING=3.5         # Minimum stars (0-5)
MEAL_TYPE=entree       # entree, dessert, appetizer, breakfast, any
PROTEIN_SOURCE=any     # chicken, beef, pork, seafood, turkey, lamb, eggs, any
```

### 5. Run It!

```bash
python recipe_bot.py
```

---

## 📧 Email Setup (Apps Script)

### Step 1: Open Apps Script

In your Google Sheet: **Extensions → Apps Script**

### Step 2: Paste This Code

```javascript
function sendRecipeEmail() {
  var sheet = SpreadsheetApp.getActiveSpreadsheet();
  var recipesSheet = sheet.getSheetByName("Selected Recipes");
  var data = recipesSheet.getDataRange().getValues();
  
  var emailBody = "🍽️ YOUR RECIPE OPTIONS\n";
  emailBody += "══════════════════════════════════════════════════\n\n";
  
  for (var i = 1; i < data.length; i++) {
    var title = data[i][0];        // Title
    var ingredients = data[i][1];   // Ingredients
    var rating = data[i][2];        // Rating
    var calories = data[i][3];      // Calories
    
    if (!title) continue;
    
    emailBody += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n";
    emailBody += "OPTION " + i + ": " + title.toUpperCase() + "\n";
    emailBody += rating + " | " + calories + "\n";
    emailBody += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n";
    
    emailBody += "Grocery List:\n";
    var ingredientList = ingredients.split("\n");
    ingredientList.forEach(function(item) {
      item = item.replace(/^[•\-]\s*/, "").trim();
      if (item) emailBody += "  [ ] " + item + "\n";
    });
    
    emailBody += "\n\n";
  }
  
  emailBody += "══════════════════════════════════════════════════\n";
  emailBody += "Happy cooking! 🍳\n";
  
  MailApp.sendEmail({
    to: Session.getActiveUser().getEmail(),
    subject: "🍽️ This Week's Recipe Options",
    body: emailBody
  });
}

function doGet(e) {
  sendRecipeEmail();
  return ContentService.createTextOutput("Email sent!");
}
```

### Step 3: Deploy as Web App

1. **Save** the script
2. **Run** `sendRecipeEmail` once and allow permissions
3. **Deploy → New deployment → Web app**
   - Execute as: Me
   - Access: Anyone
4. Copy the URL to your `.env`

---

## Configuration

| Variable | Default | Options |
|----------|---------|---------|
| `NUM_RECIPES` | 5 | Any number |
| `MIN_RATING` | 3.5 | 0-5 |
| `MEAL_TYPE` | entree | `entree`, `dessert`, `appetizer`, `breakfast`, `soup`, `side`, `any` |
| `PROTEIN_SOURCE` | any | `chicken`, `beef`, `pork`, `seafood`, `turkey`, `lamb`, `eggs`, `any` |

### Meal Type Categories

| Type | Matches |
|------|---------|
| `entree` | Main Course, Dinner, Chicken, Beef, Fish, Pasta... |
| `dessert` | Dessert, Cake, Cookie, Pie, Chocolate... |
| `appetizer` | Appetizer, Starter, Dip, Snack... |
| `breakfast` | Breakfast, Brunch, Pancake, Egg... |
| `soup` | Soup, Stew, Chili... |
| `side` | Side, Salad, Vegetable... |
| `any` | All recipes |

### Protein Source Filter (Curated Recipes Only)

| Source | Description |
|--------|-------------|
| `chicken` | Chicken dishes (835 recipes) |
| `beef` | Beef, steak, ground beef (468 recipes) |
| `pork` | Pork, bacon, ham (395 recipes) |
| `seafood` | Fish, shrimp, salmon (491 recipes) |
| `turkey` | Turkey dishes (30 recipes) |
| `lamb` | Lamb dishes (123 recipes) |
| `eggs` | Egg-based dishes (65 recipes) |
| `any` | All protein sources |

---

## Schedule (Every 2 Days)

### macOS (cron)

```bash
crontab -e
```

```cron
0 7 */2 * * cd /Users/willkannegieser/projects/Recipes && python3 recipe_bot.py >> recipe_bot.log 2>&1
```

### macOS (launchd)

Create `~/Library/LaunchAgents/com.recipebot.plist`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.recipebot</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/python3</string>
        <string>/Users/willkannegieser/projects/Recipes/recipe_bot.py</string>
    </array>
    <key>StartInterval</key>
    <integer>172800</integer>
    <key>WorkingDirectory</key>
    <string>/Users/willkannegieser/projects/Recipes</string>
    <key>StandardOutPath</key>
    <string>/Users/willkannegieser/projects/Recipes/recipe_bot.log</string>
    <key>StandardErrorPath</key>
    <string>/Users/willkannegieser/projects/Recipes/recipe_bot.log</string>
</dict>
</plist>
```

```bash
launchctl load ~/Library/LaunchAgents/com.recipebot.plist
```

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `No recipes match` | Lower `MIN_RATING` or use `MEAL_TYPE=any` |
| `service_account.json not found` | Download from Google Cloud Console |
| `Sheets permission denied` | Share sheet with service account email |
| `Apps Script error` | Run Python bot first to create "Selected Recipes" sheet |

---

## Files

| File | Purpose |
|------|---------|
| `recipe_bot.py` | Main bot script |
| `curate_recipes.py` | Script to re-curate recipes with custom filters |
| `curated_recipes.json` | 2,567 high-protein, simple, well-rated recipes |
| `full_format_recipes.json` | 20k recipes with full data (original) |
| `service_account.json` | Google API credentials |
| `.env` | Your configuration |

---

## Re-Curating Recipes

Want to adjust the filters? Edit `curate_recipes.py` and run:

```bash
python curate_recipes.py
```

Adjustable filters in the script:
- `MIN_PROTEIN` - Minimum protein per serving (default: 25g)
- `MAX_PROTEIN` - Maximum protein per serving (default: 100g)
- `MIN_RATING` - Minimum star rating (default: 3.75)
- `MAX_INGREDIENTS` - Maximum ingredients for simplicity (default: 15)

---

Enjoy your meal planning! 🍳💪
