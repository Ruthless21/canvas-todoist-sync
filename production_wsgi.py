"""
Production WSGI file for PythonAnywhere.
This file is designed to be used as the WSGI configuration file on PythonAnywhere.
"""

import os
import sys

# Add the project directory to the Python path
project_path = '/home/TatumParr/canvas-todoist-sync'
if project_path not in sys.path:
    sys.path.insert(0, project_path)

# Change working directory
os.chdir(project_path)

# Load environment variables
from dotenv import load_dotenv
load_dotenv(os.path.join(project_path, '.env'))

# Import the application instance
from app import app as application

# Print debug information
print("WSGI file loaded")
print(f"Python path: {sys.path}")
print(f"Working directory: {os.getcwd()}")
print(f"Environment: {os.environ.get('FLASK_ENV', 'production')}")

# List all registered routes
print("\nRegistered routes:")
for rule in application.url_map.iter_rules():
    print(f"{rule.endpoint}: {rule.rule}") 