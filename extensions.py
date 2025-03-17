"""
Flask extensions initialization.
This module initializes all Flask extensions used in the application.
These extensions are imported by other modules, avoiding circular imports.
"""

from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_caching import Cache
from flask_apscheduler import APScheduler
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect

# Initialize extensions
db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()
cache = Cache()
csrf = CSRFProtect()

# Initialize scheduler with configuration
scheduler = APScheduler()
# Configuration will be applied in app.py using app.config

# Configure login manager
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'info' 