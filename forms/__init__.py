"""
Forms package.
Contains all form classes for the application.
"""

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SelectField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError
from models import User

class LoginForm(FlaskForm):
    """Login form."""
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')

class RegistrationForm(FlaskForm):
    """Registration form."""
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=64)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    password2 = PasswordField('Repeat Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')
    
    def validate_username(self, username):
        """Validate username uniqueness."""
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('Please use a different username.')
    
    def validate_email(self, email):
        """Validate email uniqueness."""
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('Please use a different email address.')

class UserSettingsForm(FlaskForm):
    """User settings form."""
    email = StringField('Email', validators=[DataRequired(), Email()])
    new_password = PasswordField('New Password', validators=[Length(min=6)])
    notification_preferences = SelectField('Notification Preferences',
                                        choices=[
                                            ('all', 'All Notifications'),
                                            ('important', 'Important Only'),
                                            ('none', 'No Notifications')
                                        ])
    sync_preferences = SelectField('Sync Preferences',
                                 choices=[
                                     ('auto', 'Automatic Sync'),
                                     ('manual', 'Manual Sync Only')
                                 ])

class APICredentialsForm(FlaskForm):
    """API credentials form."""
    canvas_api_url = StringField('Canvas API URL', validators=[DataRequired()])
    canvas_api_token = PasswordField('Canvas API Token', validators=[DataRequired()])
    todoist_api_token = PasswordField('Todoist API Token', validators=[DataRequired()])
    submit = SubmitField('Save Credentials')

class AccountUpdateForm(FlaskForm):
    """Account update form."""
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=64)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Update Account')
    
    def __init__(self, original_username, original_email, *args, **kwargs):
        super(AccountUpdateForm, self).__init__(*args, **kwargs)
        self.original_username = original_username
        self.original_email = original_email
    
    def validate_username(self, username):
        if username.data != self.original_username:
            user = User.query.filter_by(username=username.data).first()
            if user is not None:
                raise ValidationError('Please use a different username.')
    
    def validate_email(self, email):
        if email.data != self.original_email:
            user = User.query.filter_by(email=email.data).first()
            if user is not None:
                raise ValidationError('Please use a different email address.')

class PasswordChangeForm(FlaskForm):
    """Password change form."""
    current_password = PasswordField('Current Password', validators=[DataRequired()])
    new_password = PasswordField('New Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm New Password', validators=[DataRequired(), EqualTo('new_password')])
    submit = SubmitField('Change Password')

class SyncSettingsForm(FlaskForm):
    """Sync settings form."""
    enabled = BooleanField('Enable Automatic Sync')
    frequency = SelectField('Sync Frequency', 
                           choices=[
                               ('hourly', 'Hourly'),
                               ('daily', 'Daily'),
                               ('weekly', 'Weekly')
                           ])
    canvas_courses = SelectField('Canvas Course', validators=[DataRequired()])
    todoist_project = SelectField('Todoist Project', validators=[DataRequired()])
    due_date_buffer = SelectField('Due Date Buffer (Days)',
                                choices=[('0', '0'), ('1', '1'), ('2', '2'), ('3', '3'), ('5', '5'), ('7', '7')])
    submit = SubmitField('Save Settings') 