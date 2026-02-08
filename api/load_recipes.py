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

# Import db_layer - now that api_dir is in sys.path
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
