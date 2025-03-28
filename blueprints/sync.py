"""
Sync blueprint.
Handles synchronization between Canvas and Todoist.
"""

from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from blueprints import sync_bp
from models import User, db, SyncSettings, SyncHistory
from services.canvas_api import CanvasAPI
from services.todoist_api import TodoistClient
from services.sync_service import SyncService
from utils.api import get_api_clients
from datetime import datetime

@sync_bp.route('/sync', methods=['GET', 'POST'])
@login_required
def index():
    """Display sync status and handle manual sync requests."""
    canvas_client, todoist_client = get_api_clients(current_user)
    
    if not canvas_client or not todoist_client:
        flash('Please configure your API credentials first', 'warning')
        return redirect(url_for('dashboard.api_credentials'))
    
    if request.method == 'POST':
        try:
            # Get latest data
            assignments = canvas_client.get_assignments()
            projects = todoist_client.get_projects()
            
            # Sync assignments to Todoist
            synced_count = 0
            for assignment in assignments:
                if todoist_client.create_or_update_task(assignment):
                    synced_count += 1
            
            flash(f'Successfully synced {synced_count} assignments', 'success')
            return redirect(url_for('sync.index'))
        except Exception as e:
            flash(f'Error during sync: {str(e)}', 'danger')
    
    # Get sync status
    try:
        assignments = canvas_client.get_assignments()
        todoist_tasks = todoist_client.get_tasks()
        sync_status = {
            'total_assignments': len(assignments),
            'synced_tasks': len(todoist_tasks),
            'last_sync': current_user.last_sync
        }
    except Exception as e:
        sync_status = {
            'error': str(e),
            'total_assignments': 0,
            'synced_tasks': 0,
            'last_sync': None
        }
    
    return render_template('sync.html', sync_status=sync_status)

@sync_bp.route('/sync/status')
@login_required
def status():
    """Get current sync status as JSON."""
    try:
        canvas_client, todoist_client = get_api_clients(current_user)
        assignments = canvas_client.get_assignments()
        todoist_tasks = todoist_client.get_tasks()
        
        return jsonify({
            'success': True,
            'data': {
                'total_assignments': len(assignments),
                'synced_tasks': len(todoist_tasks),
                'last_sync': current_user.last_sync.isoformat() if current_user.last_sync else None
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        })

@sync_bp.route('/sync/force', methods=['POST'])
@login_required
def force_sync():
    """Force a full sync between Canvas and Todoist."""
    try:
        canvas_client, todoist_client = get_api_clients(current_user)
        assignments = canvas_client.get_assignments()
        
        # Clear existing tasks
        todoist_client.clear_tasks()
        
        # Sync all assignments
        synced_count = 0
        for assignment in assignments:
            if todoist_client.create_or_update_task(assignment):
                synced_count += 1
        
        current_user.last_sync = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Successfully synced {synced_count} assignments'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        })

@sync_bp.route('/update_sync_settings', methods=['POST'])
@login_required
def update_sync_settings():
    """Update user sync settings."""
    from forms import SyncSettingsForm
    
    form = SyncSettingsForm()
    if form.validate_on_submit():
        try:
            # Get or create sync settings for user
            sync_settings = SyncSettings.query.filter_by(user_id=current_user.id).first()
            if not sync_settings:
                sync_settings = SyncSettings(user_id=current_user.id)
                db.session.add(sync_settings)
            
            # Update settings from form
            sync_settings.sync_frequency = form.frequency.data
            
            # Handle enabled state
            if form.enabled.data:
                current_user.sync_preferences = 'auto'
            else:
                current_user.sync_preferences = 'manual'
            
            # Save changes
            db.session.commit()
            flash('Sync settings updated successfully', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating sync settings: {str(e)}', 'danger')
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"{getattr(form, field).label.text}: {error}", 'danger')
    
    return redirect(url_for('settings.index')) 