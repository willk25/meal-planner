#!/usr/bin/env python3
"""
Vercel serverless function to load recipes from Supabase.
GET /api/load_recipes
"""

import json
import os
import sys
from pathlib import Path
from http.server import BaseHTTPRequestHandler

# Add api directory to path for imports (same pattern as other API files)
api_dir = Path(__file__).parent
if str(api_dir) not in sys.path:
    sys.path.insert(0, str(api_dir))

# Dummy import to ensure Vercel bundles db_layer.py (wrapped to not crash if it fails)
try:
    import db_layer  # noqa: F401
except ImportError:
    pass  # Will use importlib.util at runtime instead


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
            # Import db_layer using importlib (more reliable in Vercel)
            try:
                import importlib.util
                db_layer_path = api_dir / 'db_layer.py'
                if not db_layer_path.exists():
                    raise ImportError(f"db_layer.py not found at {db_layer_path}")
                
                spec = importlib.util.spec_from_file_location("db_layer", db_layer_path)
                if spec is None or spec.loader is None:
                    raise ImportError(f"Failed to create spec for db_layer at {db_layer_path}")
                
                db_layer = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(db_layer)
                load_recipes = db_layer.load_recipes
            except Exception as import_err:
                import traceback
                error_trace = traceback.format_exc()
                print(f"ERROR: Failed to import db_layer: {error_trace}")
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({
                    'success': False,
                    'message': f'Import error: {str(import_err)}',
                    'recipes': []
                }).encode('utf-8'))
                return
            
            # Load recipes from database
            recipes = load_recipes()
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(recipes).encode('utf-8'))
            
        except Exception as e:
            import traceback
            error_trace = traceback.format_exc()
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
