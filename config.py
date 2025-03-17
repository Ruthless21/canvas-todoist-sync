"""
Configuration file.
Contains environment-specific settings for the application.
"""

import os
from dotenv import load_dotenv
from datetime import timedelta

# Load environment variables from .env file
load_dotenv()

class Config:
    """Base configuration class."""
    # Flask configuration
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-key-please-change-in-production'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///app.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Flask-Caching configuration
    CACHE_TYPE = 'SimpleCache'
    CACHE_DEFAULT_TIMEOUT = 300
    
    # Flask-APScheduler configuration
    SCHEDULER_API_ENABLED = False
    
    # Session configuration
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    
    # Security configuration
    SESSION_COOKIE_SECURE = os.environ.get('FLASK_ENV') == 'production'
    REMEMBER_COOKIE_SECURE = os.environ.get('FLASK_ENV') == 'production'
    SESSION_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_HTTPONLY = True
    
    # Stripe configuration
    STRIPE_PUBLISHABLE_KEY = os.environ.get('STRIPE_PUBLISHABLE_KEY')
    STRIPE_SECRET_KEY = os.environ.get('STRIPE_SECRET_KEY')
    STRIPE_WEBHOOK_SECRET = os.environ.get('STRIPE_WEBHOOK_SECRET')
    STRIPE_PRODUCT_ID = os.environ.get('STRIPE_PRODUCT_ID')
    STRIPE_MONTHLY_PRICE_ID = os.environ.get('STRIPE_MONTHLY_PRICE_ID')
    STRIPE_YEARLY_PRICE_ID = os.environ.get('STRIPE_YEARLY_PRICE_ID')
    
    # Domain configuration
    DOMAIN = os.environ.get('DOMAIN') or 'localhost:5000'
    
    # Subscription pricing
    MONTHLY_PRICE = 9.99
    YEARLY_PRICE = 99.99
    TRIAL_DAYS = 14

class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    SQLALCHEMY_ECHO = True
    SESSION_COOKIE_SECURE = False
    REMEMBER_COOKIE_SECURE = False
    
class TestingConfig(Config):
    """Testing configuration."""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
    SESSION_COOKIE_SECURE = False
    REMEMBER_COOKIE_SECURE = False
    
class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    SQLALCHEMY_ECHO = False
    # Set up for HTTPS
    SESSION_COOKIE_SECURE = True
    REMEMBER_COOKIE_SECURE = True
    # Use more sophisticated caching if Redis is available
    CACHE_TYPE = os.environ.get('CACHE_TYPE') or 'simple'
    # Additional cache config
    CACHE_DEFAULT_TIMEOUT = 600  # longer timeout for production

class PythonAnywhereConfig(Config):
    """PythonAnywhere-specific production configuration."""
    DEBUG = False
    SQLALCHEMY_ECHO = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_recycle': 240,  # Less than PythonAnywhere's 300s timeout
        'pool_pre_ping': True,  # Test connections before using them
        'pool_timeout': 30,    # Don't wait too long for connections
        'pool_size': 10,       # Default pool size
        'max_overflow': 5      # Allow some extra connections
    }
    # Use FileSystemCache for better performance than SimpleCache without Redis
    CACHE_TYPE = 'FileSystemCache'
    CACHE_DIR = os.environ.get('CACHE_DIR') or '/tmp/canvas_todoist_cache'
    CACHE_THRESHOLD = 500  # Maximum number of items the cache will store
    CACHE_DEFAULT_TIMEOUT = 900  # 15 minutes
    
    # MySQL configuration for PythonAnywhere
    # Format: mysql://<username>:<password>@<username>.mysql.pythonanywhere-services.com/<dbname>
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///canvas_todoist.db'
    # Use smaller VARCHAR lengths for MySQL compatibility with specific charsets
    MYSQL_INDEXES_MAX_LENGTH = 191  # For utf8mb4 compatibility
    
    # Session and cookie settings
    SESSION_COOKIE_SECURE = False  # Temporarily disable for debugging
    REMEMBER_COOKIE_SECURE = False  # Temporarily disable for debugging
    SESSION_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_HTTPONLY = True

# Configuration dictionary for easy access
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'pythonanywhere': PythonAnywhereConfig,
    'default': DevelopmentConfig
}