# Fix Migration Issue

## Problem
The migration failed because your recipes have fields that don't exist in the Supabase table:
- `estimated_price`
- `num_ingredients`
- `num_steps`

Note: We're filtering out `calories`, `fat`, and `sodium` as they're not needed.

## Solution

### Step 1: Add Missing Columns to Supabase

1. Go to your Supabase dashboard
2. Navigate to **SQL Editor**
3. Click **New query**
4. Copy and paste the SQL from `add_missing_columns.sql`:

```sql
-- Add missing columns to recipes table
ALTER TABLE recipes 
  ADD COLUMN IF NOT EXISTS estimated_price NUMERIC(6,2),
  ADD COLUMN IF NOT EXISTS num_ingredients INTEGER,
  ADD COLUMN IF NOT EXISTS num_steps INTEGER;

-- Add indexes for commonly queried fields
CREATE INDEX IF NOT EXISTS idx_recipes_protein_source ON recipes(protein_source);
CREATE INDEX IF NOT EXISTS idx_recipes_difficulty ON recipes(difficulty);
CREATE INDEX IF NOT EXISTS idx_recipes_rating ON recipes(rating);
```

5. Click **Run** (or press Cmd/Ctrl + Enter)

### Step 2: Run Migration Again

After adding the columns, run the migration script again:

```bash
python3 migrate_to_supabase.py
```

This time it should succeed and upload all 1697 recipes to Supabase!

## What Happened Before

The migration script tried to save to Supabase, but Supabase rejected the data because the `calories` column didn't exist. The script then fell back to saving to the JSON file (which is why it said "Successfully migrated" - it saved to JSON, not Supabase).

After adding the missing columns, the migration will work correctly.
