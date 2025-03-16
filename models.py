from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import datetime

db = SQLAlchemy()

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    canvas_api_url = db.Column(db.String(256))
    canvas_api_token = db.Column(db.String(256))
    todoist_api_key = db.Column(db.String(256))
    is_premium = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password, method='pbkdf2:sha256')
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.username}>'
    
class SyncHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    sync_type = db.Column(db.String(50))  # 'canvas_to_todoist' or 'todoist_to_canvas'
    source_id = db.Column(db.String(50))  # Course ID or Project ID
    items_count = db.Column(db.Integer, default=0)
    status = db.Column(db.String(20), default='success')  # 'success' or 'failed'
    
    user = db.relationship('User', backref=db.backref('sync_history', lazy=True))

class SyncSettings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    enabled = db.Column(db.Boolean, default=False)
    frequency = db.Column(db.String(20), default='daily')  # hourly, daily, weekly
    last_sync = db.Column(db.DateTime, nullable=True)
    
    user = db.relationship('User', backref=db.backref('sync_settings', lazy=True))
    
    def __repr__(self):
        return f'<SyncSettings user_id={self.user_id}, enabled={self.enabled}, frequency={self.frequency}>'

class Subscription(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    stripe_customer_id = db.Column(db.String(255), nullable=True)
    stripe_subscription_id = db.Column(db.String(255), nullable=True)
    stripe_price_id = db.Column(db.String(255), nullable=True)
    stripe_checkout_session_id = db.Column(db.String(255), nullable=True)
    status = db.Column(db.String(50), default='inactive')  # active, past_due, canceled, trialing, unpaid
    current_period_start = db.Column(db.DateTime, nullable=True)
    current_period_end = db.Column(db.DateTime, nullable=True)
    cancel_at_period_end = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    user = db.relationship('User', backref=db.backref('subscriptions', lazy=True))
    
    def __repr__(self):
        return f'<Subscription user_id={self.user_id}, status={self.status}>'

