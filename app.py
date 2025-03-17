from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session, g
import os
from dotenv import load_dotenv
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from urllib.parse import urlparse
from models import db, User, SyncHistory, SyncSettings, Subscription
from forms import LoginForm, RegistrationForm, APICredentialsForm, SyncSettingsForm, AccountUpdateForm, PasswordChangeForm
from services.canvas_api import CanvasAPI
from services.todoist_api import TodoistClient
from services.sync_service import SyncService
from functools import wraps
from datetime import datetime, timedelta
from flask_apscheduler import APScheduler
from flask_caching import Cache
from config import config
import stripe
from stripe_routes import stripe_bp
import stripe_config
import socket

# Load environment variables
load_dotenv()

# Initialize scheduler
scheduler = APScheduler()

# Initialize cache
cache = Cache()

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
                api_token=current_user.get_canvas_api_token()
            )
            todoist_client = TodoistClient(
                api_token=current_user.get_todoist_api_key()
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
    # Create and configure the app
    app = Flask(__name__)
    
    # Load configuration from config.py
    app.config.from_object(config[config_name])
    
    # Make sure cache directory exists if using FileSystemCache
    if app.config.get('CACHE_TYPE') == 'FileSystemCache' and app.config.get('CACHE_DIR'):
        cache_dir = app.config.get('CACHE_DIR')
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir, exist_ok=True)
            print(f"Created cache directory at {cache_dir}")
    
    # Configure SQLAlchemy connection pooling for PythonAnywhere
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_recycle': 240,  # Less than PythonAnywhere's 300s timeout
        'pool_pre_ping': True,  # Test connections before using them
        'pool_timeout': 30,    # Don't wait too long for connections
        'pool_size': 10,       # Default pool size
        'max_overflow': 5      # Allow some extra connections
    }
    
    # Initialize extensions with app
    db.init_app(app)
    login_manager = LoginManager(app)
    login_manager.login_view = 'login'
    login_manager.login_message = 'Please log in to access this page.'
    scheduler.init_app(app)
    cache.init_app(app)
    
    # Setup database session cleanup after each request
    @app.teardown_appcontext
    def shutdown_session(exception=None):
        db.session.remove()
    
    # Register blueprints
    app.register_blueprint(stripe_bp)
    
    # Initialize Stripe
    stripe.api_key = stripe_config.STRIPE_SECRET_KEY
    
    # Make debug flag available to templates
    @app.context_processor
    def inject_debug():
        return dict(debug=app.debug)
    
    # Add Stripe configuration to templates
    @app.context_processor
    def inject_stripe_config():
        return dict(
            stripe_publishable_key=stripe_config.STRIPE_PUBLISHABLE_KEY,
            stripe_monthly_price_id=stripe_config.STRIPE_MONTHLY_PRICE_ID,
            stripe_yearly_price_id=stripe_config.STRIPE_YEARLY_PRICE_ID,
            monthly_price=stripe_config.MONTHLY_PRICE,
            yearly_price=stripe_config.YEARLY_PRICE,
            trial_days=stripe_config.TRIAL_DAYS
        )
    
    # User loader for Flask-Login
    @login_manager.user_loader
    def load_user(id):
        return User.query.get(int(id))
    
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
                                api_token=user.get_canvas_api_token()
                            )
                            todoist_client = TodoistClient(
                                api_token=user.get_todoist_api_key()
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
    
    # ----- ROUTES -----
    
    # Index route
    @app.route('/')
    def index():
        return render_template('index.html')
    
    # Authentication routes
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if current_user.is_authenticated:
            return redirect(url_for('dashboard'))
        
        form = LoginForm()
        if form.validate_on_submit():
            user = User.query.filter_by(username=form.username.data).first()
            if user is None or not user.check_password(form.password.data):
                flash('Invalid username or password', 'danger')
                return redirect(url_for('login'))
            
            login_user(user, remember=form.remember_me.data)
            next_page = request.args.get('next')
            if not next_page or url_parse(next_page).netloc != '':
                next_page = url_for('dashboard')
            return redirect(next_page)
        
        return render_template('login.html', title='Sign In', form=form)
    
    @app.route('/logout')
    def logout():
        logout_user()
        return redirect(url_for('index'))
    
    @app.route('/register', methods=['GET', 'POST'])
    def register():
        if current_user.is_authenticated:
            return redirect(url_for('dashboard'))
        
        form = RegistrationForm()
        if form.validate_on_submit():
            user = User(username=form.username.data, email=form.email.data)
            user.set_password(form.password.data)
            db.session.add(user)
            db.session.commit()
            flash('Congratulations, you are now a registered user!', 'success')
            return redirect(url_for('login'))
        
        return render_template('register.html', title='Register', form=form)
    
    # Dashboard route
    @app.route('/dashboard')
    @login_required
    def dashboard():
        try:
            canvas_api_client, todoist_client, sync_service_client = get_api_clients()
            
            # Check if API clients are configured
            if canvas_api_client is None or todoist_client is None:
                flash('Please set up your Canvas and Todoist API credentials to use the dashboard features.', 'warning')
                return redirect(url_for('api_credentials'))
            
            # Use cached functions instead of direct API calls
            courses = get_cached_canvas_courses(canvas_api_client)
            projects = get_cached_todoist_projects(todoist_client)
            
            # Get user's sync settings
            sync_settings = SyncSettings.query.filter_by(user_id=current_user.id).first()
            if not sync_settings:
                sync_settings = SyncSettings(user_id=current_user.id)
                db.session.add(sync_settings)
                db.session.commit()
            
            # Get recent sync history
            sync_history = SyncHistory.query.filter_by(user_id=current_user.id).order_by(SyncHistory.timestamp.desc()).limit(5).all()
            
            return render_template('dashboard.html', 
                                  courses=courses, 
                                  projects=projects, 
                                  sync_status=sync_settings,
                                  sync_history=sync_history)
        except Exception as e:
            flash(f"Error: {str(e)}", "danger")
            return render_template('dashboard.html', 
                                  courses=[], 
                                  projects=[],
                                  sync_status=None,
                                  sync_history=[])
    
    # API credentials route
    @app.route('/api_credentials', methods=['GET', 'POST'])
    @login_required
    def api_credentials():
        """Handle API credentials form submission."""
        form = APICredentialsForm()
        
        if form.validate_on_submit():
            current_user.canvas_api_url = form.canvas_api_url.data
            current_user.set_canvas_api_token(form.canvas_api_token.data)
            current_user.set_todoist_api_key(form.todoist_api_key.data)
            db.session.commit()
            flash('API credentials updated successfully!', 'success')
            return redirect(url_for('dashboard'))
        
        # Pre-fill form with user's existing credentials
        if request.method == 'GET':
            form.canvas_api_url.data = current_user.canvas_api_url
            form.canvas_api_token.data = current_user.get_canvas_api_token()
            form.todoist_api_key.data = current_user.get_todoist_api_key()
        
        return render_template('api_credentials.html', title='API Credentials', form=form)
    
    # Pricing route
    @app.route('/pricing')
    def pricing():
        return render_template('pricing.html')
    
    # Subscription management route
    @app.route('/subscription')
    @login_required
    def subscription():
        # Get the user's premium status
        subscription = Subscription.query.filter_by(user_id=current_user.id).first()
        
        return render_template('subscription.html', subscription=subscription)
    
    # Admin routes
    @app.route('/admin/users')
    @login_required
    def admin_users():
        # Use environment variable for admin email instead of hardcoding
        admin_email = os.environ.get('ADMIN_EMAIL', 'tatumparr@gmail.com')
        if current_user.email != admin_email:
            flash('Admin access required.', 'danger')
            return redirect(url_for('dashboard'))
        
        users = User.query.all()
        return render_template('admin_users.html', users=users)
    
    @app.route('/admin/toggle_premium/<int:user_id>', methods=['POST'])
    @login_required
    def toggle_premium(user_id):
        # Use environment variable for admin email instead of hardcoding
        admin_email = os.environ.get('ADMIN_EMAIL', 'tatumparr@gmail.com')
        if current_user.email != admin_email:
            flash('Admin access required.', 'danger')
            return redirect(url_for('dashboard'))
        
        user = User.query.get_or_404(user_id)
        user.is_premium = not user.is_premium
        db.session.commit()
        
        flash(f'Premium status updated for {user.username}.', 'success')
        return redirect(url_for('admin_users'))
    
    # Settings routes
    @app.route('/settings', methods=['GET', 'POST'])
    @login_required
    def settings():
        """User settings page."""
        # Get user's subscription status
        subscription = None
        if current_user.is_premium:
            subscription = Subscription.query.filter_by(user_id=current_user.id).first()
        
        # Canvas and Todoist API credentials form
        api_form = APICredentialsForm()
        
        # Forms for sync settings
        sync_form = SyncSettingsForm()
        
        # Forms for account management
        account_form = AccountUpdateForm()
        password_form = PasswordChangeForm()
        
        # API credentials update
        if api_form.is_submitted() and 'api_submit' in request.form:
            if api_form.validate():
                current_user.canvas_api_url = api_form.canvas_api_url.data
                current_user.set_canvas_api_token(api_form.canvas_api_token.data)
                current_user.set_todoist_api_key(api_form.todoist_api_key.data)
                db.session.commit()
                
                # Test the credentials
                canvas_token = current_user.get_canvas_api_token() or ""  # Ensure it's never None
                todoist_key = current_user.get_todoist_api_key() or ""    # Ensure it's never None
                
                # Success message
                flash('API credentials updated successfully!', 'success')
                return redirect(url_for('settings'))
            
        # Pre-fill forms with existing data
        if request.method == 'GET':
            # API credentials form
            api_form.canvas_api_url.data = current_user.canvas_api_url
            api_form.canvas_api_token.data = current_user.get_canvas_api_token() or ""
            api_form.todoist_api_key.data = current_user.get_todoist_api_key() or ""
            
            # Sync settings form
            settings = SyncSettings.query.filter_by(user_id=current_user.id).first()
            if settings:
                sync_form.enabled.data = settings.enabled
                sync_form.frequency.data = settings.frequency
            
            # Account form
            account_form.username.data = current_user.username
            account_form.email.data = current_user.email
            
            # Password form
            password_form.new_password.data = ""
        
        return render_template('settings.html', 
                              api_form=api_form,
                              sync_form=sync_form, 
                              account_form=account_form,
                              password_form=password_form)
    
    @app.route('/update_account', methods=['POST'])
    @login_required
    def update_account():
        form = AccountUpdateForm()
        if form.validate_on_submit():
            current_user.username = form.username.data
            current_user.email = form.email.data
            db.session.commit()
            flash('Your account information has been updated.', 'success')
        return redirect(url_for('settings'))
    
    @app.route('/change_password', methods=['POST'])
    @login_required
    def change_password():
        form = PasswordChangeForm()
        if form.validate_on_submit():
            current_user.set_password(form.new_password.data)
            db.session.commit()
            flash('Your password has been changed.', 'success')
        return redirect(url_for('settings'))
    
    @app.route('/update_sync_settings', methods=['POST'])
    @login_required
    @premium_required
    def update_sync_settings():
        form = SyncSettingsForm()
        if form.validate_on_submit():
            # Get or create sync settings for the user
            settings = SyncSettings.query.filter_by(user_id=current_user.id).first()
            if not settings:
                settings = SyncSettings(user_id=current_user.id)
                db.session.add(settings)
            
            # Update settings from form
            settings.enabled = form.enabled.data
            settings.frequency = form.frequency.data
            db.session.commit()
            
            flash('Sync settings updated successfully.', 'success')
        return redirect(url_for('settings'))
    
    # Sync history route
    @app.route('/sync_history')
    @login_required
    def sync_history():
        records = SyncHistory.query.filter_by(user_id=current_user.id).order_by(SyncHistory.timestamp.desc()).all()
        return render_template('sync_history.html', records=records)
    
    # API routes
    @app.route('/api/sync', methods=['POST'])
    @login_required
    def sync_assignments():
        data = request.json
        course_id = data.get('course_id')
        project_id = data.get('project_id')
        
        if not course_id:
            return jsonify({'error': 'Course ID is required'}), 400
        
        try:
            # Get API clients for the current user
            canvas_api_client, todoist_client, sync_service_client = get_api_clients()
            
            tasks = sync_service_client.sync_course_assignments(course_id, project_id)
            # Record sync history
            history = SyncHistory(
                user_id=current_user.id,
                sync_type='canvas_to_todoist',
                source_id=course_id,
                items_count=len(tasks),
                status='success'
            )
            db.session.add(history)
            db.session.commit()
    
            return jsonify({
                'success': True,
                'message': f'Successfully synced {len(tasks)} assignments',
                'tasks': [task.to_dict() for task in tasks]
            })
        except Exception as e:
            # Record failed sync
            history = SyncHistory(
                user_id=current_user.id,
                sync_type='canvas_to_todoist',
                source_id=course_id,
                status='failed'
            )
            db.session.add(history)
            db.session.commit()
    
            return jsonify({'error': str(e)}), 500
        finally:
            # Ensure database connections are properly closed
            db.session.close()
    
    @app.route('/api/sync_todo', methods=['POST'])
    @login_required
    def sync_todo():
        data = request.json
        project_id = data.get('project_id')
        
        try:
            # Get API clients for the current user
            canvas_api_client, todoist_client, sync_service_client = get_api_clients()
            
            tasks = sync_service_client.sync_todo_items(project_id)
            return jsonify({
                'success': True,
                'message': f'Successfully synced {len(tasks)} to-do items',
                'tasks': [task.to_dict() for task in tasks]
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500
        finally:
            # Ensure database connections are properly closed
            db.session.close()
    
    @app.route('/api/refresh_data', methods=['POST'])
    @login_required
    def refresh_data():
        try:
            # Get API clients for the current user
            canvas_api_client, todoist_client, sync_service_client = get_api_clients()
            
            # Get fresh data from Canvas and Todoist
            courses = canvas_api_client.get_courses()
            projects = todoist_client.get_projects()
            
            return jsonify({
                'success': True,
                'courses': courses,
                'projects': projects
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500
        finally:
            # Ensure database connections are properly closed
            db.session.close()
    
    @app.before_request
    def get_apis():
        """Initialize API clients if a user is logged in."""
        if current_user.is_authenticated:
            try:
                g.canvas_api = CanvasAPI(
                    api_url=current_user.canvas_api_url,
                    api_token=current_user.get_canvas_api_token()
                )
                g.todoist_api = TodoistClient(
                    api_token=current_user.get_todoist_api_key()
                )
            except ValueError:
                # If APIs aren't configured yet, set them to None
                g.canvas_api = None
                g.todoist_api = None
    
    @app.route('/sync-now')
    @login_required
    def sync_now():
        """Manual sync triggered by the user."""
        if not current_user.is_premium and current_user.created_at < datetime.utcnow() - timedelta(days=stripe_config.TRIAL_DAYS):
            flash('Your trial period has ended. Please upgrade to continue using sync features.', 'warning')
            return redirect(url_for('pricing'))
        
        try:
            # Create API instances with user's credentials
            canvas_api = CanvasAPI(
                api_url=current_user.canvas_api_url,
                api_token=current_user.get_canvas_api_token()
            )
            todoist_api = TodoistClient(
                api_token=current_user.get_todoist_api_key()
            )
            
            # Use the SyncService to sync assignments
            sync_service = SyncService(canvas_api, todoist_api)
            
            # Get all courses
            courses = canvas_api.get_courses()
            
            # Sync assignments for each course
            for course in courses:
                sync_service.sync_course_assignments(course['id'])
            
            # Record sync history
            history = SyncHistory(
                user_id=current_user.id,
                sync_type='manual_sync',
                source_id='manual',
                items_count=len(courses),
                status='success'
            )
            db.session.add(history)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': f'Successfully synced {len(courses)} assignments',
                'courses': courses  # Canvas API already returns JSON-serializable dictionaries
            })
        except Exception as e:
            # Record failed sync
            history = SyncHistory(
                user_id=current_user.id,
                sync_type='manual_sync',
                source_id='manual',
                status='failed'
            )
            db.session.add(history)
            db.session.commit()
    
            return jsonify({'error': str(e)}), 500
        finally:
            # Ensure database connections are properly closed
            db.session.close()
    
    # Create database tables before first request
    with app.app_context():
        db.create_all()
        
        # Clean up any existing MySQL connections - this helps when redeploying
        try:
            # Force SQLAlchemy to create a fresh connection pool
            db.engine.dispose()
            print("Database connection pool refreshed at startup")
        except Exception as e:
            print(f"Warning: Could not refresh connection pool: {str(e)}")
    
    # Determine the current environment
    def is_pythonanywhere():
        """Check if running on PythonAnywhere"""
        return 'pythonanywhere' in socket.gethostname().lower()
    
    # Only start the scheduler if not running on PythonAnywhere or explicitly in development mode
    if config_name == 'development' or not is_pythonanywhere():
        # Start the scheduler - this is disabled on PythonAnywhere as we use custom_scheduler.py instead
        scheduler.start()
    
    return app

# Only used when running directly with Python
if __name__ == '__main__':
    app = create_app('development')
    app.jinja_env.cache = {}
    app.run()
