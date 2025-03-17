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
    # If user is already logged in, redirect to main page
    if current_user.is_authenticated:
        current_app.logger.debug('User already authenticated: %s', current_user.username)
        return redirect(url_for('main.index'))
    
    form = LoginForm()
    
    if form.validate_on_submit():
        # Get the user from database
        user = User.query.filter_by(username=form.username.data).first()
        
        # Check user exists and password is correct
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password', 'danger')
            return render_template('login.html', title='Sign In', form=form)
        
        # Clear existing session data to avoid conflicts
        session.clear()
        
        # Set session to be permanent (according to PERMANENT_SESSION_LIFETIME)
        session.permanent = True
        
        # Log the user in
        login_success = login_user(user, remember=form.remember_me.data)
        current_app.logger.debug('Login_user result: %s', login_success)
        
        # Store important session vars directly (belt and suspenders approach)
        session['user_id'] = user.id
        session['_user_id'] = user.id  # Flask-Login key
        
        # Update last login time
        user.last_login = datetime.utcnow()
        db.session.commit()
        
        # Create success message
        flash('Login successful!', 'success')
        
        # Force a session save
        session.modified = True
        
        current_app.logger.debug('User authenticated as: %s', current_user.is_authenticated)
        current_app.logger.debug('Session contains: %s', dict(session))
        
        # Simply redirect to main page first
        return redirect(url_for('main.index'))
    
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