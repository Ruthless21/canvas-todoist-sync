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
    
    if current_user.is_authenticated:
        current_app.logger.debug('User already authenticated, redirecting to dashboard')
        return redirect(url_for('dashboard.index'))
    
    form = LoginForm()
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
        
        # Set session permanent to use PERMANENT_SESSION_LIFETIME
        session.permanent = True
        login_user(user, remember=form.remember_me.data)
        
        # Update last login time
        user.last_login = datetime.utcnow()
        db.session.commit()
        
        next_page = request.args.get('next')
        current_app.logger.debug('Next page after login: %s', next_page)
        
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('dashboard.index')
        
        # Log successful login and session info
        current_app.logger.info('User %s logged in successfully', user.username)
        current_app.logger.debug('Session after login: %s', dict(session))
        current_app.logger.debug('Remember cookie set: %s', form.remember_me.data)
        return redirect(next_page)
    
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
    logout_user()
    return redirect(url_for('main.index'))

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