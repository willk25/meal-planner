-- Verify all columns exist in recipes table
-- Run this to check what columns are actually in your table

SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_schema = 'public' 
  AND table_name = 'recipes'
ORDER BY ordinal_position;
