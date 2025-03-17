"""
Main application file.
Initializes Flask application and registers blueprints.
"""

import os
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session, g
from dotenv import load_dotenv
from flask_login import login_user, logout_user, login_required, current_user
from urllib.parse import urlparse
from extensions import db, login_manager, cache, scheduler, migrate, csrf
from models import User
# Import other model classes only when needed to avoid circular imports
from forms import LoginForm, RegistrationForm, APICredentialsForm, SyncSettingsForm, AccountUpdateForm, PasswordChangeForm
from services.canvas_api import CanvasAPI
from services.todoist_api import TodoistClient
from services.sync_service import SyncService
from functools import wraps
from datetime import datetime, timedelta
import stripe
import socket
from config import Config, config

# Load environment variables
load_dotenv()

# URL parsing helper
def url_parse(url):
    return urlparse(url)

# Decorator for premium features
def premium_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_premium:
            flash('This feature requires a premium subscription.', 'warning')
            return redirect(url_for('pricing'))
        return f(*args, **kwargs)
    return decorated_function

# API client initialization helper
def get_api_clients():
    if current_user.is_authenticated:
        try:
            canvas_api_client = CanvasAPI(
                api_url=current_user.canvas_api_url,
                api_token=current_user.get_canvas_token()
            )
            todoist_client = TodoistClient(
                api_token=current_user.get_todoist_token()
            )
            sync_service_client = SyncService(canvas_api_client, todoist_client)
            return canvas_api_client, todoist_client, sync_service_client
        except ValueError:
            # If API credentials are missing, redirect to API credentials page
            return None, None, None
    return None, None, None

# API functions
def get_canvas_courses(api_client):
    if not api_client:
        return []
    try:
        return api_client.get_courses()
    except Exception as e:
        print(f"Error fetching Canvas courses: {str(e)}")
        return []

def get_todoist_projects(api_client):
    if not api_client:
        return []
    try:
        return api_client.get_projects()
    except Exception as e:
        print(f"Error fetching Todoist projects: {str(e)}")
        return []

# Global cached functions to be used by routes
def get_cached_canvas_courses(api_client):
    """Cached wrapper for get_canvas_courses that will be properly initialized with the app's cache"""
    if not api_client:
        return []
    try:
        return get_canvas_courses(api_client)
    except Exception as e:
        print(f"Error in cached Canvas courses: {str(e)}")
        return []
    
def get_cached_todoist_projects(api_client):
    """Cached wrapper for get_todoist_projects that will be properly initialized with the app's cache"""
    if not api_client:
        return []
    try:
        return get_todoist_projects(api_client)
    except Exception as e:
        print(f"Error in cached Todoist projects: {str(e)}")
        return []

