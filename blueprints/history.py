"""
History blueprint.
Handles routes for viewing and managing synchronization history.
"""

from flask import render_template, redirect, url_for, flash, request, jsonify, current_app
from flask_login import login_required, current_user
from blueprints import history_bp
from models import SyncHistory, db
from datetime import datetime, timedelta
from sqlalchemy import func, desc, text

@history_bp.route('/')
@login_required
def index():
    """Display sync history for the current user."""
    current_app.logger.debug('History index route accessed by user: %s', current_user.username)
    
    # Get the recent sync history for this user
    current_app.logger.debug('Querying sync history for user ID: %s', current_user.id)
    try:
        # Only select columns that definitely exist in the database
        # Use a raw SQL query to avoid SQLAlchemy querying for non-existent columns
        query = text("""
            SELECT id, user_id, sync_type, status, items_synced, started_at, completed_at
            FROM sync_history
            WHERE user_id = :user_id
            ORDER BY started_at DESC
            LIMIT 20
        """)
        result = db.session.execute(query, {'user_id': current_user.id})
        history = []
        
        # Convert result to a list of dictionaries
        for row in result:
            history.append({
                'id': row[0],
                'user_id': row[1],
                'sync_type': row[2],
                'status': row[3],
                'items_synced': row[4],
                'started_at': row[5],
                'completed_at': row[6]
            })
        
        current_app.logger.debug('Found %s history records', len(history))
    except Exception as e:
        current_app.logger.error('Error querying sync history: %s', str(e))
        # If the query fails, create an empty list for the template
        history = []
        current_app.logger.debug('Using empty history list due to error')
    
    # Get stats for this user
    try:
        # Use raw SQL to avoid SQLAlchemy issues
        total_query = text("SELECT COUNT(*) FROM sync_history WHERE user_id = :user_id")
        total_result = db.session.execute(total_query, {'user_id': current_user.id})
        total_syncs = total_result.scalar() or 0
        
        success_query = text("SELECT COUNT(*) FROM sync_history WHERE user_id = :user_id AND status = 'success'")
        success_result = db.session.execute(success_query, {'user_id': current_user.id})
        successful_syncs = success_result.scalar() or 0
        
        failed_query = text("SELECT COUNT(*) FROM sync_history WHERE user_id = :user_id AND status = 'failed'")
        failed_result = db.session.execute(failed_query, {'user_id': current_user.id})
        failed_syncs = failed_result.scalar() or 0
        
        items_query = text("SELECT SUM(items_synced) FROM sync_history WHERE user_id = :user_id")
        items_result = db.session.execute(items_query, {'user_id': current_user.id})
        total_items = items_result.scalar() or 0
    
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
        # Use raw SQL to get the last successful sync
        last_sync_query = text("""
            SELECT id, user_id, sync_type, status, items_synced, started_at, completed_at
            FROM sync_history 
            WHERE user_id = :user_id AND status = 'success'
            ORDER BY completed_at DESC
            LIMIT 1
        """)
        last_sync_result = db.session.execute(last_sync_query, {'user_id': current_user.id})
        
        # Convert to dictionary if found
        last_successful = None
        for row in last_sync_result:
            last_successful = {
                'id': row[0],
                'user_id': row[1],
                'sync_type': row[2],
                'status': row[3],
                'items_synced': row[4],
                'started_at': row[5],
                'completed_at': row[6]
            }
            break
    except Exception as e:
        current_app.logger.error('Error getting last successful sync: %s', str(e))
        last_successful = None
    
    # Prepare data for the chart - last 14 days of sync activity
    today = datetime.utcnow().date()
    fourteen_days_ago = today - timedelta(days=13)
    
    # Get sync counts for each day
    chart_labels = []
    chart_values = []
    
    try:
        for i in range(14):
            day = fourteen_days_ago + timedelta(days=i)
            next_day = day + timedelta(days=1)
            
            # Count syncs on this day using raw SQL
            day_query = text("""
                SELECT COUNT(*) 
                FROM sync_history 
                WHERE user_id = :user_id 
                  AND started_at >= :day_start 
                  AND started_at < :day_end
            """)
            day_result = db.session.execute(
                day_query, 
                {
                    'user_id': current_user.id,
                    'day_start': day,
                    'day_end': next_day
                }
            )
            count = day_result.scalar() or 0
            
            # Add to chart data (ensure all values are simple Python primitives)
            chart_labels.append(day.strftime('%m/%d'))
            chart_values.append(int(count))  # Ensure count is a standard int, not a SQLAlchemy Integer
    except Exception as e:
        current_app.logger.error('Error building chart data: %s', str(e))
        # Provide empty chart data if there's an error
        chart_labels = [day.strftime('%m/%d') for day in 
                [fourteen_days_ago + timedelta(days=i) for i in range(14)]]
        chart_values = [0] * 14
    
    # Debug the chart data
    current_app.logger.debug('Chart data: labels=%s, values=%s', chart_labels, chart_values)
    
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
                              'labels': chart_labels,
                              'values': chart_values
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
    try:
        # Get the history item and ensure it belongs to the current user
        query = text("""
            SELECT id, user_id, sync_type, status, items_synced, started_at, completed_at
            FROM sync_history
            WHERE id = :history_id AND user_id = :user_id
            LIMIT 1
        """)
        result = db.session.execute(query, {'history_id': history_id, 'user_id': current_user.id})
        
        history = None
        for row in result:
            history = {
                'id': row[0],
                'user_id': row[1],
                'sync_type': row[2],
                'status': row[3],
                'items_synced': row[4],
                'started_at': row[5],
                'completed_at': row[6]
            }
            break
            
        if not history:
            return render_template('errors/404.html'), 404
            
        return render_template('history_detail.html', history=history)
    except Exception as e:
        current_app.logger.error('Error getting history detail: %s', str(e))
        flash('Error retrieving history details.', 'danger')
        return redirect(url_for('history.index')) 