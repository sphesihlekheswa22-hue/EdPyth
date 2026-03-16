from typing import List, Dict, Optional, Union
from flask import (
    Blueprint, render_template, redirect, url_for, 
    flash, request, abort, current_app, jsonify
)
from flask_login import login_required, current_user
from datetime import datetime, date
from http import HTTPStatus

from app import db
from app.models import Attendance, Course, Student, Enrollment, Lecturer, User

attendance_bp = Blueprint('attendance', __name__, url_prefix='/attendance')


def check_attendance_permission(course_id: int, require_record: bool = False) -> tuple:
    """Verify access to attendance records."""
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
        if require_record:
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
            abort(HTTPStatus.FORBIDDEN, 'Not enrolled')
        
        return course, student, False
    
    abort(HTTPStatus.FORBIDDEN)


@attendance_bp.route('/course/<int:course_id>')
@login_required
def course_attendance(course_id: int) -> str:
    """View attendance for course."""
    course, student, can_record = check_attendance_permission(course_id)
    
    if student:
        # Student personal view
        records: List[Attendance] = Attendance.query.filter_by(
            student_id=student.id,
            course_id=course_id
        ).order_by(Attendance.date.desc()).all()
        
        # Calculate stats
        stats: Dict = {
            'total': len(records),
            'present': sum(1 for r in records if r.status == 'present'),
            'absent': sum(1 for r in records if r.status == 'absent'),
            'excused': sum(1 for r in records if r.status == 'excused'),
            'late': sum(1 for r in records if r.status == 'late')
        }
        
        stats['rate'] = (
            (stats['present'] / stats['total'] * 100) if stats['total'] > 0 else 0
        )
        
        return render_template(
            'attendance_student.html',
            course=course,
            records=records,
            stats=stats
        )
    
    # Instructor view
    enrollments: List[Enrollment] = Enrollment.query.filter_by(
        course_id=course_id,
        status='active'
    ).join(Student).join(User).order_by(User.last_name).all()
    
    students: List[Student] = [e.student for e in enrollments]
    
    # Get recent attendance dates (last 30 days)
    recent_dates: List[date] = db.session.query(
        Attendance.date
    ).filter_by(course_id=course_id).distinct().order_by(
        Attendance.date.desc()
    ).limit(30).all()
    
    recent_dates = [d[0] for d in recent_dates]
    
    # Get all records for matrix view
    all_records: List[Attendance] = Attendance.query.filter(
        Attendance.course_id == course_id,
        Attendance.date.in_(recent_dates)
    ).all()
    
    # Organize as matrix: student_id -> date -> status
    matrix: Dict[int, Dict[date, str]] = {}
    for e in enrollments:
        matrix[e.student_id] = {}
    
    for record in all_records:
        if record.student_id in matrix:
            matrix[record.student_id][record.date] = record.status
    
    # Calculate rates per student
    student_stats: Dict[int, Dict] = {}
    for e in enrollments:
        sid: int = e.student_id
        student_records: List[Attendance] = [
            r for r in all_records if r.student_id == sid
        ]
        
        present_count: int = sum(1 for r in student_records if r.status == 'present')
        total_count: int = len(student_records)
        
        student_stats[sid] = {
            'present': present_count,
            'total': total_count,
            'rate': (present_count / total_count * 100) if total_count > 0 else 0
        }
    
    return render_template(
        'attendance_course.html',
        course=course,
        students=students,
        dates=recent_dates,
        matrix=matrix,
        student_stats=student_stats,
        can_record=can_record
    )


