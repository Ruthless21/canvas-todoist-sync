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
        
        # Flash success message
        flash('Login successful!', 'success')
        
        next_page = request.args.get('next')
        current_app.logger.debug('Next page after login: %s', next_page)
        
        # Ensure we have a valid redirect destination
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('dashboard.index')
            current_app.logger.debug('No next page specified, redirecting to dashboard: %s', next_page)
        
        # Log successful login and session info
        current_app.logger.info('User %s logged in successfully', user.username)
        current_app.logger.debug('Session after login: %s', dict(session))
        current_app.logger.debug('Remember cookie set: %s', form.remember_me.data)
        
        # Force a session save before redirecting
        session.modified = True
        
        # Return a proper redirect response
        response = redirect(next_page)
        current_app.logger.debug('Redirecting to: %s', next_page)
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