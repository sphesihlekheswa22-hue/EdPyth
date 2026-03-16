from flask import Blueprint, render_template, jsonify
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from sqlalchemy import func
import random
from app import db
from app.models import (
    User, Student, Lecturer, Course, Enrollment, QuizResult, 
    Attendance, Mark, CourseMaterial, RiskScore
)

analytics_bp = Blueprint('analytics', __name__, url_prefix='/analytics')


@analytics_bp.route('/dashboard')
@login_required
def dashboard():
    """Analytics dashboard."""
    if current_user.role == 'admin':
        return admin_analytics()
    elif current_user.role == 'lecturer':
        return lecturer_analytics()
    elif current_user.role == 'student':
        return student_analytics()
    else:
        abort(403)


@analytics_bp.route('/admin')
@login_required
def admin_analytics():
    """Admin analytics dashboard."""
    if current_user.role != 'admin':
        abort(403)
    
    # User statistics
    total_students = Student.query.count()
    total_lecturers = Lecturer.query.count()
    total_courses = Course.query.filter_by(is_active=True).count()
    total_users = User.query.count()
    
    # Recent activity
    new_students_30d = User.query.filter(
        User.role == 'student',
        User.created_at >= datetime.utcnow() - timedelta(days=30)
    ).count()
    
    # Enrollment trends
    enrollments_by_month = db.session.query(
        func.extract('month', Enrollment.enrolled_at).label('month'),
        func.count(Enrollment.id).label('count')
    ).filter(
        Enrollment.enrolled_at >= datetime.utcnow() - timedelta(days=365)
    ).group_by('month').all()
    
    # Course popularity
    popular_courses = db.session.query(
        Course.name,
        func.count(Enrollment.id).label('enrollments')
    ).join(Enrollment).group_by(Course.id).order_by(func.count(Enrollment.id).desc()).limit(10).all()
    
    # Quiz performance
    avg_quiz_score = db.session.query(func.avg(QuizResult.percentage)).scalar() or 0
    
    # At-risk students
    at_risk = RiskScore.query.filter(
        RiskScore.risk_level.in_(['high', 'critical'])
    ).count()
    
    return render_template('analytics_admin.html',
                          total_students=total_students,
                          total_lecturers=total_lecturers,
                          total_courses=total_courses,
                          total_users=total_users,
                          new_students_30d=new_students_30d,
                          enrollments_by_month=enrollments_by_month,
                          popular_courses=popular_courses,
                          avg_quiz_score=round(avg_quiz_score, 1),
                          at_risk=at_risk)


@analytics_bp.route('/lecturer')
@login_required
def lecturer_analytics():
    """Lecturer analytics dashboard."""
    if current_user.role != 'lecturer':
        abort(403)
    
    lecturer = Lecturer.query.filter_by(user_id=current_user.id).first()
    
    # Get lecturer's courses
    courses = Course.query.filter_by(lecturer_id=lecturer.id).all()
    course_ids = [c.id for c in courses]
    
    # Course statistics
    total_students = sum(c.get_student_count() for c in courses)
    total_materials = CourseMaterial.query.filter(
        CourseMaterial.course_id.in_(course_ids)
    ).count() if course_ids else 0
    
    # Quiz performance per course
    course_performance = []
    for course in courses:
        avg_score = db.session.query(func.avg(QuizResult.percentage)).join(
            QuizResult.quiz
        ).filter(QuizResult.quiz.has(course_id=course.id)).scalar() or 0
        
        course_performance.append({
            'code': course.code,
            'name': course.name,
            'avg_score': round(avg_score, 1),
            'students': course.get_student_count(),
            'student_count': course.get_student_count(),
            'pass_rate': round(80 + random.random() * 15, 1),  # Placeholder
            'attendance': round(75 + random.random() * 20, 1),  # Placeholder
            'submission_rate': round(70 + random.random() * 25, 1)  # Placeholder
        })
    
    # Attendance rates
    attendance_rates = []
    for course in courses:
        total = Attendance.query.filter_by(course_id=course.id).count()
        if total > 0:
            present = Attendance.query.filter_by(
                course_id=course.id, status='present'
            ).count()
            rate = (present / total) * 100
        else:
            rate = 0
        attendance_rates.append({
            'code': course.code,
            'name': course.name,
            'rate': round(rate, 1)
        })
    
    # At-risk students in lecturer's courses
    at_risk_students = []
    if course_ids:
        risk_scores = RiskScore.query.filter(
            RiskScore.course_id.in_(course_ids),
            RiskScore.risk_level.in_(['high', 'critical'])
        ).all()
        
        for rs in risk_scores:
            student = Student.query.get(rs.student_id)
            if student and student.user:
                # Calculate attendance for this student in lecturer's courses
                attendance_records = Attendance.query.filter(
                    Attendance.student_id == student.id,
                    Attendance.course_id.in_(course_ids)
                ).all()
                total_att = len(attendance_records)
                present_att = sum(1 for a in attendance_records if a.status == 'present')
                attendance_pct = round((present_att / total_att) * 100, 1) if total_att > 0 else 0
                
                # Get average mark for student in lecturer's courses
                marks = Mark.query.join(Course).filter(
                    Mark.student_id == student.id,
                    Course.id.in_(course_ids)
                ).all()
                avg_score = round(sum(m.percentage for m in marks) / len(marks), 1) if marks else 0
                
                at_risk_students.append({
                    'id': student.id,
                    'name': student.user.full_name,
                    'risk_score': rs.risk_score,
                    'attendance': attendance_pct,
                    'avg_score': avg_score
                })
    
    return render_template('analytics_lecturer.html',
                          courses=courses,
                          total_students=total_students,
                          total_materials=total_materials,
                          course_performance=course_performance,
                          attendance_rates=attendance_rates,
                          at_risk_students=at_risk_students)


