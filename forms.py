from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, SelectField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError, Optional
from models import User

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=64)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=8)])
    password2 = PasswordField('Repeat Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')
    
    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('Please use a different username.')
            
    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('Please use a different email address.')

class APICredentialsForm(FlaskForm):
    canvas_api_url = StringField('Canvas API URL', validators=[DataRequired()])
    canvas_api_token = PasswordField('Canvas API Token', validators=[DataRequired()])
    todoist_api_key = PasswordField('Todoist API Key', validators=[DataRequired()])
    submit = SubmitField('Save Credentials')

class SyncSettingsForm(FlaskForm):
    enabled = BooleanField('Enable Automatic Sync')
    frequency = SelectField('Sync Frequency', 
                          choices=[
                              ('hourly', 'Hourly - Every hour'),
                              ('daily', 'Daily - Once every 24 hours'),
                              ('weekly', 'Weekly - Once every 7 days')
                          ])
    submit = SubmitField('Save Sync Settings')

class AccountUpdateForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Update Account')

class PasswordChangeForm(FlaskForm):
    current_password = PasswordField('Current Password', validators=[DataRequired()])
    new_password = PasswordField('New Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm New Password', 
                                     validators=[DataRequired(), EqualTo('new_password')])
    submit = SubmitField('Change Password')