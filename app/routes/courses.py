from typing import List, Optional, Union
from flask import (
    Blueprint, render_template, redirect, url_for, 
    flash, request, abort, current_app
)
from flask_login import login_required, current_user
from http import HTTPStatus

from app import db
from app.models import Course, Module, Enrollment, Student, Lecturer, CourseMaterial, Quiz
from app.forms.auth_forms import FlaskForm, StringField, TextAreaField, IntegerField, SubmitField
from wtforms.validators import DataRequired, Optional as OptionalValidator

courses_bp = Blueprint('courses', __name__, url_prefix='/courses')


class CourseForm(FlaskForm):
    """Course creation/editing form."""
    code = StringField('Course Code', validators=[DataRequired()])
    name = StringField('Course Name', validators=[DataRequired()])
    description = TextAreaField('Description')
    credits = IntegerField('Credits', default=3)
    semester = StringField('Semester (e.g., Fall 2024)')
    year = IntegerField('Year', default=2024)
    submit = SubmitField('Save Course')


class ModuleForm(FlaskForm):
    """Module creation/editing form."""
    title = StringField('Module Title', validators=[DataRequired()])
    description = TextAreaField('Description')
    order = IntegerField('Order', default=0)
    submit = SubmitField('Save Module')


def get_course_or_404(course_id: int) -> Course:
    """Fetch course with 404 handling."""
    return Course.query.get_or_404(course_id)


def check_course_permission(course: Course, action: str = 'view') -> Optional[Lecturer]:
    """
    Verify user has permission for course action.
    Returns lecturer object if applicable.
    """
    if current_user.role == 'admin':
        return None
    
    if current_user.role == 'lecturer':
        lecturer: Lecturer = Lecturer.query.filter_by(
            user_id=current_user.id
        ).first_or_404()
        
        if course.lecturer_id != lecturer.id:
            abort(HTTPStatus.FORBIDDEN, 'Not authorized for this course')
        
        return lecturer
    
    if action in ['edit', 'delete', 'create_module']:
        abort(HTTPStatus.FORBIDDEN)
    
    return None


def get_student_enrollment(course_id: int) -> tuple:
    """Get student and enrollment for course access check."""
    student: Student = Student.query.filter_by(
        user_id=current_user.id
    ).first_or_404()
    
    enrollment: Optional[Enrollment] = Enrollment.query.filter_by(
        student_id=student.id,
        course_id=course_id
    ).first()
    
    return student, enrollment


@courses_bp.route('/')
@login_required
def index() -> str:
    """List courses based on user role."""
    context = {}
    
    if current_user.role == 'student':
        student: Student = Student.query.filter_by(
            user_id=current_user.id
        ).first_or_404()
        
        # Get enrolled course IDs
        enrollments: List[Enrollment] = Enrollment.query.filter_by(
            student_id=student.id
        ).all()
        
        enrolled_ids: List[int] = [
            e.course_id for e in enrollments if e.status == 'active'
        ]
        
        # All active courses for browsing
        all_courses: List[Course] = Course.query.filter_by(
            is_active=True
        ).order_by(Course.name).all()
        
        context.update({
            'courses': all_courses,
            'enrolled_course_ids': enrolled_ids,
            'enrollments': {e.course_id: e for e in enrollments}
        })
        
    elif current_user.role == 'lecturer':
        lecturer: Lecturer = Lecturer.query.filter_by(
            user_id=current_user.id
        ).first_or_404()
        
        teaching_courses: List[Course] = Course.query.filter_by(
            lecturer_id=lecturer.id
        ).order_by(Course.created_at.desc()).all()
        
        context.update({
            'courses': teaching_courses,
            'is_lecturer_view': True
        })
        
    else:  # admin
        all_courses = Course.query.order_by(
            Course.created_at.desc()
        ).all()
        
        context.update({
            'courses': all_courses,
            'is_admin_view': True
        })
    
    return render_template('courses.html', **context)


@courses_bp.route('/<int:course_id>')
@login_required
def detail(course_id: int) -> str:
    """Course detail page with role-based content."""
    course: Course = get_course_or_404(course_id)
    
    is_enrolled: bool = False
    enrollment: Optional[Enrollment] = None
    
    if current_user.role == 'student':
        _, enrollment = get_student_enrollment(course_id)
        is_enrolled = enrollment is not None and enrollment.status == 'active'
        
        if not is_enrolled and not course.is_active:
            abort(HTTPStatus.FORBIDDEN, 'Course not available')
    
    # Get modules ordered
    modules: List[Module] = Module.query.filter_by(
        course_id=course_id
    ).order_by(Module.order).all()
    
    # Get materials count
    materials_count: int = db.session.query(CourseMaterial).filter_by(
        course_id=course_id, is_published=True
    ).count() if hasattr(CourseMaterial, 'query') else 0
    
    # Get quizzes count
    quizzes_count: int = db.session.query(Quiz).filter_by(
        course_id=course_id, is_published=True
    ).count() if hasattr(Quiz, 'query') else 0
    
    return render_template(
        'course_detail.html',
        course=course,
        is_enrolled=is_enrolled,
        enrollment=enrollment,
        modules=modules,
        materials_count=materials_count,
        quizzes_count=quizzes_count
    )


