"""
PythonAnywhere WSGI entry point.
This is a dedicated WSGI file for PythonAnywhere that guarantees the pythonanywhere configuration is used.
"""

import os
import sys
from dotenv import load_dotenv

# Add the project directory to the Python path
path = os.path.dirname(os.path.abspath(__file__))
if path not in sys.path:
    sys.path.append(path)

# Load environment variables
load_dotenv()

# Create the application instance with forced pythonanywhere config
from app import create_app
app = create_app('pythonanywhere')
print("PythonAnywhere WSGI file loaded with forced pythonanywhere configuration")

# Export the WSGI application object
application = app 