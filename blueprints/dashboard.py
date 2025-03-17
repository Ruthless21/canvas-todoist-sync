"""
Dashboard blueprint.
Handles main dashboard display and API credential management.
"""

from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from . import dashboard_bp
from ..models import User, db
from ..services.canvas_api import CanvasAPI
from ..services.todoist_api import TodoistAPI
from ..utils import get_api_clients

@dashboard_bp.route('/')
@login_required
def index():
    """Display the main dashboard."""
    canvas_client, todoist_client = get_api_clients(current_user)
    
    if not canvas_client or not todoist_client:
        return redirect(url_for('dashboard.api_credentials'))
    
    try:
        courses = canvas_client.get_courses()
        projects = todoist_client.get_projects()
        assignments = canvas_client.get_assignments()
        todo_items = canvas_client.get_todo_items()
        
        return render_template('dashboard.html',
                             courses=courses,
                             projects=projects,
                             assignments=assignments,
                             todo_items=todo_items)
    except Exception as e:
        flash(f'Error loading dashboard data: {str(e)}', 'danger')
        return render_template('dashboard.html',
                             courses=[],
                             projects=[],
                             assignments=[],
                             todo_items=[])

@dashboard_bp.route('/api_credentials', methods=['GET', 'POST'])
@login_required
def api_credentials():
    """Handle API credential management."""
    if request.method == 'POST':
        canvas_url = request.form.get('canvas_url', '').strip()
        canvas_token = request.form.get('canvas_token', '').strip()
        todoist_token = request.form.get('todoist_token', '').strip()
        
        if not all([canvas_url, canvas_token, todoist_token]):
            flash('All fields are required', 'danger')
            return redirect(url_for('dashboard.api_credentials'))
        
        current_user.canvas_api_url = canvas_url
        current_user.set_canvas_token(canvas_token)
        current_user.set_todoist_token(todoist_token)
        
        try:
            db.session.commit()
            flash('API credentials saved successfully', 'success')
            return redirect(url_for('dashboard.index'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error saving credentials: {str(e)}', 'danger')
    
    return render_template('api_credentials.html')

@dashboard_bp.route('/api/test_canvas', methods=['POST'])
@login_required
def test_canvas_api():
    """Test Canvas API connection."""
    try:
        canvas_client, _ = get_api_clients(current_user)
        if not canvas_client:
            return jsonify({'success': False, 'message': 'Canvas API credentials not found'})
        
        courses = canvas_client.get_courses()
        return jsonify({
            'success': True,
            'message': f'Successfully connected to Canvas API. Found {len(courses)} courses.'
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@dashboard_bp.route('/api/test_todoist', methods=['POST'])
@login_required
def test_todoist_api():
    """Test Todoist API connection."""
    try:
        _, todoist_client = get_api_clients(current_user)
        if not todoist_client:
            return jsonify({'success': False, 'message': 'Todoist API credentials not found'})
        
        projects = todoist_client.get_projects()
        return jsonify({
            'success': True,
            'message': f'Successfully connected to Todoist API. Found {len(projects)} projects.'
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}) 