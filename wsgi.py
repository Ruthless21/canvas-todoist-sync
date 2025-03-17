"""
WSGI entry point for the application.
This file serves as the entry point for both development and production environments.
"""

import os
import sys

# Add the project directory to the Python path
project_path = '/home/TatumParr/canvas-todoist-sync'
if project_path not in sys.path:
    sys.path.insert(0, project_path)

# Change working directory to ensure relative paths work
os.chdir(project_path)

# Load environment variables
from dotenv import load_dotenv
load_dotenv(os.path.join(project_path, '.env'))

# Import the application factory
from app import create_app

# Create the application instance with pythonanywhere config
application = create_app('pythonanywhere')

# Print debug information
print("WSGI file loaded")
print(f"Python version: {sys.version}")
print(f"Working directory: {os.getcwd()}")
print(f"Python path: {sys.path}")
print(f"Environment: {os.environ.get('FLASK_ENV', 'production')}")
print(f"Project path exists: {os.path.exists(project_path)}")
print(f"Templates path exists: {os.path.exists(os.path.join(project_path, 'templates'))}")

# List all registered routes for debugging
print("\nRegistered routes:")
for rule in application.url_map.iter_rules():
    print(f"{rule.endpoint}: {rule.rule}")

# No need for __main__ check in production WSGI file 