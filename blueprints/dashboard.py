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
@login_required
def sync_assignments():
    """Sync assignments from Canvas to Todoist."""
    from flask import current_app
    import json
    import datetime
    from models import SyncHistory, db
    
    current_app.logger.debug(f"Request method: {request.method}, path: {request.path}")
    current_app.logger.debug(f"Headers: {request.headers}")
    current_app.logger.debug(f"Session: {session}")
    
    # Get data from request
    try:
        data = request.get_json()
        course_id = data.get('course_id')
        project_id = data.get('project_id')
        
        if not course_id or not project_id:
            return jsonify({
                'success': False,
                'error': 'Missing required parameters'
            }), 400
            
        current_app.logger.debug(f"Syncing assignments from Canvas course {course_id} to Todoist project {project_id}")
        
        # Get API clients
        canvas_client, todoist_client = get_api_clients(current_user)
        if not canvas_client or not todoist_client:
            return jsonify({
                'success': False,
                'error': 'API clients not configured properly'
            }), 400
        
        # Get assignments from Canvas
        assignments = canvas_client.get_assignments(course_id)
        if not assignments:
            return jsonify({
                'success': False,
                'error': 'No assignments found for this course'
            }), 404
            
        current_app.logger.debug(f"Found {len(assignments)} assignments in Canvas course")
        
        # Sync each assignment to Todoist
        synced_count = 0
        for assignment in assignments:
            # Skip assignments that have been submitted or don't have due dates
            if assignment.get('submission', {}).get('submitted_at') or not assignment.get('due_at'):
                continue
                
            # Create task in Todoist
            due_date = assignment.get('due_at')
            if due_date:
                # Convert from ISO format to YYYY-MM-DD
                try:
                    due_date_obj = datetime.datetime.fromisoformat(due_date.replace('Z', '+00:00'))
                    due_date = due_date_obj.strftime('%Y-%m-%d')
                except Exception as e:
                    current_app.logger.error(f"Error parsing due date: {e}")
                    due_date = None
            
            # Create the task in Todoist
            task = todoist_client.create_task(
                content=assignment.get('name', 'Unnamed assignment'),
                due_date=due_date,
                project_id=project_id,
                priority=3,  # Medium priority
                # Add the Canvas assignment link as a comment
                description=f"Canvas Assignment: {assignment.get('html_url', '')}\n\n{assignment.get('description', '')}"
            )
            
            if task:
                synced_count += 1
        
        # Log the sync in history
        try:
            # Create sync record with flexible field names to support both models
            sync_record_data = {
                'user_id': current_user.id,
                'sync_type': 'canvas_to_todoist',
                'status': 'success' if synced_count > 0 else 'failed',
                'started_at': datetime.datetime.utcnow(),
                'completed_at': datetime.datetime.utcnow(),
            }
            
            # Check which fields the model supports
            model_columns = SyncHistory.__table__.columns.keys()
            
            # Add fields depending on what's available in the model
            if 'items_synced' in model_columns:
                sync_record_data['items_synced'] = synced_count
            elif 'items_count' in model_columns:
                sync_record_data['items_count'] = synced_count
                
            if 'error_message' in model_columns and synced_count == 0:
                sync_record_data['error_message'] = 'No assignments were synced'
                
            # Optional newer fields
            if 'source_id' in model_columns:
                sync_record_data['source_id'] = course_id
            if 'destination_id' in model_columns:
                sync_record_data['destination_id'] = project_id
            if 'details' in model_columns:
                sync_record_data['details'] = json.dumps({
                    'course_id': course_id,
                    'project_id': project_id,
                    'total_assignments': len(assignments),
                    'synced_assignments': synced_count
                })
                
            # Create and save the record
            sync_record = SyncHistory(**sync_record_data)
            db.session.add(sync_record)
            db.session.commit()
        except Exception as e:
            current_app.logger.error(f"Error saving sync history: {e}")
            db.session.rollback()
        
        # Update user's last sync time
        try:
            current_user.last_sync = datetime.datetime.utcnow()
            db.session.commit()
        except Exception as e:
            current_app.logger.error(f"Error updating user's last sync time: {e}")
            db.session.rollback()
        
        return jsonify({
            'success': True,
            'message': f"{synced_count} assignments to Todoist",
            'total': len(assignments),
            'synced': synced_count
        })
    except Exception as e:
        current_app.logger.error(f"Error in sync_assignments: {str(e)}")
        import traceback
        current_app.logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@dashboard_bp.route('/api/refresh_data', methods=['POST'])
@login_required
def refresh_data():
    """Refresh dashboard data."""
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