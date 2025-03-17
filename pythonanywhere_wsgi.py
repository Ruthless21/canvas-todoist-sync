import os
import sys
import socket

# Add project directory to path
path = '/home/TatumParr/canvas-todoist-sync'
if path not in sys.path:
    sys.path.append(path)

# For debugging
print("WSGI initialization started")

# 1. Patch socket.gethostname BEFORE any imports
socket.gethostname = lambda: 'pythonanywhere.com'

# 2. Set environment variables
os.environ['FLASK_ENV'] = 'pythonanywhere'
os.environ['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'default-secret-key-for-development')

# 3. Set up MySQL database URL for PythonAnywhere
# IMPORTANT: MySQL database credentials on PythonAnywhere
# 1. Go to Databases tab in PythonAnywhere dashboard
# 2. Look for your MySQL password there (Click "Show this password" if needed)
# 3. Replace the placeholder below with your actual MySQL password
# 4. Make sure database has been created (TatumParr$canvas_todoist)

# Database connection format for PythonAnywhere:
# mysql://<username>:<password>@<username>.mysql.pythonanywhere-services.com/<username>$<dbname>

db_username = 'TatumParr'  # Your PythonAnywhere username
db_password = 'FEo3f5gBOpIZF'  # ← REPLACE THIS with your ACTUAL MySQL password from the Databases tab
db_name = 'TatumParr$canvas_todoist'  # Format must be username$dbname
db_host = 'TatumParr.mysql.pythonanywhere-services.com'  # Standard host format

# Test direct connection to verify credentials
try:
    import MySQLdb
    print("Testing direct MySQL connection...")
    conn = MySQLdb.connect(
        user=db_username,
        passwd=db_password,
        host=db_host,
        db=db_name
    )
    print("✓ Direct MySQL connection successful!")
    conn.close()
except Exception as e:
    print(f"× Warning: Could not connect directly to MySQL: {str(e)}")

# Construct and set the database URL
os.environ['DATABASE_URL'] = f"mysql+mysqldb://{db_username}:{db_password}@{db_host}/{db_name}"
print(f"Set DATABASE_URL for MySQL connection to {db_host}")

# Import and patch the app
try:
    # Import app module
    from importlib import import_module
    app = import_module('app')
    
    # Save original create_app function
    original_create_app = app.create_app
    
    # Create wrapper function
    def safe_create_app(config_name='pythonanywhere'):
        # Set the config_name as a global in the app module
        app.env = config_name
        print(f"Creating app with config: {config_name}")
        
        # Create the Flask app
        flask_app = original_create_app(config_name)
        
        # Verify database connection
        if hasattr(flask_app, 'config'):
            db_uri = flask_app.config.get('SQLALCHEMY_DATABASE_URI', 'Not set')
            print(f"Using database: {db_uri}")
            
            # Set MySQL connection pooling options
            flask_app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
                'pool_recycle': 240,   # Recycle connections before MySQL's 300s timeout
                'pool_pre_ping': True, # Test connections before using them
                'pool_timeout': 30,    # Don't wait too long for connections
                'pool_size': 10,       # Default pool size
                'max_overflow': 5      # Allow some extra connections
            }
        
        return flask_app
    
    # Replace the original function
    app.create_app = safe_create_app
    
    # Create the application
    application = app.create_app()
    print("Application created successfully")
    
    # Clean any existing database connections
    from flask_sqlalchemy import SQLAlchemy
    with application.app_context():
        try:
            db = SQLAlchemy(application)
            db.engine.dispose()
            print("Database connection pool refreshed after initialization")
        except Exception as e:
            print(f"Warning: Could not refresh connection pool: {str(e)}")
    
except Exception as ex:
    # Store the error message in a variable that will be in scope
    error_message = str(ex)
    import traceback
    print(f"Error creating application: {error_message}")
    print(traceback.format_exc())
    
    # Create an error application
    def application(environ, start_response):
        start_response('500 Internal Server Error', [('Content-Type', 'text/html')])
        html = f"""
        <html>
            <head>
                <title>Database Connection Error</title>
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 800px; margin: 0 auto; padding: 20px; }}
                    h1 {{ color: #e74c3c; }}
                    .error {{ background-color: #f9f9f9; padding: 15px; border-left: 5px solid #e74c3c; }}
                    .help {{ background-color: #f0f7fb; padding: 15px; border-left: 5px solid #3498db; margin-top: 20px; }}
                    .code {{ font-family: monospace; background-color: #f8f8f8; padding: 10px; }}
                </style>
            </head>
            <body>
                <h1>Database Connection Error</h1>
                <div class="error">
                    <p>The application encountered a database connection issue:</p>
                    <p><strong>Error:</strong> {error_message}</p>
                </div>
                
                <div class="help">
                    <h3>Common Solutions:</h3>
                    <ol>
                        <li>Check that you've created a MySQL database in your PythonAnywhere account</li>
                        <li>Make sure the database password in the WSGI file is correct</li>
                        <li>Verify the database name follows the username$dbname format</li>
                        <li>Check that your MySQL service is running on PythonAnywhere</li>
                    </ol>
                    
                    <h3>MySQL Configuration:</h3>
                    <p>Your WSGI file should contain the correct database credentials:</p>
                    <div class="code">
                        db_username = 'TatumParr'<br>
                        db_password = 'FEo3f5gBOpIZF'<br>
                        db_name = 'TatumParr$canvas_todoist'<br>
                        db_host = 'TatumParr.mysql.pythonanywhere-services.com'
                    </div>
                </div>
            </body>
        </html>
        """
        return [html.encode('utf-8')]

print("WSGI initialization completed") 