"""
Utils package.
Contains utility functions for the application.
"""

import os
import logging
from .encryption import encrypt_data, decrypt_data
from .api import get_api_clients, validate_canvas_url

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

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