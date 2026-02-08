#!/usr/bin/env python3
"""
Vercel serverless function to load recipes from Supabase.
GET /api/load-recipes
"""

import json
import sys
from pathlib import Path
from http.server import BaseHTTPRequestHandler

# Add api directory to path for imports
api_dir = Path(__file__).parent
if str(api_dir) not in sys.path:
    sys.path.insert(0, str(api_dir))

from db_layer import load_recipes


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
            import os
            # Log environment status for debugging
            use_supabase = os.getenv('USE_SUPABASE', 'false').lower() == 'true'
            has_url = bool(os.getenv('SUPABASE_URL', ''))
            has_key = bool(os.getenv('SUPABASE_KEY', ''))
            
            # Load recipes from database
            recipes = load_recipes()
            
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
            print(f"ERROR in load-recipes: {error_trace}")
            
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({
                'success': False,
                'message': f'Error loading recipes: {str(e)}',
                'recipes': []
            }).encode('utf-8'))
