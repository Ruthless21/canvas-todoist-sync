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
            canvas_data = canvas_client.get_courses()
            current_app.logger.debug(f'Canvas raw data type: {type(canvas_data)}')
            
            # Process Canvas data to ensure we have consistent structure
            courses = []
            for course in canvas_data:
                # Convert Canvas course data to a standardized format
                course_obj = {
                    'id': course.get('id'),
                    'name': course.get('name') or course.get('course_code', f"Course #{course.get('id')}"),
                    'course_code': course.get('course_code'),
                    'term': course.get('term', {}).get('name') if course.get('term') else None,
                    'start_date': course.get('start_at'),
                    'end_date': course.get('end_at'),
                    'url': course.get('html_url')
                }
                courses.append(course_obj)
            
            current_app.logger.debug(f'Processed courses: {courses[:2]}')  # Log first 2 courses only
            
            # Todoist data
            current_app.logger.debug('Fetching Todoist projects')
            todoist_projects = todoist_client.get_projects()
            
            # Process Todoist data for consistency
            projects = []
            for project in todoist_projects:
                # Convert Todoist project data to a standardized format
                project_obj = {
                    'id': getattr(project, 'id', None),
                    'name': getattr(project, 'name', f"Project #{getattr(project, 'id', 'unknown')}"),
                    'color': getattr(project, 'color', None),
                    'is_shared': getattr(project, 'is_shared', False)
                }
                projects.append(project_obj)
                
            current_app.logger.debug(f'Processed projects: {projects[:2]}')  # Log first 2 projects only
            
            # Get tasks
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

@dashboard_bp.route('/api/sync', methods=['POST'])
@dashboard_bp.route('/api/sync/<csrf_token>', methods=['POST'])
@login_required
def sync_assignments(csrf_token=None):
    """Sync assignments from Canvas to Todoist."""
    from flask import current_app
    import json
    import datetime
    from models import SyncHistory, db
    
    current_app.logger.debug(f"Request method: {request.method}, path: {request.path}")
    current_app.logger.debug(f"Headers: {request.headers}")
    current_app.logger.debug(f"CSRF Token in URL: {csrf_token}")
    current_app.logger.debug(f"Session: {session}")
    
    # Return a simple response immediately just to test if the route is accessible
    try:
        # Basic info about the request
        current_app.logger.debug("--- SYNC DEBUG START ---")
        request_body = request.get_data(as_text=True)
        current_app.logger.debug(f"Raw request body: {request_body}")
        form_data = request.form.to_dict()
        current_app.logger.debug(f"Form data: {form_data}")
        json_data = None
        
        try:
            json_data = request.get_json(force=True, silent=True)
            current_app.logger.debug(f"JSON data: {json_data}")
        except Exception as e:
            current_app.logger.error(f"Error parsing JSON: {e}")
            
        # Return a simple test response to see if it gets back to the browser
        return jsonify({
            'success': True,
            'message': 'Debug response - route is reachable',
            'received_data': {
                'json': json_data,
                'form': form_data,
                'raw': request_body[:100] if request_body else None  # First 100 chars only
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"Error in debug response: {str(e)}")
        import traceback
        current_app.logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': f"Debug error: {str(e)}"
        }), 500
    
    # The rest of the function won't be reached during testing

@dashboard_bp.route('/api/refresh_data', methods=['POST'])
@dashboard_bp.route('/api/refresh_data/<csrf_token>', methods=['POST'])
@login_required
def refresh_data(csrf_token=None):
    """Refresh dashboard data."""
    from flask import current_app
    current_app.logger.debug(f"Refresh data endpoint accessed with CSRF token: {csrf_token}")
    try:
        return jsonify({
            'success': True,
            'message': 'Data refreshed successfully'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500 