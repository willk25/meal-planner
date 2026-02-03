# Supabase Setup Guide

This guide will help you set up Supabase for persistent recipe storage in the Recipe Curator.

## Step 1: Create a Supabase Project

1. Go to [https://supabase.com](https://supabase.com)
2. Sign up or log in
3. Click "New Project"
4. Fill in:
   - **Name**: Recipes (or your preferred name)
   - **Database Password**: Choose a strong password (save it!)
   - **Region**: Choose closest to you
5. Click "Create new project" (takes ~2 minutes)

## Step 2: Get Your Project Credentials

1. In your Supabase project dashboard, go to **Settings** → **API**
2. Copy these values:
   - **Project URL** (looks like: `https://xxxxx.supabase.co`)
   - **anon/public key** (under "Project API keys")

## Step 3: Create the Database Table

1. In Supabase dashboard, go to **SQL Editor**
2. Click "New query"
3. Paste and run this SQL:

```sql
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
  date TIMESTAMPTZ DEFAULT NOW(),
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create index for faster queries
CREATE INDEX IF NOT EXISTS idx_recipes_user_id ON recipes(user_id);
CREATE INDEX IF NOT EXISTS idx_recipes_title ON recipes(title);
CREATE INDEX IF NOT EXISTS idx_recipes_protein_source ON recipes(protein_source);
CREATE INDEX IF NOT EXISTS idx_recipes_meal_type ON recipes(meal_type);

-- Enable Row Level Security (RLS)
ALTER TABLE recipes ENABLE ROW LEVEL SECURITY;

-- Create policies for anonymous users (or authenticated users)
-- Option 1: Allow anyone to read, but only authenticated users to write
CREATE POLICY "Anyone can read recipes" ON recipes
  FOR SELECT USING (true);

CREATE POLICY "Anyone can insert recipes" ON recipes
  FOR INSERT WITH CHECK (true);

CREATE POLICY "Users can update their own recipes" ON recipes
  FOR UPDATE USING (auth.uid() = user_id OR user_id IS NULL);

CREATE POLICY "Users can delete their own recipes" ON recipes
  FOR DELETE USING (auth.uid() = user_id OR user_id IS NULL);

-- Option 2: If you want completely public read/write (simpler for now)
-- DROP POLICY IF EXISTS "Anyone can read recipes" ON recipes;
-- DROP POLICY IF EXISTS "Anyone can insert recipes" ON recipes;
-- DROP POLICY IF EXISTS "Users can update their own recipes" ON recipes;
-- DROP POLICY IF EXISTS "Users can delete their own recipes" ON recipes;

-- CREATE POLICY "Public read access" ON recipes FOR SELECT USING (true);
-- CREATE POLICY "Public insert access" ON recipes FOR INSERT WITH CHECK (true);
-- CREATE POLICY "Public update access" ON recipes FOR UPDATE USING (true);
-- CREATE POLICY "Public delete access" ON recipes FOR DELETE USING (true);
```

4. Click "Run" to execute the SQL

## Step 4: Configure Your App

1. Create a file called `supabase-config.js` in your project root (or we'll add it inline)
2. Add your Supabase credentials:

```javascript
const SUPABASE_URL = 'https://your-project-id.supabase.co';
const SUPABASE_ANON_KEY = 'your-anon-key-here';
```

**OR** use environment variables (recommended for production):

For Vercel deployment, add these in your Vercel project settings:
- `NEXT_PUBLIC_SUPABASE_URL`
- `NEXT_PUBLIC_SUPABASE_ANON_KEY`

## Step 5: Enable Authentication (Optional but Recommended)

If you want user-specific recipes:

1. In Supabase dashboard, go to **Authentication** → **Providers**
2. Enable **Email** provider (or others like Google, GitHub)
3. Configure email templates if needed

For anonymous access (simpler, no login required):
- The table policies above already allow anonymous access
- Recipes will have `user_id = NULL` for anonymous users

## Step 6: Test the Setup

1. Open `recipe_curator.html` in your browser
2. Open browser console (F12)
3. Try adding a recipe
4. Check Supabase dashboard → **Table Editor** → **recipes** to see if it appears

## Troubleshooting

- **"Invalid API key"**: Check that you copied the correct anon key
- **"Row Level Security policy violation"**: Check your RLS policies in SQL Editor
- **"Table doesn't exist"**: Make sure you ran the SQL schema creation
- **CORS errors**: Supabase handles CORS automatically, but check your project URL

## Next Steps

- Consider adding user authentication for personal recipe collections
- Set up backups in Supabase dashboard
- Monitor usage in Supabase dashboard → **Settings** → **Usage**
