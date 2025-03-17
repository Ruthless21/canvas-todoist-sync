"""
WSGI entry point for the application.
This file serves as the entry point for both development and production environments.
"""

import os
import sys
import socket
from dotenv import load_dotenv

# Add the project directory to the Python path
path = os.path.dirname(os.path.abspath(__file__))
if path not in sys.path:
    sys.path.append(path)

# Load environment variables
load_dotenv()

# Create the application instance
from app import create_app

# In production WSGI file, always use pythonanywhere config
production_mode = os.path.abspath(__file__) != os.path.join(os.path.dirname(os.path.abspath(__file__)), 'wsgi.py')
is_pythonanywhere = 'pythonanywhere' in socket.gethostname().lower() or production_mode

print(f"Socket hostname: {socket.gethostname()}")
print(f"Production mode detected: {production_mode}")
print(f"Using pythonanywhere config: {is_pythonanywhere}")

# Force pythonanywhere mode for www_syncmyassignments_com_wsgi.py
if 'www_syncmyassignments_com_wsgi.py' in os.path.abspath(__file__):
    print(f"PythonAnywhere WSGI file detected, forcing pythonanywhere config")
    app = create_app('pythonanywhere')
else:
    app = create_app('pythonanywhere' if is_pythonanywhere else 'development')

print(f"Application created with configuration: {'pythonanywhere' if is_pythonanywhere else 'development'}")

if __name__ == '__main__':
    # Development server
    app.run(debug=True)
else:
    # Production WSGI
    application = app 