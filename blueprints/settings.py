"""
Settings blueprint.
Handles user settings and preferences management.
"""

from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from . import settings_bp
from ..models import User, db
from ..forms import UserSettingsForm

@settings_bp.route('/settings', methods=['GET', 'POST'])
@login_required
def index():
    """Display and handle user settings."""
    form = UserSettingsForm(obj=current_user)
    
    if form.validate_on_submit():
        try:
            current_user.email = form.email.data
            current_user.notification_preferences = form.notification_preferences.data
            current_user.sync_preferences = form.sync_preferences.data
            
            if form.new_password.data:
                current_user.set_password(form.new_password.data)
            
            db.session.commit()
            flash('Settings updated successfully', 'success')
            return redirect(url_for('settings.index'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating settings: {str(e)}', 'danger')
    
    return render_template('settings.html', form=form)

@settings_bp.route('/settings/delete_account', methods=['POST'])
@login_required
def delete_account():
    """Handle account deletion."""
    try:
        # Delete user's data
        current_user.delete_all_data()
        db.session.delete(current_user)
        db.session.commit()
        
        flash('Your account has been deleted', 'success')
        return redirect(url_for('auth.login'))
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting account: {str(e)}', 'danger')
        return redirect(url_for('settings.index')) 