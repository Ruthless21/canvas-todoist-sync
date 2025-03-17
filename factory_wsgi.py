"""
Factory WSGI file for PythonAnywhere
This file works specifically with the create_app factory pattern.
"""

import os
import sys

# Set project path
project_path = '/home/TatumParr/canvas-todoist-sync'
if project_path not in sys.path:
    sys.path.insert(0, project_path)

# Use the app factory
from app import create_app

# Create application explicitly with 'pythonanywhere' config
application = create_app('pythonanywhere')

# Print debugging information
try:
    print(f"WSGI file loaded with factory pattern, routes: {list(application.url_map.iter_rules())}")
except Exception as e:
    print(f"Error getting routes: {str(e)}") 