"""
Main blueprint.
Handles the main landing page and other general routes.
"""

from flask import render_template, flash, redirect, url_for, current_app
from flask_login import current_user, login_required
from blueprints import main_bp

@main_bp.route('/')
def index():
    """Display the home page with login status."""
    # Log authentication status
    current_app.logger.debug('Main index accessed, user authenticated: %s', current_user.is_authenticated)
    
    # For logged in users, display a status message
    if current_user.is_authenticated:
        flash(f'You are logged in as {current_user.username}', 'success')
        
    return render_template('index.html', title='Home')

@main_bp.route('/dashboard-redirect')
@login_required
def dashboard_redirect():
    """Simple redirect to dashboard for testing."""
    return redirect(url_for('dashboard.index')) 