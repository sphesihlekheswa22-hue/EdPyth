from typing import Union, Optional
from flask import (
    Blueprint, render_template, redirect, url_for, 
    flash, request, current_app
)
from flask_login import login_user, logout_user, login_required, current_user
from http import HTTPStatus

from app import db
from app.models import User, Student, Lecturer
from app.forms.auth_forms import (
    RegistrationForm, LoginForm, 
    StudentProfileForm, LecturerProfileForm
)

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')


def redirect_authenticated_user() -> Optional[str]:
    """Redirect already authenticated users to dashboard."""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return None


@auth_bp.route('/register', methods=['GET', 'POST'])
def register() -> Union[str, redirect]:
    """Handle user registration with role-specific profile creation."""
    if redirect_to := redirect_authenticated_user():
        return redirect_to
    
    form = RegistrationForm()
    
    if form.validate_on_submit():
        try:
            # Create base user
            user = User(
                email=form.email.data,
                first_name=form.first_name.data,
                last_name=form.last_name.data,
                role=form.role.data
            )
            user.set_password(form.password.data)
            db.session.add(user)
            db.session.flush()  # Get user.id without committing
            
            # Create role-specific profile
            if form.role.data == 'student':
                profile = Student(
                    user_id=user.id,
                    student_id=f"STU{user.id:06d}"
                )
                db.session.add(profile)
                redirect_target = url_for('auth.complete_student_profile')
                
            elif form.role.data == 'lecturer':
                profile = Lecturer(
                    user_id=user.id,
                    employee_id=f"LEC{user.id:06d}"
                )
                db.session.add(profile)
                redirect_target = url_for('auth.complete_lecturer_profile')
            else:
                redirect_target = url_for('auth.login')
            
            db.session.commit()
            
            flash('Registration successful! Please complete your profile.', 'success')
            return redirect(redirect_target)
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f'Registration error: {str(e)}')
            flash('Registration failed. Please try again.', 'danger')
    
    return render_template('register.html', form=form)


@auth_bp.route('/complete_student_profile', methods=['GET', 'POST'])
@login_required
def complete_student_profile() -> Union[str, redirect]:
    """Complete student profile after registration."""
    if current_user.role != 'student':
        return redirect(url_for('main.dashboard'))
    
    student = Student.query.filter_by(user_id=current_user.id).first_or_404()
    
    # Check if already completed
    if student.program:
        flash('Profile already completed.', 'info')
        return redirect(url_for('main.dashboard'))
    
    form = StudentProfileForm()
    
    if form.validate_on_submit():
        try:
            student.student_id = form.student_id.data or student.student_id
            student.date_of_birth = form.date_of_birth.data
            student.phone = form.phone.data
            student.address = form.address.data
            student.program = form.program.data
            student.year_of_study = int(form.year_of_study.data) if form.year_of_study.data else None
            
            db.session.commit()
            flash('Profile completed successfully!', 'success')
            return redirect(url_for('main.dashboard'))
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f'Profile completion error: {str(e)}')
            flash('Error saving profile. Please try again.', 'danger')
    
    return render_template('complete_profile.html', form=form, role='student')


@auth_bp.route('/complete_lecturer_profile', methods=['GET', 'POST'])
@login_required
def complete_lecturer_profile() -> Union[str, redirect]:
    """Complete lecturer profile after registration."""
    if current_user.role != 'lecturer':
        return redirect(url_for('main.dashboard'))
    
    lecturer = Lecturer.query.filter_by(user_id=current_user.id).first_or_404()
    
    if lecturer.department:
        flash('Profile already completed.', 'info')
        return redirect(url_for('main.dashboard'))
    
    form = LecturerProfileForm()
    
    if form.validate_on_submit():
        try:
            lecturer.employee_id = form.employee_id.data or lecturer.employee_id
            lecturer.department = form.department.data
            lecturer.title = form.title.data
            lecturer.phone = form.phone.data
            lecturer.office = form.office.data
            lecturer.specialization = form.specialization.data
            
            db.session.commit()
            flash('Profile completed successfully!', 'success')
            return redirect(url_for('main.dashboard'))
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f'Profile completion error: {str(e)}')
            flash('Error saving profile. Please try again.', 'danger')
    
    return render_template('complete_profile.html', form=form, role='lecturer')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login() -> Union[str, redirect]:
    """Handle user login with remember me functionality."""
    if redirect_to := redirect_authenticated_user():
        return redirect_to
    
    form = LoginForm()
    
    if form.validate_on_submit():
        user: Optional[User] = User.query.filter_by(email=form.email.data).first()
        
        if user and user.check_password(form.password.data):
            if not user.is_active:
                flash('Your account has been deactivated. Please contact admin.', 'danger')
                return render_template('login.html', form=form), HTTPStatus.FORBIDDEN
            
            # Login with remember me
            remember = form.remember.data == 'yes'
            login_user(user, remember=remember)
            
            # Redirect to dashboard
            next_page = '/dashboard'
            
            flash(f'Welcome back, {user.first_name}!', 'success')
            return redirect(next_page)
        
        flash('Invalid email or password.', 'danger')
        return render_template('login.html', form=form), HTTPStatus.UNAUTHORIZED
    
    return render_template('login.html', form=form)


@auth_bp.route('/logout')
@login_required
def logout() -> redirect:
    """Handle user logout."""
    logout_user()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('auth.login'))


@auth_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile() -> Union[str, redirect]:
    """Handle profile management for all user roles."""
    profile_obj = None
    form = None
    
    try:
        if current_user.role == 'student':
            profile_obj = Student.query.filter_by(user_id=current_user.id).first_or_404()
            form = StudentProfileForm(obj=profile_obj)
            
            if form.validate_on_submit():
                profile_obj.student_id = form.student_id.data or profile_obj.student_id
                profile_obj.date_of_birth = form.date_of_birth.data
                profile_obj.phone = form.phone.data
                profile_obj.address = form.address.data
                profile_obj.program = form.program.data or profile_obj.program
                if form.year_of_study.data:
                    profile_obj.year_of_study = int(form.year_of_study.data)
        
        elif current_user.role == 'lecturer':
            profile_obj = Lecturer.query.filter_by(user_id=current_user.id).first_or_404()
            form = LecturerProfileForm(obj=profile_obj)
            
            if form.validate_on_submit():
                profile_obj.employee_id = form.employee_id.data or profile_obj.employee_id
                profile_obj.department = form.department.data
                profile_obj.title = form.title.data
                profile_obj.phone = form.phone.data
                profile_obj.office = form.office.data
                profile_obj.specialization = form.specialization.data
        
        else:
            return render_template('profile.html', form=None, profile=None)
        
        if form and form.validate_on_submit():
            db.session.commit()
            flash('Profile updated successfully!', 'success')
            return redirect(url_for('auth.profile'))
            
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Profile update error: {str(e)}')
        flash('Error updating profile. Please try again.', 'danger')
    
    return render_template('profile.html', form=form, profile=profile_obj)