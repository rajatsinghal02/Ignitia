# forms.py
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms.validators import DataRequired, Email, EqualTo, ValidationError, Length
from wtforms import StringField, PasswordField, SubmitField, BooleanField, TextAreaField, SelectField
from app.models import User
from flask_login import current_user

class SignUpForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=80)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Sign Up')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('That username is taken. Please choose a different one.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('That email is already registered.')

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')

class UpdateProfileForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=80)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    picture = FileField('Update Profile Picture', validators=[FileAllowed(['jpg', 'png', 'jpeg'])])
    
    first_name = StringField('First Name', validators=[Length(max=80)])
    last_name = StringField('Last Name', validators=[Length(max=80)])
    
    # NEW FIELDS
    role = SelectField('I am a...', choices=[
        ('Professional', 'Professional Pilot'),
        ('Hobbyist', 'Hobbyist / Enthusiast'),
        ('Student', 'Student'),
        ('Researcher', 'Researcher / Academic'),
        ('Other', 'Other')
    ])
    organization = StringField('Company / Organization', validators=[Length(max=120)])
    website_url = StringField('Website URL', validators=[Length(max=200)])
    
    bio = TextAreaField('About Me')
    submit = SubmitField('Save Changes')

    def validate_username(self, username):
        if username.data != current_user.username:
            user = User.query.filter_by(username=username.data).first()
            if user:
                raise ValidationError('That username is taken.')

    def validate_email(self, email):
        if email.data != current_user.email:
            user = User.query.filter_by(email=email.data).first()
            if user:
                raise ValidationError('That email is already registered.')
            
            
# --- NEW: Investigation Form ---
class NewInvestigationForm(FlaskForm):
    title = StringField('Investigation Title', validators=[DataRequired(), Length(min=5, max=100)])
    location = StringField('Location (e.g., City, State)', validators=[DataRequired(), Length(max=150)])
    drone_type = SelectField('Primary Drone Type', choices=[
        ('Multirotor', 'Multirotor'),
        ('Fixed-Wing', 'Fixed-Wing'),
        ('VTOL', 'VTOL Hybrid'),
        ('FPV', 'FPV Freestyle/Racing'),
        ('Unknown', 'Unknown/Other')
    ], validators=[DataRequired()])
    drone_photo = FileField('Upload Drone Photo', validators=[FileAllowed(['jpg', 'png', 'jpeg'])])
    description = TextAreaField('Brief Description / Objectives', validators=[DataRequired(), Length(max=500)])
    submit = SubmitField('Establish Investigation')
    
    
# --- NEW: Investigation EDIT Form ---
class EditInvestigationForm(FlaskForm):
    title = StringField('Investigation Title', validators=[DataRequired(), Length(min=5, max=100)])
    location = StringField('Location (e.g., City, State)', validators=[DataRequired(), Length(max=150)])
    drone_photo = FileField('Update Drone Photo', validators=[FileAllowed(['jpg', 'png', 'jpeg'])])
    description = TextAreaField('Brief Description / Objectives', validators=[DataRequired(), Length(max=500)])
    submit = SubmitField('Save Changes')