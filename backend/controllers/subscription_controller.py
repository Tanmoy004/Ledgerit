from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models.user import User

SUBSCRIPTION_PLANS = {
    'monthly': {
        'name': 'Monthly Plan',
        'price': 800,
        'duration_months': 1,
        'features': ['Unlimited PDF processing', 'All bank support', 'Priority support']
    },
    'quarterly': {
        'name': 'Quarterly Plan', 
        'price': 2000,
        'duration_months': 3,
        'features': ['Unlimited PDF processing', 'All bank support', 'Priority support', '17% savings']
    },
    'yearly': {
        'name': 'Yearly Plan',
        'price': 3000,
        'duration_months': 12,
        'features': ['Unlimited PDF processing', 'All bank support', 'Priority support', '69% savings']
    }
}

def get_plans():
    """Get all subscription plans"""
    try:
        return jsonify({
            'plans': SUBSCRIPTION_PLANS
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@jwt_required()
def subscribe():
    """Subscribe to a plan"""
    try:
        data = request.get_json()
        
        if not data or 'plan' not in data:
            return jsonify({'error': 'Plan is required'}), 400
        
        plan = data['plan']
        if plan not in SUBSCRIPTION_PLANS:
            return jsonify({'error': 'Invalid plan'}), 400
        
        user_id = get_jwt_identity()
        
        # In a real application, you would integrate with a payment gateway here
        # For now, we'll just update the subscription
        
        plan_info = SUBSCRIPTION_PLANS[plan]
        result = User.update_subscription(user_id, plan, plan_info['duration_months'])
        
        if result.modified_count == 0:
            return jsonify({'error': 'Failed to update subscription'}), 500
        
        # Get updated user stats
        stats = User.get_user_stats(user_id)
        
        return jsonify({
            'message': f'Successfully subscribed to {plan_info["name"]}',
            'subscription': stats['subscription']
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@jwt_required()
def get_subscription_status():
    """Get user's subscription status"""
    try:
        user_id = get_jwt_identity()
        stats = User.get_user_stats(user_id)
        
        if not stats:
            return jsonify({'error': 'User not found'}), 404
        
        is_active = User.check_subscription_status(user_id)
        
        return jsonify({
            'stats': stats,
            'is_active': is_active,
            'needs_upgrade': not is_active and stats['subscription']['plan'] == 'free'
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500