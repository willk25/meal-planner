-- Migration script to add missing columns and fix policies
-- Run this in Supabase SQL Editor

-- Add missing columns if they don't exist
ALTER TABLE recipes ADD COLUMN IF NOT EXISTS source_url TEXT;
ALTER TABLE recipes ADD COLUMN IF NOT EXISTS tags JSONB DEFAULT '[]'::jsonb;

-- Drop existing policies if they exist (to avoid conflicts)
DROP POLICY IF EXISTS "Anyone can read recipes" ON recipes;
DROP POLICY IF EXISTS "Anyone can insert recipes" ON recipes;
DROP POLICY IF EXISTS "Anyone can update recipes" ON recipes;
DROP POLICY IF EXISTS "Anyone can delete recipes" ON recipes;
DROP POLICY IF EXISTS "Users can read own recipes" ON recipes;
DROP POLICY IF EXISTS "Users can insert own recipes" ON recipes;
DROP POLICY IF EXISTS "Users can update own recipes" ON recipes;
DROP POLICY IF EXISTS "Users can delete own recipes" ON recipes;

-- Create user-specific policies (users can only see/edit their own recipes)
CREATE POLICY "Users can read own recipes" ON recipes
  FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own recipes" ON recipes
  FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own recipes" ON recipes
  FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own recipes" ON recipes
  FOR DELETE USING (auth.uid() = user_id);

-- Optional: If you want to allow anonymous users to read recipes (but not write)
-- Uncomment the line below:
-- CREATE POLICY "Anyone can read recipes" ON recipes FOR SELECT USING (true);
