#!/usr/bin/env python3
"""
Vercel serverless function to load recipes from Supabase.
GET /api/load-recipes
"""

import json
import sys
import os
from pathlib import Path
from http.server import BaseHTTPRequestHandler

# Add api directory to path for imports (Vercel-specific path handling)
api_dir = Path(__file__).parent.absolute()
if str(api_dir) not in sys.path:
    sys.path.insert(0, str(api_dir))

# Also try adding parent directory in case Vercel structures it differently
parent_dir = api_dir.parent.absolute()
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

# Try importing - handle both possible locations
try:
    from api.db_layer import load_recipes
except ImportError:
    try:
        from db_layer import load_recipes
    except ImportError:
        # Last resort: import directly
        import importlib.util
        db_layer_path = api_dir / 'db_layer.py'
        if db_layer_path.exists():
            spec = importlib.util.spec_from_file_location("db_layer", db_layer_path)
            db_layer = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(db_layer)
            load_recipes = db_layer.load_recipes
        else:
            raise ImportError("Could not find db_layer.py")


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
