from flask import request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity, get_jwt
from models.user import User
from otp_service import otp_service
import re

# JWT blacklist for logout
blacklisted_tokens = set()

def send_otp():
    """Send OTP to email address"""
    try:
        data = request.get_json()
        
        if not data or 'email' not in data:
            return jsonify({'error': 'Email address is required'}), 400
        
        email = data['email'].lower().strip()
        
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
            return jsonify({'error': 'Invalid email format'}), 400
        
        if User.find_by_email(email):
            return jsonify({'error': 'Email already registered'}), 409
        
        success, message = otp_service.send_otp(email)
        
        if success:
            return jsonify({'message': message}), 200
        else:
            return jsonify({'error': message}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def verify_otp():
    """Verify OTP"""
    try:
        data = request.get_json()
        
        if not data or not all(k in data for k in ('email', 'otp')):
            return jsonify({'error': 'Email and OTP are required'}), 400
        
        email = data['email'].lower().strip()
        otp = data['otp'].strip()
        
        success, message = otp_service.verify_otp(email, otp)
        
        if success:
            return jsonify({'message': message, 'verified': True}), 200
        else:
            return jsonify({'error': message, 'verified': False}), 400
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def signup():
    """User registration with email OTP verification"""
    try:
        data = request.get_json()
        
        # Validation
        if not data or not all(k in data for k in ('email', 'password', 'name', 'phone', 'email_verified')):
            return jsonify({'error': 'All fields including email verification are required'}), 400
        
        if not data['email_verified']:
            return jsonify({'error': 'Email must be verified before signup'}), 400
        
        email = data['email'].lower().strip()
        password = data['password']
        name = data['name'].strip()
        phone = data['phone'].strip()
        
        # Email validation
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
            return jsonify({'error': 'Invalid email format'}), 400
        
        # Password validation
        if len(password) < 6:
            return jsonify({'error': 'Password must be at least 6 characters'}), 400
        
        # Name validation
        if len(name) < 2:
            return jsonify({'error': 'Name must be at least 2 characters'}), 400
        
        # Phone validation (required but no verification needed)
        if not phone or len(phone) < 10:
            return jsonify({'error': 'Valid WhatsApp number is required'}), 400
        
        # Create user
        user_id = User.create_user(email, password, name, phone)
        if not user_id:
            return jsonify({'error': 'User already exists'}), 409
        
        # Create access token
        access_token = create_access_token(identity=user_id)
        
        # Get user stats
        stats = User.get_user_stats(user_id)
        
        return jsonify({
            'message': 'User created successfully',
            'access_token': access_token,
            'user': {
                'id': user_id,
                'email': email,
                'name': name,
                'stats': stats
            }
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def login():
    """User login"""
    try:
        data = request.get_json()
        
        if not data or not all(k in data for k in ('email', 'password')):
            return jsonify({'error': 'Email and password are required'}), 400
        
        email = data['email'].lower().strip()
        password = data['password']
        
        # Find user
        user = User.find_by_email(email)
        if not user:
            return jsonify({'error': 'Invalid credentials'}), 401
        
        # Verify password
        if not User.verify_password(user['password'], password):
            return jsonify({'error': 'Invalid credentials'}), 401
        
        # Create access token
        access_token = create_access_token(identity=str(user['_id']))
        
        # Get user stats
        stats = User.get_user_stats(str(user['_id']))
        
        return jsonify({
            'message': 'Login successful',
            'access_token': access_token,
            'user': {
                'id': str(user['_id']),
                'email': user['email'],
                'name': user['name'],
                'stats': stats
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@jwt_required()
def logout():
    """User logout"""
    try:
        jti = get_jwt()['jti']
        blacklisted_tokens.add(jti)
        return jsonify({'message': 'Successfully logged out'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@jwt_required()
def get_profile():
    """Get user profile"""
    try:
        user_id = get_jwt_identity()
        user = User.find_by_id(user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        stats = User.get_user_stats(user_id)
        
        return jsonify({
            'user': {
                'id': str(user['_id']),
                'email': user['email'],
                'name': user['name'],
                'phone': user.get('phone'),
                'stats': stats
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def check_token_blacklist(jwt_header, jwt_payload):
    """Check if token is blacklisted"""
    jti = jwt_payload['jti']
    return jti in blacklisted_tokens