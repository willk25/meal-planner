-- Complete recipes table setup script
-- Run this in Supabase SQL Editor to create/update the recipes table

-- Drop table if it exists (only if you want to start fresh)
-- DROP TABLE IF EXISTS recipes CASCADE;

-- Create recipes table with all columns
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
  estimated_price NUMERIC(6,2),
  num_ingredients INTEGER,
  num_steps INTEGER,
  date TIMESTAMPTZ DEFAULT NOW(),
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Add any missing columns (safe to run even if columns exist)
ALTER TABLE recipes 
  ADD COLUMN IF NOT EXISTS "desc" TEXT,
  ADD COLUMN IF NOT EXISTS categories JSONB,
  ADD COLUMN IF NOT EXISTS estimated_price NUMERIC(6,2),
  ADD COLUMN IF NOT EXISTS num_ingredients INTEGER,
  ADD COLUMN IF NOT EXISTS num_steps INTEGER;

-- Create indexes for faster lookups
CREATE INDEX IF NOT EXISTS idx_recipes_title ON recipes(title);
CREATE INDEX IF NOT EXISTS idx_recipes_meal_type ON recipes(meal_type);
CREATE INDEX IF NOT EXISTS idx_recipes_protein_source ON recipes(protein_source);
CREATE INDEX IF NOT EXISTS idx_recipes_difficulty ON recipes(difficulty);
CREATE INDEX IF NOT EXISTS idx_recipes_rating ON recipes(rating);

-- Disable Row Level Security (for now - you can enable it later for multi-user)
ALTER TABLE recipes DISABLE ROW LEVEL SECURITY;

-- Refresh the PostgREST schema cache (required for API to see all columns)
-- Wait 10-15 seconds after running this before using the API
NOTIFY pgrst, 'reload schema';
