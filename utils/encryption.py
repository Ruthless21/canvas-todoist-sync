"""
Encryption utilities for the application.
"""

import base64
import hashlib
import logging
from cryptography.fernet import Fernet
from config import Config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_fernet_key(secret_key):
    """
    Generate a valid Fernet key from any string.
    Creates a 32-byte url-safe base64-encoded key using SHA-256 hash.
    """
    if not secret_key:
        raise ValueError("Secret key cannot be empty")
    
    # Use SHA-256 to get a consistent 32 bytes from the secret key
    key_bytes = hashlib.sha256(secret_key.encode()).digest()
    # Encode to base64 format that Fernet requires
    encoded_key = base64.urlsafe_b64encode(key_bytes)
    return encoded_key

# Initialize encryption
try:
    fernet = Fernet(get_fernet_key(Config.SECRET_KEY))
    logger.info("Encryption initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize encryption: {e}")
    # Use a dummy Fernet key for development only
    # In production, this should raise an exception to prevent running with insecure keys
    fernet = Fernet(Fernet.generate_key())
    logger.warning("Using fallback encryption key - NOT SUITABLE FOR PRODUCTION")

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