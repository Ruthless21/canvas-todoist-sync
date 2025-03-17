"""
Main application file.
Initializes Flask application and registers blueprints.
"""

import os
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session, g, make_response
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
        if not current_user.is_authenticated:
            flash('Please log in to access this feature.', 'warning')
            return redirect(url_for('auth.login', next=request.url))
        if not current_user.is_premium:
            flash('This feature requires a premium subscription.', 'warning')
            return redirect(url_for('payments.pricing'))
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
    
    # Set up logging
    import logging
    from logging.handlers import RotatingFileHandler
    import os
    
    # Ensure the logs directory exists
    if not os.path.exists('logs'):
        os.mkdir('logs')
    
    # Set up the main application log file
    file_handler = RotatingFileHandler('logs/canvas_todoist.log', maxBytes=10240, backupCount=10)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    file_handler.setLevel(logging.DEBUG)
    app.logger.addHandler(file_handler)
    
    app.logger.setLevel(logging.DEBUG)
    app.logger.info('Canvas-Todoist startup')
    
    # Add scheduler configuration
    app.config['SCHEDULER_API_ENABLED'] = True
    app.config['SCHEDULER_JOB_DEFAULTS'] = {
        'coalesce': False,
        'max_instances': 1
    }
    
    # Session configuration - use only one consistent session cookie name
    app.config['SESSION_COOKIE_NAME'] = 'session'  # Use default Flask session cookie name
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)
    app.config['SESSION_REFRESH_EACH_REQUEST'] = True
    app.config['SESSION_COOKIE_SECURE'] = True  # Only send cookie over HTTPS
    app.config['SESSION_COOKIE_HTTPONLY'] = True  # Prevent JavaScript access
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'  # CSRF protection
    app.config['SESSION_TYPE'] = 'null'  # Use Flask's default session implementation instead of filesystem
    app.config['SECRET_KEY'] = app.config['SECRET_KEY']  # Reuse the same secret key
    
    # Configure Flask-Login more extensively
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'
    login_manager.session_protection = None  # Disable session protection temporarily to diagnose issues
    
    # Debug mode configuration
    app.debug = True  # Enable debug mode
    
    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app)
    cache.init_app(app)
    csrf.init_app(app)
    scheduler.init_app(app)
    
    # User loader for Flask-Login - simplified and more reliable
    @login_manager.user_loader
    def load_user(user_id):
        try:
            app.logger.debug('Loading user with ID: %s', user_id)
            return User.query.get(int(user_id))
        except Exception as e:
            app.logger.error('Error loading user: %s', str(e))
            return None

    # Debug logging for session and auth
    if app.debug:
        @app.before_request
        def log_request_info():
            app.logger.debug('Request method: %s, path: %s', request.method, request.path)
            app.logger.debug('Headers: %s', request.headers)
            app.logger.debug('Session: %s', dict(session))
            app.logger.debug('User: %s', current_user)
            
            # Clear old session cookie if present - this is causing problems
            if 'canvas_todoist_session' in request.cookies:
                app.logger.debug('Detected old canvas_todoist_session cookie, marking for deletion')
                g.delete_old_cookie = True
            
            # Force load the user if in session but not recognized by Flask-Login
            if not current_user.is_authenticated and 'user_id' in session:
                user_id = session.get('user_id')
                app.logger.debug('Attempting to restore user session for user_id: %s', user_id)
                user = User.query.get(user_id)
                if user:
                    login_user(user)
                    session.modified = True
                    app.logger.debug('Restored user session for: %s', user.username)
                
        # After request handler to ensure session is saved
        @app.after_request
        def after_request_func(response):
            # Always save the session
            session.modified = True
            
            # Add debug logging for response
            app.logger.debug('Response status: %s', response.status_code)
            app.logger.debug('Response headers: %s', response.headers)
            
            # For redirect responses, be extra careful
            if response.status_code in (301, 302, 303, 307, 308):
                app.logger.debug('Processing redirect response to: %s', response.headers.get('Location'))
            
            # Delete old session cookie if needed, but don't mess with redirects
            if hasattr(g, 'delete_old_cookie') and g.delete_old_cookie:
                response.delete_cookie('canvas_todoist_session')
                app.logger.debug('Deleted old canvas_todoist_session cookie in after_request')
            
            return response

    # Add error handlers
    @app.errorhandler(404)
    def not_found_error(error):
        """Handle 404 errors."""
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_error(error):
        """Handle 500 errors."""
        db.session.rollback()
        return render_template('errors/500.html'), 500
    
    # Register blueprints
    from blueprints import main_bp, auth_bp, dashboard_bp, settings_bp, admin_bp, sync_bp, payments_bp
    app.register_blueprint(main_bp)  # No url_prefix for main blueprint
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(dashboard_bp, url_prefix='/dashboard')
    app.register_blueprint(settings_bp, url_prefix='/settings')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(sync_bp, url_prefix='/sync')
    app.register_blueprint(payments_bp, url_prefix='/payments')
    
    # Initialize Stripe
    stripe.api_key = app.config['STRIPE_SECRET_KEY']
    
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

# Only used when running directly with Python
if __name__ == '__main__':
    app.jinja_env.cache = {}
    app.run()

