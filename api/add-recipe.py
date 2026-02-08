#!/usr/bin/env python3
"""
Vercel serverless function to add a recipe to Supabase.
POST /api/add-recipe
"""

import json
import sys
from http.server import BaseHTTPRequestHandler
from pathlib import Path

# Add parent directory to path to import upload_recipe
sys.path.insert(0, str(Path(__file__).parent.parent))

from upload_recipe import add_recipe


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
            
            # Add recipe using existing function (saves to Supabase via db_layer)
            success, message = add_recipe(recipe_data)
            
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
