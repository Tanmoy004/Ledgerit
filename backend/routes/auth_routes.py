from flask import Blueprint
from controllers.auth_controller import signup, login, logout, get_profile, send_otp, verify_otp

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

auth_bp.route('/signup', methods=['POST'])(signup)
auth_bp.route('/login', methods=['POST'])(login)
auth_bp.route('/logout', methods=['POST'])(logout)
auth_bp.route('/profile', methods=['GET'])(get_profile)
auth_bp.route('/send-otp', methods=['POST'])(send_otp)
auth_bp.route('/verify-otp', methods=['POST'])(verify_otp)