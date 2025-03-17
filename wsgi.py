"""
WSGI entry point for the application.
This file serves as the entry point for both development and production environments.
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

# Create the application instance
from app import create_app
app = create_app()

if __name__ == '__main__':
    # Development server
    app.run(debug=True)
else:
    # Production WSGI
    application = app 