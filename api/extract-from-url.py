#!/usr/bin/env python3
"""
Vercel serverless function to extract recipe from URL.
POST /api/extract-from-url
Uses recipe-scrapers library (keep existing logic unchanged).
"""

import json
import sys
from pathlib import Path

# Add parent directory to path to import upload_recipe
sys.path.insert(0, str(Path(__file__).parent.parent))

from upload_recipe import enrich_recipe

# Import recipe-scrapers (keep existing logic unchanged)
try:
    from recipe_scrapers import scrape_me
except ImportError:
    scrape_me = None


def handler(request):
    """Vercel serverless function handler."""
    # Handle CORS preflight
    if request.method == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'POST, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type',
            },
            'body': ''
        }
    
    # Only allow POST
    if request.method != 'POST':
        return {
            'statusCode': 405,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
            },
            'body': json.dumps({
                'success': False,
                'message': 'Method not allowed. Use POST.'
            })
        }
    
    try:
        # Parse request body
        body = json.loads(request.body) if isinstance(request.body, str) else request.body
        url = body.get('url', '').strip()
        
        if not url:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*',
                },
                'body': json.dumps({
                    'success': False,
                    'message': 'URL is required.'
                })
            }
        
        # Check if recipe-scrapers is available
        if scrape_me is None:
            return {
                'statusCode': 500,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*',
                },
                'body': json.dumps({
                    'success': False,
                    'message': 'Recipe scrapers library not available.'
                })
            }
        
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
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
            },
            'body': json.dumps({
                'success': True,
                'recipe': recipe
            })
        }
        
    except Exception as e:
        error_message = str(e)
        # Provide more helpful error messages
        if 'certificate' in error_message.lower() or 'ssl' in error_message.lower():
            error_message = 'Failed to extract recipe: SSL certificate error. Make sure the URL is a valid recipe page.'
        elif 'not found' in error_message.lower() or '404' in error_message:
            error_message = 'Failed to extract recipe: URL not found or recipe page not accessible.'
        else:
            error_message = f'Failed to extract recipe: {error_message}'
        
        return {
            'statusCode': 400,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
            },
            'body': json.dumps({
                'success': False,
                'message': error_message
            })
        }
