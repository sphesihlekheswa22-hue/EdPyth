from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db
from app.models import (
    User, Student, Lecturer, Course, Enrollment,
    Quiz, QuizResult, Attendance, Mark, StudyPlan, ChatSession, CVReview
)

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    """Home page."""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return redirect(url_for('auth.login'))


@main_bp.route('/dashboard')
@login_required
def dashboard():
    """Main dashboard based on user role."""
    if current_user.role == 'student':
        return redirect(url_for('main.student_dashboard'))
    elif current_user.role == 'lecturer':
        return redirect(url_for('main.lecturer_dashboard'))
    elif current_user.role == 'admin':
        return redirect(url_for('main.admin_dashboard'))
    elif current_user.role == 'career_advisor':
        return redirect(url_for('main.career_advisor_dashboard'))
    else:
        flash('Unknown role. Please contact admin.', 'danger')
        return redirect(url_for('auth.logout'))


@main_bp.route('/dashboard/student')
@login_required
def student_dashboard():
    """Student dashboard."""
    if current_user.role != 'student':
        flash('Access denied.', 'danger')
        return redirect(url_for('main.dashboard'))
    
    student = Student.query.filter_by(user_id=current_user.id).first()
    
    # Get enrolled courses
    enrollments = Enrollment.query.filter_by(student_id=student.id, status='active').all()
    courses = [e.course for e in enrollments]
    
    # Get recent quiz results
    recent_quizzes = QuizResult.query.filter_by(student_id=student.id)\
        .order_by(QuizResult.completed_at.desc()).limit(5).all()
    
    # Get upcoming study plans
    study_plans = StudyPlan.query.filter_by(student_id=student.id, status='active')\
        .order_by(StudyPlan.created_at.desc()).limit(3).all()
    
    # Get recent chat sessions
    chat_sessions = ChatSession.query.filter_by(student_id=student.id)\
        .order_by(ChatSession.updated_at.desc()).limit(3).all()
    
    # Calculate GPA (simple average)
    marks = Mark.query.filter_by(student_id=student.id).all()
    gpa = sum(m.percentage for m in marks) / len(marks) if marks else 0
    
    # Attendance rate
    attendance_records = Attendance.query.filter_by(student_id=student.id).all()
    attendance_rate = 0
    if attendance_records:
        present = sum(1 for a in attendance_records if a.status == 'present')
        attendance_rate = (present / len(attendance_records)) * 100
    
    return render_template('dashboard_student.html',
                           courses=courses,
                           recent_quizzes=recent_quizzes,
                           study_plans=study_plans,
                           chat_sessions=chat_sessions,
                           gpa=round(gpa, 2),
                           attendance_rate=round(attendance_rate, 1),
                           student=student)


@main_bp.route('/dashboard/lecturer')
@login_required
def lecturer_dashboard():
    """Lecturer dashboard."""
    if current_user.role != 'lecturer':
        flash('Access denied.', 'danger')
        return redirect(url_for('main.dashboard'))
    
    lecturer = Lecturer.query.filter_by(user_id=current_user.id).first()
    
    # Get teaching courses
    courses = Course.query.filter_by(lecturer_id=lecturer.id, is_active=True).all()
    
    # Get total students
    total_students = sum(c.get_student_count() for c in courses)
    
    # Get recent quiz results for their courses
    course_ids = [c.id for c in courses]
    if course_ids:
        recent_quizzes = QuizResult.query.join(Quiz).filter(
            Quiz.course_id.in_(course_ids)
        ).order_by(QuizResult.completed_at.desc()).limit(5).all()
    else:
        recent_quizzes = []
    
    return render_template('dashboard_lecturer.html',
                           courses=courses,
                           total_students=total_students,
                           recent_quizzes=recent_quizzes,
                           lecturer=lecturer)


@main_bp.route('/dashboard/admin')
@login_required
def admin_dashboard():
    """Admin dashboard."""
    if current_user.role != 'admin':
        flash('Access denied.', 'danger')
        return redirect(url_for('main.dashboard'))
    
    # Get statistics
    total_students = Student.query.count()
    total_lecturers = Lecturer.query.count()
    total_courses = Course.query.filter_by(is_active=True).count()
    total_users = User.query.count()
    
    # Recent registrations
    recent_users = User.query.order_by(User.created_at.desc()).limit(10).all()
    
    return render_template('dashboard_admin.html',
                           total_students=total_students,
                           total_lecturers=total_lecturers,
                           total_courses=total_courses,
                           total_users=total_users,
                           recent_users=recent_users)


@main_bp.route('/dashboard/career')
@login_required
def career_advisor_dashboard():
    """Career advisor dashboard."""
    if current_user.role != 'career_advisor':
        flash('Access denied.', 'danger')
        return redirect(url_for('main.dashboard'))
    
    # Get pending CV reviews
    pending_reviews = CVReview.query.filter_by(status='pending').all()
    reviewed_count = CVReview.query.filter_by(status='reviewed').count()
    
    return render_template('dashboard_career.html',
                           pending_reviews=pending_reviews,
                           reviewed_count=reviewed_count)


@main_bp.route('/about')
def about():
    """About page."""
    return render_template('about.html')


@main_bp.route('/help')
def help():
    """Help page."""
    return render_template('help.html')