@courses_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create() -> Union[str, redirect]:
    """Create new course."""
    if current_user.role not in ['lecturer', 'admin']:
        abort(HTTPStatus.FORBIDDEN)
    
    lecturer: Optional[Lecturer] = None
    if current_user.role == 'lecturer':
        lecturer = Lecturer.query.filter_by(
            user_id=current_user.id
        ).first_or_404()
    
    form = CourseForm()
    
    if form.validate_on_submit():
        try:
            course = Course(
                code=form.code.data.strip().upper(),
                name=form.name.data.strip(),
                description=form.description.data.strip() if form.description.data else None,
                credits=form.credits.data or 3,
                semester=form.semester.data.strip() if form.semester.data else None,
                year=form.year.data or datetime.utcnow().year,
                lecturer_id=lecturer.id if lecturer else None
            )
            
            # Admin can assign different lecturer
            if current_user.role == 'admin':
                lecturer_id: Optional[str] = request.form.get('lecturer_id')
                if lecturer_id:
                    course.lecturer_id = int(lecturer_id)
            
            db.session.add(course)
            db.session.commit()
            
            flash(f'Course "{course.name}" created successfully!', 'success')
            return redirect(url_for('courses.detail', course_id=course.id))
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f'Course creation error: {str(e)}')
            flash('Error creating course. Please try again.', 'danger')
    
    # Get lecturers for admin dropdown
    lecturers: List[Lecturer] = []
    if current_user.role == 'admin':
        lecturers = Lecturer.query.join(User).order_by(User.last_name).all()
    
    return render_template(
        'course_form.html',
        form=form,
        action='Create',
        lecturers=lecturers
    )


@courses_bp.route('/<int:course_id>/edit', methods=['GET', 'POST'])
@login_required
def edit(course_id: int) -> Union[str, redirect]:
    """Edit existing course."""
    course: Course = get_course_or_404(course_id)
    check_course_permission(course, action='edit')
    
    form = CourseForm(obj=course)
    
    if form.validate_on_submit():
        try:
            course.code = form.code.data.strip().upper()
            course.name = form.name.data.strip()
            course.description = form.description.data.strip() if form.description.data else None
            course.credits = form.credits.data or 3
            course.semester = form.semester.data.strip() if form.semester.data else None
            course.year = form.year.data or datetime.utcnow().year
            
            db.session.commit()
            
            flash(f'Course "{course.name}" updated successfully!', 'success')
            return redirect(url_for('courses.detail', course_id=course.id))
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f'Course update error: {str(e)}')
            flash('Error updating course. Please try again.', 'danger')
    
    return render_template(
        'course_form.html',
        form=form,
        action='Edit',
        course=course
    )


@courses_bp.route('/<int:course_id>/enroll', methods=['POST'])
@login_required
def enroll(course_id: int) -> redirect:
    """Enroll student in course."""
    if current_user.role != 'student':
        flash('Only students can enroll in courses.', 'danger')
        return redirect(url_for('courses.detail', course_id=course_id))
    
    course: Course = get_course_or_404(course_id)
    student: Student = Student.query.filter_by(
        user_id=current_user.id
    ).first_or_404()
    
    try:
        # Check existing enrollment
        existing: Optional[Enrollment] = Enrollment.query.filter_by(
            student_id=student.id,
            course_id=course_id
        ).first()
        
        if existing:
            if existing.status == 'active':
                flash('You are already enrolled in this course.', 'info')
            elif existing.status == 'dropped':
                existing.status = 'active'
                existing.enrolled_at = datetime.utcnow()
                db.session.commit()
                flash('Re-enrolled successfully!', 'success')
            else:  # completed
                flash('You have completed this course. Contact admin to re-enroll.', 'warning')
        else:
            enrollment = Enrollment(
                student_id=student.id,
                course_id=course_id,
                status='active'
            )
            db.session.add(enrollment)
            db.session.commit()
            flash(f'Successfully enrolled in {course.name}!', 'success')
            
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Enrollment error: {str(e)}')
        flash('Error enrolling in course. Please try again.', 'danger')
    
    return redirect(url_for('courses.detail', course_id=course_id))


@courses_bp.route('/<int:course_id>/unenroll', methods=['POST'])
@login_required
def unenroll(course_id: int) -> redirect:
    """Unenroll student from course."""
    if current_user.role != 'student':
        abort(HTTPStatus.FORBIDDEN)
    
    student: Student = Student.query.filter_by(
        user_id=current_user.id
    ).first_or_404()
    
    enrollment: Optional[Enrollment] = Enrollment.query.filter_by(
        student_id=student.id,
        course_id=course_id,
        status='active'
    ).first()
    
    if not enrollment:
        flash('You are not enrolled in this course.', 'warning')
        return redirect(url_for('courses.detail', course_id=course_id))
    
    try:
        enrollment.status = 'dropped'
        db.session.commit()
        flash('Successfully unenrolled from course.', 'success')
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Unenrollment error: {str(e)}')
        flash('Error processing unenrollment.', 'danger')
    
    return redirect(url_for('courses.detail', course_id=course_id))


@courses_bp.route('/<int:course_id>/modules/create', methods=['GET', 'POST'])
@login_required
def create_module(course_id: int) -> Union[str, redirect]:
    """Create module for course."""
    course: Course = get_course_or_404(course_id)
    check_course_permission(course, action='create_module')
    
    form = ModuleForm()
    
    # Set default order
    if request.method == 'GET':
        last_module: Optional[Module] = Module.query.filter_by(
            course_id=course_id
        ).order_by(Module.order.desc()).first()
        
        form.order.data = (last_module.order + 1) if last_module else 1
    
    if form.validate_on_submit():
        try:
            module = Module(
                course_id=course_id,
                title=form.title.data.strip(),
                description=form.description.data.strip() if form.description.data else None,
                order=form.order.data or 0
            )
            
            db.session.add(module)
            db.session.commit()
            
            flash(f'Module "{module.title}" created!', 'success')
            return redirect(url_for('courses.detail', course_id=course_id))
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f'Module creation error: {str(e)}')
            flash('Error creating module.', 'danger')
    
    return render_template('module_form.html', form=form, course=course)