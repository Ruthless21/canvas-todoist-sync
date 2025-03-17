"""
Admin blueprint.
Handles administrative functionality and system management.
"""

from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from functools import wraps
from . import admin_bp
from ..models import User, db

def admin_required(f):
    """Decorator to require admin privileges."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_admin:
            flash('You do not have permission to access this page.', 'danger')
            return redirect(url_for('dashboard.index'))
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/admin')
@login_required
@admin_required
def index():
    """Display admin dashboard."""
    users = User.query.all()
    return render_template('admin/index.html', users=users)

@admin_bp.route('/admin/users')
@login_required
@admin_required
def users():
    """Display user management page."""
    users = User.query.all()
    return render_template('admin/users.html', users=users)

@admin_bp.route('/admin/users/<int:user_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_user(user_id):
    """Edit user details."""
    user = User.query.get_or_404(user_id)
    
    if request.method == 'POST':
        try:
            user.username = request.form.get('username')
            user.email = request.form.get('email')
            user.is_active = 'is_active' in request.form
            user.is_admin = 'is_admin' in request.form
            
            if request.form.get('new_password'):
                user.set_password(request.form.get('new_password'))
            
            db.session.commit()
            flash('User updated successfully', 'success')
            return redirect(url_for('admin.users'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating user: {str(e)}', 'danger')
    
    return render_template('admin/edit_user.html', user=user)

@admin_bp.route('/admin/users/<int:user_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_user(user_id):
    """Delete a user."""
    user = User.query.get_or_404(user_id)
    
    if user.id == current_user.id:
        flash('You cannot delete your own account', 'danger')
        return redirect(url_for('admin.users'))
    
    try:
        user.delete_all_data()
        db.session.delete(user)
        db.session.commit()
        flash('User deleted successfully', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting user: {str(e)}', 'danger')
    
    return redirect(url_for('admin.users'))

@admin_bp.route('/admin/system')
@login_required
@admin_required
def system_status():
    """Display system status and health information."""
    try:
        # Get system statistics
        stats = {
            'total_users': User.query.count(),
            'active_users': User.query.filter_by(is_active=True).count(),
            'admin_users': User.query.filter_by(is_admin=True).count(),
            'subscribed_users': User.query.filter_by(subscription_status='active').count(),
        }
        
        return render_template('admin/system.html', stats=stats)
    except Exception as e:
        flash(f'Error retrieving system status: {str(e)}', 'danger')
        return redirect(url_for('admin.index'))

@admin_bp.route('/admin/logs')
@login_required
@admin_required
def view_logs():
    """Display system logs."""
    # This would typically read from a log file or database
    # For now, we'll just show a placeholder
    return render_template('admin/logs.html') 