"""
Simple Flask WSGI file for PythonAnywhere
This file creates a minimal Flask application that should work with PythonAnywhere.
"""

import os
import sys

# Add the project directory to the Python path
project_path = '/home/TatumParr/canvas-todoist-sync'
if project_path not in sys.path:
    sys.path.insert(0, project_path)

# Change directory to ensure relative paths work
os.chdir(project_path)

# Create a simple Flask application
from flask import Flask, jsonify

# Create the Flask application
simple_app = Flask(__name__)

@simple_app.route('/')
def home():
    """Simple home route to verify the Flask app is working."""
    return """
    <html>
        <head>
            <title>Simple Flask App</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }
                h1 { color: #4285f4; }
                pre { background: #f5f5f5; padding: 15px; border-radius: 5px; }
                .success { color: green; font-weight: bold; }
                .info { color: blue; }
                .next-steps { margin-top: 30px; padding: 20px; background: #e9f7fe; border-radius: 5px; }
            </style>
        </head>
        <body>
            <h1>Simple Flask App is Working! 🎉</h1>
            <p class="success">Your Flask server is running correctly on PythonAnywhere.</p>
            
            <div class="next-steps">
                <h2>Next Steps:</h2>
                <p>Now that we know a simple Flask app works, we need to fix your main application.</p>
                <ol>
                    <li>Check <a href="/debug">/debug</a> route for more diagnostic information</li>
                    <li>Verify all blueprint registrations in app.py</li>
                    <li>Ensure proper Flask app configuration</li>
                </ol>
            </div>
        </body>
    </html>
    """

@simple_app.route('/debug')
def debug():
    """Debug route that shows useful environment information."""
    try:
        from app import create_app
        app_import_success = True
    except Exception as e:
        app_import_success = False
        import_error = str(e)
    
    debug_info = {
        "environment": {
            "python_version": sys.version,
            "sys_path": sys.path,
            "working_directory": os.getcwd(),
            "environment_variables": {k: v for k, v in os.environ.items() if not k.startswith('_')}
        },
        "flask_app": {
            "import_success": app_import_success,
            "import_error": import_error if not app_import_success else None
        }
    }
    
    return jsonify(debug_info)

# Export Flask application for WSGI
application = simple_app 