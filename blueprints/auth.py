"""
Authentication blueprint.
Handles user login, registration, and logout functionality.
"""

from flask import render_template, redirect, url_for, flash, request, session, current_app
from flask_login import login_user, logout_user, login_required, current_user
from urllib.parse import urlparse
from blueprints import auth_bp
from forms import LoginForm, RegistrationForm
from models import User, db
from datetime import datetime

def url_parse(url):
    """Parse URL for security checks."""
    return urlparse(url)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Handle user login."""
    current_app.logger.debug('Login route accessed with method: %s', request.method)
    current_app.logger.debug('Request form data: %s', request.form.to_dict())
    current_app.logger.debug('Request headers: %s', dict(request.headers))
    current_app.logger.debug('Cookies: %s', request.cookies)
    
    # If user is already logged in, redirect to dashboard
    if current_user.is_authenticated:
        current_app.logger.debug('User already authenticated, redirecting to dashboard')
        return redirect(url_for('dashboard.index'))
    
    form = LoginForm()
    current_app.logger.debug('Form CSRF token: %s', form.csrf_token.current_token)
    current_app.logger.debug('Session CSRF token: %s', session.get('csrf_token'))
    
    if request.method == 'POST':
        current_app.logger.debug('Processing POST request')
        current_app.logger.debug('Form data before validation: %s', {field.name: field.data for field in form})
        
        # Log CSRF token information for debugging
        current_app.logger.debug('Form CSRF token value: %s', form.csrf_token.data)
        current_app.logger.debug('Session CSRF token: %s', session.get('csrf_token'))
        
        current_app.logger.debug('Form validation status: %s', form.validate())
        current_app.logger.debug('Form errors: %s', form.errors)
    
    if form.validate_on_submit():
        current_app.logger.debug('Login form submitted and validated')
        user = User.query.filter_by(username=form.username.data).first()
        
        if user is None:
            current_app.logger.debug('Login failed: User not found - %s', form.username.data)
            flash('Invalid username or password', 'danger')
            return redirect(url_for('auth.login'))
            
        if not user.check_password(form.password.data):
            current_app.logger.debug('Login failed: Invalid password for user - %s', user.username)
            flash('Invalid username or password', 'danger')
            return redirect(url_for('auth.login'))
        
        # Clear session first to avoid issues with existing sessions
        session.clear()
        
        # Set session permanent to use PERMANENT_SESSION_LIFETIME
        session.permanent = True
        
        # Login user
        login_user(user, remember=form.remember_me.data)
        
        # Update last login time
        user.last_login = datetime.utcnow()
        db.session.commit()
        
        # For debugging - set these even though Flask-Login handles them
        session['user_id'] = user.id
        session['username'] = user.username
        session['is_authenticated'] = True
        
        current_app.logger.debug('Updated session data: %s', dict(session))
        current_app.logger.debug('Current user after login: %s', current_user)
        
        # Force session saving
        session.modified = True
        
        # Choose different redirect methods based on what might work
        
        # Try a reliable redirect method - HTML meta refresh
        next_page = request.args.get('next')
        current_app.logger.debug('Next page parameter: %s', next_page)
        
        # Validate next_page to avoid open redirect vulnerabilities
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('dashboard.index')
        
        # Add a flash message for the next request
        flash('Login successful!', 'success')
        
        current_app.logger.debug('Using HTML meta redirect to: %s', next_page)
        current_app.logger.info('User %s logged in successfully - using HTML meta redirect to %s', user.username, next_page)
        
        # Create HTML with meta refresh for reliable browser redirect
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Redirecting...</title>
            <meta http-equiv="refresh" content="0;url={next_page}">
            <script>window.location.href = "{next_page}";</script>
        </head>
        <body>
            <p>Login successful! Redirecting to <a href="{next_page}">dashboard</a>...</p>
        </body>
        </html>
        """
        
        response = current_app.response_class(
            response=html_content,
            status=200,
            mimetype='text/html'
        )
        
        # Log the response
        current_app.logger.debug('Created HTML meta redirect response')
        
        return response
    
    # Log form errors if any
    if form.errors:
        current_app.logger.warning('Login form errors: %s', form.errors)
    
    # Log the CSRF token status
    current_app.logger.debug('CSRF Token present: %s', 'csrf_token' in session)
    return render_template('login.html', title='Sign In', form=form)

@auth_bp.route('/logout')
@login_required
def logout():
    """Handle user logout."""
    current_app.logger.debug('Logout route accessed by user: %s', current_user.username)
    
    # Store username for logging after logout
    username = current_user.username if current_user.is_authenticated else "Unknown"
    
    # Log the user out
    logout_user()
    
    # Clear the session
    session.clear()
    
    # Flash message for user feedback
    flash('You have been logged out successfully.', 'info')
    
    current_app.logger.info('User %s logged out successfully', username)
    
    # Create response with redirect
    response = redirect(url_for('main.index'))
    
    # Clear the session cookie (in case Flask-Login's logout_user didn't)
    response.delete_cookie('session')
    
    # Also clear any other cookies that might exist from previous configurations
    response.delete_cookie('canvas_todoist_session')
    
    return response

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Handle user registration."""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('register.html', title='Register', form=form)

@auth_bp.route('/test-redirect')
def test_redirect():
    """Test route to diagnose redirect issues."""
    current_app.logger.debug('Test redirect route accessed')
    
    # Use different redirect methods to see which one works
    
    # Method 1: Flask redirect function
    current_app.logger.debug('Using Flask redirect function')
    return redirect(url_for('dashboard.index'))
    
    # Method 2: Direct response
    # current_app.logger.debug('Using direct response with 302')
    # return current_app.response_class(
    #     response=None,
    #     status=302,
    #     headers={'Location': url_for('dashboard.index')}
    # )
    
    # Method 3: HTML meta redirect (fallback)
    # current_app.logger.debug('Using HTML meta redirect')
    # dashboard_url = url_for('dashboard.index')
    # return f"""
    # <!DOCTYPE html>
    # <html>
    # <head>
    #     <meta http-equiv="refresh" content="0;url={dashboard_url}">
    # </head>
    # <body>
    #     <p>Redirecting to <a href="{dashboard_url}">dashboard</a>...</p>
    # </body>
    # </html>
    # """ 