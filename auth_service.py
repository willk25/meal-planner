#!/usr/bin/env python3
"""
Authentication service for multi-user support (COMMENTED OUT - Enable when ready).

This file contains Flask routes and helpers for user authentication.
Uncomment when you're ready to enable multi-user features.

See MULTI_USER_SETUP.md for implementation guide.
"""

"""
from flask import Blueprint, request, jsonify, session
from functools import wraps
from db_layer import sign_up, sign_in, sign_out, get_current_user, get_current_user_id

auth_bp = Blueprint('auth', __name__)

# Authentication routes
@auth_bp.route('/api/auth/signup', methods=['POST'])
def api_signup():
    \"\"\"Sign up a new user.\"\"\"
    try:
        data = request.json
        email = data.get('email', '').strip()
        password = data.get('password', '')
        full_name = data.get('full_name', '').strip()
        
        if not email or not password:
            return jsonify({
                'success': False,
                'message': 'Email and password are required'
            }), 400
        
        success, message, user_id = sign_up(email, password, full_name)
        
        if success:
            # Store user in session
            session['user_id'] = user_id
            session['email'] = email
            
            return jsonify({
                'success': True,
                'message': message,
                'user': {
                    'id': user_id,
                    'email': email,
                    'full_name': full_name
                }
            })
        else:
            return jsonify({
                'success': False,
                'message': message
            }), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500

@auth_bp.route('/api/auth/signin', methods=['POST'])
def api_signin():
    \"\"\"Sign in a user.\"\"\"
    try:
        data = request.json
        email = data.get('email', '').strip()
        password = data.get('password', '')
        
        if not email or not password:
            return jsonify({
                'success': False,
                'message': 'Email and password are required'
            }), 400
        
        success, message, user_id = sign_in(email, password)
        
        if success:
            # Store user in session
            session['user_id'] = user_id
            session['email'] = email
            
            # Get full user profile
            user = get_current_user()
            
            return jsonify({
                'success': True,
                'message': message,
                'user': user or {
                    'id': user_id,
                    'email': email
                }
            })
        else:
            return jsonify({
                'success': False,
                'message': message
            }), 401
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500

@auth_bp.route('/api/auth/signout', methods=['POST'])
def api_signout():
    \"\"\"Sign out current user.\"\"\"
    try:
        sign_out()
        session.clear()
        return jsonify({
            'success': True,
            'message': 'Signed out successfully'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500

@auth_bp.route('/api/auth/me', methods=['GET'])
def api_get_current_user():
    \"\"\"Get current authenticated user.\"\"\"
    try:
        user_id = get_current_user_id()
        if not user_id:
            return jsonify({
                'success': False,
                'message': 'Not authenticated'
            }), 401
        
        user = get_current_user()
        if user:
            return jsonify({
                'success': True,
                'user': user
            })
        else:
            return jsonify({
                'success': False,
                'message': 'User not found'
            }), 404
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500

# Decorator for protected routes
def require_auth(f):
    \"\"\"Decorator to require authentication for a route.\"\"\"
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_id = get_current_user_id()
        if not user_id:
            return jsonify({
                'success': False,
                'message': 'Authentication required'
            }), 401
        return f(*args, **kwargs)
    return decorated_function

# Usage in recipe_adder_server.py:
# from auth_service import auth_bp, require_auth
# app.register_blueprint(auth_bp)
# 
# @app.route('/api/add-recipe', methods=['POST'])
# @require_auth  # Add this decorator to protect the route
# def add_recipe_api():
#     # ... existing code ...
"""
