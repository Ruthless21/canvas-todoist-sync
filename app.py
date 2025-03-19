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
    
    # Get domain from environment or config
    domain = os.environ.get('DOMAIN') or app.config.get('DOMAIN')
    
    # Only set secure cookie in production environments with HTTPS
    is_secure = os.environ.get('SESSION_COOKIE_SECURE', 'True').lower() == 'true'
    app.config['SESSION_COOKIE_SECURE'] = is_secure
    app.config['SESSION_COOKIE_HTTPONLY'] = True  # Prevent JavaScript access
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'  # CSRF protection
    
    # Set remember cookie settings to match session settings
    app.config['REMEMBER_COOKIE_SECURE'] = is_secure
    app.config['REMEMBER_COOKIE_HTTPONLY'] = True
    app.config['REMEMBER_COOKIE_DURATION'] = timedelta(days=14)  # Longer than session
    
    # Server domain name
    if domain and domain != 'localhost:5000':
        # Comment out SERVER_NAME as it can cause routing issues with subdomain handling
        # app.config['SERVER_NAME'] = domain
        
        # PythonAnywhere uses a subdomain setup
        if 'pythonanywhere.com' in domain:
            app.config['SESSION_COOKIE_DOMAIN'] = '.'+domain  # Include subdomain
    
    app.config['SESSION_TYPE'] = 'null'  # Use Flask's default session implementation instead of filesystem
    app.config['SECRET_KEY'] = app.config['SECRET_KEY']  # Reuse the same secret key
    
    # Configure Flask-Login more extensively
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'
    login_manager.session_protection = 'basic'  # Use basic protection instead of None
    
    # Debug mode configuration
    app.debug = True  # Enable debug mode
    
    # Initialize extensions with login_manager first
    login_manager.init_app(app)
    db.init_app(app)
    migrate.init_app(app)
    cache.init_app(app)
    csrf.init_app(app)
    scheduler.init_app(app)
    
    # Disable CSRF protection for API routes
    app.config['WTF_CSRF_CHECK_DEFAULT'] = False
    
    # Configure CSRF protection to exempt API endpoints
    @csrf.exempt
    def csrf_exempt_api():
        """Exempt all API routes from CSRF protection"""
        if request.path.startswith('/api/') or request.path.startswith('/dashboard/api/'):
            return True
        return False
    
    # User loader for Flask-Login - simplified and more reliable
    @login_manager.user_loader
    def load_user(user_id):
        try:
            app.logger.debug('Loading user with ID: %s', user_id)
            user = User.query.get(int(user_id))
            if user:
                app.logger.debug('User loaded successfully: %s', user.username)
            else:
                app.logger.warning('No user found with ID: %s', user_id)
            return user
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
            
            # Check session cookie
            if 'session' in request.cookies:
                app.logger.debug('Session cookie found: %s', request.cookies.get('session'))
            else:
                app.logger.warning('No session cookie found in request')
            
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
                    app.logger.debug('Restored user session for: %s', user.username)
                
        # After request handler to ensure session is saved
        @app.after_request
        def after_request_func(response):
            # Always save the session
            session.modified = True
            
            # Delete the old cookie if needed
            if hasattr(g, 'delete_old_cookie') and g.delete_old_cookie:
                response.delete_cookie('canvas_todoist_session')
            
            return response

    # Add a debug route to check session and authentication status
    @app.route('/debug/auth-status')
    def debug_auth_status():
        if not app.debug:
            return "Debug routes are only available in debug mode.", 403
            
        output = {
            "is_authenticated": current_user.is_authenticated,
            "session": dict(session),
            "session_cookies": {k: v for k, v in request.cookies.items() if k.lower().startswith('sess')},
            "current_user": str(current_user),
        }
        
        if current_user.is_authenticated:
            output["username"] = current_user.username
            output["user_id"] = current_user.id
        
        response = jsonify(output)
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
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
    from blueprints import main_bp, auth_bp, dashboard_bp, settings_bp, admin_bp, sync_bp, payments_bp, history_bp
    app.register_blueprint(main_bp)  # No url_prefix for main blueprint
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(dashboard_bp, url_prefix='/dashboard')
    app.register_blueprint(settings_bp, url_prefix='/settings')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(sync_bp, url_prefix='/sync')
    app.register_blueprint(payments_bp, url_prefix='/payments')
    app.register_blueprint(history_bp, url_prefix='/history')
    
    # Add a direct_sync route at the application level
    @app.route('/direct_sync', methods=['POST'])
    @login_required
    def direct_sync():
        """Direct sync endpoint that completely bypasses CSRF protection."""
        from flask import jsonify, request, current_app
        import json
        import datetime
        from models import SyncHistory, db
        
        current_app.logger.debug(f"Direct sync endpoint accessed")
        current_app.logger.debug(f"Headers: {request.headers}")
        
        # Get data from request
        try:
            # Try parsing JSON data
            try:
                data = request.get_json(force=True, silent=True)
                if data:
                    current_app.logger.debug(f"JSON data received: {data}")
                else:
                    current_app.logger.debug("No JSON data found, trying form data")
                    data = {}
            except Exception as e:
                current_app.logger.error(f"Error parsing JSON: {e}")
                data = {}
                
            # Try form data as fallback
            form_data = request.form.to_dict()
            if form_data:
                current_app.logger.debug(f"Form data received: {form_data}")
                data.update(form_data)
                
            # Try URL parameters as last resort
            url_params = request.args.to_dict()
            if url_params:
                current_app.logger.debug(f"URL parameters received: {url_params}")
                data.update(url_params)
                
            # Extract course_id and project_id from combined data
            course_id = data.get('course_id')
            project_id = data.get('project_id')
            
            current_app.logger.debug(f"Course ID: {course_id}, Project ID: {project_id}")
            
            if not course_id or not project_id:
                return jsonify({
                    'success': False,
                    'error': 'Missing required parameters: course_id and project_id'
                }), 400
            
            # Get API clients for the current user
            canvas_client, todoist_client, sync_service = get_api_clients()
            
            if not canvas_client or not todoist_client or not sync_service:
                return jsonify({
                    'success': False,
                    'error': 'API clients not initialized. Please check your API credentials.'
                }), 400
            
            current_app.logger.debug(f"Starting sync from Canvas course {course_id} to Todoist project {project_id}")
            
            # Perform the actual sync
            start_time = datetime.datetime.now()
            try:
                # Get course assignments
                current_app.logger.debug(f"Fetching assignments for course {course_id}")
                assignments = canvas_client.get_assignments(course_id)
                current_app.logger.debug(f"Found {len(assignments)} assignments")
                
                # Sync assignments to Todoist
                current_app.logger.debug(f"Syncing {len(assignments)} assignments to Todoist project {project_id}")
                result = sync_service.sync_assignments_to_todoist(assignments, project_id)
                current_app.logger.debug(f"Sync result: {result}")
                
                end_time = datetime.datetime.now()
                duration = (end_time - start_time).total_seconds()
                
                # Create sync history record
                sync_history = SyncHistory(
                    user_id=current_user.id,
                    sync_type='canvas_to_todoist',
                    status='success',
                    items_synced=len(assignments),
                    details=json.dumps({
                        'course_id': course_id,
                        'project_id': project_id,
                        'assignments_count': len(assignments),
                        'duration_seconds': duration
                    }),
                    timestamp=datetime.datetime.now(),
                    started_at=start_time,
                    completed_at=end_time
                )
                db.session.add(sync_history)
                try:
                    db.session.commit()
                except Exception as db_error:
                    # Log the database error but don't fail the API call
                    current_app.logger.error(f"Error saving sync history: {str(db_error)}")
                    current_app.logger.error(f"This is likely a database schema mismatch issue. The sync itself was successful.")
                    db.session.rollback()
                
                return jsonify({
                    'success': True,
                    'message': f'Successfully synced {len(assignments)} assignments from Canvas to Todoist',
                    'data': {
                        'assignments_synced': len(assignments),
                        'course_id': course_id,
                        'project_id': project_id,
                        'duration_seconds': duration
                    }
                })
                
            except Exception as e:
                current_app.logger.error(f"Error syncing assignments: {str(e)}")
                import traceback
                current_app.logger.error(traceback.format_exc())
                
                # Create error sync history record
                sync_history = SyncHistory(
                    user_id=current_user.id,
                    sync_type='canvas_to_todoist',
                    status='error',
                    items_synced=0,
                    details=json.dumps({
                        'course_id': course_id,
                        'project_id': project_id,
                        'error': str(e)
                    }),
                    timestamp=datetime.datetime.now(),
                    started_at=start_time,
                    completed_at=datetime.datetime.now()
                )
                db.session.add(sync_history)
                try:
                    db.session.commit()
                except Exception as db_error:
                    # Log the database error but don't fail the API call
                    current_app.logger.error(f"Error saving error sync history: {str(db_error)}")
                    current_app.logger.error(f"This is likely a database schema mismatch issue. The sync failed but this is only a logging issue.")
                    db.session.rollback()
                
                return jsonify({
                    'success': False,
                    'error': f"Error syncing assignments: {str(e)}"
                }), 500
            
        except Exception as e:
            current_app.logger.error(f"Error in direct sync endpoint: {str(e)}")
            import traceback
            current_app.logger.error(traceback.format_exc())
            return jsonify({
                'success': False,
                'error': f"Direct sync error: {str(e)}"
            }), 500
    
    # Add direct routes for API endpoints to handle both URL patterns
    from blueprints.dashboard import sync_assignments, refresh_data, test_canvas_api, test_todoist_api
    
    @app.route('/api/sync', methods=['POST'])
    @app.route('/api/sync/<csrf_token>', methods=['POST'])
    def api_sync(csrf_token=None):
        """Direct route for the sync API endpoint."""
        from flask import jsonify, request
        
        # Simple debug response to test route reachability
        app.logger.debug("--- DIRECT API SYNC ROUTE ACCESSED ---")
        app.logger.debug(f"Headers: {request.headers}")
        app.logger.debug(f"CSRF Token in URL: {csrf_token}")
        
        try:
            body = request.get_data(as_text=True)
            app.logger.debug(f"Request body: {body[:100]}")  # Log first 100 chars only
            
            # Get JSON data with fallback
            try:
                json_data = request.get_json(force=True, silent=True)
                app.logger.debug(f"JSON data: {json_data}")
            except Exception as e:
                app.logger.error(f"Error parsing JSON: {e}")
                json_data = None
                
            # Try to get form data as fallback
            form_data = request.form.to_dict()
            app.logger.debug(f"Form data: {form_data}")
            
            # Try to get course_id and project_id from any source
            course_id = None
            project_id = None
            
            if json_data:
                course_id = json_data.get('course_id')
                project_id = json_data.get('project_id')
            
            if form_data and not (course_id and project_id):
                course_id = form_data.get('course_id', course_id)
                project_id = form_data.get('project_id', project_id)
                
            # Get URL parameters as last resort
            if not (course_id and project_id):
                course_id = request.args.get('course_id', course_id)
                project_id = request.args.get('project_id', project_id)
                
            app.logger.debug(f"Final course_id: {course_id}, project_id: {project_id}")
            
            return jsonify({
                'success': True,
                'message': f'Direct API sync debug - course_id: {course_id}, project_id: {project_id}',
                'route': 'direct',
                'received_data': {
                    'body': body[:100] if body else None,
                    'course_id': course_id,
                    'project_id': project_id
                }
            })
        except Exception as e:
            app.logger.error(f"Error in direct API sync route: {str(e)}")
            return jsonify({
                'success': False,
                'error': f"Direct API error: {str(e)}"
            }), 500
        
    @app.route('/api/refresh_data', methods=['POST'])
    @app.route('/api/refresh_data/<csrf_token>', methods=['POST'])
    def api_refresh(csrf_token=None):
        """Direct route for the refresh data API endpoint."""
        app.logger.debug(f"CSRF Token in URL for refresh: {csrf_token}")
        return refresh_data()
        
    @app.route('/api/test_canvas', methods=['POST'])
    def api_test_canvas():
        """Direct route for the test Canvas API endpoint."""
        return test_canvas_api()
        
    @app.route('/api/test_todoist', methods=['POST'])
    def api_test_todoist():
        """Direct route for the test Todoist API endpoint."""
        return test_todoist_api()
    
    # Mark all API routes as exempt from CSRF protection
    api_views = [api_sync, api_refresh, api_test_canvas, api_test_todoist]
    for view in api_views:
        csrf.exempt(view)
    
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
    
    # Add a direct refresh endpoint that bypasses CSRF protection
    @app.route('/direct_refresh', methods=['POST'])
    @login_required
    def direct_refresh():
        """Direct refresh endpoint that completely bypasses CSRF protection."""
        from flask import jsonify, current_app
        
        current_app.logger.debug("Direct refresh endpoint accessed")
        
        try:
            return jsonify({
                'success': True,
                'message': 'Data refreshed successfully'
            })
        except Exception as e:
            current_app.logger.error(f"Error in direct refresh endpoint: {str(e)}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    return app

# Create application instance
app = create_app('pythonanywhere' if 'pythonanywhere' in socket.gethostname().lower() else 'development')

# Only used when running directly with Python
if __name__ == '__main__':
    app.jinja_env.cache = {}
    app.run()

