-- Multi-user setup for Meal Planner
-- Keeps recipes public/shared, adds profiles + favorites with RLS

-- 1) Add optional user_id on recipes (existing recipes remain public)
ALTER TABLE public.recipes
  ADD COLUMN IF NOT EXISTS user_id uuid REFERENCES auth.users(id);

CREATE INDEX IF NOT EXISTS idx_recipes_user_id ON public.recipes(user_id);

-- 2) Profiles table for username
CREATE TABLE IF NOT EXISTS public.profiles (
  id uuid PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  username text UNIQUE NOT NULL,
  created_at timestamptz DEFAULT now()
);

-- If profiles table already exists without a unique constraint, add a unique index.
-- Note: this will fail if you have duplicate usernames; clean them up first.
CREATE UNIQUE INDEX IF NOT EXISTS idx_profiles_username ON public.profiles(username);

-- 3) Favorites table (per-user)
CREATE TABLE IF NOT EXISTS public.favorites (
  id bigserial PRIMARY KEY,
  user_id uuid NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  recipe_id bigint NOT NULL REFERENCES public.recipes(id) ON DELETE CASCADE,
  created_at timestamptz DEFAULT now(),
  UNIQUE (user_id, recipe_id)
);

CREATE INDEX IF NOT EXISTS idx_favorites_user_id ON public.favorites(user_id);
CREATE INDEX IF NOT EXISTS idx_favorites_recipe_id ON public.favorites(recipe_id);

-- 4) RLS
ALTER TABLE public.recipes ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.favorites ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;

-- Recipes: anyone can read (public). Inserts allowed for public recipes (user_id null) or own recipes.
CREATE POLICY "recipes are public" ON public.recipes
  FOR SELECT USING (true);

CREATE POLICY "insert public or own recipes" ON public.recipes
  FOR INSERT WITH CHECK (user_id IS NULL OR auth.uid() = user_id);

CREATE POLICY "update own recipes" ON public.recipes
  FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "delete own recipes" ON public.recipes
  FOR DELETE USING (auth.uid() = user_id);

-- Favorites: only owner can read/write
CREATE POLICY "favorites read own" ON public.favorites
  FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "favorites insert own" ON public.favorites
  FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "favorites delete own" ON public.favorites
  FOR DELETE USING (auth.uid() = user_id);

-- Profiles: only owner can read/write their profile
CREATE POLICY "profiles read own" ON public.profiles
  FOR SELECT USING (auth.uid() = id);

CREATE POLICY "profiles insert own" ON public.profiles
  FOR INSERT WITH CHECK (auth.uid() = id);

CREATE POLICY "profiles update own" ON public.profiles
  FOR UPDATE USING (auth.uid() = id);

-- Optional: allow everyone to read usernames for display
-- CREATE POLICY "profiles read public" ON public.profiles
--   FOR SELECT USING (true);
