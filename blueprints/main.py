"""
Main blueprint.
Handles the main landing page and other general routes.
"""

from flask import render_template
from blueprints import main_bp

@main_bp.route('/')
def index():
    """Display the home page."""
    return render_template('index.html') 