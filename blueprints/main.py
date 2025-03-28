"""
Main blueprint.
Handles the main landing page and other general routes.
"""

from flask import render_template, flash, redirect, url_for, current_app, session
from flask_login import current_user, login_required
from blueprints import main_bp
from models import User
from flask_login import login_user

@main_bp.route('/')
def index():
    """Display the home page with login status."""
    from models import User
    from flask_login import login_user
    
    # Log authentication status
    current_app.logger.debug('Main index accessed, user authenticated: %s', current_user.is_authenticated)
    current_app.logger.debug('Session contains: %s', dict(session))
    
    # Check if we need to recover the user authentication
    if not current_user.is_authenticated and 'user_id' in session:
        user_id = session.get('user_id')
        current_app.logger.debug('Session has user_id but user not authenticated, restoring user: %s', user_id)
        
        try:
            # Try to recover user authentication
            user = User.query.get(int(user_id))
            if user:
                login_success = login_user(user)
                current_app.logger.debug('Login recovery result: %s', login_success)
                
                # Ensure both session keys are set
                session['user_id'] = user.id
                session['_user_id'] = user.id
                session.modified = True
                
                if login_success:
                    current_app.logger.debug('Recovered authentication for user: %s', user.username)
                else:
                    current_app.logger.warning('Failed to recover authentication for user: %s', user.username)
        except Exception as e:
            current_app.logger.error('Error recovering authentication: %s', str(e))
    
    # For logged in users, display a status message
    if current_user.is_authenticated:
        current_app.logger.debug('User is authenticated: %s', current_user.username)
        flash(f'You are logged in as {current_user.username}', 'success')
    else:
        current_app.logger.debug('User is not authenticated')
        
    return render_template('index.html', title='Home')

@main_bp.route('/dashboard-redirect')
@login_required
def dashboard_redirect():
    """Simple redirect to dashboard for testing."""
    return redirect(url_for('dashboard.index')) 