"""
History blueprint.
Handles routes for viewing and managing synchronization history.
"""

from flask import render_template, redirect, url_for, flash, request, jsonify, current_app
from flask_login import login_required, current_user
from blueprints import history_bp
from models import SyncHistory, db
from datetime import datetime, timedelta
from sqlalchemy import func, desc

@history_bp.route('/')
@login_required
def index():
    """Display sync history for the current user."""
    current_app.logger.debug('History index route accessed by user: %s', current_user.username)
    
    # Get the recent sync history for this user
    current_app.logger.debug('Querying sync history for user ID: %s', current_user.id)
    try:
        # Only select columns that definitely exist in the database
        history = db.session.query(
            SyncHistory.id,
            SyncHistory.user_id,
            SyncHistory.sync_type,
            SyncHistory.status,
            SyncHistory.items_synced,
            SyncHistory.details,
            SyncHistory.error_message,
            SyncHistory.started_at,
            SyncHistory.completed_at,
            SyncHistory.timestamp
        ).filter(SyncHistory.user_id == current_user.id).order_by(
            SyncHistory.started_at.desc()
        ).limit(20).all()
        current_app.logger.debug('Found %s history records', len(history))
    except Exception as e:
        current_app.logger.error('Error querying sync history: %s', str(e))
        # If the query fails, create an empty list for the template
        history = []
        current_app.logger.debug('Using empty history list due to error')
    
    # Get stats for this user
    try:
        total_syncs = SyncHistory.query.filter_by(user_id=current_user.id).count()
        successful_syncs = SyncHistory.query.filter_by(user_id=current_user.id, status='success').count()
        failed_syncs = SyncHistory.query.filter_by(user_id=current_user.id, status='failed').count()
        total_items = db.session.query(func.sum(SyncHistory.items_synced)).filter_by(user_id=current_user.id).scalar() or 0
    
        current_app.logger.debug('Sync stats - Total: %s, Success: %s, Failed: %s, Items: %s', 
                             total_syncs, successful_syncs, failed_syncs, total_items)
    except Exception as e:
        current_app.logger.error('Error getting sync stats: %s', str(e))
        total_syncs = 0
        successful_syncs = 0
        failed_syncs = 0
        total_items = 0
        current_app.logger.debug('Using default stats due to error')
    
    # Get the most recent successful sync
    try:
        last_successful = SyncHistory.query.filter_by(
            user_id=current_user.id,
            status='success'
        ).order_by(SyncHistory.completed_at.desc()).first()
    except Exception as e:
        current_app.logger.error('Error getting last successful sync: %s', str(e))
        last_successful = None
    
    # Prepare data for the chart - last 14 days of sync activity
    today = datetime.utcnow().date()
    fourteen_days_ago = today - timedelta(days=13)
    
    # Get sync counts for each day
    chart_data = []
    labels = []
    
    try:
        for i in range(14):
            day = fourteen_days_ago + timedelta(days=i)
            next_day = day + timedelta(days=1)
            
            # Count syncs on this day
            count = SyncHistory.query.filter(
                SyncHistory.user_id == current_user.id,
                SyncHistory.started_at >= day,
                SyncHistory.started_at < next_day
            ).count()
            
            # Add to chart data
            labels.append(day.strftime('%m/%d'))
            chart_data.append(count)
    except Exception as e:
        current_app.logger.error('Error building chart data: %s', str(e))
        # Provide empty chart data if there's an error
        labels = [day.strftime('%m/%d') for day in 
                [fourteen_days_ago + timedelta(days=i) for i in range(14)]]
        chart_data = [0] * 14
    
    return render_template('history.html', 
                          history=history,
                          stats={
                              'total': total_syncs,
                              'successful': successful_syncs,
                              'failed': failed_syncs,
                              'items_synced': total_items,
                              'last_successful': last_successful
                          },
                          chart_data={
                              'labels': labels,
                              'values': chart_data
                          })

@history_bp.route('/clear', methods=['POST'])
@login_required
def clear_history():
    """Clear all sync history for the current user."""
    try:
        # Delete all history records for this user
        SyncHistory.query.filter_by(user_id=current_user.id).delete()
        db.session.commit()
        flash('Your sync history has been cleared successfully.', 'success')
    except Exception as e:
        current_app.logger.error('Error clearing sync history: %s', str(e))
        db.session.rollback()
        flash('Error clearing sync history. Please try again.', 'danger')
    
    return redirect(url_for('history.index'))

@history_bp.route('/detail/<int:history_id>')
@login_required
def detail(history_id):
    """Show detailed information for a specific sync operation."""
    # Get the history item and ensure it belongs to the current user
    history = SyncHistory.query.filter_by(
        id=history_id,
        user_id=current_user.id
    ).first_or_404()
    
    return render_template('history_detail.html', history=history) 