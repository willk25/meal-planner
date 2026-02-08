#!/usr/bin/env python3
"""
Vercel serverless function to add a recipe to Supabase.
POST /api/add-recipe
"""

import json
import sys
import traceback
from pathlib import Path

# Add parent directory to path to import upload_recipe
sys.path.insert(0, str(Path(__file__).parent.parent))

# Initialize log path for debugging
log_path = Path(__file__).parent.parent / '.cursor' / 'debug.log'

from upload_recipe import add_recipe


def handler(event):
    """Vercel serverless function handler."""
    # #region agent log
    import json as json_module
    try:
        with open(log_path, 'a') as f:
            f.write(json_module.dumps({'location':'api/add-recipe.py:17','message':'Handler called','data':{'eventKeys':list(event.keys()) if isinstance(event,dict) else 'not_dict','httpMethod':event.get('httpMethod') if isinstance(event,dict) else None},'timestamp':int(__import__('time').time()*1000),'runId':'run1','hypothesisId':'D'})+'\n')
    except: pass
    # #endregion
    
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
        # #region agent log
        try:
            with open(log_path, 'a') as f:
                f.write(json_module.dumps({'location':'api/add-recipe.py:48','message':'About to parse request body','data':{'bodyType':type(event.get('body')).__name__,'bodyPreview':str(event.get('body'))[:100] if event.get('body') else None},'timestamp':int(__import__('time').time()*1000),'runId':'run1','hypothesisId':'B'})+'\n')
        except: pass
        # #endregion
        
        # Parse request body
        request_body = event.get('body', '{}')
        if isinstance(request_body, str):
            body = json.loads(request_body)
        else:
            body = request_body
        
        # #region agent log
        try:
            with open(log_path, 'a') as f:
                f.write(json_module.dumps({'location':'api/add-recipe.py:54','message':'Request body parsed','data':{'bodyKeys':list(body.keys()) if isinstance(body,dict) else 'not_dict'},'timestamp':int(__import__('time').time()*1000),'runId':'run1','hypothesisId':'B'})+'\n')
        except: pass
        # #endregion
        
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
        
        # #region agent log
        try:
            with open(log_path, 'a') as f:
                f.write(json_module.dumps({'location':'api/add-recipe.py:70','message':'About to call add_recipe','data':{'recipeTitle':body.get('title')},'timestamp':int(__import__('time').time()*1000),'runId':'run1','hypothesisId':'B'})+'\n')
        except: pass
        # #endregion
        
        # Add recipe using existing function (saves to Supabase via db_layer)
        success, message = add_recipe(body)
        
        # #region agent log
        try:
            with open(log_path, 'a') as f:
                f.write(json_module.dumps({'location':'api/add-recipe.py:72','message':'add_recipe returned','data':{'success':success,'message':message},'timestamp':int(__import__('time').time()*1000),'runId':'run1','hypothesisId':'B'})+'\n')
        except: pass
        # #endregion
        
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
        # #region agent log
        try:
            with open(log_path, 'a') as f:
                f.write(json_module.dumps({'location':'api/add-recipe.py:110','message':'Exception caught in handler','data':{'errorType':type(e).__name__,'errorMessage':str(e),'errorTraceback':__import__('traceback').format_exc()[:500]},'timestamp':int(__import__('time').time()*1000),'runId':'run1','hypothesisId':'B'})+'\n')
        except: pass
        # #endregion
        
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


# Export handler for Vercel
__vercel_handler__ = handler
