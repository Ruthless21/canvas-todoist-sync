"""
Fallback WSGI file for PythonAnywhere
This file uses a completely standalone application with no dependencies.
"""

import os
import sys

# Set project path for PythonAnywhere
project_path = '/home/TatumParr/canvas-todoist-sync'
if project_path not in sys.path:
    sys.path.insert(0, project_path)

try:
    # Try to import the fallback app
    from fallback_app import app as fallback_app
    print("Using fallback application")
    application = fallback_app
except Exception as e:
    # If even the fallback fails, create a super simple app on the fly
    from flask import Flask, render_template_string
    emergency_app = Flask(__name__)
    
    @emergency_app.route('/')
    def emergency_index():
        return render_template_string("""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Emergency Mode</title>
            <style>body { font-family: Arial; padding: 20px; }</style>
        </head>
        <body>
            <h1>Emergency Fallback Mode</h1>
            <p>The application is in emergency mode. Please contact the administrator.</p>
            <p>Error: {{ error }}</p>
        </body>
        </html>
        """, error=str(e))
    
    print(f"Using emergency application due to error: {str(e)}")
    application = emergency_app 