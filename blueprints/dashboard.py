"""
Dashboard blueprint.
Handles main dashboard display and API credential management.
"""

from flask import render_template, redirect, url_for, flash, request, jsonify, session
from flask_login import login_required, current_user
from blueprints import dashboard_bp
from models import User, db
from services.canvas_api import CanvasAPI
from services.todoist_api import TodoistClient
from utils.api import get_api_clients
from forms import APICredentialsForm

@dashboard_bp.route('/')
@login_required
def index():
    """Display the main dashboard."""
    from flask import current_app
    
    current_app.logger.debug('Dashboard index route accessed by user: %s', current_user.username if current_user.is_authenticated else 'Anonymous')
    current_app.logger.debug('Current user authentication status: %s', current_user.is_authenticated)
    
    try:
        # Get API clients
        current_app.logger.debug('Getting API clients for user: %s', current_user.username)
        canvas_client, todoist_client = get_api_clients(current_user)
        
        if not canvas_client or not todoist_client:
            current_app.logger.debug('API clients not configured, redirecting to settings')
            
            # Add specific flash messages about what's missing
            if not canvas_client and not todoist_client:
                flash('You need to configure both Canvas and Todoist API credentials before accessing the dashboard. Please set them up in the API Credentials tab below.', 'warning')
            elif not canvas_client:
                flash('You need to configure your Canvas API credentials before accessing the dashboard. Please set them up in the API Credentials tab below.', 'warning')
            elif not todoist_client:
                flash('You need to configure your Todoist API credentials before accessing the dashboard. Please set them up in the API Credentials tab below.', 'warning')
                
            # Set session variable to trigger credentials modal
            session['show_api_creds_modal'] = True
            
            return redirect(url_for('settings.index'))
        
        # Gather data for dashboard display
        try:
            # Canvas data
            current_app.logger.debug('Fetching Canvas courses')
            courses = canvas_client.get_courses()
            
            # Todoist data
            current_app.logger.debug('Fetching Todoist projects')
            projects = todoist_client.get_projects()
            tasks = todoist_client.get_tasks()
            
            current_app.logger.debug('Successfully loaded dashboard data')
            return render_template('dashboard.html', 
                                  title='Dashboard',
                                  courses=courses,
                                  projects=projects,
                                  tasks=tasks)
        except Exception as e:
            current_app.logger.error('Error fetching dashboard data: %s', str(e))
            flash('Error loading dashboard data. Please check your API credentials.', 'danger')
            return render_template('dashboard.html', 
                                  title='Dashboard',
                                  error=str(e))
    except Exception as e:
        current_app.logger.error('Unexpected error in dashboard: %s', str(e))
        flash('An unexpected error occurred.', 'danger')
        return render_template('dashboard.html', 
                              title='Dashboard',
                              error=str(e))

@dashboard_bp.route('/api_credentials', methods=['GET', 'POST'])
@login_required
def api_credentials():
    """Handle API credential management."""
    form = APICredentialsForm()
    
    if request.method == 'POST':
        # Get values from form or fallback to direct request.form
        canvas_url = form.canvas_api_url.data if form.validate() else request.form.get('canvas_api_url', '').strip()
        canvas_token = form.canvas_api_token.data if form.validate() else request.form.get('canvas_api_token', '').strip()
        todoist_token = form.todoist_api_token.data if form.validate() else request.form.get('todoist_api_token', '').strip()
        
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
    
    return render_template('api_credentials.html', form=form)

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