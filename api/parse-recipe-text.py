#!/usr/bin/env python3
"""
Vercel serverless function to parse text recipe.
POST /api/parse-recipe-text
Uses parse_text_recipe() from upload_recipe.py (keep existing logic unchanged).
"""

import json
import sys
from pathlib import Path

# Add parent directory to path to import upload_recipe
sys.path.insert(0, str(Path(__file__).parent.parent))

from upload_recipe import parse_text_recipe, enrich_recipe


def handler(event):
    """Vercel serverless function handler."""
    # Get HTTP method
    method = event.get('httpMethod', 'GET')
    
    # Handle CORS preflight
    if method == 'OPTIONS':
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
    if method != 'POST':
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
        request_body = event.get('body', '{}')
        if isinstance(request_body, str):
            body = json.loads(request_body)
        else:
            body = request_body
        text = body.get('text', '').strip()
        
        if not text:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*',
                },
                'body': json.dumps({
                    'success': False,
                    'message': 'Text is required.'
                })
            }
        
        # Parse text recipe (keep existing logic unchanged)
        recipe = parse_text_recipe(text)
        
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
        
    except json.JSONDecodeError:
        return {
            'statusCode': 400,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
            },
            'body': json.dumps({
                'success': False,
                'message': 'Invalid JSON in request body.'
            })
        }
    except Exception as e:
        return {
            'statusCode': 400,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
            },
            'body': json.dumps({
                'success': False,
                'message': f'Failed to parse recipe: {str(e)}'
            })
        }
