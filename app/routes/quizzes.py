import json
from typing import List, Dict, Union, Optional
from dataclasses import dataclass
from flask import (
    Blueprint, render_template, redirect, url_for, 
    flash, request, jsonify, abort, current_app
)
from flask_login import login_required, current_user
from datetime import datetime
from http import HTTPStatus

from app import db
from app.models import Quiz, QuizQuestion, QuizResult, Course, Student, Module, Enrollment, Lecturer

quizzes_bp = Blueprint('quizzes', __name__, url_prefix='/quizzes')


@dataclass
class QuizStats:
    """Data class for quiz statistics."""
    total_questions: int
    total_points: int
    estimated_time: int  # minutes


def check_course_access(course_id: int, require_enrollment: bool = True) -> tuple:
    """
    Verify user has access to course.
    Returns (course, student) tuple or aborts.
    """
    course: Course = Course.query.get_or_404(course_id)
    
    if current_user.role == 'student' and require_enrollment:
        student: Student = Student.query.filter_by(
            user_id=current_user.id
        ).first_or_404()
        
        enrollment: Optional[Enrollment] = Enrollment.query.filter_by(
            student_id=student.id,
            course_id=course_id,
            status='active'
        ).first()
        
        if not enrollment:
            abort(HTTPStatus.FORBIDDEN, 'Active enrollment required')
        
        return course, student
    
    return course, None


def check_quiz_permission(quiz: Quiz, action: str = 'view') -> None:
    """Check if current user can perform action on quiz."""
    if current_user.role == 'admin':
        return
    
    if current_user.role == 'lecturer':
        lecturer: Lecturer = Lecturer.query.filter_by(
            user_id=current_user.id
        ).first()
        if quiz.course.lecturer_id == lecturer.id:
            return
    
    if action == 'take' and current_user.role == 'student':
        return
    
    abort(HTTPStatus.FORBIDDEN)


@quizzes_bp.route('/course/<int:course_id>')
@login_required
def list_quizzes(course_id: int) -> str:
    """List quizzes for a course with role-based filtering."""
    course, student = check_course_access(course_id)
    
    if current_user.role == 'student':
        # Students see only published quizzes with their results
        quizzes: List[Quiz] = Quiz.query.filter_by(
            course_id=course_id,
            is_published=True
        ).order_by(Quiz.created_at.desc()).all()
        
        results: List[QuizResult] = QuizResult.query.filter_by(
            student_id=student.id
        ).all()
        
        completed_ids: set = {r.quiz_id for r in results}
        results_map: Dict[int, QuizResult] = {r.quiz_id: r for r in results}
        
        return render_template(
            'quizzes.html',
            course=course,
            quizzes=quizzes,
            completed_quiz_ids=completed_ids,
            results=results_map
        )
    
    # Lecturers/Admins see all quizzes
    quizzes = Quiz.query.filter_by(course_id=course_id)\
        .order_by(Quiz.created_at.desc()).all()
    
    return render_template(
        'quizzes.html',  # Fixed: was 'quizzes/list.html' - template doesn't exist in subfolder
        course=course,
        quizzes=quizzes,
        is_instructor_view=True
    )


@quizzes_bp.route('/course/<int:course_id>/create', methods=['GET', 'POST'])
@login_required
def create_quiz(course_id: int) -> Union[str, redirect]:
    """Create new quiz with validation."""
    course, _ = check_course_access(course_id, require_enrollment=False)
    
    if current_user.role not in ['lecturer', 'admin']:
        abort(HTTPStatus.FORBIDDEN)
    
    if request.method == 'POST':
        try:
            # Validate input
            title: str = request.form.get('title', '').strip()
            if not title:
                flash('Quiz title is required.', 'danger')
                return render_template('quiz_form.html', course=course)
            
            time_limit: int = int(request.form.get('time_limit', 30))
            passing_score: int = int(request.form.get('passing_score', 60))
            
            if not (0 <= passing_score <= 100):
                raise ValueError("Passing score must be between 0 and 100")
            
            quiz = Quiz(
                course_id=course_id,
                title=title,
                description=request.form.get('description', '').strip(),
                time_limit=max(1, time_limit),
                passing_score=passing_score,
                created_by=current_user.id,
                due_date=datetime.strptime(
                    request.form.get('due_date'), '%Y-%m-%d'
                ) if request.form.get('due_date') else None
            )
            
            db.session.add(quiz)
            db.session.commit()
            
            flash('Quiz created! Now add questions.', 'success')
            return redirect(url_for('quizzes.edit_quiz', quiz_id=quiz.id))
            
        except ValueError as e:
            flash(f'Invalid input: {str(e)}', 'danger')
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f'Quiz creation error: {str(e)}')
            flash('Error creating quiz. Please try again.', 'danger')
    
    return render_template('quiz_form.html', course=course, action='Create')


