#!/usr/bin/env python3
"""
Vercel serverless function to load recipes from Supabase.
GET /api/load_recipes
"""

import json
import os
from http.server import BaseHTTPRequestHandler

# Use normal Python import - Vercel will bundle db_layer.py automatically
from db_layer import load_recipes

# #region agent log
print(f"DEBUG [load_recipes]: Module loaded - has load_recipes={hasattr(load_recipes, '__call__')}")
# #endregion


class handler(BaseHTTPRequestHandler):
    """Vercel serverless function handler."""
    
    def do_OPTIONS(self):
        """Handle CORS preflight."""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def do_GET(self):
        """Handle GET request to load recipes."""
        try:
            # #region agent log
            print(f"DEBUG [load_recipes]: do_GET called")
            # #endregion
            
            # Log environment status for debugging
            use_supabase = os.getenv('USE_SUPABASE', 'false').lower() == 'true'
            has_url = bool(os.getenv('SUPABASE_URL', ''))
            has_key = bool(os.getenv('SUPABASE_KEY', ''))
            
            # #region agent log
            print(f"DEBUG [load_recipes]: Environment check - USE_SUPABASE={use_supabase}, has_url={has_url}, has_key={has_key}")
            # #endregion
            
            # Load recipes from database
            recipes = load_recipes()
            
            # #region agent log
            print(f"DEBUG [load_recipes]: load_recipes() returned {len(recipes)} recipes")
            # #endregion
            
            # Log for debugging (will appear in Vercel function logs)
            print(f"DEBUG: USE_SUPABASE={use_supabase}, has_url={has_url}, has_key={has_key}")
            print(f"DEBUG: Loaded {len(recipes)} recipes")
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(recipes).encode('utf-8'))
            
        except Exception as e:
            import traceback
            error_trace = traceback.format_exc()
            # #region agent log
            print(f"DEBUG [load_recipes]: Exception in do_GET - {str(e)}")
            print(f"DEBUG [load_recipes]: Traceback - {error_trace}")
            # #endregion
            print(f"ERROR in load_recipes: {error_trace}")
            
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({
                'success': False,
                'message': f'Error loading recipes: {str(e)}',
                'recipes': []
            }).encode('utf-8'))
