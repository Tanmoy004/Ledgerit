from datetime import datetime, timedelta
from bson import ObjectId
from database import db
from flask_bcrypt import Bcrypt
import os

bcrypt = Bcrypt()

class User:
    collection = db.users
    
    @staticmethod
    def create_user(email, password, name, phone=None):
        """Create a new user with free plan"""
        if User.find_by_email(email):
            return None
        
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        
        user_data = {
            'email': email,
            'password': hashed_password,
            'name': name,
            'phone': phone,
            'pages_used': 0,
            'free_pages_limit': int(os.getenv('FREE_PAGE_LIMIT', 100)),
            'subscription': {
                'plan': 'free',
                'status': 'active',
                'start_date': datetime.utcnow(),
                'end_date': None,
                'pages_limit': int(os.getenv('FREE_PAGE_LIMIT', 100))
            },
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }
        
        result = User.collection.insert_one(user_data)
        return str(result.inserted_id)
    
    @staticmethod
    def find_by_email(email):
        """Find user by email"""
        return User.collection.find_one({'email': email})
    
    @staticmethod
    def find_by_id(user_id):
        """Find user by ID"""
        return User.collection.find_one({'_id': ObjectId(user_id)})
    
    @staticmethod
    def verify_password(stored_password, provided_password):
        """Verify password"""
        return bcrypt.check_password_hash(stored_password, provided_password)
    
    @staticmethod
    def update_pages_used(user_id, pages_count):
        """Update pages used by user"""
        return User.collection.update_one(
            {'_id': ObjectId(user_id)},
            {
                '$inc': {'pages_used': pages_count},
                '$set': {'updated_at': datetime.utcnow()}
            }
        )
    
    @staticmethod
    def update_subscription(user_id, plan, duration_months):
        """Update user subscription"""
        start_date = datetime.utcnow()
        end_date = start_date + timedelta(days=duration_months * 30)
        
        # Set pages limit based on plan
        pages_limit = float('inf')  # Unlimited for paid plans
        
        subscription_data = {
            'plan': plan,
            'status': 'active',
            'start_date': start_date,
            'end_date': end_date,
            'pages_limit': pages_limit
        }
        
        return User.collection.update_one(
            {'_id': ObjectId(user_id)},
            {
                '$set': {
                    'subscription': subscription_data,
                    'updated_at': datetime.utcnow()
                }
            }
        )
    
    @staticmethod
    def check_subscription_status(user_id):
        """Check if user's subscription is active"""
        user = User.find_by_id(user_id)
        if not user:
            return False
        
        subscription = user.get('subscription', {})
        
        # Free plan - check pages limit
        if subscription.get('plan') == 'free':
            return user.get('pages_used', 0) < user.get('free_pages_limit', 100)
        
        # Paid plan - check expiry date
        if subscription.get('end_date'):
            return datetime.utcnow() < subscription['end_date']
        
        return False
    
    @staticmethod
    def get_user_stats(user_id):
        """Get user usage statistics"""
        user = User.find_by_id(user_id)
        if not user:
            return None
        
        subscription = user.get('subscription', {})
        pages_used = user.get('pages_used', 0)
        
        if subscription.get('plan') == 'free':
            pages_limit = user.get('free_pages_limit', 100)
            pages_remaining = max(0, pages_limit - pages_used)
        else:
            pages_limit = float('inf')
            pages_remaining = float('inf')
        
        return {
            'pages_used': pages_used,
            'pages_limit': pages_limit,
            'pages_remaining': pages_remaining,
            'subscription': subscription
        }