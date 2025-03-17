"""
Minimal test WSGI file for PythonAnywhere
This file creates a simple WSGI application that returns a basic HTML response
without loading the Flask application. This helps determine if the issue is with
the WSGI configuration or with the Flask application.
"""

def application(environ, start_response):
    status = '200 OK'
    output = b'<!DOCTYPE html><html><head><title>Test WSGI</title></head><body><h1>WSGI Test Successful</h1><p>This page confirms that the WSGI server is working correctly. The issue is likely with the Flask application itself.</p><pre>' + str(environ).encode('utf-8') + b'</pre></body></html>'
    
    response_headers = [
        ('Content-type', 'text/html'),
        ('Content-Length', str(len(output)))
    ]
    
    start_response(status, response_headers)
    return [output] 