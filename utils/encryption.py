"""
Encryption utilities for the application.
"""

import logging
from cryptography.fernet import Fernet
from config import Config

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