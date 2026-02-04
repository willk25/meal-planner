#!/usr/bin/env python3
"""
Web server for recipe adder - allows testing recipe uploads via web interface
Run with: python recipe_adder_server.py
Then visit: http://localhost:5000
"""

from flask import Flask, render_template_string, request, jsonify
from pathlib import Path
import json
from upload_recipe import add_recipe, validate_recipe, enrich_recipe, load_existing_recipes

app = Flask(__name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Recipe Adder - Test Interface</title>
  <style>
    * {
      margin: 0;
      padding: 0;
      box-sizing: border-box;
    }

    body {
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      min-height: 100vh;
      padding: 2rem;
    }

    .container {
      max-width: 800px;
      margin: 0 auto;
      background: white;
      border-radius: 24px;
      padding: 3rem;
      box-shadow: 0 20px 60px rgba(0,0,0,0.3);
    }

    h1 {
      font-size: 2.5rem;
      color: #2d3748;
      margin-bottom: 0.5rem;
      font-weight: 800;
    }

    .subtitle {
      color: #718096;
      margin-bottom: 2rem;
      font-size: 1.1rem;
    }

    .form-group {
      margin-bottom: 1.5rem;
    }

    label {
      display: block;
      font-weight: 600;
      color: #2d3748;
      margin-bottom: 0.5rem;
      font-size: 0.95rem;
    }

    .required {
      color: #e53e3e;
    }

    input[type="text"],
    input[type="number"],
    textarea,
    select {
      width: 100%;
      padding: 0.75rem;
      border: 2px solid #e2e8f0;
      border-radius: 8px;
      font-size: 1rem;
      font-family: inherit;
      transition: border-color 0.2s;
    }

    input:focus,
    textarea:focus,
    select:focus {
      outline: none;
      border-color: #667eea;
    }

    textarea {
      resize: vertical;
      min-height: 100px;
    }

    .ingredients-input,
    .directions-input {
      font-family: 'Courier New', monospace;
      font-size: 0.9rem;
    }

    .help-text {
      font-size: 0.85rem;
      color: #718096;
      margin-top: 0.25rem;
    }

    .optional-section {
      background: #f7fafc;
      padding: 1.5rem;
      border-radius: 12px;
      margin-top: 1.5rem;
      border: 1px solid #e2e8f0;
    }

    .optional-section h3 {
      color: #4a5568;
      font-size: 1.1rem;
      margin-bottom: 1rem;
    }

    .row {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 1rem;
      gap: 1rem;
    }

    @media (max-width: 640px) {
      .row {
        grid-template-columns: 1fr;
      }
    }

    .btn {
      padding: 1rem 2rem;
      border: none;
      border-radius: 12px;
      font-size: 1rem;
      font-weight: 600;
      cursor: pointer;
      transition: all 0.2s;
      display: inline-flex;
      align-items: center;
      gap: 0.5rem;
    }

    .btn-primary {
      background: linear-gradient(135deg, #667eea, #764ba2);
      color: white;
    }

    .btn-primary:hover {
      transform: translateY(-2px);
      box-shadow: 0 8px 25px rgba(102, 126, 234, 0.3);
    }

    .btn-secondary {
      background: #e2e8f0;
      color: #4a5568;
    }

    .btn-secondary:hover {
      background: #cbd5e0;
    }

    .buttons {
      display: flex;
      gap: 1rem;
      margin-top: 2rem;
    }

    .message {
      padding: 1rem;
      border-radius: 8px;
      margin-bottom: 1.5rem;
      display: none;
    }

    .message.show {
      display: block;
    }

    .message.success {
      background: #c6f6d5;
      color: #22543d;
      border: 1px solid #9ae6b4;
    }

    .message.error {
      background: #fed7d7;
      color: #742a2a;
      border: 1px solid #fc8181;
    }

    .preview-section {
      background: #f7fafc;
      padding: 1.5rem;
      border-radius: 12px;
      margin-top: 1.5rem;
      border: 1px solid #e2e8f0;
      display: none;
    }

    .preview-section.show {
      display: block;
    }

    .preview-section h3 {
      color: #4a5568;
      margin-bottom: 1rem;
    }

    .preview-content {
      background: white;
      padding: 1rem;
      border-radius: 8px;
      font-family: 'Courier New', monospace;
      font-size: 0.85rem;
      white-space: pre-wrap;
      max-height: 400px;
      overflow-y: auto;
    }

    /* Tags styling */
    .tags-container {
      display: flex;
      flex-direction: column;
      gap: 1rem;
    }

    .tags-suggestions,
    .tags-selected {
      display: flex;
      flex-direction: column;
      gap: 0.5rem;
    }

    .tags-label {
      font-size: 0.85rem;
      font-weight: 600;
      color: #4a5568;
      margin-bottom: 0.25rem;
    }

    .tag-chips {
      display: flex;
      flex-wrap: wrap;
      gap: 0.5rem;
    }

    .tag-chip {
      padding: 0.5rem 1rem;
      border-radius: 20px;
      font-size: 0.85rem;
      cursor: pointer;
      transition: all 0.2s;
      display: inline-flex;
      align-items: center;
      gap: 0.5rem;
    }

    .tag-chip.suggestion {
      background: #e2e8f0;
      color: #4a5568;
      border: 1px solid #cbd5e0;
    }

    .tag-chip.suggestion:hover {
      background: #cbd5e0;
      border-color: #a0aec0;
    }

    .tag-chip.selected {
      background: linear-gradient(135deg, #667eea, #764ba2);
      color: white;
      border: 1px solid #667eea;
    }

    .tag-chip.selected:hover {
      background: linear-gradient(135deg, #5568d3, #6a3f91);
    }

    .tag-chip .remove {
      background: rgba(255, 255, 255, 0.3);
      border-radius: 50%;
      width: 18px;
      height: 18px;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 0.7rem;
      line-height: 1;
    }

    .tag-chip.selected .remove:hover {
      background: rgba(255, 255, 255, 0.5);
    }

    .tags-input-wrapper {
      display: flex;
      flex-direction: column;
      gap: 0.25rem;
    }

    .tags-selected {
      min-height: 40px;
      padding: 0.75rem;
      background: #f7fafc;
      border-radius: 8px;
      border: 1px solid #e2e8f0;
    }

    #selected-tags-list:empty::after {
      content: "No tags selected";
      color: #a0aec0;
      font-style: italic;
      font-size: 0.85rem;
    }
  </style>
</head>
<body>
  <div class="container">
    <h1>🍽️ Recipe Adder</h1>
    <p class="subtitle">Add new recipes to your meal planner</p>

    <div id="message" class="message"></div>

    <form id="recipe-form" method="POST" action="/api/add-recipe">
      <div class="form-group">
        <label for="title">Title <span class="required">*</span></label>
        <input type="text" id="title" name="title" required placeholder="e.g., Grilled Chicken with Vegetables">
      </div>

      <div class="form-group">
        <label for="ingredients">Ingredients <span class="required">*</span></label>
        <textarea 
          id="ingredients" 
          name="ingredients" 
          class="ingredients-input"
          required 
          placeholder="Enter one ingredient per line:&#10;1 cup flour&#10;2 eggs&#10;1/2 cup milk"
        ></textarea>
        <p class="help-text">Enter one ingredient per line. Include quantities (e.g., "1 cup flour", "2 tablespoons olive oil")</p>
      </div>

      <div class="form-group">
        <label for="directions">Directions <span class="required">*</span></label>
        <textarea 
          id="directions" 
          name="directions" 
          class="directions-input"
          required 
          placeholder="Enter one step per line:&#10;Preheat oven to 350°F&#10;Mix ingredients in a bowl&#10;Bake for 30 minutes"
        ></textarea>
        <p class="help-text">Enter one cooking step per line</p>
      </div>

      <div class="optional-section">
        <h3>Optional Fields (Auto-detected if not provided)</h3>
        
        <div class="row">
          <div class="form-group">
            <label for="protein_source">Protein Source</label>
            <select id="protein_source" name="protein_source">
              <option value="">Auto-detect</option>
              <option value="chicken">Chicken</option>
              <option value="beef">Beef</option>
              <option value="pork">Pork</option>
              <option value="seafood">Seafood</option>
              <option value="turkey">Turkey</option>
              <option value="lamb">Lamb</option>
              <option value="eggs">Eggs</option>
              <option value="other">Other</option>
            </select>
          </div>

          <div class="form-group">
            <label for="meal_type">Meal Type</label>
            <select id="meal_type" name="meal_type">
              <option value="">Auto-detect</option>
              <option value="entree">Entree</option>
              <option value="appetizer">Appetizer</option>
              <option value="dessert">Dessert</option>
              <option value="breakfast">Breakfast</option>
              <option value="soup">Soup</option>
              <option value="salad">Salad</option>
            </select>
          </div>
        </div>

        <div class="row">
          <div class="form-group">
            <label for="difficulty">Difficulty</label>
            <select id="difficulty" name="difficulty">
              <option value="">Auto-detect</option>
              <option value="easy">Easy</option>
              <option value="medium">Medium</option>
              <option value="involved">Involved</option>
            </select>
          </div>

          <div class="form-group">
            <label for="rating">Rating (0-5)</label>
            <input type="number" id="rating" name="rating" min="0" max="5" step="0.1" placeholder="e.g., 4.5">
          </div>
        </div>

        <div class="row">
          <div class="form-group">
            <label for="protein">Protein (grams)</label>
            <input type="number" id="protein" name="protein" min="0" step="0.1" placeholder="e.g., 35">
          </div>

          <div class="form-group">
            <label for="calories">Calories</label>
            <input type="number" id="calories" name="calories" min="0" placeholder="e.g., 450">
          </div>
        </div>

        <div class="form-group">
          <label for="desc">Description</label>
          <textarea id="desc" name="desc" placeholder="Optional recipe description"></textarea>
        </div>

        <div class="form-group">
          <label for="source">Source</label>
          <input type="text" id="source" name="source" placeholder="e.g., Bon Appétit, Family Recipe">
        </div>

        <div class="form-group">
          <label for="tags">Tags</label>
          <div class="tags-container">
            <div class="tags-suggestions">
              <span class="tags-label">Click to add:</span>
              <div class="tag-chips" id="tag-suggestions">
                <span class="tag-chip suggestion" data-tag="NYT Recipe">NYT Recipe</span>
                <span class="tag-chip suggestion" data-tag="Family Recipe">Family Recipe</span>
                <span class="tag-chip suggestion" data-tag="Barefoot Contessa">Barefoot Contessa</span>
              </div>
            </div>
            <div class="tags-input-wrapper">
              <input type="text" id="tag-input" placeholder="Type a new tag and press Enter">
              <p class="help-text">Type a tag and press Enter to add it, or click a suggestion above</p>
            </div>
            <div class="tags-selected" id="selected-tags">
              <span class="tags-label">Selected tags:</span>
              <div class="tag-chips" id="selected-tags-list"></div>
            </div>
          </div>
        </div>
      </div>

      <div class="buttons">
        <button type="button" class="btn btn-secondary" onclick="previewRecipe()">👁️ Preview</button>
        <button type="submit" class="btn btn-primary">✅ Add Recipe</button>
      </div>
    </form>

    <div id="preview-section" class="preview-section">
      <h3>Recipe Preview</h3>
      <div id="preview-content" class="preview-content"></div>
    </div>
  </div>

  <script>
    const form = document.getElementById('recipe-form');
    const messageEl = document.getElementById('message');
    let selectedTags = new Set();

    // Tag management
    function addTag(tag) {
      if (!tag || !tag.trim()) return;
      const trimmedTag = tag.trim();
      if (selectedTags.has(trimmedTag)) return;
      
      selectedTags.add(trimmedTag);
      renderSelectedTags();
      updateSuggestionChips();
    }

    function removeTag(tag) {
      selectedTags.delete(tag);
      renderSelectedTags();
      updateSuggestionChips();
    }

    function renderSelectedTags() {
      const container = document.getElementById('selected-tags-list');
      if (selectedTags.size === 0) {
        container.innerHTML = '';
        return;
      }
      
      container.innerHTML = Array.from(selectedTags).map(tag => {
        const escapedTag = tag.replace(/'/g, "\\'").replace(/"/g, '&quot;');
        return `<span class="tag-chip selected" data-tag="${escapedTag}">
          ${tag}
          <span class="remove" onclick="removeTag('${escapedTag}')">×</span>
        </span>`;
      }).join('');
    }

    function updateSuggestionChips() {
      document.querySelectorAll('#tag-suggestions .tag-chip').forEach(chip => {
        const tag = chip.getAttribute('data-tag');
        if (selectedTags.has(tag)) {
          chip.classList.remove('suggestion');
          chip.classList.add('selected');
          chip.style.pointerEvents = 'none';
          chip.style.opacity = '0.6';
        } else {
          chip.classList.remove('selected');
          chip.classList.add('suggestion');
          chip.style.pointerEvents = 'auto';
          chip.style.opacity = '1';
        }
      });
    }

    // Initialize tag event listeners
    document.addEventListener('DOMContentLoaded', () => {
      // Click suggestions to add tags
      document.querySelectorAll('#tag-suggestions .tag-chip').forEach(chip => {
        chip.addEventListener('click', () => {
          const tag = chip.getAttribute('data-tag');
          if (!selectedTags.has(tag)) {
            addTag(tag);
          }
        });
      });

      // Enter key to add new tag
      const tagInput = document.getElementById('tag-input');
      tagInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
          e.preventDefault();
          const tag = tagInput.value.trim();
          if (tag) {
            addTag(tag);
            tagInput.value = '';
          }
        }
      });

      // Reset tags when form is reset
      form.addEventListener('reset', () => {
        selectedTags.clear();
        renderSelectedTags();
        updateSuggestionChips();
      });
    });

    window.addTag = addTag;
    window.removeTag = removeTag;

    function showMessage(text, isError = false) {
      messageEl.textContent = text;
      messageEl.className = 'message show ' + (isError ? 'error' : 'success');
      setTimeout(() => {
        messageEl.classList.remove('show');
      }, 5000);
    }

    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      
      const formData = new FormData(form);
      const data = {
        title: formData.get('title'),
        ingredients: formData.get('ingredients').split('\\n').filter(i => i.trim()),
        directions: formData.get('directions').split('\\n').filter(d => d.trim()),
        protein_source: formData.get('protein_source') || undefined,
        meal_type: formData.get('meal_type') || undefined,
        difficulty: formData.get('difficulty') || undefined,
        rating: formData.get('rating') ? parseFloat(formData.get('rating')) : undefined,
        protein: formData.get('protein') ? parseFloat(formData.get('protein')) : undefined,
        calories: formData.get('calories') ? parseFloat(formData.get('calories')) : undefined,
        desc: formData.get('desc') || undefined,
        source: formData.get('source') || undefined,
        categories: Array.from(selectedTags).length > 0 ? Array.from(selectedTags) : undefined,
      };

      try {
        const response = await fetch('/api/add-recipe', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(data),
        });

        const result = await response.json();
        
        if (result.success) {
          showMessage(result.message, false);
          form.reset();
          selectedTags.clear();
          renderSelectedTags();
          updateSuggestionChips();
          document.getElementById('preview-section').classList.remove('show');
        } else {
          showMessage(result.message, true);
        }
      } catch (error) {
        showMessage('Error: ' + error.message, true);
      }
    });

    function previewRecipe() {
      const formData = new FormData(form);
      const data = {
        title: formData.get('title'),
        ingredients: formData.get('ingredients').split('\\n').filter(i => i.trim()),
        directions: formData.get('directions').split('\\n').filter(d => d.trim()),
        protein_source: formData.get('protein_source') || undefined,
        meal_type: formData.get('meal_type') || undefined,
        difficulty: formData.get('difficulty') || undefined,
        rating: formData.get('rating') ? parseFloat(formData.get('rating')) : undefined,
        protein: formData.get('protein') ? parseFloat(formData.get('protein')) : undefined,
        calories: formData.get('calories') ? parseFloat(formData.get('calories')) : undefined,
        desc: formData.get('desc') || undefined,
        source: formData.get('source') || undefined,
        categories: Array.from(selectedTags).length > 0 ? Array.from(selectedTags) : undefined,
      };

      fetch('/api/preview-recipe', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
      })
      .then(response => response.json())
      .then(result => {
        if (result.success) {
          document.getElementById('preview-content').textContent = JSON.stringify(result.recipe, null, 2);
          document.getElementById('preview-section').classList.add('show');
        } else {
          showMessage(result.message, true);
        }
      })
      .catch(error => {
        showMessage('Error: ' + error.message, true);
      });
    }

    window.previewRecipe = previewRecipe;
  </script>
