"""
Minimal WSGI file for PythonAnywhere
This file contains only the essential code needed to serve the Flask application.
"""

import os
import sys

# Set project path for PythonAnywhere
project_path = '/home/TatumParr/canvas-todoist-sync'
if project_path not in sys.path:
    sys.path.insert(0, project_path)

# Import the app instance
from app import app

# Set application variable for WSGI
application = app

print("Minimal WSGI configured - importing application from app.py") 