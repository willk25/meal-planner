#!/usr/bin/env python3
"""
Vercel serverless function to parse text recipe.
POST /api/parse-recipe-text
Uses parse_text_recipe() from api_helpers (keep existing logic unchanged).
"""

import json
import sys
from pathlib import Path
from http.server import BaseHTTPRequestHandler

# Add api directory to path for imports
api_dir = Path(__file__).parent
if str(api_dir) not in sys.path:
    sys.path.insert(0, str(api_dir))

from api_helpers import parse_text_recipe, enrich_recipe


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
        """Handle POST request to parse text recipe."""
        try:
            # Read request body
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length).decode('utf-8')
            
            # Parse JSON body
            try:
                data = json.loads(body)
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
            
            text = data.get('text', '').strip()
            
            if not text:
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({
                    'success': False,
                    'message': 'Text is required.'
                }).encode('utf-8'))
                return
            
            # Parse text recipe (keep existing logic unchanged)
            recipe = parse_text_recipe(text)
            
            # Enrich recipe with auto-detected metadata
            recipe = enrich_recipe(recipe)
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({
                'success': True,
                'recipe': recipe
            }).encode('utf-8'))
            
        except Exception as e:
            self.send_response(400)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({
                'success': False,
                'message': f'Failed to parse recipe: {str(e)}'
            }).encode('utf-8'))
