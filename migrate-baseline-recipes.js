// Migration script to import curated_recipes.json into Supabase as baseline recipes
// 
// Prerequisites:
//   1. Run the updated supabase-complete-setup.sql in Supabase SQL Editor first
//   2. Install dependencies: npm install @supabase/supabase-js
//   3. Run with: node migrate-baseline-recipes.js
//
// This script will:
//   - Read curated_recipes.json
//   - Insert all recipes into Supabase with is_baseline = true and user_id = NULL
//   - Process in batches of 100 to avoid timeouts

const { createClient } = require('@supabase/supabase-js');
const fs = require('fs');

// Supabase configuration
const SUPABASE_URL = 'https://dtavyealoifnyqkanovx.supabase.co';
const SUPABASE_ANON_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImR0YXZ5ZWFsb2lmbnlxa2Fub3Z4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzAwODgyMDIsImV4cCI6MjA4NTY2NDIwMn0._jLnINmj8expMf90KKH0FTwBPba3P4RSrnJeo_KO9IQ';

// Initialize Supabase client
const supabase = createClient(SUPABASE_URL, SUPABASE_ANON_KEY);

async function migrateRecipes() {
  try {
    // Read curated_recipes.json
    console.log('📖 Reading curated_recipes.json...');
    const recipesData = JSON.parse(fs.readFileSync('curated_recipes.json', 'utf8'));
    console.log(`✅ Found ${recipesData.length} recipes to migrate`);

    // Transform recipes to Supabase format
    const supabaseRecipes = recipesData.map(recipe => ({
      user_id: null, // Baseline recipes have no user_id
      title: recipe.title,
      protein_source: recipe.protein_source || null,
      meal_type: recipe.meal_type || null,
      difficulty: recipe.difficulty || null,
      ingredients: recipe.ingredients || [],
      directions: recipe.directions || [],
      rating: recipe.rating ? parseFloat(recipe.rating) : null,
      protein: recipe.protein ? parseFloat(recipe.protein) : null,
      num_ingredients: recipe.num_ingredients || (recipe.ingredients ? recipe.ingredients.length : 0),
      num_steps: recipe.num_steps || (recipe.directions ? recipe.directions.length : 0),
      is_family_recipe: recipe.is_family_recipe || false,
      photo: recipe.photo || null,
      photos: recipe.photos || null,
      estimated_price: recipe.estimated_price ? parseFloat(recipe.estimated_price) : null,
      source: recipe.source || null,
      source_url: recipe.source_url || null,
      tags: recipe.tags || [],
      is_baseline: true, // Mark as baseline recipe
      date: recipe.date || new Date().toISOString()
    }));

    // Insert in batches of 100 to avoid timeout
    const batchSize = 100;
    let inserted = 0;
    let errors = 0;

    console.log('📤 Inserting recipes into Supabase...');
    
    for (let i = 0; i < supabaseRecipes.length; i += batchSize) {
      const batch = supabaseRecipes.slice(i, i + batchSize);
      
      const { data, error } = await supabase
        .from('recipes')
        .insert(batch)
        .select();

      if (error) {
        console.error(`❌ Error inserting batch ${Math.floor(i / batchSize) + 1}:`, error.message);
        errors += batch.length;
      } else {
        inserted += data.length;
        console.log(`✅ Inserted batch ${Math.floor(i / batchSize) + 1}: ${data.length} recipes (${inserted}/${supabaseRecipes.length} total)`);
      }
    }

    console.log('\n📊 Migration Summary:');
    console.log(`   ✅ Successfully inserted: ${inserted} recipes`);
    console.log(`   ❌ Errors: ${errors} recipes`);
    console.log(`   📦 Total processed: ${supabaseRecipes.length} recipes`);

    if (inserted > 0) {
      console.log('\n🎉 Migration complete! Baseline recipes are now in Supabase.');
    }

  } catch (error) {
    console.error('❌ Migration failed:', error);
    process.exit(1);
  }
}

// Run migration
migrateRecipes();
