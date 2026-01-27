from flask import Blueprint
from controllers.subscription_controller import get_plans, subscribe, get_subscription_status

subscription_bp = Blueprint('subscription', __name__, url_prefix='/api/subscription')

subscription_bp.route('/plans', methods=['GET'])(get_plans)
subscription_bp.route('/subscribe', methods=['POST'])(subscribe)
subscription_bp.route('/status', methods=['GET'])(get_subscription_status)