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
from sqlalchemy import func

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
        
        # Convert username to lowercase for case-insensitive comparison
        username_lower = form.username.data.lower()
        current_app.logger.debug('Attempting login with username (converted to lowercase): %s', username_lower)
        
        # Try to find the user with case-insensitive search
        user = User.query.filter(func.lower(User.username) == username_lower).first()
        
        if user is None:
            current_app.logger.debug('Login failed: User not found')
            flash('Invalid username or password', 'danger')
            return redirect(url_for('auth.login'))
            
        if not user.check_password(form.password.data):
            current_app.logger.debug('Login failed: Incorrect password for user: %s', user.username)
            
            # Add detailed debugging for password validation
            current_app.logger.debug('Password debug info:')
            current_app.logger.debug('- Input password length: %s', len(form.password.data))
            current_app.logger.debug('- First/last chars: %s...%s', 
                                 form.password.data[:1] if form.password.data else '', 
                                 form.password.data[-1:] if form.password.data else '')
            
            # Check if there are any non-ascii characters
            has_non_ascii = any(ord(c) > 127 for c in form.password.data)
            current_app.logger.debug('- Contains non-ASCII chars: %s', has_non_ascii)
            
            # Check for leading/trailing whitespace
            has_leading_whitespace = form.password.data.startswith(' ')
            has_trailing_whitespace = form.password.data.endswith(' ')
            current_app.logger.debug('- Has leading/trailing whitespace: %s/%s', 
                                 has_leading_whitespace, has_trailing_whitespace)
            
            # Get password hash info (safely)
            if user.password_hash:
                hash_len = len(user.password_hash)
                hash_start = user.password_hash[:10] if hash_len > 10 else ''
                current_app.logger.debug('- Stored hash length: %s, starts with: %s...', 
                                     hash_len, hash_start)
                
                # TEMPORARY TESTING CODE - Only for debugging
                if current_app.config.get('DEBUG', False) and form.password.data == 'debug_master_override':
                    current_app.logger.warning('Using debug override - REMOVE THIS IN PRODUCTION')
                    
                    # Simulate a successful login for debugging
                    try:
                        login_success = login_user(user)
                        current_app.logger.debug('Debug override login result: %s', login_success)
                        if login_success:
                            user.last_login = datetime.utcnow()
                            db.session.commit()
                            flash('Login successful (DEBUG MODE)!', 'success')
                            return redirect(url_for('main.index'))
                    except Exception as e:
                        current_app.logger.error('Error in debug login: %s', str(e))
            else:
                current_app.logger.debug('- No password hash stored!')
                
            flash('Invalid username or password', 'danger')
            return redirect(url_for('auth.login'))
        
        # Check if user is active - temporarily disabled
        """
        if not user.is_active:
            current_app.logger.error('Login failed: User account is inactive')
            # Add SQL update for testing to reactivate account
            user.account_active = True
            db.session.commit()
            current_app.logger.info('Reactivated user account for %s', user.username)
            # Proceed with login attempt without redirecting
            # flash('Your account is inactive. Please contact support.', 'danger')
            # return redirect(url_for('auth.login'))
        """
        
        # Log important user attributes
        current_app.logger.debug('User attempting login: ID=%s, Username=%s, Active=%s', 
                             user.id, user.username, user.is_active)
        
        # Make sure Flask-Login's session management is using the right cookie name
        # These should match config settings
        current_app.logger.debug('Session cookie name: %s', current_app.config.get('SESSION_COOKIE_NAME'))
        current_app.logger.debug('Remember cookie name: %s', current_app.config.get('REMEMBER_COOKIE_NAME', 'remember_token'))
        
        # Try to get the secret key - don't log the actual key, just check if it exists
        current_app.logger.debug('Secret key exists: %s', bool(current_app.config.get('SECRET_KEY')))
        
        # Make sure the session is ready for login
        session.permanent = True
        
        # Login user with Flask-Login
        try:
            login_success = login_user(user, remember=form.remember_me.data)
            current_app.logger.debug('login_user() result: %s', login_success)
            
            # Check for flask_login messages in session
            current_app.logger.debug('Session after login: %s', dict(session))
            
            if not login_success:
                current_app.logger.error('Login user failed despite valid credentials')
                flash('Login failed. Please try again.', 'danger')
                return redirect(url_for('auth.login'))
            
            # Update last login time
            user.last_login = datetime.utcnow()
            db.session.commit()
            
            # Explicitly check if user was added to session by Flask-Login
            if '_user_id' in session:
                current_app.logger.debug('User ID in session: %s', session.get('_user_id'))
            else:
                current_app.logger.error('Flask-Login did not add _user_id to session')
                
            # Force Flask-Login to set cookies correctly
            if hasattr(current_app, 'login_manager'):
                current_app.logger.debug('Login manager exists')
            
            current_app.logger.debug('Current authentication status: %s', current_user.is_authenticated)
        except Exception as e:
            current_app.logger.exception('Exception during login_user(): %s', str(e))
            flash('An error occurred during login. Please try again.', 'danger')
            return redirect(url_for('auth.login'))
        
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
        # Log registration attempt
        current_app.logger.debug('Registration form submitted and validated')
        current_app.logger.debug('Registering new user with username: %s, email: %s', 
                             form.username.data, form.email.data)
        
        # Log password details (safely)
        current_app.logger.debug('Password info:')
        current_app.logger.debug('- Length: %d', len(form.password.data))
        current_app.logger.debug('- First/last chars: %s...%s', 
                             form.password.data[:1] if form.password.data else '',
                             form.password.data[-1:] if form.password.data else '')
        current_app.logger.debug('- Contains non-ASCII: %s', 
                             any(ord(c) > 127 for c in form.password.data))
        current_app.logger.debug('- Has whitespace: %s', 
                             any(c.isspace() for c in form.password.data))
        
        # Create user with preserved username display but normalized internal representation
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        
        try:
            db.session.add(user)
            db.session.commit()
            current_app.logger.debug('User registered successfully: %s (ID: %s)', user.username, user.id)
            flash('Congratulations, you are now a registered user!', 'success')
            
            # Add helpful login instructions
            flash('Please login with your username and password', 'info')
            return redirect(url_for('auth.login'))
        except Exception as e:
            db.session.rollback()
            current_app.logger.error('Registration failed: %s', str(e))
            flash('Registration failed. Please try again.', 'danger')
    
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