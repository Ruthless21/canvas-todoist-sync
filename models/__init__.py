"""
Models package.
Contains all database models for the application.
"""

from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from extensions import db, login_manager
from utils import encrypt_data, decrypt_data

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
    
    def set_password(self, password):
        """Set user password."""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check user password."""
        return check_password_hash(self.password_hash, password)
    
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

@login_manager.user_loader
def load_user(id):
    """Load user for Flask-Login."""
    return User.query.get(int(id)) 