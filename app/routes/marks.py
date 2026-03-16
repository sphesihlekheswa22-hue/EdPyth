from typing import List, Dict, Optional, Union
from flask import (
    Blueprint, render_template, redirect, url_for, 
    flash, request, abort, current_app
)
from flask_login import login_required, current_user
from datetime import datetime
from http import HTTPStatus

from app import db
from app.models import Mark, Course, Student, Enrollment, Lecturer, User

marks_bp = Blueprint('marks', __name__, url_prefix='/marks')


def check_mark_permission(course_id: int, require_edit: bool = False) -> tuple:
    """Verify access to marks for course."""
    course: Course = Course.query.get_or_404(course_id)
    
    if current_user.role == 'admin':
        return course, None, True
    
    if current_user.role == 'lecturer':
        lecturer: Lecturer = Lecturer.query.filter_by(
            user_id=current_user.id
        ).first_or_404()
        
        if course.lecturer_id != lecturer.id:
            abort(HTTPStatus.FORBIDDEN, 'Not course instructor')
        
        return course, None, True
    
    if current_user.role == 'student':
        if require_edit:
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
            abort(HTTPStatus.FORBIDDEN, 'Not enrolled in course')
        
        return course, student, False
    
    abort(HTTPStatus.FORBIDDEN)


@marks_bp.route('/course/<int:course_id>')
@login_required
def course_marks(course_id: int) -> str:
    """View marks for course."""
    course, student, can_edit = check_mark_permission(course_id)
    
    if student:
        # Student view - own marks only
        marks: List[Mark] = Mark.query.filter_by(
            student_id=student.id,
            course_id=course_id
        ).order_by(Mark.marked_at.desc()).all()
        
        # Calculate statistics
        overall: Dict = {
            'average': 0.0,
            'highest': 0.0,
            'lowest': 0.0,
            'count': len(marks)
        }
        
        if marks:
            percentages: List[float] = [m.percentage for m in marks]
            overall['average'] = sum(percentages) / len(percentages)
            overall['highest'] = max(percentages)
            overall['lowest'] = min(percentages)
        
        # Grade distribution
        grade_counts: Dict[str, int] = {}
        for mark in marks:
            grade: str = mark.grade or 'N/A'
            grade_counts[grade] = grade_counts.get(grade, 0) + 1
        
        # Calculate overall percentage and grade for template
        overall_percentage: float = overall['average']
        overall_grade: str = 'N/A'
        if marks:
            # Use the calculate_grade method to get letter grade from average percentage
            temp_mark = Mark(percentage=overall_percentage)
            overall_grade = temp_mark.calculate_grade()
        
        return render_template(
            'marks_student.html',
            course=course,
            marks=marks,
            overall=overall,
            overall_percentage=overall_percentage,
            overall_grade=overall_grade,
            grade_counts=grade_counts
        )
    
    # Instructor view - all students
    enrollments: List[Enrollment] = Enrollment.query.filter_by(
        course_id=course_id,
        status='active'
    ).all()
    
    student_ids: List[int] = [e.student_id for e in enrollments]
    
    # Get all marks for these students
    all_marks: List[Mark] = Mark.query.filter(
        Mark.course_id == course_id,
        Mark.student_id.in_(student_ids)
    ).order_by(Mark.marked_at.desc()).all()
    
    # Organize by student
    student_marks: Dict[int, Dict] = {}
    
    for e in enrollments:
        student_marks[e.student_id] = {
            'student': e.student,
            'marks': [],
            'total': 0.0,
            'count': 0,
            'average': 0.0
        }
    
    for mark in all_marks:
        if mark.student_id in student_marks:
            student_marks[mark.student_id]['marks'].append(mark)
            student_marks[mark.student_id]['total'] += mark.percentage
            student_marks[mark.student_id]['count'] += 1
    
    # Calculate averages
    for sid, data in student_marks.items():
        if data['count'] > 0:
            data['average'] = data['total'] / data['count']
    
    # Assessment types for filtering
    assessment_types: List[str] = db.session.query(
        Mark.assessment_type
    ).filter_by(course_id=course_id).distinct().all()
    
    return render_template(
        'marks_course.html',
        course=course,
        student_marks=student_marks,
        assessment_types=[t[0] for t in assessment_types if t[0]],
        can_edit=can_edit
    )


