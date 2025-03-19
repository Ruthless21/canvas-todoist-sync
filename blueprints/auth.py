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
    # If user is already authenticated, redirect to dashboard
    if current_user.is_authenticated:
        current_app.logger.debug('User already authenticated: %s', current_user.username)
        return redirect(url_for('main.index'))
    
    form = LoginForm()
    
    if form.validate_on_submit():
        current_app.logger.debug('Login form submitted and validated')
        user = User.query.filter_by(username=form.username.data).first()
        
        if user is None or not user.check_password(form.password.data):
            current_app.logger.debug('Login failed: Invalid credentials')
            flash('Invalid username or password', 'danger')
            return redirect(url_for('auth.login'))
        
        # Login user with Flask-Login
        login_success = login_user(user, remember=form.remember_me.data)
        current_app.logger.debug('login_user() result: %s', login_success)
        
        if not login_success:
            current_app.logger.error('Login user failed despite valid credentials')
            flash('Login failed. Please try again.', 'danger')
            return redirect(url_for('auth.login'))
        
        # Update last login time
        user.last_login = datetime.utcnow()
        db.session.commit()
        
        current_app.logger.debug('Current authentication status: %s', current_user.is_authenticated)
        current_app.logger.debug('Session data: %s', dict(session))
        
        # Show success message only if actually logged in
        if current_user.is_authenticated:
            flash('Login successful!', 'success')
            
            # Redirect to the home page
            current_app.logger.debug('Redirecting to index page after successful login')
            return redirect(url_for('main.index'))
        else:
            # This should not normally happen, but handle it just in case
            current_app.logger.error('User not authenticated after successful login_user()')
            flash('Login failed. Please try again.', 'danger')
            return redirect(url_for('auth.login'))
        
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
    
    # No need to explicitly delete cookies - already handled by session.clear() and logout_user()
    
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
    
    # Use Flask redirect function - simplify to use only one approach
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