</body>
</html>
"""

@app.route('/')
def index():
    """Serve the recipe adder form"""
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/preview-recipe', methods=['POST'])
def preview_recipe():
    """Preview a recipe without saving it"""
    try:
        data = request.json
        
        # Convert ingredients and directions to lists if they're strings
        recipe = {
            'title': data.get('title', '').strip(),
            'ingredients': data.get('ingredients', []),
            'directions': data.get('directions', []),
        }
        
        # Add optional fields
        if data.get('protein_source'):
            recipe['protein_source'] = data['protein_source']
        if data.get('meal_type'):
            recipe['meal_type'] = data['meal_type']
        if data.get('difficulty'):
            recipe['difficulty'] = data['difficulty']
        if data.get('rating') is not None:
            recipe['rating'] = data['rating']
        if data.get('protein') is not None:
            recipe['protein'] = data['protein']
        if data.get('calories') is not None:
            recipe['calories'] = data['calories']
        if data.get('desc'):
            recipe['desc'] = data['desc']
        if data.get('source'):
            recipe['source'] = data['source']
        if data.get('categories'):
            recipe['categories'] = data['categories']
        
        # Validate
        is_valid, errors = validate_recipe(recipe)
        if not is_valid:
            return jsonify({
                'success': False,
                'message': f'Validation failed: {", ".join(errors)}'
            }), 400
        
        # Enrich with auto-detected metadata
        enriched_recipe = enrich_recipe(recipe)
        
        return jsonify({
            'success': True,
            'recipe': enriched_recipe
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500

@app.route('/api/add-recipe', methods=['POST'])
def add_recipe_api():
    """Add a recipe via API"""
    try:
        data = request.json
        
        # Convert ingredients and directions to lists if they're strings
        recipe = {
            'title': data.get('title', '').strip(),
            'ingredients': data.get('ingredients', []),
            'directions': data.get('directions', []),
        }
        
        # Add optional fields
        if data.get('protein_source'):
            recipe['protein_source'] = data['protein_source']
        if data.get('meal_type'):
            recipe['meal_type'] = data['meal_type']
        if data.get('difficulty'):
            recipe['difficulty'] = data['difficulty']
        if data.get('rating') is not None:
            recipe['rating'] = data['rating']
        if data.get('protein') is not None:
            recipe['protein'] = data['protein']
        if data.get('calories') is not None:
            recipe['calories'] = data['calories']
        if data.get('desc'):
            recipe['desc'] = data['desc']
        if data.get('source'):
            recipe['source'] = data['source']
        if data.get('categories'):
            recipe['categories'] = data['categories']
        
        # Use the upload_recipe function
        success, message = add_recipe(recipe)
        
        if success:
            return jsonify({
                'success': True,
                'message': message
            })
        else:
            return jsonify({
                'success': False,
                'message': message
            }), 400
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500

@app.route('/api/recipes', methods=['GET'])
def list_recipes():
    """List all recipes (for testing)"""
    try:
        recipes = load_existing_recipes()
        return jsonify({
            'success': True,
            'count': len(recipes),
            'recipes': recipes
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500

if __name__ == '__main__':
    print("=" * 60)
    print("🍽️  Recipe Adder Server")
    print("=" * 60)
    print("Starting server on http://localhost:5001")
    print("Press Ctrl+C to stop")
    print("=" * 60)
    app.run(debug=True, host='127.0.0.1', port=5001)