@marks_bp.route('/course/<int:course_id>/enter', methods=['GET', 'POST'])
@login_required
def enter_marks(course_id: int) -> Union[str, redirect]:
    """Enter marks for assessment."""
    course, _, can_edit = check_mark_permission(course_id, require_edit=True)
    
    if not can_edit:
        abort(HTTPStatus.FORBIDDEN)
    
    if request.method == 'POST':
        try:
            assessment_type: str = request.form.get('assessment_type', '').strip()
            assessment_name: str = request.form.get('assessment_name', '').strip()
            total_marks: float = float(request.form.get('total_marks', 100))
            
            if not assessment_type or not assessment_name:
                flash('Assessment type and name are required.', 'danger')
                return redirect(request.url)
            
            if total_marks <= 0:
                flash('Total marks must be greater than 0.', 'danger')
                return redirect(request.url)
            
            # Get enrolled students
            enrollments: List[Enrollment] = Enrollment.query.filter_by(
                course_id=course_id,
                status='active'
            ).all()
            
            marks_entered: int = 0
            
            for enrollment in enrollments:
                student_id: int = enrollment.student_id
                mark_value_str: Optional[str] = request.form.get(f'mark_{student_id}')
                
                if not mark_value_str or not mark_value_str.strip():
                    continue  # Skip empty marks
                
                try:
                    mark_value: float = float(mark_value_str)
                except ValueError:
                    flash(f'Invalid mark for student {enrollment.student.user.full_name}', 'warning')
                    continue
                
                # Validate range
                if mark_value < 0 or mark_value > total_marks:
                    flash(
                        f'Mark for {enrollment.student.user.full_name} must be between 0 and {total_marks}',
                        'warning'
                    )
                    continue
                
                percentage: float = (mark_value / total_marks) * 100
                
                # Check for existing mark
                existing: Optional[Mark] = Mark.query.filter_by(
                    course_id=course_id,
                    student_id=student_id,
                    assessment_type=assessment_type,
                    assessment_name=assessment_name
                ).first()
                
                if existing:
                    # Update existing
                    existing.mark = mark_value
                    existing.total_marks = total_marks
                    existing.percentage = percentage
                    existing.grade = existing.calculate_grade()
                    existing.feedback = request.form.get(f'feedback_{student_id}', '').strip()
                    existing.marked_at = datetime.utcnow()
                else:
                    # Create new
                    new_mark = Mark(
                        course_id=course_id,
                        student_id=student_id,
                        assessment_type=assessment_type,
                        assessment_name=assessment_name,
                        mark=mark_value,
                        total_marks=total_marks,
                        percentage=percentage,
                        grade='',
                        recorded_by=current_user.id,
                        feedback=request.form.get(f'feedback_{student_id}', '').strip()
                    )
                    new_mark.grade = new_mark.calculate_grade()
                    db.session.add(new_mark)
                
                marks_entered += 1
            
            db.session.commit()
            
            if marks_entered > 0:
                flash(f'Successfully entered/updated {marks_entered} marks.', 'success')
            else:
                flash('No marks were entered.', 'warning')
            
            return redirect(url_for('marks.course_marks', course_id=course_id))
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f'Mark entry error: {str(e)}')
            flash('Error saving marks. Please try again.', 'danger')
    
    # GET request
    enrollments: List[Enrollment] = Enrollment.query.filter_by(
        course_id=course_id,
        status='active'
    ).join(Student).join(User).order_by(User.last_name).all()
    
    # Get existing assessment types for dropdown
    assessment_types: List[str] = db.session.query(
        Mark.assessment_type
    ).filter_by(course_id=course_id).distinct().all()
    
    return render_template(
        'marks_enter.html',
        course=course,
        students=enrollments,
        assessment_types=[t[0] for t in assessment_types if t[0]]
    )


@marks_bp.route('/student')
@login_required
def my_marks() -> str:
    """Student's complete marks summary."""
    if current_user.role != 'student':
        abort(HTTPStatus.FORBIDDEN)
    
    student: Student = Student.query.filter_by(
        user_id=current_user.id
    ).first_or_404()
    
    # Get all marks with course info
    marks: List[Mark] = Mark.query.filter_by(
        student_id=student.id
    ).order_by(Mark.marked_at.desc()).all()
    
    # Overall statistics
    gpa: float = 0.0
    if marks:
        gpa = sum(m.percentage for m in marks) / len(marks)
    
    # Group by course
    courses_data: Dict[int, Dict] = {}
    
    for mark in marks:
        cid: int = mark.course_id
        if cid not in courses_data:
            courses_data[cid] = {
                'course': mark.course,
                'marks': [],
                'average': 0.0,
                'highest': 0.0,
                'lowest': 100.0
            }
        
        courses_data[cid]['marks'].append(mark)
    
    # Calculate course averages
    for cid, data in courses_data.items():
        if data['marks']:
            percentages: List[float] = [m.percentage for m in data['marks']]
            data['average'] = sum(percentages) / len(percentages)
            data['highest'] = max(percentages)
            data['lowest'] = min(percentages)
    
    # Recent activity
    recent_marks: List[Mark] = marks[:5]
    
    return render_template(
        'marks_summary.html',
        marks=marks,
        courses=courses_data,
        gpa=round(gpa, 2),
        recent_marks=recent_marks,
        total_courses=len(courses_data)
    )