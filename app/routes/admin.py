from functools import wraps
from typing import List, Optional, Union
from flask import (
    Blueprint, render_template, redirect, url_for, 
    flash, request, jsonify, abort
)
from flask_login import login_required, current_user
from datetime import datetime
from http import HTTPStatus

from app import db
from app.models import User, Student, Lecturer, Course, Enrollment

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


class AdminRequiredError(Exception):
    """Custom exception for admin privilege violations."""
    pass


def admin_required(f):
    """Decorator to require admin role with proper error handling."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('auth.login', next=request.url))
        
        if current_user.role != 'admin':
            flash('Access denied. Admin privileges required.', 'danger')
            return redirect(url_for('main.dashboard'))
        
        return f(*args, **kwargs)
    return decorated_function


@admin_bp.errorhandler(AdminRequiredError)
def handle_admin_error(error):
    """Handle admin-specific errors."""
    flash(str(error), 'danger')
    return redirect(url_for('main.dashboard'))


@admin_bp.route('/users')
@login_required
@admin_required
def users() -> str:
    """Display user management interface with filtering."""
    role: Optional[str] = request.args.get('role', type=str)
    
    query = User.query.order_by(User.created_at.desc())
    
    if role and role in ['student', 'lecturer', 'admin', 'career_advisor']:
        query = query.filter_by(role=role)
    
    users_list: List[User] = query.all()
    
    # Statistics for dashboard
    stats = {
        'total': User.query.count(),
        'active': User.query.filter_by(is_active=True).count(),
        'by_role': {
            'student': User.query.filter_by(role='student').count(),
            'lecturer': User.query.filter_by(role='lecturer').count(),
            'admin': User.query.filter_by(role='admin').count(),
        }
    }
    
    return render_template(
        'admin_users.html', 
        users=users_list, 
        role=role,
        stats=stats
    )


@admin_bp.route('/users/<int:user_id>/toggle-active', methods=['POST'])
@login_required
@admin_required
def toggle_user_active(user_id: int) -> Union[str, tuple]:
    """Toggle user active status with validation."""
    user: User = User.query.get_or_404(user_id)
    
    # Prevent self-deactivation
    if user.id == current_user.id:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({
                'success': False,
                'message': 'You cannot deactivate your own account.'
            }), HTTPStatus.BAD_REQUEST
        
        flash('You cannot deactivate yourself.', 'danger')
        return redirect(url_for('admin.users'))
    
    try:
        user.is_active = not user.is_active
        db.session.commit()
        
        status_msg = 'activated' if user.is_active else 'deactivated'
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({
                'success': True,
                'message': f'User {status_msg} successfully.',
                'is_active': user.is_active
            })
        
        flash(f'User {status_msg} successfully!', 'success')
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error toggling user {user_id}: {str(e)}')
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({
                'success': False,
                'message': 'An error occurred. Please try again.'
            }), HTTPStatus.INTERNAL_SERVER_ERROR
        
        flash('An error occurred. Please try again.', 'danger')
    
    return redirect(url_for('admin.users'))


@admin_bp.route('/users/<int:user_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_user(user_id: int) -> str:
    """Delete user with cascade handling."""
    user: User = User.query.get_or_404(user_id)
    
    if user.id == current_user.id:
        flash('You cannot delete yourself.', 'danger')
        return redirect(url_for('admin.users'))
    
    try:
        db.session.delete(user)
        db.session.commit()
        flash('User deleted successfully!', 'success')
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error deleting user {user_id}: {str(e)}')
        flash('Error deleting user. They may have associated records.', 'danger')
    
    return redirect(url_for('admin.users'))


@admin_bp.route('/courses')
@login_required
@admin_required
def courses() -> str:
    """Display course management interface."""
    courses_list: List[Course] = Course.query.order_by(
        Course.created_at.desc()
    ).all()
    
    stats = {
        'total': len(courses_list),
        'active': sum(1 for c in courses_list if c.is_active),
        'total_enrollments': db.session.query(Enrollment).count(),
        'total_students': sum(c.get_student_count() for c in courses_list)
    }
    
    return render_template(
        'admin_courses.html', 
        courses=courses_list,
        stats=stats
    )


@admin_bp.route('/courses/<int:course_id>/toggle-active', methods=['POST'])
@login_required
@admin_required
def toggle_course_active(course_id: int) -> str:
    """Toggle course active status."""
    course: Course = Course.query.get_or_404(course_id)
    
    try:
        course.is_active = not course.is_active
        db.session.commit()
        
        status = 'activated' if course.is_active else 'deactivated'
        flash(f'Course {status} successfully!', 'success')
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error toggling course {course_id}: {str(e)}')
        flash('Error updating course status.', 'danger')
    
    return redirect(url_for('admin.courses'))


@admin_bp.route('/courses/<int:course_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_course(course_id: int) -> str:
    """Delete course with validation."""
    course: Course = Course.query.get_or_404(course_id)
    
    try:
        db.session.delete(course)
        db.session.commit()
        flash('Course deleted successfully!', 'success')
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error deleting course {course_id}: {str(e)}')
        flash('Error deleting course. It may have enrolled students or materials.', 'danger')
    
    return redirect(url_for('admin.courses'))


@admin_bp.route('/enrollments')
@login_required
@admin_required
def enrollments() -> str:
    """Display enrollment management with filtering."""
    status: str = request.args.get('status', 'active')
    
    query = Enrollment.query
    
    if status != 'all':
        query = query.filter_by(status=status)
    
    enrollments_list = query.order_by(Enrollment.enrolled_at.desc()).all()
    
    # Calculate statistics
    stats = {
        'total': Enrollment.query.count(),
        'active': Enrollment.query.filter_by(status='active').count(),
        'completed': Enrollment.query.filter_by(status='completed').count(),
        'dropped': Enrollment.query.filter_by(status='dropped').count()
    }
    
    return render_template(
        'admin_enrollments.html',
        enrollments=enrollments_list,
        status=status,
        stats=stats
    )


@admin_bp.route('/enrollments/<int:enrollment_id>/status', methods=['POST'])
@login_required
@admin_required
def update_enrollment_status(enrollment_id: int) -> str:
    """Update enrollment status with validation."""
    enrollment: Enrollment = Enrollment.query.get_or_404(enrollment_id)
    
    new_status: Optional[str] = request.form.get('status')
    valid_statuses = ['active', 'completed', 'dropped']
    
    if not new_status or new_status not in valid_statuses:
        flash('Invalid status provided.', 'danger')
        return redirect(url_for('admin.enrollments'))
    
    try:
        enrollment.status = new_status
        
        if new_status == 'completed':
            enrollment.completed_at = datetime.utcnow()
        
        db.session.commit()
        flash(f'Enrollment status updated to {new_status}!', 'success')
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error updating enrollment {enrollment_id}: {str(e)}')
        flash('Error updating enrollment status.', 'danger')
    
    return redirect(url_for('admin.enrollments'))


@admin_bp.route('/settings')
@login_required
@admin_required
def settings() -> str:
    """System settings page."""
    return render_template('dashboard_admin.html')