@analytics_bp.route('/student')
@login_required
def student_analytics():
    """Student analytics dashboard."""
    if current_user.role != 'student':
        abort(403)
    
    student = Student.query.filter_by(user_id=current_user.id).first()
    
    # Academic performance
    marks = Mark.query.filter_by(student_id=student.id).all()
    avg_mark = sum(m.percentage for m in marks) / len(marks) if marks else 0
    
    # Quiz performance
    quiz_results = QuizResult.query.filter_by(student_id=student.id).all()
    avg_quiz = sum(r.percentage for r in quiz_results) / len(quiz_results) if quiz_results else 0
    quizzes_passed = sum(1 for r in quiz_results if r.passed)
    
    # Attendance
    attendance = Attendance.query.filter_by(student_id=student.id).all()
    attendance_rate = 0
    if attendance:
        present = sum(1 for a in attendance if a.status == 'present')
        attendance_rate = (present / len(attendance)) * 100
    
    # Course progress
    enrollments = Enrollment.query.filter_by(student_id=student.id, status='active').all()
    course_progress = []
    for e in enrollments:
        course = e.course
        
        # Calculate progress
        course_marks = Mark.query.filter_by(student_id=student.id, course_id=course.id).all()
        course_quizzes = QuizResult.query.join(QuizResult.quiz).filter(
            QuizResult.student_id == student.id,
            QuizResult.quiz.has(course_id=course.id)
        ).all()
        
        course_avg = 0
        if course_marks:
            course_avg = sum(m.percentage for m in course_marks) / len(course_marks)
        
        course_progress.append({
            'id': course.id,
            'name': course.name,
            'avg': round(course_avg, 1),
            'marks_count': len(course_marks),
            'quizzes_count': len(course_quizzes)
        })
    
    # Risk assessment
    risk = RiskScore.query.filter_by(student_id=student.id).first()
    
    return render_template('analytics_student.html',
                          avg_mark=round(avg_mark, 1),
                          avg_quiz=round(avg_quiz, 1),
                          quizzes_passed=quizzes_passed,
                          total_quizzes=len(quiz_results),
                          attendance_rate=round(attendance_rate, 1),
                          course_progress=course_progress,
                          risk=risk)


@analytics_bp.route('/api/enrollment-trend')
@login_required
def enrollment_trend_api():
    """API for enrollment trend data."""
    if current_user.role != 'admin':
        return jsonify({'error': 'Access denied'}), 403
    
    # Get last 12 months of enrollment data
    data = db.session.query(
        func.extract('year', Enrollment.enrolled_at).label('year'),
        func.extract('month', Enrollment.enrolled_at).label('month'),
        func.count(Enrollment.id).label('count')
    ).filter(
        Enrollment.enrolled_at >= datetime.utcnow() - timedelta(days=365)
    ).group_by('year', 'month').all()
    
    result = []
    for d in data:
        result.append({
            'year': int(d.year),
            'month': int(d.month),
            'count': d.count
        })
    
    return jsonify(result)


@analytics_bp.route('/api/quiz-performance/<int:course_id>')
@login_required
def quiz_performance_api(course_id):
    """API for quiz performance in a course."""
    if current_user.role not in ['lecturer', 'admin']:
        return jsonify({'error': 'Access denied'}), 403
    
    results = db.session.query(
        QuizResult.student_id,
        func.avg(QuizResult.percentage).label('avg_score'),
        func.count(QuizResult.id).label('quiz_count')
    ).join(QuizResult.quiz).filter(
        QuizResult.quiz.has(course_id=course_id)
    ).group_by(QuizResult.student_id).all()
    
    result = []
    for r in results:
        student = Student.query.get(r.student_id)
        result.append({
            'student_name': student.user.full_name if student else 'Unknown',
            'avg_score': round(r.avg_score, 1),
            'quiz_count': r.quiz_count
        })
    
    return jsonify(result)
