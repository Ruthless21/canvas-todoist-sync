"""
WSGI entry point for the application.
This file serves as the entry point for both development and production environments.
"""

import os
from dotenv import load_dotenv
from app import create_app

# Load environment variables
load_dotenv()

# Create the application instance
app = create_app()

if __name__ == '__main__':
    # Development server
    app.run(debug=True)
else:
    # Production WSGI
    application = app 