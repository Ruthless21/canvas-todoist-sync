"""
API client utilities for the application.
"""

import logging
from services.canvas_api import CanvasAPI
from services.todoist_api import TodoistClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

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
            todoist_client = TodoistClient(
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