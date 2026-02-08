# Debug: Recipes Not Loading from Supabase

## Quick Checklist

### 1. Verify Vercel Environment Variables

Go to your Vercel project dashboard:
1. **Settings** → **Environment Variables**
2. Make sure these are set for **Production**, **Preview**, AND **Development**:
   - `USE_SUPABASE` = `true` (exactly lowercase "true")
   - `SUPABASE_URL` = `https://your-project.supabase.co`
   - `SUPABASE_KEY` = `your-anon-key-here` (the anon/public key, NOT service_role)

### 2. Check Vercel Function Logs

1. Go to your Vercel project dashboard
2. Click on **Deployments** → Latest deployment
3. Click **Functions** tab
4. Click on `/api/load-recipes`
5. Check the logs - you should see DEBUG messages showing:
   - `USE_SUPABASE=true`
   - `supabase_client=True`
   - Number of recipes loaded

### 3. Test the API Endpoint Directly

Open your browser console and run:
```javascript
fetch('/api/load-recipes')
  .then(r => r.json())
  .then(data => {
    console.log('Recipes loaded:', data.length);
    console.log('First recipe:', data[0]);
  })
  .catch(err => console.error('Error:', err));
```

### 4. Common Issues

**Issue: Empty array returned**
- Check Vercel environment variables are set correctly
- Check Supabase dashboard to verify recipes exist
- Check Vercel function logs for errors

**Issue: "Supabase client not initialized"**
- `USE_SUPABASE` might not be set to `true`
- `SUPABASE_URL` or `SUPABASE_KEY` might be missing
- Check Vercel environment variables

**Issue: "No recipes found in Supabase"**
- Verify recipes exist in Supabase dashboard
- Check that you ran the migration script successfully
- Check Supabase table has data

### 5. Redeploy After Setting Environment Variables

After adding/updating environment variables:
1. Go to **Deployments**
2. Click the three dots on the latest deployment
3. Click **Redeploy**
4. Or push a new commit to trigger redeploy

### 6. Verify Recipes in Supabase

1. Go to Supabase dashboard
2. **Table Editor** → **recipes**
3. You should see your 1697 recipes
4. If empty, run the migration script again locally
