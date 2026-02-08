# How to Set Vercel Environment Variables

## Step-by-Step Guide

### 1. Go to Your Vercel Project

1. Go to https://vercel.com and log in
2. Click on your project (Meal Planner)
3. You should see your project dashboard

### 2. Navigate to Environment Variables

**Option A: From Project Settings**
1. Click on **Settings** (top navigation bar)
2. Click on **Environment Variables** (left sidebar)

**Option B: From Project Overview**
1. In your project dashboard, look for **Settings** in the top menu
2. Click **Settings** → **Environment Variables**

### 3. Add Environment Variables

Click the **Add New** button (or **Add** button) and add these three variables:

#### Variable 1: USE_SUPABASE
- **Key**: `USE_SUPABASE`
- **Value**: `true`
- **Environment**: Select all three: ☑ Production, ☑ Preview, ☑ Development
- Click **Save**

#### Variable 2: SUPABASE_URL
- **Key**: `SUPABASE_URL`
- **Value**: `https://your-project-id.supabase.co` (your actual Supabase URL)
- **Environment**: Select all three: ☑ Production, ☑ Preview, ☑ Development
- Click **Save**

#### Variable 3: SUPABASE_KEY
- **Key**: `SUPABASE_KEY`
- **Value**: Your Supabase anon/public key (starts with `eyJ...`)
- **Environment**: Select all three: ☑ Production, ☑ Preview, ☑ Development
- Click **Save**

### 4. Get Your Supabase Credentials

If you don't have them:

1. Go to https://supabase.com and log in
2. Select your project
3. Go to **Settings** (gear icon) → **API**
4. Copy:
   - **Project URL** → This is your `SUPABASE_URL`
   - **anon public** key → This is your `SUPABASE_KEY` (NOT the service_role key!)

### 5. Verify Variables Are Set

After adding all three, you should see them listed:
- `USE_SUPABASE`
- `SUPABASE_URL`
- `SUPABASE_KEY`

### 6. Redeploy

**Important**: Environment variables only take effect after redeploying!

1. Go to **Deployments** tab
2. Click the three dots (⋯) on your latest deployment
3. Click **Redeploy**
4. Or push a new commit to trigger automatic redeploy

### 7. Verify It Worked

After redeploy:
1. Go to **Deployments** → Latest deployment
2. Click **Functions** tab
3. Click on `/api/load-recipes`
4. Check the logs - you should see DEBUG messages showing the variables are set

## Troubleshooting

### Can't Find Settings?
- Make sure you're logged into Vercel
- Make sure you're in the correct project
- Try: https://vercel.com/dashboard → Select your project → Settings

### Variables Not Showing?
- Make sure you clicked "Save" after adding each variable
- Refresh the page
- Check you're looking at the right project

### Still Not Working?
- Make sure you selected all three environments (Production, Preview, Development)
- Make sure values are exactly: `USE_SUPABASE=true` (lowercase "true")
- Redeploy after adding variables
