"""
Models package.
Contains all database models for the application.
"""

from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from extensions import db, login_manager
from utils.encryption import encrypt_data, decrypt_data

class User(UserMixin, db.Model):
    """User model."""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    is_admin = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    # API Credentials
    canvas_api_url = db.Column(db.String(256))
    canvas_token_encrypted = db.Column(db.String(256))
    todoist_token_encrypted = db.Column(db.String(256))
    
    # Subscription
    subscription_status = db.Column(db.String(20), default='inactive')
    stripe_customer_id = db.Column(db.String(64))
    stripe_subscription_id = db.Column(db.String(64))
    subscription_start = db.Column(db.DateTime)
    subscription_end = db.Column(db.DateTime)
    
    # Sync Settings
    last_sync = db.Column(db.DateTime)
    sync_preferences = db.Column(db.String(20), default='auto')
    notification_preferences = db.Column(db.String(20), default='all')
    
    # Explicitly define Flask-Login properties
    @property
    def is_authenticated(self):
        """Return True if the user is authenticated."""
        return True
    
    @property
    def is_active(self):
        """Return True to allow all users to login for now."""
        return True
    
    def get_id(self):
        """Return the user ID as a string."""
        return str(self.id)
    
    def set_password(self, password):
        """Set user password."""
        from flask import current_app
        if hasattr(current_app, 'logger'):
            current_app.logger.debug('Setting password for user %s', self.username)
            current_app.logger.debug('Password length: %d', len(password))
            
            # Check for problematic characters
            non_ascii = any(ord(c) > 127 for c in password)
            whitespace = any(c.isspace() for c in password)
            current_app.logger.debug('Password contains non-ASCII: %s, whitespace: %s', 
                                 non_ascii, whitespace)
        
        # Use default algorithm (scrypt) for consistency with existing accounts
        self.password_hash = generate_password_hash(password)
        
        if hasattr(current_app, 'logger'):
            current_app.logger.debug('Generated hash length: %d, starts with: %s...', 
                                 len(self.password_hash), self.password_hash[:10])
    
    def check_password(self, password):
        """Check user password."""
        from flask import current_app
        if hasattr(current_app, 'logger'):
            current_app.logger.debug('Checking password for user %s', self.username)
            current_app.logger.debug('Password length: %d', len(password))
            current_app.logger.debug('Stored hash length: %d, starts with: %s...', 
                                 len(self.password_hash) if self.password_hash else 0, 
                                 self.password_hash[:10] if self.password_hash else '')
        
        # DEBUGGING: Try both ways of checking the password
        normal_result = check_password_hash(self.password_hash, password)
        
        # This is for debugging only - never store or compare plaintext passwords in production
        from flask import current_app
        if hasattr(current_app, 'config') and current_app.config.get('DEBUG', False):
            try:
                from utils.encryption import encrypt_data, decrypt_data
                # Try a workaround for debugging only
                from werkzeug.security import generate_password_hash
                test_hash = generate_password_hash(password)
                current_app.logger.debug('Test hash for input: %s', test_hash[:10])
                
                # Store password temporarily for debugging - DELETE THIS AFTER FIXING THE ISSUE
                if not hasattr(self, '_temp_pwd'):
                    self._temp_pwd = encrypt_data(password)
                    current_app.logger.debug('Storing temporary debug password reference')
                    db.session.commit()
                else:
                    stored_pwd = decrypt_data(self._temp_pwd)
                    match = stored_pwd == password
                    current_app.logger.debug('Direct compare (TEMPORARY DEBUG ONLY): %s', match)
            except Exception as e:
                current_app.logger.error('Error in debug password check: %s', str(e))
        
        if hasattr(current_app, 'logger'):
            current_app.logger.debug('Password check result: %s', normal_result)
        
        return normal_result
    
    def set_canvas_token(self, token):
        """Set encrypted Canvas API token."""
        self.canvas_token_encrypted = encrypt_data(token)
    
    def get_canvas_token(self):
        """Get decrypted Canvas API token."""
        if self.canvas_token_encrypted:
            return decrypt_data(self.canvas_token_encrypted)
        return None
    
    def set_todoist_token(self, token):
        """Set encrypted Todoist API token."""
        self.todoist_token_encrypted = encrypt_data(token)
    
    def get_todoist_token(self):
        """Get decrypted Todoist API token."""
        if self.todoist_token_encrypted:
            return decrypt_data(self.todoist_token_encrypted)
        return None
    
    def delete_all_data(self):
        """Delete all user data."""
        # Clear API credentials
        self.canvas_api_url = None
        self.canvas_token_encrypted = None
        self.todoist_token_encrypted = None
        
        # Clear subscription data
        self.subscription_status = 'inactive'
        self.stripe_customer_id = None
        self.stripe_subscription_id = None
        self.subscription_start = None
        self.subscription_end = None
        
        # Clear sync data
        self.last_sync = None
        self.sync_preferences = 'auto'
        self.notification_preferences = 'all'
        
        db.session.commit()

class SyncSettings(db.Model):
    """Model for storing sync settings."""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    sync_frequency = db.Column(db.String(20), default='daily')
    sync_time = db.Column(db.String(5), default='00:00')
    last_sync = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref=db.backref('sync_settings', uselist=False))

class SyncHistory(db.Model):
    """Model for storing sync history."""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    sync_type = db.Column(db.String(20), nullable=False)  # 'canvas_to_todoist' or 'todoist_to_canvas'
    status = db.Column(db.String(20), nullable=False)  # 'success' or 'failed'
    items_synced = db.Column(db.Integer, default=0)
    source_id = db.Column(db.String(50), nullable=True)  # Canvas course ID
    destination_id = db.Column(db.String(50), nullable=True)  # Todoist project ID
    details = db.Column(db.Text, nullable=True)  # JSON data with additional details
    error_message = db.Column(db.Text)
    started_at = db.Column(db.DateTime, nullable=False)
    completed_at = db.Column(db.DateTime)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref=db.backref('sync_history', lazy='dynamic'))

class Subscription(db.Model):
    """Model for storing subscription information."""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    stripe_subscription_id = db.Column(db.String(100), unique=True)
    stripe_customer_id = db.Column(db.String(100))
    status = db.Column(db.String(20), default='inactive')  # 'active', 'inactive', 'canceled', 'trial'
    plan_id = db.Column(db.String(100))
    plan_name = db.Column(db.String(50))
    price_id = db.Column(db.String(100))
    price_amount = db.Column(db.Integer)  # in cents
    billing_cycle = db.Column(db.String(20))  # 'monthly', 'yearly'
    start_date = db.Column(db.DateTime)
    end_date = db.Column(db.DateTime)
    trial_end = db.Column(db.DateTime)
    cancel_at_period_end = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref=db.backref('subscriptions', lazy='dynamic'))

@login_manager.user_loader
def load_user(id):
    """Load user for Flask-Login."""
    return User.query.get(int(id)) 