"""
Fixed PythonAnywhere WSGI entry point
This file safely loads your Flask application with proper error handling.
"""

import os
import sys
import traceback

# Set project path - use absolute path for system WSGI file
project_path = '/home/TatumParr/canvas-todoist-sync'
if project_path not in sys.path:
    sys.path.insert(0, project_path)

# Change working directory to ensure relative paths work
os.chdir(project_path)

print(f"Starting WSGI - Sys.path: {sys.path}")
print(f"Working directory: {os.getcwd()}")

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(project_path, '.env'))
    print("Environment variables loaded from .env file")
except Exception as e:
    print(f"Error loading environment variables: {str(e)}")

# Ensure DATABASE_URL is set correctly
if 'DATABASE_URL' not in os.environ:
    db_username = 'TatumParr'
    db_password = os.environ.get('DB_PASSWORD', 'ReMV1vyaAnqV')
    db_name = 'TatumParr$canvas_todoist'
    db_host = 'TatumParr.mysql.pythonanywhere-services.com'
    os.environ['DATABASE_URL'] = f"mysql://TatumParr:{db_password}@{db_host}/{db_name}"
    print(f"Set DATABASE_URL for MySQL connection")

# Set Flask environment
os.environ['FLASK_ENV'] = 'production'
os.environ['FLASK_APP'] = 'wsgi.py'
    
# Create a fallback Flask application in case the main app fails
from flask import Flask, request, jsonify, render_template_string
fallback_app = Flask(__name__)

@fallback_app.route('/')
def fallback_home():
    return render_template_string("""
    <html>
        <head>
            <title>Flask Fallback</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }
                h1 { color: #d9534f; }
                pre { background: #f5f5f5; padding: 15px; border-radius: 5px; overflow: auto; }
                .error { color: red; }
            </style>
        </head>
        <body>
            <h1>Flask Fallback Page</h1>
            <p class="error">The main application failed to load. See the error details below:</p>
            <pre>{{ error }}</pre>
            
            <h2>Debugging Information:</h2>
            <ul>
                <li>Python version: {{ python_version }}</li>
                <li>Working directory: {{ working_dir }}</li>
                <li>First sys.path entries: {{ sys_path[:3] }}</li>
            </ul>
            
            <h2>What to Check:</h2>
            <ol>
                <li>Blueprint registration in app.py</li>
                <li>Import errors or circular dependencies</li>
                <li>Configuration issues in your Flask app</li>
                <li>Database connection problems</li>
                <li>Check the server logs for more details</li>
            </ol>
        </body>
    </html>
    """, error=fallback_app.config.get('ERROR_MESSAGE', 'Unknown error'),
         python_version=sys.version,
         working_dir=os.getcwd(),
         sys_path=sys.path)

# Try to load the main Flask application
try:
    print("Attempting to import create_app from app module...")
    from app import create_app
    
    print("Creating application instance with pythonanywhere config...")
    app = create_app('pythonanywhere')
    
    print("Main application loaded successfully")
    application = app
    
except Exception as e:
    error_traceback = traceback.format_exc()
    print(f"Error loading main application: {str(e)}")
    print(error_traceback)
    
    # Set the error message in the fallback app configuration
    fallback_app.config['ERROR_MESSAGE'] = f"{str(e)}\n\n{error_traceback}"
    
    # Use the fallback application
    application = fallback_app
    print("Using fallback application due to error in main application") 