def create_app(config_name='default'):
    """Create and configure the Flask application."""
    app = Flask(__name__)
    
    # Load the appropriate configuration
    app.config.from_object(config[config_name])
    
    # Add scheduler configuration
    app.config['SCHEDULER_API_ENABLED'] = True
    app.config['SCHEDULER_JOB_DEFAULTS'] = {
        'coalesce': False,
        'max_instances': 1
    }
    
    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    cache.init_app(app)
    csrf.init_app(app)
    scheduler.init_app(app)
    
    # Configure login manager
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'
    
    # Register blueprints
    from blueprints import auth_bp, dashboard_bp, settings_bp, admin_bp, sync_bp, payments_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(dashboard_bp, url_prefix='/dashboard')
    app.register_blueprint(settings_bp, url_prefix='/settings')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(sync_bp, url_prefix='/sync')
    app.register_blueprint(payments_bp, url_prefix='/payments')
    
    # Initialize Stripe
    stripe.api_key = app.config['STRIPE_SECRET_KEY']
    
    # Make debug flag available to templates
    @app.context_processor
    def inject_debug():
        return dict(debug=app.debug)
    
    # Add Stripe configuration to templates
    @app.context_processor
    def inject_stripe_config():
        return dict(
            stripe_publishable_key=app.config['STRIPE_PUBLISHABLE_KEY'],
            stripe_monthly_price_id=app.config['STRIPE_MONTHLY_PRICE_ID'],
            stripe_yearly_price_id=app.config['STRIPE_YEARLY_PRICE_ID'],
            monthly_price=app.config['MONTHLY_PRICE'],
            yearly_price=app.config['YEARLY_PRICE'],
            trial_days=app.config['TRIAL_DAYS']
        )
    
    # Set up cache functions with proper decorators now that we have app context
    @cache.cached(timeout=app.config['CACHE_DEFAULT_TIMEOUT'], key_prefix=lambda: f"courses_{current_user.id}" if current_user.is_authenticated else "courses_anonymous")
    def get_cached_canvas_courses_with_app(api_client):
        return get_canvas_courses(api_client)
    
    @cache.cached(timeout=app.config['CACHE_DEFAULT_TIMEOUT'], key_prefix=lambda: f"projects_{current_user.id}" if current_user.is_authenticated else "projects_anonymous")
    def get_cached_todoist_projects_with_app(api_client):
        return get_todoist_projects(api_client)
    
    # Replace the global functions with the decorated versions
    global get_cached_canvas_courses, get_cached_todoist_projects
    get_cached_canvas_courses = get_cached_canvas_courses_with_app
    get_cached_todoist_projects = get_cached_todoist_projects_with_app
    
    # Scheduled task for automated syncing
    @scheduler.task('interval', id='sync_assignments', seconds=60*15)  # Run every 15 minutes
    def scheduled_sync():
        with app.app_context():
            try:
                now = datetime.utcnow()
                
                # Import here to avoid circular imports
                from models import SyncSettings
                
                # Get all enabled sync settings
                settings = SyncSettings.query.filter_by(enabled=True).all()
                
                for setting in settings:
                    user = User.query.get(setting.user_id)
                    
                    # Skip if user is not premium
                    if not user.is_premium:
                        continue
                        
                    # Check if it's time to sync based on frequency
                    should_sync = False
                    
                    if setting.last_sync is None:
                        should_sync = True
                    elif setting.frequency == 'hourly' and (now - setting.last_sync).total_seconds() >= 3600:
                        should_sync = True
                    elif setting.frequency == 'daily' and (now - setting.last_sync).total_seconds() >= 86400:
                        should_sync = True
                    elif setting.frequency == 'weekly' and (now - setting.last_sync).total_seconds() >= 604800:
                        should_sync = True
                        
                    if should_sync:
                        try:
                            # Initialize API clients for the user
                            canvas_api_client = CanvasAPI(
                                api_url=user.canvas_api_url,
                                api_token=user.get_canvas_token()
                            )
                            todoist_client = TodoistClient(
                                api_token=user.get_todoist_token()
                            )
                            sync_service_client = SyncService(canvas_api_client, todoist_client)
                            
                            # Get all courses
                            courses = canvas_api_client.get_courses()
                            
                            # Sync assignments for each course
                            for course in courses:
                                sync_service_client.sync_course_assignments(course['id'])
                            
                            # Update last sync time
                            setting.last_sync = now
                            db.session.commit()
                            
                            app.logger.info(f"Automatic sync completed for user {user.username}")
                        except Exception as e:
                            app.logger.error(f"Error syncing for user {user.username}: {str(e)}")
            finally:
                # Ensure database connections are properly closed
                db.session.remove()
    
    # Ensure database connections are properly closed
    with app.app_context():
        db.create_all()
        
        # Clean up any existing MySQL connections - this helps when redeploying
        try:
            # Force SQLAlchemy to create a fresh connection pool
            db.engine.dispose()
            print("Database connection pool refreshed at startup")
        except Exception as e:
            print(f"Warning: Could not refresh connection pool: {str(e)}")
    
    # Check if running under uWSGI
    try:
        import uwsgi
        # Running under uWSGI - don't start the scheduler
        print("Detected uWSGI environment - scheduler will not start automatically")
        # The scheduler can be run separately using a scheduled task in PythonAnywhere
    except ImportError:
        # Not running under uWSGI, safe to start scheduler
        if not os.environ.get('FLASK_RUN_FROM_CLI') and os.environ.get('WERKZEUG_RUN_MAIN') != 'true':
            print("Starting scheduler in non-uWSGI environment")
            scheduler.start()
    
    return app

# Create application instance
app = create_app('pythonanywhere' if 'pythonanywhere' in socket.gethostname().lower() else 'development')

@app.route('/')
def index():
    """Display the home page."""
    return render_template('index.html')

@app.errorhandler(404)
def not_found_error(error):
    """Handle 404 errors."""
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    db.session.rollback()
    return render_template('errors/500.html'), 500

# Only used when running directly with Python
if __name__ == '__main__':
    app.jinja_env.cache = {}
    app.run()

