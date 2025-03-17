"""
PythonAnywhere WSGI entry point - system version for /var/www/www_syncmyassignments_com_wsgi.py
This file should be used as the content for your PythonAnywhere WSGI configuration file.
"""

import os
import sys
import socket

# Set project path - use absolute path for system WSGI file
project_path = '/home/TatumParr/canvas-todoist-sync'
if project_path not in sys.path:
    sys.path.insert(0, project_path)

# Change working directory to ensure relative paths work
os.chdir(project_path)

# Override hostname to ensure correct configuration detection
original_gethostname = socket.gethostname
socket.gethostname = lambda: 'pythonanywhere.com'

# Load environment variables
from dotenv import load_dotenv
load_dotenv(os.path.join(project_path, '.env'))

# Ensure DATABASE_URL is set correctly for PythonAnywhere if not in .env
if 'DATABASE_URL' not in os.environ:
    db_username = 'TatumParr'
    db_password = os.environ.get('DB_PASSWORD', 'ReMV1vyaAnqV')  # Use the latest password
    db_name = 'TatumParr$canvas_todoist'
    db_host = 'TatumParr.mysql.pythonanywhere-services.com'
    os.environ['DATABASE_URL'] = f"mysql://TatumParr:{db_password}@{db_host}/{db_name}"
    print(f"Set DATABASE_URL for MySQL connection to {db_host}/{db_name}")

# Set env for Flask
os.environ['FLASK_ENV'] = 'production'
os.environ['FLASK_APP'] = 'wsgi.py'

# Debug logging
print(f"Python path: {sys.path}")
print(f"Current directory: {os.getcwd()}")
print(f"Environment variables: DATABASE_URL is {'set' if 'DATABASE_URL' in os.environ else 'NOT SET'}")

try:
    # Create the application instance with forced pythonanywhere config
    from app import create_app
    app = create_app('pythonanywhere')
    print("PythonAnywhere WSGI file loaded with forced pythonanywhere configuration")
    
    # Export the WSGI application object
    application = app
except Exception as e:
    import traceback
    print(f"Error loading application: {str(e)}")
    print(traceback.format_exc())
    # Provide a simple application for debugging
    def application(environ, start_response):
        status = '500 Internal Server Error'
        response_headers = [('Content-type', 'text/plain')]
        start_response(status, response_headers)
        error_message = f"Error loading application: {str(e)}\n\n{traceback.format_exc()}"
        return [error_message.encode()] 