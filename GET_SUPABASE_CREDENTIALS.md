# How to Get Your Supabase Credentials

## Step 1: Go to Supabase Dashboard

1. Go to https://supabase.com
2. Log in
3. Click on your project (the one you created for Meal Planner)

## Step 2: Find API Settings

1. Look for **Settings** icon (⚙️ gear icon) in the left sidebar
2. Click **Settings**
3. Click **API** (in the Settings submenu)

## Step 3: Copy Your Credentials

You'll see two things you need:

### 1. Project URL
- Look for **Project URL** section
- Copy the URL (looks like: `https://xxxxxxxxxxxxx.supabase.co`)
- This is your `SUPABASE_URL`

### 2. API Keys
- Look for **Project API keys** section
- Find the **anon public** key (NOT the service_role key!)
- It's a long string starting with `eyJ...`
- Copy this entire key
- This is your `SUPABASE_KEY`

## What You'll See

```
Project URL
https://xxxxxxxxxxxxx.supabase.co

Project API keys
┌─────────────────────────────────────────────────────────┐
│ anon public                                             │
│ eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9... (long string) │
│ [Copy]                                                  │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│ service_role (secret)                                   │
│ (Don't use this one!)                                   │
└─────────────────────────────────────────────────────────┘
```

## Important Notes

- Use the **anon public** key, NOT the service_role key
- The anon key is safe to use in frontend/Vercel
- The service_role key should NEVER be exposed

## Next Step

Once you have these two values:
1. Go to **Vercel** (not Supabase!)
2. Set them as environment variables (see VERCEL_ENV_SETUP.md)
