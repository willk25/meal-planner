#!/usr/bin/env python3
"""
Vercel serverless function to extract recipe from URL.
POST /api/extract-from-url
Uses recipe-scrapers library (keep existing logic unchanged).
"""

import json
import sys
from pathlib import Path
from http.server import BaseHTTPRequestHandler

# Add api directory to path for imports
api_dir = Path(__file__).parent
if str(api_dir) not in sys.path:
    sys.path.insert(0, str(api_dir))

from api_helpers import enrich_recipe

# Use lightweight scraper instead of recipe-scrapers
try:
    from recipe_scraper import scrape_recipe
    SCRAPING_AVAILABLE = True
except ImportError:
    SCRAPING_AVAILABLE = False


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
        """Handle POST request to extract recipe from URL."""
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
            
            url = data.get('url', '').strip()
            
            if not url:
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({
                    'success': False,
                    'message': 'URL is required.'
                }).encode('utf-8'))
                return
            
            # Check if scraping is available
            if not SCRAPING_AVAILABLE:
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({
                    'success': False,
                    'message': 'Recipe scraping library not available.'
                }).encode('utf-8'))
                return
            
            # Extract recipe from URL using lightweight scraper
            recipe = scrape_recipe(url)
            
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
            error_message = str(e)
            # Provide more helpful error messages
            if 'certificate' in error_message.lower() or 'ssl' in error_message.lower():
                error_message = 'Failed to extract recipe: SSL certificate error. Make sure the URL is a valid recipe page.'
            elif 'not found' in error_message.lower() or '404' in error_message:
                error_message = 'Failed to extract recipe: URL not found or recipe page not accessible.'
            else:
                error_message = f'Failed to extract recipe: {error_message}'
            
            self.send_response(400)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({
                'success': False,
                'message': error_message
            }).encode('utf-8'))
