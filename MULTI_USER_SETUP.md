# Multi-User Authentication Setup Guide

This guide explains how to enable username-based, passwordless auth so favorites can sync across devices. Recipes remain public/shared.

## Current State

- All recipes are shared (no user filtering)
- Shortlist and pantry stay local (browser storage)
- Favorites are wired to Supabase but require a username to save/sync
- Preview mode works without sign-in

## When You're Ready to Enable

### Step 1: Enable Supabase Authentication

1. Go to Supabase Dashboard → **Authentication** → **Providers**
2. Enable **Anonymous** provider (no password required)
3. (Optional) Keep Email provider enabled if you want future upgrades

### Step 2: Run Database Migration

1. Go to **SQL Editor** in Supabase
2. Run the SQL in `multi_user_setup.sql`
3. This will:
   - Create `profiles` table
   - Add `user_id` column to `recipes` table
   - Create indexes
   - Enable Row Level Security (RLS)
   - Create RLS policies

### Step 3: Verify Environment Variables

Ensure these are set (locally or in Vercel):
- `USE_SUPABASE=true`
- `SUPABASE_URL=...`
- `SUPABASE_KEY=...` (anon key)

No additional code changes are required for the username + favorites flow.

### Step 4: Test

1. Open `meal_planner.html`
2. Click **Set Username** and choose a username
3. Add a few favorites and refresh the page
4. Verify favorites persist and the favorites count matches
5. Test with a different browser/device to confirm sync

Recipes should still load publicly without sign-in.

## Optional: User-Specific Recipes (Not Enabled)

This project keeps recipes public by design. If you want to make recipes private per user, you can enable the commented-out multi-user functions in `db_layer.py` and update `upload_recipe.py` to use `load_user_recipes()` and `add_user_recipe()`. See the old instructions in version control or reach out if you want this path.

## Migration: Moving Existing Recipes to User Accounts

If you have existing recipes in the database and want to assign them to users:

```sql
-- Assign all existing recipes to a specific user (replace USER_ID_HERE)
UPDATE recipes 
SET user_id = 'USER_ID_HERE' 
WHERE user_id IS NULL;
```

Or create a migration script:

```python
# migrate_recipes_to_user.py
from db_layer import load_recipes, save_recipes, get_current_user_id

# Sign in first, then:
user_id = get_current_user_id()
if not user_id:
    print("Please sign in first")
    exit()

# Load all recipes
recipes = load_recipes()

# Assign to current user
for recipe in recipes:
    recipe['user_id'] = user_id

# Save back (this will update with user_id)
save_recipes(recipes)
print(f"✅ Migrated {len(recipes)} recipes to user {user_id}")
```

## Architecture

### Data Flow

```
User Chooses Username
    ↓
Supabase Anonymous Auth creates a session
    ↓
profiles row is created/updated
    ↓
Favorites are stored in `favorites` with `user_id`
    ↓
RLS policies enforce data isolation for favorites/profiles
```

### Row Level Security (RLS)

RLS policies ensure:
- Recipes are public (anyone can SELECT)
- Users can only SELECT/INSERT/DELETE their own favorites
- Users can only SELECT/INSERT/UPDATE their own profiles

### Preview Mode

If a user skips the username prompt, the planner still works. Favorites will be disabled until they set a username.

## Troubleshooting

### "User not authenticated" error
- Make sure Anonymous Auth is enabled in Supabase
- Verify `SUPABASE_URL` and `SUPABASE_KEY` are correct

### Favorites not showing up
- Ensure `multi_user_setup.sql` has been run
- Verify RLS policies were created
- Check that the username was saved successfully

### RLS blocking queries
- Verify RLS policies are created correctly
- Check that `auth.uid()` matches `favorites.user_id`
- Test with Supabase dashboard to see if policies work

## Files Modified

- `meal_planner.html` - Username modal + Supabase favorites
- `api/db_layer.py` - Includes `id` in recipe payload
- `multi_user_setup.sql` - SQL migration

## Next Steps After Enabling

1. Add optional profile display (avatar, display name)
2. Consider recipe sharing features
3. Add admin role for managing all recipes
