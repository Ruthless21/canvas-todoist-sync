import base64
import os
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from dotenv import load_dotenv

load_dotenv()

def get_encryption_key():
    """
    Get or generate an encryption key based on the SECRET_KEY environment variable
    """
    secret_key = os.environ.get('SECRET_KEY', 'hard-to-guess-secret-key')
    salt = b'canvas_todoist_salt'  # Fixed salt for deterministic key generation
    
    # Generate a key using PBKDF2HMAC
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
    )
    
    # Use the app's secret key to derive the encryption key
    key = base64.urlsafe_b64encode(kdf.derive(secret_key.encode()))
    return key

def encrypt_data(data):
    """
    Encrypt sensitive data for storage
    """
    if not data:
        return None
        
    key = get_encryption_key()
    f = Fernet(key)
    return f.encrypt(data.encode()).decode()

def decrypt_data(encrypted_data):
    """
    Decrypt sensitive data from storage
    """
    if not encrypted_data:
        return None
        
    key = get_encryption_key()
    f = Fernet(key)
    try:
        return f.decrypt(encrypted_data.encode()).decode()
    except Exception as e:
        print(f"Error decrypting data: {e}")
        return None 