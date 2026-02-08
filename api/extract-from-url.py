#!/usr/bin/env python3
"""
Vercel serverless function to extract recipe from URL.
POST /api/extract-from-url
Uses recipe-scrapers library (keep existing logic unchanged).
"""

import json
import sys
from http.server import BaseHTTPRequestHandler
from pathlib import Path

# Add parent directory to path to import upload_recipe
sys.path.insert(0, str(Path(__file__).parent.parent))

from upload_recipe import enrich_recipe

# Import recipe-scrapers (keep existing logic unchanged)
try:
    from recipe_scrapers import scrape_me
except ImportError:
    scrape_me = None


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
            
            # Check if recipe-scrapers is available
            if scrape_me is None:
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({
                    'success': False,
                    'message': 'Recipe scrapers library not available.'
                }).encode('utf-8'))
                return
            
            # Extract recipe from URL (keep existing logic unchanged)
            scraper = scrape_me(url)
            
            # Build recipe dictionary from scraped data
            recipe = {
                'title': scraper.title() if scraper.title() else '',
                'ingredients': scraper.ingredients() if scraper.ingredients() else [],
                'directions': scraper.instructions_list() if scraper.instructions_list() else [],
            }
            
            # Add optional fields if available
            if scraper.total_time():
                recipe['total_time'] = scraper.total_time()
            if scraper.yields():
                recipe['yields'] = scraper.yields()
            if scraper.image():
                recipe['image'] = scraper.image()
            
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
