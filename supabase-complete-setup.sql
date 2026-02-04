-- Complete Supabase Setup for Recipe Curator
-- Run this entire script in Supabase SQL Editor
-- This script is idempotent - safe to run multiple times

-- ============================================================================
-- 1) Create recipes table if it doesn't exist
-- ============================================================================
CREATE TABLE IF NOT EXISTS public.recipes (
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

-- ============================================================================
-- 2) Add missing columns (safe if already exist)
-- ============================================================================
ALTER TABLE public.recipes
  ADD COLUMN IF NOT EXISTS source_url TEXT;

ALTER TABLE public.recipes
  ADD COLUMN IF NOT EXISTS is_baseline BOOLEAN DEFAULT FALSE;

-- Handle tags column carefully - check if it exists and what type it is
DO $$
BEGIN
  -- Check if tags column exists
  IF EXISTS (
    SELECT 1 FROM information_schema.columns 
    WHERE table_schema = 'public' 
    AND table_name = 'recipes' 
    AND column_name = 'tags'
  ) THEN
    -- Column exists, check if it's the wrong type
    IF EXISTS (
      SELECT 1 FROM information_schema.columns 
      WHERE table_schema = 'public' 
      AND table_name = 'recipes' 
      AND column_name = 'tags' 
      AND udt_name = '_text'
    ) THEN
      -- It's TEXT[], convert to JSONB
      ALTER TABLE public.recipes ALTER COLUMN tags DROP DEFAULT;
      ALTER TABLE public.recipes 
        ALTER COLUMN tags TYPE JSONB 
        USING CASE 
          WHEN tags IS NULL THEN '[]'::jsonb
          WHEN array_length(tags, 1) IS NULL THEN '[]'::jsonb
          ELSE to_jsonb(tags)
        END;
      ALTER TABLE public.recipes ALTER COLUMN tags SET DEFAULT '[]'::jsonb;
    END IF;
    -- If it's already JSONB, do nothing
  ELSE
    -- Column doesn't exist, add it
    ALTER TABLE public.recipes ADD COLUMN tags JSONB DEFAULT '[]'::jsonb;
  END IF;
END $$;

-- ============================================================================
-- 3) Create indexes
-- ============================================================================
CREATE INDEX IF NOT EXISTS idx_recipes_user_id ON public.recipes(user_id);
CREATE INDEX IF NOT EXISTS idx_recipes_title ON public.recipes(title);
CREATE INDEX IF NOT EXISTS idx_recipes_protein_source ON public.recipes(protein_source);
CREATE INDEX IF NOT EXISTS idx_recipes_meal_type ON public.recipes(meal_type);
CREATE INDEX IF NOT EXISTS idx_recipes_is_baseline ON public.recipes(is_baseline);

-- ============================================================================
-- 4) Enable Row Level Security
-- ============================================================================
ALTER TABLE public.recipes ENABLE ROW LEVEL SECURITY;

-- ============================================================================
-- 5) Create profiles table
-- ============================================================================
CREATE TABLE IF NOT EXISTS public.profiles (
  id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  username TEXT,
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;

-- ============================================================================
-- 6) Drop all existing policies (clean slate)
-- ============================================================================
DROP POLICY IF EXISTS "Anyone can read recipes" ON public.recipes;
DROP POLICY IF EXISTS "Anyone can insert recipes" ON public.recipes;
DROP POLICY IF EXISTS "Anyone can update recipes" ON public.recipes;
DROP POLICY IF EXISTS "Anyone can delete recipes" ON public.recipes;
DROP POLICY IF EXISTS "Users can read own recipes" ON public.recipes;
DROP POLICY IF EXISTS "Users can insert own recipes" ON public.recipes;
DROP POLICY IF EXISTS "Users can update own recipes" ON public.recipes;
DROP POLICY IF EXISTS "Users can delete own recipes" ON public.recipes;
DROP POLICY IF EXISTS "Anyone can read baseline recipes" ON public.recipes;
DROP POLICY IF EXISTS "Users can read own user recipes" ON public.recipes;
DROP POLICY IF EXISTS "Users can insert own user recipes" ON public.recipes;
DROP POLICY IF EXISTS "Users can update own user recipes" ON public.recipes;
DROP POLICY IF EXISTS "Users can delete own user recipes" ON public.recipes;
DROP POLICY IF EXISTS "Users can read own profile" ON public.profiles;
DROP POLICY IF EXISTS "Users can update own profile" ON public.profiles;
DROP POLICY IF EXISTS "Users can insert own profile" ON public.profiles;

-- ============================================================================
-- 7) Create recipes policies (baseline + user-scoped)
-- ============================================================================
-- Baseline recipes: Readable by everyone, not editable by users
CREATE POLICY "Anyone can read baseline recipes"
  ON public.recipes
  FOR SELECT
  USING (is_baseline = true);

-- User recipes: Readable/writable by owner only
CREATE POLICY "Users can read own user recipes"
  ON public.recipes
  FOR SELECT
  USING (is_baseline = false AND auth.uid() = user_id);

CREATE POLICY "Users can insert own user recipes"
  ON public.recipes
  FOR INSERT
  WITH CHECK (is_baseline = false AND auth.uid() = user_id);

CREATE POLICY "Users can update own user recipes"
  ON public.recipes
  FOR UPDATE
  USING (is_baseline = false AND auth.uid() = user_id);

CREATE POLICY "Users can delete own user recipes"
  ON public.recipes
  FOR DELETE
  USING (is_baseline = false AND auth.uid() = user_id);

-- ============================================================================
-- 8) Create profiles policies
-- ============================================================================
CREATE POLICY "Users can read own profile"
  ON public.profiles
  FOR SELECT
  USING (auth.uid() = id);

CREATE POLICY "Users can update own profile"
  ON public.profiles
  FOR UPDATE
  USING (auth.uid() = id);

CREATE POLICY "Users can insert own profile"
  ON public.profiles
  FOR INSERT
  WITH CHECK (auth.uid() = id);

-- ============================================================================
-- 9) Create updated_at trigger function
-- ============================================================================
CREATE OR REPLACE FUNCTION public.set_updated_at()
RETURNS trigger AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- 10) Create triggers
-- ============================================================================
DROP TRIGGER IF EXISTS set_recipes_updated_at ON public.recipes;
CREATE TRIGGER set_recipes_updated_at
  BEFORE UPDATE ON public.recipes
  FOR EACH ROW
  EXECUTE FUNCTION public.set_updated_at();

DROP TRIGGER IF EXISTS set_profiles_updated_at ON public.profiles;
CREATE TRIGGER set_profiles_updated_at
  BEFORE UPDATE ON public.profiles
  FOR EACH ROW
  EXECUTE FUNCTION public.set_updated_at();