@attendance_bp.route('/course/<int:course_id>/record', methods=['GET', 'POST'])
@login_required
def record_attendance(course_id: int) -> Union[str, redirect]:
    """Record attendance for a session."""
    course, _, can_record = check_attendance_permission(course_id, require_record=True)
    
    if not can_record:
        abort(HTTPStatus.FORBIDDEN)
    
    if request.method == 'POST':
        try:
            attendance_date_str: str = request.form.get('date', '')
            if not attendance_date_str:
                flash('Date is required.', 'danger')
                return redirect(request.url)
            
            attendance_date: date = date.fromisoformat(attendance_date_str)
            
            # Validate date not in future
            if attendance_date > date.today():
                flash('Cannot record attendance for future dates.', 'danger')
                return redirect(request.url)
            
            # Get enrolled students
            enrollments: List[Enrollment] = Enrollment.query.filter_by(
                course_id=course_id,
                status='active'
            ).all()
            
            records_updated: int = 0
            records_created: int = 0
            
            for enrollment in enrollments:
                student_id: int = enrollment.student_id
                status: str = request.form.get(f'status_{student_id}', 'absent')
                notes: str = request.form.get(f'notes_{student_id}', '').strip()
                
                # Validate status
                valid_statuses: List[str] = ['present', 'absent', 'excused', 'late']
                if status not in valid_statuses:
                    status = 'absent'
                
                # Check for existing record
                existing: Optional[Attendance] = Attendance.query.filter_by(
                    course_id=course_id,
                    student_id=student_id,
                    date=attendance_date
                ).first()
                
                if existing:
                    existing.status = status
                    existing.notes = notes if notes else existing.notes
                    existing.recorded_by = current_user.id
                    existing.updated_at = datetime.utcnow()
                    records_updated += 1
                else:
                    attendance = Attendance(
                        course_id=course_id,
                        student_id=student_id,
                        date=attendance_date,
                        status=status,
                        recorded_by=current_user.id,
                        notes=notes if notes else None
                    )
                    db.session.add(attendance)
                    records_created += 1
            
            db.session.commit()
            
            total: int = records_updated + records_created
            flash(
                f'Attendance recorded for {total} students '
                f'({records_created} new, {records_updated} updated).',
                'success'
            )
            
            return redirect(url_for('attendance.course_attendance', course_id=course_id))
            
        except ValueError as e:
            flash(f'Invalid date format: {str(e)}', 'danger')
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f'Attendance recording error: {str(e)}')
            flash('Error recording attendance. Please try again.', 'danger')
    
    # GET request
    enrollments: List[Enrollment] = Enrollment.query.filter_by(
        course_id=course_id,
        status='active'
    ).join(Student).join(User).order_by(User.last_name).all()
    
    today: date = date.today()
    
    # Check for existing records today
    existing_records: List[Attendance] = Attendance.query.filter_by(
        course_id=course_id,
        date=today
    ).all()
    
    existing_dict: Dict[int, Attendance] = {r.student_id: r for r in existing_records}
    
    # Calculate attendance trend
    recent_stats: Dict = {
        'average_rate': 0.0,
        'total_sessions': 0
    }
    
    recent_records: List[Attendance] = Attendance.query.filter_by(
        course_id=course_id
    ).order_by(Attendance.date.desc()).limit(100).all()
    
    if recent_records:
        by_date: Dict[date, List[Attendance]] = {}
        for r in recent_records:
            if r.date not in by_date:
                by_date[r.date] = []
            by_date[r.date].append(r)
        
        rates: List[float] = []
        for d, records in by_date.items():
            present: int = sum(1 for r in records if r.status == 'present')
            rates.append(present / len(records) * 100)
        
        recent_stats['average_rate'] = sum(rates) / len(rates) if rates else 0
        recent_stats['total_sessions'] = len(by_date)
    
    return render_template(
        'attendance_record.html',
        course=course,
        students=enrollments,
        existing_records=existing_dict,
        date=today,
        recent_stats=recent_stats
    )


@attendance_bp.route('/student')
@login_required
def my_attendance() -> str:
    """Student's attendance summary across all courses."""
    if current_user.role != 'student':
        abort(HTTPStatus.FORBIDDEN)
    
    student: Student = Student.query.filter_by(
        user_id=current_user.id
    ).first_or_404()
    
    # Get all records
    records: List[Attendance] = Attendance.query.filter_by(
        student_id=student.id
    ).order_by(Attendance.date.desc()).all()
    
    # Overall stats
    overall: Dict = {
        'total': len(records),
        'present': sum(1 for r in records if r.status == 'present'),
        'absent': sum(1 for r in records if r.status == 'absent'),
        'excused': sum(1 for r in records if r.status == 'excused'),
        'late': sum(1 for r in records if r.status == 'late'),
        'rate': 0.0
    }
    
    overall['rate'] = (
        (overall['present'] / overall['total'] * 100) if overall['total'] > 0 else 0
    )
    
    # Group by course
    courses_data: Dict[int, Dict] = {}
    
    for record in records:
        cid: int = record.course_id
        if cid not in courses_data:
            courses_data[cid] = {
                'course': record.course,
                'records': [],
                'stats': {
                    'present': 0, 'absent': 0, 'excused': 0, 
                    'late': 0, 'total': 0, 'rate': 0.0
                }
            }
        
        courses_data[cid]['records'].append(record)
        courses_data[cid]['stats']['total'] += 1
        courses_data[cid]['stats'][record.status] += 1
    
    # Calculate course rates
    for cid, data in courses_data.items():
        stats = data['stats']
        stats['rate'] = (
            (stats['present'] / stats['total'] * 100) 
            if stats['total'] > 0 else 0
        )
    
    # Recent activity (last 7 days)
    recent_cutoff: date = date.today() - datetime.timedelta(days=7)
    recent_records: List[Attendance] = [
        r for r in records if r.date >= recent_cutoff
    ]
    
    return render_template(
        'attendance_summary.html',
        records=records,
        courses=courses_data,
        overall=overall,
        recent_records=recent_records
    )