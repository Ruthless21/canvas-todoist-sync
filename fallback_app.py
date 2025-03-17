"""
Fallback Flask application that can be used as a last resort.
This app has no dependencies on the main application and should always work.
"""

from flask import Flask, render_template_string

# Create a standalone application
app = Flask(__name__)

@app.route('/')
def index():
    """Simple homepage that confirms the application is working."""
    return render_template_string("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Canvas-Todoist Sync - Fallback Mode</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                line-height: 1.6;
                max-width: 800px;
                margin: 0 auto;
                padding: 20px;
            }
            .card {
                border: 1px solid #ddd;
                border-radius: 8px;
                padding: 20px;
                margin-top: 20px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }
            h1 {
                color: #5E72E4;
            }
            code {
                background: #f5f5f5;
                padding: 2px 5px;
                border-radius: 3px;
            }
        </style>
    </head>
    <body>
        <h1>Canvas-Todoist Sync - Fallback Mode</h1>
        
        <div class="card">
            <h2>Application Status</h2>
            <p>This is the <strong>fallback version</strong> of the Canvas-Todoist Sync application.</p>
            <p>The main application is currently unavailable, but this confirms that the web server is working.</p>
        </div>
        
        <div class="card">
            <h2>Troubleshooting Steps</h2>
            <ol>
                <li>Check server logs for specific errors</li>
                <li>Verify the proper WSGI configuration is used</li>
                <li>Ensure database connection settings are correct</li>
                <li>Check for any import or module errors</li>
            </ol>
        </div>
    </body>
    </html>
    """)

# Set the application variable for WSGI
application = app

if __name__ == '__main__':
    app.run(debug=True, port=5001) 