import os
import socket
from app import create_app

# Detect if running on PythonAnywhere
def is_pythonanywhere():
    """Check if we're running on PythonAnywhere based on hostname"""
    return 'pythonanywhere' in socket.gethostname().lower()

# Get the environment from the environment variable or use development as default
env = os.environ.get('FLASK_ENV', 'development')

# Override with pythonanywhere config if we're on that platform and not explicitly set
if is_pythonanywhere() and env == 'production':
    env = 'pythonanywhere'
    print("Detected PythonAnywhere environment, using PythonAnywhere-specific configuration")

app = create_app(env)

if __name__ == '__main__':
    # Only enable debug mode in development
    debug = env == 'development'
    app.run(debug=debug, host='0.0.0.0', port=int(os.environ.get('PORT', 5000))) 