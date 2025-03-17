"""
Ultra simple WSGI file for PythonAnywhere
This file focuses solely on properly importing and exposing the Flask app.
"""

import os
import sys

# Set project path
project_path = '/home/TatumParr/canvas-todoist-sync'
if project_path not in sys.path:
    sys.path.insert(0, project_path)

# Import the application
from app import app as flask_app

# Export the application object
application = flask_app

# Print debugging information
print(f"WSGI file loaded, application routes: {list(flask_app.url_map.iter_rules())}") 