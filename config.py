import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Base configuration class."""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'hard-to-guess-secret-key'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///canvas_todoist.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Flask-Caching configuration
    CACHE_TYPE = os.environ.get('CACHE_TYPE') or 'simple'
    CACHE_DEFAULT_TIMEOUT = 300
    
    # Flask-APScheduler configuration
    SCHEDULER_API_ENABLED = False

class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    
class TestingConfig(Config):
    """Testing configuration."""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
    
class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    # Set up for HTTPS
    SESSION_COOKIE_SECURE = True
    REMEMBER_COOKIE_SECURE = True
    # Use more sophisticated caching if Redis is available
    CACHE_TYPE = os.environ.get('CACHE_TYPE') or 'simple'
    # Additional cache config
    CACHE_DEFAULT_TIMEOUT = 600  # longer timeout for production

class PythonAnywhereConfig(ProductionConfig):
    """PythonAnywhere-specific production configuration."""
    # Use FileSystemCache for better performance than SimpleCache without Redis
    CACHE_TYPE = 'FileSystemCache'
    CACHE_DIR = os.environ.get('CACHE_DIR') or '/tmp/canvas_todoist_cache'
    CACHE_THRESHOLD = 500  # Maximum number of items the cache will store
    CACHE_DEFAULT_TIMEOUT = 900  # 15 minutes

# Configuration dictionary for easy access
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'pythonanywhere': PythonAnywhereConfig,
    'default': DevelopmentConfig
}