#!/usr/bin/env python3
"""
Vercel serverless function to add a recipe to Supabase.
POST /api/add_recipe
"""

import json
from http.server import BaseHTTPRequestHandler

# Use normal Python imports - Vercel will bundle these automatically
from api_helpers import validate_recipe, enrich_recipe, add_recipe_to_db

# #region agent log
print(f"DEBUG [add_recipe]: Module loaded - imports successful")
# #endregion


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
            # #region agent log
            print(f"DEBUG [add_recipe]: do_POST called")
            # #endregion
            
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
            
            # #region agent log
            print(f"DEBUG [add_recipe]: Calling add_recipe_to_db")
            # #endregion
            
            # Add recipe to database
            success, message = add_recipe_to_db(recipe_data)
            
            # #region agent log
            print(f"DEBUG [add_recipe]: add_recipe_to_db returned - success={success}, message={message}")
            # #endregion
            
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
            import traceback
            error_trace = traceback.format_exc()
            # #region agent log
            print(f"DEBUG [add_recipe]: Exception in do_POST - {str(e)}")
            print(f"DEBUG [add_recipe]: Traceback - {error_trace}")
            # #endregion
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({
                'success': False,
                'message': f'Error: {str(e)}'
            }).encode('utf-8'))
