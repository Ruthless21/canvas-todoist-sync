"""
Direct WSGI file for PythonAnywhere
This file directly imports the app instance (not the factory function).
"""

import os
import sys
import traceback

# Set project path for PythonAnywhere
project_path = '/home/TatumParr/canvas-todoist-sync'
if project_path not in sys.path:
    sys.path.insert(0, project_path)

# Change working directory to ensure relative paths work
try:
    os.chdir(project_path)
    print(f"Working directory set to: {os.getcwd()}")
except Exception as e:
    print(f"Error setting working directory: {str(e)}")

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(project_path, '.env'))
    print("Environment variables loaded from .env file")
except Exception as e:
    print(f"Error loading environment variables: {str(e)}")

# Import the application instance directly
try:
    from app import app
    print("Successfully imported app instance")
    
    # Log all registered routes for debugging
    routes = [f"{rule.rule} -> {rule.endpoint}" for rule in app.url_map.iter_rules()]
    print(f"Registered routes: {routes}")
    
    # Set the application variable for WSGI
    application = app
    
except Exception as e:
    print(f"Error importing app: {str(e)}")
    print(traceback.format_exc())
    
    # Create a minimal fallback app
    from flask import Flask, render_template_string
    application = Flask(__name__)
    
    @application.route('/')
    def error_index():
        return render_template_string("""
        <html>
            <head><title>Error Loading Application</title></head>
            <body>
                <h1>Error Loading Application</h1>
                <p>{{ error }}</p>
                <pre>{{ traceback }}</pre>
            </body>
        </html>
        """, error=str(e), traceback=traceback.format_exc()) 