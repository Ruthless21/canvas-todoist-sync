"""
PythonAnywhere WSGI entry point.
This is a dedicated WSGI file for PythonAnywhere that guarantees the pythonanywhere configuration is used.
"""

import os
import sys
import socket
from dotenv import load_dotenv

# Add the project directory to the Python path
path = os.path.dirname(os.path.abspath(__file__))
if path not in sys.path:
    sys.path.append(path)

# Override hostname to ensure correct configuration detection
original_gethostname = socket.gethostname
socket.gethostname = lambda: 'pythonanywhere.com'

# Load environment variables
load_dotenv()

# Ensure DATABASE_URL is set correctly for PythonAnywhere if not in .env
if 'DATABASE_URL' not in os.environ:
    db_username = 'TatumParr'
    db_password = os.environ.get('DB_PASSWORD', 'ReMV1vyaAnqV')  # Use the latest password
    db_name = 'TatumParr$canvas_todoist'
    db_host = 'TatumParr.mysql.pythonanywhere-services.com'
    os.environ['DATABASE_URL'] = f"mysql://TatumParr:{db_password}@{db_host}/{db_name}"
    print(f"Set DATABASE_URL for MySQL connection to {db_host}")

# Set env for Flask
os.environ['FLASK_ENV'] = 'production'
os.environ['FLASK_APP'] = 'wsgi.py'

# Create the application instance with forced pythonanywhere config
from app import create_app
app = create_app('pythonanywhere')
print("PythonAnywhere WSGI file loaded with forced pythonanywhere configuration")

# Export the WSGI application object
application = app 