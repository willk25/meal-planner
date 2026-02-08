# Multi-User Authentication Setup Guide

This guide explains how to enable user authentication and personal recipe collections when you're ready.

## Current State

- All recipes are shared (no user filtering)
- No authentication required
- Works with anonymous/public access
- All code for multi-user is commented out

## When You're Ready to Enable

### Step 1: Enable Supabase Authentication

1. Go to Supabase Dashboard → **Authentication** → **Settings**
2. Enable **Email** provider
3. Configure email templates (optional):
   - Confirmation email
   - Password reset email
   - Magic link email (if using)

### Step 2: Run Database Migration

1. Go to **SQL Editor** in Supabase
2. Uncomment and run the SQL from `SUPABASE_SETUP.md` (Step 3b)
3. This will:
   - Create `profiles` table
   - Add `user_id` column to `recipes` table
   - Create indexes
   - Enable Row Level Security (RLS)
   - Create RLS policies

### Step 3: Update Code

#### 3a. Uncomment Functions in `db_layer.py`

1. Find the multi-user section at the bottom of `db_layer.py`
2. Remove the triple quotes `"""` that wrap the functions
3. The functions will now be active:
   - `get_current_user_id()`
   - `load_user_recipes()`
   - `add_user_recipe()`
   - `sign_up()`
   - `sign_in()`
   - `sign_out()`
   - `get_current_user()`

#### 3b. Update `upload_recipe.py`

In `add_recipe()` function, change:
```python
# OLD (shared recipes):
return db_add_recipe(recipe)

# NEW (user-specific):
from db_layer import get_current_user_id, add_user_recipe
user_id = get_current_user_id()
if not user_id:
    return (False, "Please sign in to add recipes")
return add_user_recipe(recipe, user_id)
```

In `load_existing_recipes()` function, change:
```python
# OLD (all recipes):
return load_recipes()

# NEW (user-specific):
from db_layer import get_current_user_id, load_user_recipes
user_id = get_current_user_id()
if user_id:
    return load_user_recipes(user_id)
else:
    return []  # Or return all recipes if you want anonymous access
```

#### 3c. Update `meal_planner.html`

Add authentication UI (see commented section in the file for examples):
- Login/signup form
- User profile display
- "My Recipes" vs "All Recipes" toggle
- Sign out button

#### 3d. Create `auth_service.py` (Optional)

For Flask server authentication, create a new file with:
- Supabase auth client initialization
- Session management
- Token refresh logic
- Protected route decorators

### Step 4: Test

1. Create a test user account via sign up
2. Add a recipe - verify it's associated with your user
3. Sign out and sign in as different user
4. Verify you only see your own recipes
5. Test that RLS policies prevent cross-user access

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
User Signs In
    ↓
Supabase Auth creates session
    ↓
get_current_user_id() gets user UUID
    ↓
All recipe queries filter by user_id
    ↓
RLS policies enforce data isolation
```

### Row Level Security (RLS)

RLS policies ensure:
- Users can only SELECT their own recipes
- Users can only INSERT recipes with their own user_id
- Users can only UPDATE their own recipes
- Users can only DELETE their own recipes

### Anonymous Access

If you want to allow anonymous users to view recipes but not add them:

```python
# In load_existing_recipes():
user_id = get_current_user_id()
if user_id:
    return load_user_recipes(user_id)  # User's recipes
else:
    return load_recipes()  # All recipes (read-only for anonymous)
```

## Troubleshooting

### "User not authenticated" error
- Make sure user is signed in
- Check that `get_current_user_id()` returns a valid UUID
- Verify Supabase auth session is active

### Recipes not showing up
- Check that recipes have `user_id` set
- Verify RLS policies are enabled
- Check that you're signed in as the correct user

### RLS blocking queries
- Verify RLS policies are created correctly
- Check that `auth.uid()` matches the `user_id` in recipes
- Test with Supabase dashboard to see if policies work

## Files Modified

- `db_layer.py` - Multi-user functions (commented)
- `upload_recipe.py` - Will need updates when enabled
- `meal_planner.html` - Will need auth UI when enabled
- `SUPABASE_SETUP.md` - SQL migration (commented)

## Next Steps After Enabling

1. Add login/signup UI to meal planner
2. Add user profile management
3. Consider recipe sharing features
4. Add admin role for managing all recipes
5. Add recipe favorites/bookmarks per user
