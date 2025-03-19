"""
Settings blueprint.
Handles user settings and preferences management.
"""

from flask import render_template, redirect, url_for, flash, request, current_app, session
from flask_login import login_required, current_user
from blueprints import settings_bp
from models import User, db
from forms import UserSettingsForm, APICredentialsForm, SyncSettingsForm, AccountUpdateForm, PasswordChangeForm
from utils.api import get_api_clients

@settings_bp.route('/settings', methods=['GET', 'POST'])
@login_required
def index():
    """Display and handle user settings."""
    # Create all the forms needed by the template
    form = UserSettingsForm(obj=current_user)
    api_form = APICredentialsForm(obj=current_user)
    
    # For the sync form, we would typically load actual values from the database
    # For now, just create an empty form
    sync_form = SyncSettingsForm()
    
    # Initialize the account form with the current user's data
    account_form = AccountUpdateForm(
        original_username=current_user.username,
        original_email=current_user.email,
        obj=current_user
    )
    
    # Password change form doesn't need pre-population
    password_form = PasswordChangeForm()
    
    current_app.logger.debug('Settings page accessed by: %s', current_user.username)
    
    # Determine which form was submitted
    form_name = request.form.get('form_name', '')
    current_app.logger.debug('Form submission detected: %s', form_name)
    
    # Handle API credentials form submission
    if 'canvas_api_url' in request.form and 'canvas_api_token' in request.form and 'todoist_api_token' in request.form:
        current_app.logger.debug('Processing API credentials form')
        try:
            # Get values from the form
            canvas_url = request.form.get('canvas_api_url', '').strip()
            canvas_token = request.form.get('canvas_api_token', '').strip()
            todoist_token = request.form.get('todoist_api_token', '').strip()
            
            current_app.logger.debug('Canvas URL: %s', canvas_url)
            current_app.logger.debug('Canvas token length: %s', len(canvas_token) if canvas_token else 0)
            current_app.logger.debug('Todoist token length: %s', len(todoist_token) if todoist_token else 0)
            
            # Validate that all fields are provided
            if not all([canvas_url, canvas_token, todoist_token]):
                flash('All API credential fields are required', 'danger')
                return redirect(url_for('settings.index'))
            
            # Update user credentials
            current_user.canvas_api_url = canvas_url
            current_user.set_canvas_token(canvas_token)
            current_user.set_todoist_token(todoist_token)
            
            # Save to database
            db.session.commit()
            current_app.logger.debug('API credentials saved successfully')
            flash('API credentials saved successfully', 'success')
            
            # Redirect to dashboard to try again
            return redirect(url_for('dashboard.index'))
        except Exception as e:
            db.session.rollback()
            current_app.logger.error('Error saving API credentials: %s', str(e))
            flash(f'Error saving API credentials: {str(e)}', 'danger')
    
    # Handle general settings form
    elif form.validate_on_submit():
        try:
            current_app.logger.debug('Processing general settings form')
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
            current_app.logger.error('Error updating settings: %s', str(e))
            flash(f'Error updating settings: {str(e)}', 'danger')
    
    # Handle account settings form
    elif account_form.validate_on_submit():
        try:
            current_app.logger.debug('Processing account settings form')
            current_user.username = account_form.username.data
            current_user.email = account_form.email.data
            
            db.session.commit()
            flash('Account settings updated successfully', 'success')
            return redirect(url_for('settings.index'))
        except Exception as e:
            db.session.rollback()
            current_app.logger.error('Error updating account settings: %s', str(e))
            flash(f'Error updating account settings: {str(e)}', 'danger')
    
    # Handle password change form
    elif password_form.validate_on_submit():
        try:
            current_app.logger.debug('Processing password change form')
            # Verify current password
            if not current_user.check_password(password_form.current_password.data):
                flash('Current password is incorrect', 'danger')
                return redirect(url_for('settings.index'))
            
            # Set new password
            current_user.set_password(password_form.new_password.data)
            db.session.commit()
            flash('Password updated successfully', 'success')
            return redirect(url_for('settings.index'))
        except Exception as e:
            db.session.rollback()
            current_app.logger.error('Error changing password: %s', str(e))
            flash(f'Error changing password: {str(e)}', 'danger')
    
    # Prepare template variables
    trial_days = 14  # Placeholder - could come from config
    monthly_price = 9.99  # Placeholder - could come from config
    
    return render_template('settings.html', 
                          form=form,
                          api_form=api_form,
                          sync_form=sync_form,
                          account_form=account_form,
                          password_form=password_form,
                          trial_days=trial_days,
                          monthly_price=monthly_price)

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