@quizzes_bp.route('/<int:quiz_id>/submit', methods=['POST'])
@login_required
def submit_quiz(quiz_id: int) -> Union[redirect, tuple]:
    """Submit quiz answers with automatic grading."""
    quiz: Quiz = Quiz.query.get_or_404(quiz_id)
    
    if current_user.role != 'student':
        return jsonify({'error': 'Students only'}), HTTPStatus.FORBIDDEN
    
    student: Student = Student.query.filter_by(
        user_id=current_user.id
    ).first_or_404()
    
    # Check for existing result
    existing: Optional[QuizResult] = QuizResult.query.filter_by(
        quiz_id=quiz_id,
        student_id=student.id
    ).first()
    
    if existing:
        flash('You have already completed this quiz.', 'info')
        return redirect(url_for('quizzes.quiz_result', result_id=existing.id))
    
    try:
        # Process answers
        answers: Dict[str, Optional[str]] = {}
        score: int = 0
        total_points: int = 0
        
        questions: List[QuizQuestion] = QuizQuestion.query\
            .filter_by(quiz_id=quiz_id)\
            .order_by(QuizQuestion.order)\
            .all()
        
        for question in questions:
            answer: Optional[str] = request.form.get(f'question_{question.id}')
            answers[str(question.id)] = answer
            
            total_points += question.points
            if answer and question.check_answer(answer):
                score += question.points
        
        # Calculate metrics
        percentage: float = (score / total_points * 100) if total_points > 0 else 0
        passed: bool = percentage >= quiz.passing_score
        
        # Time tracking
        started_at: Optional[datetime] = None
        if request.form.get('started_at'):
            started_at = datetime.fromisoformat(request.form.get('started_at'))
        
        time_taken: int = 0
        if started_at:
            time_taken = int((datetime.utcnow() - started_at).total_seconds())
        
        # Save result
        result = QuizResult(
            quiz_id=quiz_id,
            student_id=student.id,
            score=score,
            total_points=total_points,
            percentage=round(percentage, 2),
            passed=passed,
            time_taken=time_taken,
            started_at=started_at or datetime.utcnow()
        )
        result.set_answers(answers)
        
        db.session.add(result)
        db.session.commit()
        
        # Flash appropriate message
        if passed:
            flash(f'Congratulations! You passed with {percentage:.1f}%', 'success')
        else:
            flash(f'Quiz completed. Score: {percentage:.1f}% (Pass: {quiz.passing_score}%)', 'warning')
        
        return redirect(url_for('quizzes.quiz_result', result_id=result.id))
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Quiz submission error: {str(e)}')
        flash('Error submitting quiz. Please contact support.', 'danger')
        return redirect(url_for('quizzes.list_quizzes', course_id=quiz.course_id))


@quizzes_bp.route('/<int:quiz_id>/take')
@login_required
def take_quiz(quiz_id: int) -> Union[str, redirect]:
    """Display quiz for students to take."""
    quiz: Quiz = Quiz.query.get_or_404(quiz_id)
    
    if current_user.role != 'student':
        flash('Only students can take quizzes.', 'danger')
        return redirect(url_for('quizzes.list_quizzes', course_id=quiz.course_id))
    
    # Check enrollment
    student: Student = Student.query.filter_by(user_id=current_user.id).first()
    if not student:
        flash('Student profile not found.', 'danger')
        return redirect(url_for('main.dashboard'))
    
    enrollment = Enrollment.query.filter_by(
        student_id=student.id,
        course_id=quiz.course_id
    ).first()
    
    if not enrollment:
        flash('You are not enrolled in this course.', 'warning')
        return redirect(url_for('courses.course_list'))
    
    # Check if already completed
    existing = QuizResult.query.filter_by(
        quiz_id=quiz_id,
        student_id=student.id
    ).first()
    
    if existing:
        flash('You have already completed this quiz.', 'info')
        return redirect(url_for('quizzes.quiz_result', result_id=existing.id))
    
    # Check if quiz is published
    if not quiz.is_published:
        flash('This quiz is not available yet.', 'warning')
        return redirect(url_for('quizzes.list_quizzes', course_id=quiz.course_id))
    
    # Get questions
    questions = QuizQuestion.query.filter_by(quiz_id=quiz_id).order_by(QuizQuestion.order).all()
    
    if not questions:
        flash('No questions in this quiz yet.', 'warning')
        return redirect(url_for('quizzes.list_quizzes', course_id=quiz.course_id))
    
    # Get the course for this quiz
    course = Course.query.get_or_404(quiz.course_id)
    
    return render_template('quiz_take.html', quiz=quiz, questions=questions, course=course, current_time=datetime.utcnow())


