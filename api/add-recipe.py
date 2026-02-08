#!/usr/bin/env python3
"""
Vercel serverless function to add a recipe to Supabase.
POST /api/add-recipe
"""

import json
import sys
from pathlib import Path
from http.server import BaseHTTPRequestHandler

# Add api directory to path for imports
api_dir = Path(__file__).parent
if str(api_dir) not in sys.path:
    sys.path.insert(0, str(api_dir))

from api_helpers import validate_recipe, enrich_recipe, add_recipe_to_db


class handler(BaseHTTPRequestHandler):
    """Vercel serverless function handler."""
    
    def do_OPTIONS(self):
        """Handle CORS preflight."""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def do_POST(self):
        """Handle POST request to add recipe."""
        try:
            # Read request body
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length).decode('utf-8')
            
            # Parse JSON body
            try:
                recipe_data = json.loads(body)
            except json.JSONDecodeError:
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({
                    'success': False,
                    'message': 'Invalid JSON in request body.'
                }).encode('utf-8'))
                return
            
            # Validate recipe data
            if not recipe_data or not isinstance(recipe_data, dict):
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({
                    'success': False,
                    'message': 'Invalid request body. Expected JSON object.'
                }).encode('utf-8'))
                return
            
            # Validate recipe
            is_valid, errors = validate_recipe(recipe_data)
            if not is_valid:
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({
                    'success': False,
                    'message': f"Validation failed: {', '.join(errors)}"
                }).encode('utf-8'))
                return
            
            # Enrich with auto-detected metadata
            recipe_data = enrich_recipe(recipe_data)
            
            # Add recipe to database
            success, message = add_recipe_to_db(recipe_data)
            
            if success:
                self.send_response(200)
            else:
                self.send_response(400)
            
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({
                'success': success,
                'message': message
            }).encode('utf-8'))
            
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({
                'success': False,
                'message': f'Error: {str(e)}'
            }).encode('utf-8'))
