-- Supabase Recipes Table Schema
-- Run this in Supabase SQL Editor

-- Create recipes table
CREATE TABLE IF NOT EXISTS recipes (
  id BIGSERIAL PRIMARY KEY,
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
  title TEXT NOT NULL,
  protein_source TEXT,
  meal_type TEXT,
  difficulty TEXT,
  ingredients JSONB,
  directions JSONB,
  rating NUMERIC(3,1),
  protein NUMERIC(5,1),
  num_ingredients INTEGER,
  num_steps INTEGER,
  is_family_recipe BOOLEAN DEFAULT FALSE,
  photo TEXT,
  photos JSONB,
  estimated_price NUMERIC(6,2),
  source TEXT,
  source_url TEXT,
  tags JSONB DEFAULT '[]'::jsonb,
  date TIMESTAMPTZ DEFAULT NOW(),
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes for faster queries
CREATE INDEX IF NOT EXISTS idx_recipes_user_id ON recipes(user_id);
CREATE INDEX IF NOT EXISTS idx_recipes_title ON recipes(title);
CREATE INDEX IF NOT EXISTS idx_recipes_protein_source ON recipes(protein_source);
CREATE INDEX IF NOT EXISTS idx_recipes_meal_type ON recipes(meal_type);

-- Enable Row Level Security (RLS)
ALTER TABLE recipes ENABLE ROW LEVEL SECURITY;

-- Public access policies (for anonymous users)
-- Adjust these based on your security needs

-- Allow anyone to read recipes
CREATE POLICY "Anyone can read recipes" ON recipes
  FOR SELECT USING (true);

-- Allow anyone to insert recipes
CREATE POLICY "Anyone can insert recipes" ON recipes
  FOR INSERT WITH CHECK (true);

-- Allow anyone to update recipes (or restrict to owner)
CREATE POLICY "Anyone can update recipes" ON recipes
  FOR UPDATE USING (true);

-- Allow anyone to delete recipes (or restrict to owner)
CREATE POLICY "Anyone can delete recipes" ON recipes
  FOR DELETE USING (true);

-- Optional: More restrictive policies for authenticated users only
-- Uncomment and modify if you want user-specific recipes

-- DROP POLICY IF EXISTS "Anyone can read recipes" ON recipes;
-- DROP POLICY IF EXISTS "Anyone can insert recipes" ON recipes;
-- DROP POLICY IF EXISTS "Anyone can update recipes" ON recipes;
-- DROP POLICY IF EXISTS "Anyone can delete recipes" ON recipes;

-- CREATE POLICY "Users can read their own recipes" ON recipes
--   FOR SELECT USING (auth.uid() = user_id OR user_id IS NULL);
-- 
-- CREATE POLICY "Users can insert their own recipes" ON recipes
--   FOR INSERT WITH CHECK (auth.uid() = user_id);
-- 
-- CREATE POLICY "Users can update their own recipes" ON recipes
--   FOR UPDATE USING (auth.uid() = user_id);
-- 
-- CREATE POLICY "Users can delete their own recipes" ON recipes
--   FOR DELETE USING (auth.uid() = user_id);