@quizzes_bp.route('/result/<int:result_id>')
@login_required
def quiz_result(result_id: int) -> str:
    """Display quiz result after submission."""
    result: QuizResult = QuizResult.query.get_or_404(result_id)
    
    # Check permission - only the student who took the quiz can view results
    if current_user.role == 'student':
        student: Student = Student.query.filter_by(user_id=current_user.id).first_or_404()
        if result.student_id != student.id:
            abort(HTTPStatus.FORBIDDEN)
    
    quiz: Quiz = Quiz.query.get_or_404(result.quiz_id)
    course: Course = Course.query.get_or_404(quiz.course_id)
    
    # Get answers for display
    answers = result.get_answers() if hasattr(result, 'get_answers') else {}
    
    # Get questions for review
    questions = QuizQuestion.query.filter_by(quiz_id=quiz.id).order_by(QuizQuestion.order).all()
    
    return render_template('quiz_result.html', 
                          result=result, 
                          quiz=quiz, 
                          course=course, 
                          answers=answers,
                          questions=questions)


@quizzes_bp.route('/<int:quiz_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_quiz(quiz_id: int) -> Union[str, redirect]:
    """Edit existing quiz."""
    quiz: Quiz = Quiz.query.get_or_404(quiz_id)
    
    # Check permission
    check_quiz_permission(quiz, 'edit')
    
    course = Course.query.get_or_404(quiz.course_id)
    
    # Get modules for the course
    modules = Module.query.filter_by(course_id=course.id).order_by(Module.order).all()
    
    # Get questions
    questions = QuizQuestion.query.filter_by(quiz_id=quiz_id).order_by(QuizQuestion.order).all()
    
    # Handle question form submission
    if request.method == 'POST':
        question_text = request.form.get('question_text', '').strip()
        if question_text:
            question_type = request.form.get('question_type', 'multiple_choice')
            points = int(request.form.get('points', 1))
            module_id = request.form.get('module_id')
            
            # Create new question
            new_question = QuizQuestion(
                quiz_id=quiz_id,
                question_text=question_text,
                question_type=question_type,
                points=points,
                order=len(questions) + 1,
                module_id=int(module_id) if module_id else None
            )
            
            # Handle answer options for multiple choice
            if question_type == 'multiple_choice':
                options = []
                for i in range(1, 5):
                    option_text = request.form.get(f'option_{i}', '').strip()
                    if option_text:
                        is_correct = request.form.get('correct_option') == str(i)
                        options.append({'text': option_text, 'is_correct': is_correct})
                new_question.options_json = json.dumps(options)
            
            # Handle true/false answer
            elif question_type == 'true_false':
                correct_answer = request.form.get('true_false_answer', 'true')
                new_question.correct_answer = correct_answer
            
            # Handle short answer
            elif question_type == 'short_answer':
                new_question.correct_answer = request.form.get('short_answer', '').strip()
            
            db.session.add(new_question)
            db.session.commit()
            flash('Question added successfully!', 'success')
        else:
            flash('Question text is required.', 'danger')
        
        return redirect(url_for('quizzes.edit_quiz', quiz_id=quiz_id))
    
    return render_template('quiz_edit.html', quiz=quiz, course=course, modules=modules, questions=questions)


@quizzes_bp.route('/<int:quiz_id>/publish', methods=['POST'])
@login_required
def publish_quiz(quiz_id: int) -> redirect:
    """Publish or unpublish a quiz."""
    quiz: Quiz = Quiz.query.get_or_404(quiz_id)
    
    # Check permission - only lecturer/admin can publish
    check_quiz_permission(quiz, 'edit')
    
    # Toggle published status
    quiz.is_published = not quiz.is_published
    db.session.commit()
    
    action = 'published' if quiz.is_published else 'unpublished'
    flash(f'Quiz "{quiz.title}" has been {action}.', 'success')
    
    return redirect(url_for('quizzes.list_quizzes', course_id=quiz.course_id))