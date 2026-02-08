-- Add missing columns to recipes table (if table already exists)
-- For a complete fresh setup, use create_recipes_table_complete.sql instead

-- Ensure all required columns exist
ALTER TABLE recipes 
  ADD COLUMN IF NOT EXISTS "desc" TEXT,
  ADD COLUMN IF NOT EXISTS categories JSONB,
  ADD COLUMN IF NOT EXISTS estimated_price NUMERIC(6,2),
  ADD COLUMN IF NOT EXISTS num_ingredients INTEGER,
  ADD COLUMN IF NOT EXISTS num_steps INTEGER;

-- Refresh the PostgREST schema cache (required for API to see new columns)
NOTIFY pgrst, 'reload schema';

-- Add indexes for commonly queried fields
CREATE INDEX IF NOT EXISTS idx_recipes_protein_source ON recipes(protein_source);
CREATE INDEX IF NOT EXISTS idx_recipes_difficulty ON recipes(difficulty);
CREATE INDEX IF NOT EXISTS idx_recipes_rating ON recipes(rating);
