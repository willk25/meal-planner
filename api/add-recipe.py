#!/usr/bin/env python3
"""
Vercel serverless function to add a recipe to Supabase.
POST /api/add-recipe
"""

import json
import sys
from pathlib import Path

# Add parent directory to path to import upload_recipe
sys.path.insert(0, str(Path(__file__).parent.parent))

from upload_recipe import add_recipe


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
        
        # Validate recipe data
        if not body or not isinstance(body, dict):
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*',
                },
                'body': json.dumps({
                    'success': False,
                    'message': 'Invalid request body. Expected JSON object.'
                })
            }
        
        # Add recipe using existing function (saves to Supabase via db_layer)
        success, message = add_recipe(body)
        
        if success:
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*',
                },
                'body': json.dumps({
                    'success': True,
                    'message': message
                })
            }
        else:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*',
                },
                'body': json.dumps({
                    'success': False,
                    'message': message
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
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
            },
            'body': json.dumps({
                'success': False,
                'message': f'Error: {str(e)}'
            })
        }
