# Vercel + Supabase Setup Guide

This guide will help you set up Supabase for your Vercel deployment so recipes load from the database instead of JSON files.

## Why This Setup?

1. **Multi-user ready**: Supabase supports user authentication and per-user recipes
2. **No large files**: Recipes stored in database, not bundled in deployment
3. **Scalable**: Database can handle thousands of recipes efficiently
4. **Real-time**: Can add real-time features later if needed

## Step 1: Set Up Supabase

Follow the instructions in `SUPABASE_SETUP.md` to:
1. Create a Supabase project
2. Create the `recipes` table
3. Get your API credentials (URL and anon key)

## Step 2: Migrate Existing Recipes

Once Supabase is set up locally, migrate your curated recipes:

```bash
# Make sure you have .env file with Supabase credentials
python3 migrate_to_supabase.py
```

This will upload all recipes from `curated_recipes.json` to Supabase.

## Step 3: Configure Vercel Environment Variables

1. Go to your Vercel project dashboard
2. Navigate to **Settings** → **Environment Variables**
3. Add these three variables:

```
USE_SUPABASE=true
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key-here
```

**Important**: 
- Use the `anon` key (public key), not the `service_role` key
- Make sure `USE_SUPABASE` is exactly `true` (lowercase)
- Apply to **Production**, **Preview**, and **Development** environments

## Step 4: Redeploy

After adding environment variables, trigger a new deployment:

```bash
git commit --allow-empty -m "Trigger redeploy with Supabase config"
git push
```

Or manually trigger a redeploy from the Vercel dashboard.

## Step 5: Verify It Works

1. Check your Vercel deployment logs - should not show Supabase errors
2. Visit your meal planner - recipes should load from Supabase
3. Try adding a new recipe - it should save to Supabase

## How It Works

### Local Development
- Uses `db_layer.py` (root) which has JSON fallback
- Can work with or without Supabase
- Reads from `curated_recipes.json` if Supabase not configured

### Vercel Deployment
- Uses `api/db_layer.py` which is Supabase-only (no JSON fallback)
- Recipes must be in Supabase
- Environment variables control Supabase connection

### API Endpoints
- `GET /api/load-recipes` - Loads all recipes from Supabase
- `POST /api/add-recipe` - Adds a recipe to Supabase
- `POST /api/extract-from-url` - Extracts recipe from URL, saves to Supabase
- `POST /api/parse-recipe-text` - Parses text recipe, saves to Supabase

## Multi-User Setup (Future)

When you're ready for multi-user support:

1. Enable Authentication in Supabase Dashboard
2. Add `user_id` column to recipes table (see `SUPABASE_SETUP.md`)
3. Update API functions to filter by `user_id`
4. Add authentication to your frontend

The infrastructure is already in place - you just need to enable it!

## Troubleshooting

### "No recipes showing"
- Check Vercel environment variables are set correctly
- Verify recipes were migrated to Supabase (check Supabase dashboard)
- Check Vercel function logs for errors

### "Database layer not available"
- This means `api/db_layer.py` can't import Supabase
- Check that `supabase>=2.0.0` is in `api/requirements.txt`
- Verify environment variables are set in Vercel

### "Supabase not configured"
- Check `USE_SUPABASE=true` in Vercel environment variables
- Verify `SUPABASE_URL` and `SUPABASE_KEY` are set
- Make sure you're using the `anon` key, not `service_role`

### Recipes not loading
- Check Supabase dashboard → Table Editor → recipes
- Verify recipes exist in the table
- Check browser console for API errors
- Check Vercel function logs

## The db_layer Issue Explained

**Root `db_layer.py`** (for local development):
- Has JSON fallback
- Can work without Supabase
- Used by local scripts like `upload_recipe.py`

**API `api/db_layer.py`** (for Vercel):
- Supabase only, no JSON fallback
- Returns empty list if Supabase not configured
- Keeps bundle size small (no large JSON files)

This is intentional - Vercel functions should use Supabase, not JSON files.
