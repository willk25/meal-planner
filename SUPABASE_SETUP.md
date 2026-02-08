# Supabase Setup Guide

This guide will help you set up Supabase for recipe storage without breaking your existing app.

## ✅ What's Already Done

1. ✅ Database abstraction layer (`db_layer.py`) created
2. ✅ `upload_recipe.py` updated to use database layer
3. ✅ Automatic fallback to JSON if Supabase fails
4. ✅ Supabase package added to `requirements.txt`

## Step 1: Install Supabase Package

```bash
pip install supabase>=2.0.0
```

## Step 2: Create Supabase Project

1. Go to https://supabase.com and sign up/login
2. Click "New Project"
3. Fill in:
   - **Name**: `meal-planner` (or your choice)
   - **Database Password**: Choose a strong password (save it!)
   - **Region**: Choose closest to you
4. Click "Create new project" (takes ~2 minutes)

## Step 3: Create Recipes Table

1. In your Supabase dashboard, go to **SQL Editor**
2. Click "New query"
3. Paste this SQL:

```sql
-- Create recipes table
CREATE TABLE IF NOT EXISTS recipes (
  id BIGSERIAL PRIMARY KEY,
  title TEXT NOT NULL,
  ingredients JSONB NOT NULL,
  directions JSONB NOT NULL,
  protein_source TEXT,
  meal_type TEXT,
  difficulty TEXT,
  rating NUMERIC(3,1),
  protein NUMERIC(5,1),
  "desc" TEXT,
  categories JSONB,
  date TIMESTAMPTZ DEFAULT NOW(),
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes for faster lookups
CREATE INDEX IF NOT EXISTS idx_recipes_title ON recipes(title);
CREATE INDEX IF NOT EXISTS idx_recipes_meal_type ON recipes(meal_type);

-- Disable Row Level Security (for now - you can enable it later)
ALTER TABLE recipes DISABLE ROW LEVEL SECURITY;
```

4. Click "Run" (or press Cmd/Ctrl + Enter)

## Step 3b: Multi-User Setup (COMMENTED OUT - Enable Later)

<!-- 
Uncomment this section when ready to add user authentication and personal recipe collections.

1. First, enable Authentication in Supabase Dashboard:
   - Go to Authentication → Settings
   - Enable Email provider
   - Configure email templates (optional)

2. Then run this SQL in the SQL Editor:

```sql
-- Create profiles table for user accounts
CREATE TABLE IF NOT EXISTS profiles (
  id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  email TEXT,
  full_name TEXT,
  avatar_url TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Add user_id to recipes table (foreign key to profiles)
ALTER TABLE recipes ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES profiles(id) ON DELETE CASCADE;

-- Create index for user-specific queries
CREATE INDEX IF NOT EXISTS idx_recipes_user_id ON recipes(user_id);

-- Enable Row Level Security for multi-user
ALTER TABLE recipes ENABLE ROW LEVEL SECURITY;

-- RLS Policies: Users can only access their own recipes
CREATE POLICY "Users can view own recipes" ON recipes
  FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own recipes" ON recipes
  FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own recipes" ON recipes
  FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own recipes" ON recipes
  FOR DELETE USING (auth.uid() = user_id);
```

3. Update your code to use user-specific functions (see MULTI_USER_SETUP.md for details)
-->

## Step 4: Get API Credentials

1. Go to **Settings** → **API**
2. Copy these values:
   - **Project URL** (looks like: `https://xxxxx.supabase.co`)
   - **anon/public key** (the `anon` key, not the `service_role` key)

## Step 5: Configure Environment Variables

Create a `.env` file in your project root:

```bash
# Database Configuration
USE_SUPABASE=true
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_KEY=your-anon-key-here
```

**Important**: The `.env` file is already in `.gitignore` so it won't be committed.

## Step 6: Test It

1. Make sure Supabase is working:
   ```bash
   python3 -c "from db_layer import get_storage_type; print(f'Storage: {get_storage_type()}')"
   ```
   Should print: `Storage: Supabase`

2. Test adding a recipe:
   ```bash
   python3 upload_recipe.py --interactive
   ```

3. Check your Supabase dashboard → **Table Editor** → **recipes** to see if it appears

## How It Works

- **If Supabase is enabled and working**: Recipes are stored in Supabase
- **If Supabase fails or is disabled**: Automatically falls back to JSON file
- **No breaking changes**: Your app keeps working either way!

## Troubleshooting

### "Supabase client not initialized"
- Check that `USE_SUPABASE=true` in your `.env` file
- Verify `SUPABASE_URL` and `SUPABASE_KEY` are set correctly
- Check that `supabase` package is installed: `pip install supabase`

### "Table does not exist"
- Make sure you ran the SQL script in Step 3
- Check the table name is exactly `recipes` (lowercase)

### "Permission denied"
- Make sure you're using the `anon` key, not `service_role`
- Check that Row Level Security is disabled (see SQL script)

### Still using JSON?
- Check that `USE_SUPABASE=true` (not `True` or `1`)
- Check the console output when importing - it will say which storage is being used
- Default is JSON (safe fallback)

## Disabling Supabase (Fallback to JSON)

Just set `USE_SUPABASE=false` in your `.env` file or remove the variable. The app will automatically use JSON files.

## Migration: Moving Existing Recipes to Supabase

Once Supabase is working, you can migrate your existing JSON recipes:

```python
# Run this once to migrate
from db_layer import load_recipes, save_recipes
import json

# Load from JSON (if Supabase is disabled, this loads from JSON)
# Enable Supabase first, then:
recipes = load_recipes()  # This will load from JSON if Supabase is off
# Then enable Supabase and:
save_recipes(recipes)  # This will save to Supabase
print(f"Migrated {len(recipes)} recipes to Supabase!")
```

Or use this migration script:

```python
# migrate_to_supabase.py
from pathlib import Path
import json
from db_layer import save_recipes

# Load from JSON file directly
json_file = Path(__file__).parent / "curated_recipes.json"
with open(json_file, 'r') as f:
    recipes = json.load(f)

# Save to Supabase (make sure USE_SUPABASE=true in .env)
save_recipes(recipes)
print(f"✅ Migrated {len(recipes)} recipes to Supabase!")
```
