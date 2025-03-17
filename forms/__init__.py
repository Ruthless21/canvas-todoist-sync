"""
Forms package.
Contains all form classes for the application.
"""

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SelectField, TextAreaField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError
from ..models import User

class LoginForm(FlaskForm):
    """Login form."""
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')

class RegistrationForm(FlaskForm):
    """Registration form."""
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=64)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    password2 = PasswordField('Repeat Password', validators=[DataRequired(), EqualTo('password')])
    
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
    canvas_url = StringField('Canvas API URL', validators=[DataRequired()])
    canvas_token = PasswordField('Canvas API Token', validators=[DataRequired()])
    todoist_token = PasswordField('Todoist API Token', validators=[DataRequired()]) 