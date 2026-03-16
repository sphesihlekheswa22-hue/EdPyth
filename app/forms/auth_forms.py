from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField, DateField, TextAreaField, IntegerField
from wtforms.validators import DataRequired, Email, EqualTo, Length, Optional, ValidationError
from app.models import User


class RegistrationForm(FlaskForm):
    """User registration form."""
    email = StringField('Email', validators=[DataRequired(), Email()])
    first_name = StringField('First Name', validators=[DataRequired(), Length(min=2, max=50)])
    last_name = StringField('Last Name', validators=[DataRequired(), Length(min=2, max=50)])
    role = SelectField('Role', choices=[
        ('student', 'Student'),
        ('lecturer', 'Lecturer'),
        ('admin', 'Admin'),
        ('career_advisor', 'Career Advisor')
    ], validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')
    
    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Email already registered. Please login.')


class LoginForm(FlaskForm):
    """User login form."""
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = SelectField('Remember Me', choices=[
        ('yes', 'Yes'),
        ('no', 'No')
    ], default='no')
    submit = SubmitField('Login')


class StudentProfileForm(FlaskForm):
    """Student profile additional details form."""
    student_id = StringField('Student ID', validators=[DataRequired(), Length(min=5, max=20)])
    date_of_birth = DateField('Date of Birth', validators=[Optional()])
    phone = StringField('Phone', validators=[Optional(), Length(max=20)])
    address = StringField('Address', validators=[Optional(), Length(max=200)])
    program = StringField('Program/Major', validators=[Optional(), Length(max=100)])
    year_of_study = SelectField('Year of Study', choices=[
        ('', 'Select Year'),
        ('1', '1st Year'),
        ('2', '2nd Year'),
        ('3', '3rd Year'),
        ('4', '4th Year'),
        ('5', '5th Year+')
    ], validators=[Optional()])
    submit = SubmitField('Save Profile')


class LecturerProfileForm(FlaskForm):
    """Lecturer profile additional details form."""
    employee_id = StringField('Employee ID', validators=[DataRequired(), Length(min=5, max=20)])
    department = StringField('Department', validators=[Optional(), Length(max=100)])
    title = StringField('Title (e.g., Professor, Dr.)', validators=[Optional(), Length(max=50)])
    phone = StringField('Phone', validators=[Optional(), Length(max=20)])
    office = StringField('Office', validators=[Optional(), Length(max=50)])
    specialization = StringField('Specialization', validators=[Optional(), Length(max=200)])
    submit = SubmitField('Save Profile')
