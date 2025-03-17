"""
Utils package.
Contains utility functions for the application.
"""

import os
import logging
from cryptography.fernet import Fernet
from config import Config
from models import User
from services.canvas_api import CanvasAPI
from services.todoist_api import TodoistAPI

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize encryption
fernet = Fernet(Config.SECRET_KEY.encode())

def encrypt_data(data):
    """Encrypt sensitive data."""
    if not data:
        return None
    try:
        return fernet.encrypt(data.encode()).decode()
    except Exception as e:
        logger.error(f"Error encrypting data: {str(e)}")
        return None

def decrypt_data(encrypted_data):
    """Decrypt sensitive data."""
    if not encrypted_data:
        return None
    try:
        return fernet.decrypt(encrypted_data.encode()).decode()
    except Exception as e:
        logger.error(f"Error decrypting data: {str(e)}")
        return None

def get_api_clients(user):
    """Get Canvas and Todoist API clients for a user."""
    if not user:
        return None, None
    
    try:
        canvas_client = None
        todoist_client = None
        
        # Initialize Canvas client
        if user.canvas_api_url and user.get_canvas_token():
            canvas_client = CanvasAPI(
                api_url=user.canvas_api_url,
                api_token=user.get_canvas_token()
            )
        
        # Initialize Todoist client
        if user.get_todoist_token():
            todoist_client = TodoistAPI(
                api_token=user.get_todoist_token()
            )
        
        return canvas_client, todoist_client
    except Exception as e:
        logger.error(f"Error initializing API clients: {str(e)}")
        return None, None

def validate_canvas_url(url):
    """Validate Canvas API URL format."""
    if not url:
        return False
    
    # Remove trailing slashes
    url = url.rstrip('/')
    
    # Check if URL ends with /api/v1
    if not url.endswith('/api/v1'):
        url = f"{url}/api/v1"
    
    try:
        # Test URL format
        canvas_client = CanvasAPI(api_url=url, api_token='test')
        return True
    except Exception:
        return False

def format_datetime(dt):
    """Format datetime for display."""
    if not dt:
        return None
    return dt.strftime('%Y-%m-%d %H:%M:%S')

def get_file_size(file_path):
    """Get file size in human-readable format."""
    try:
        size = os.path.getsize(file_path)
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.2f} {unit}"
            size /= 1024
        return f"{size:.2f} TB"
    except Exception:
        return "Unknown" 