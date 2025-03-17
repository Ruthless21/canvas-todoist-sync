"""
Blueprint package initialization.
This module registers all blueprints with the Flask application.
"""

from flask import Blueprint

# Create blueprints
main_bp = Blueprint('main', __name__)
auth_bp = Blueprint('auth', __name__)
dashboard_bp = Blueprint('dashboard', __name__)
settings_bp = Blueprint('settings', __name__)
admin_bp = Blueprint('admin', __name__)
sync_bp = Blueprint('sync', __name__)
payments_bp = Blueprint('payments', __name__)

# Import routes after blueprint creation to avoid circular imports
from blueprints import main, auth, dashboard, settings, admin, sync, payments 