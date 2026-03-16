import os
import json
from typing import List, Optional, Union
from werkzeug.utils import secure_filename
from flask import (
    Blueprint, render_template, redirect, url_for, 
    flash, request, send_from_directory, current_app, abort
)
from flask_login import login_required, current_user
from datetime import datetime
from http import HTTPStatus

from app import db
from app.models import CVReview, Student, User

career_bp = Blueprint('career', __name__, url_prefix='/career')


# Configuration
ALLOWED_CV_EXTENSIONS: set = {'pdf', 'doc', 'docx'}
MAX_CV_SIZE: int = 10 * 1024 * 1024  # 10MB


def allowed_cv_file(filename: str) -> bool:
    """Check if CV file extension is allowed."""
    return (
        '.' in filename and 
        filename.rsplit('.', 1)[1].lower() in ALLOWED_CV_EXTENSIONS
    )


def get_cv_upload_path(student_id: int, filename: str) -> str:
    """Generate secure upload path for CV."""
    upload_folder: str = current_app.config.get('UPLOAD_FOLDER', 'uploads')
    cv_folder: str = os.path.join(upload_folder, 'cv', str(student_id))
    os.makedirs(cv_folder, exist_ok=True)
    return os.path.join(cv_folder, secure_filename(filename))


def get_ai_client():
    """Get NVIDIA AI client with error handling."""
    api_key: Optional[str] = current_app.config.get('NVIDIA_API_KEY')
    if not api_key:
        return None
    
    try:
        import openai
        return openai.OpenAI(
            base_url="https://integrate.api.nvidia.com/v1",
            api_key=api_key
        )
    except ImportError:
        current_app.logger.warning('OpenAI package not installed')
        return None
    except Exception as e:
        current_app.logger.error(f'AI client error: {str(e)}')
        return None


def check_cv_access(review: CVReview, require_advisor: bool = False) -> None:
    """Verify access to CV review."""
    if current_user.role == 'admin':
        return
    
    if current_user.role == 'career_advisor':
        if require_advisor:
            return
        # Advisors can view all pending/reviewed
        return
    
    if current_user.role == 'student':
        student: Student = Student.query.filter_by(
            user_id=current_user.id
        ).first_or_404()
        
        if review.student_id != student.id:
            abort(HTTPStatus.FORBIDDEN, 'Not your CV review')
        
        return
    
    abort(HTTPStatus.FORBIDDEN)


@career_bp.route('/dashboard')
@login_required
def dashboard() -> str:
    """Career dashboard for students."""
    if current_user.role != 'student':
        abort(HTTPStatus.FORBIDDEN)
    
    student: Student = Student.query.filter_by(
        user_id=current_user.id
    ).first_or_404()
    
    # Get CV reviews
    reviews: List[CVReview] = CVReview.query.filter_by(
        student_id=student.id
    ).order_by(CVReview.created_at.desc()).all()
    
    latest: Optional[CVReview] = reviews[0] if reviews else None
    
    # Calculate stats
    stats: Dict = {
        'total_uploads': len(reviews),
        'pending': sum(1 for r in reviews if r.status == 'pending'),
        'reviewed': sum(1 for r in reviews if r.status == 'reviewed'),
        'average_score': None
    }
    
    reviewed_scores: List[float] = [
        r.job_readiness_score for r in reviews 
        if r.status == 'reviewed' and r.job_readiness_score
    ]
    
    if reviewed_scores:
        stats['average_score'] = sum(reviewed_scores) / len(reviewed_scores)
    
    return render_template(
        'career_dashboard.html',
        reviews=reviews,
        latest_review=latest,
        stats=stats
    )


@career_bp.route('/upload-cv', methods=['GET', 'POST'])
@login_required
def upload_cv() -> Union[str, redirect]:
    """Upload CV for review."""
    if current_user.role != 'student':
        abort(HTTPStatus.FORBIDDEN)
    
    student: Student = Student.query.filter_by(
        user_id=current_user.id
    ).first_or_404()
    
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file selected.', 'danger')
            return redirect(request.url)
        
        file = request.files['file']
        
        if file.filename == '':
            flash('No file selected.', 'danger')
            return redirect(request.url)
        
        if not allowed_cv_file(file.filename):
            flash(
                f'Invalid file type. Allowed: {", ".join(ALLOWED_CV_EXTENSIONS)}',
                'danger'
            )
            return redirect(request.url)
        
        try:
            # Check file size
            file.seek(0, os.SEEK_END)
            file_size: int = file.tell()
            file.seek(0)
            
            if file_size > MAX_CV_SIZE:
                flash(f'File too large. Maximum: {MAX_CV_SIZE // (1024*1024)}MB', 'danger')
                return redirect(request.url)
            
            # Save file
            filename: str = secure_filename(file.filename)
            file_path: str = get_cv_upload_path(student.id, filename)
            
            # Handle duplicate filename
            if os.path.exists(file_path):
                name, ext = os.path.splitext(filename)
                filename = f"{name}_{int(datetime.utcnow().timestamp())}{ext}"
                file_path = get_cv_upload_path(student.id, filename)
            
            file.save(file_path)
            
            # Create review record
            review = CVReview(
                student_id=student.id,
                file_path=f'/static/uploads/cv/{student.id}/{filename}',
                file_name=filename,
                file_size=file_size,
                status='pending',
                upload_notes=request.form.get('notes', '').strip() or None
            )
            
            db.session.add(review)
            db.session.commit()
            
            flash(
                'CV uploaded successfully! A career advisor will review it soon.',
                'success'
            )
            return redirect(url_for('career.dashboard'))
            
        except Exception as e:
            db.session.rollback()
            if 'file_path' in locals() and os.path.exists(file_path):
                os.remove(file_path)
            
            current_app.logger.error(f'CV upload error: {str(e)}')
            flash('Error uploading CV. Please try again.', 'danger')
    
    # Get upload history for context
    recent_uploads: List[CVReview] = CVReview.query.filter_by(
        student_id=student.id
    ).order_by(CVReview.created_at.desc()).limit(3).all()
    
    return render_template(
        'cv_upload.html',
        recent_uploads=recent_uploads,
        max_size_mb=MAX_CV_SIZE // (1024*1024)
    )


@career_bp.route('/cv/<int:review_id>')
@login_required
def view_cv_review(review_id: int) -> str:
    """View CV review details."""
    review: CVReview = CVReview.query.get_or_404(review_id)
    check_cv_access(review)
    
    # Parse JSON fields
    suggested_skills: List[str] = []
    suggested_projects: List[str] = []
    
    if review.suggested_skills:
        try:
            suggested_skills = json.loads(review.suggested_skills)
        except json.JSONDecodeError:
            pass
    
    if review.suggested_projects:
        try:
            suggested_projects = json.loads(review.suggested_projects)
        except json.JSONDecodeError:
            pass
    
    # Get student info for advisors
    student_info: Optional[Dict] = None
    if current_user.role in ['career_advisor', 'admin']:
        student_info = {
            'name': review.student.user.full_name,
            'program': review.student.program,
            'year': review.student.year_of_study,
            'email': review.student.user.email
        }
    
    return render_template(
        'advisor_cv_review.html',
        review=review,
        suggested_skills=suggested_skills,
        suggested_projects=suggested_projects,
        student_info=student_info
    )


@career_bp.route('/advisor/reviews')
@login_required
def advisor_reviews() -> str:
    """Career advisor review queue."""
    if current_user.role not in ['career_advisor', 'admin']:
        abort(HTTPStatus.FORBIDDEN)
    
    status: str = request.args.get('status', 'pending')
    
    query = CVReview.query
    
    if status == 'pending':
        query = query.filter_by(status='pending')
    else:
        query = query.filter(CVReview.status != 'pending')
    
    reviews: List[CVReview] = query.order_by(
        CVReview.created_at.desc() if status != 'pending' else CVReview.created_at.asc()
    ).all()
    
    # Statistics
    stats: Dict = {
        'pending': CVReview.query.filter_by(status='pending').count(),
        'reviewed_today': CVReview.query.filter(
            CVReview.status == 'reviewed',
            CVReview.reviewed_at >= datetime.utcnow().date()
        ).count(),
        'total_reviewed': CVReview.query.filter_by(status='reviewed').count()
    }
    
    return render_template(
        'advisor_reviews.html',
        reviews=reviews,
        status=status,
        stats=stats
    )


@career_bp.route('/advisor/review/<int:review_id>', methods=['GET', 'POST'])
@login_required
def advisor_review_cv(review_id: int) -> Union[str, redirect]:
    """Career advisor reviews CV."""
    if current_user.role not in ['career_advisor', 'admin']:
        abort(HTTPStatus.FORBIDDEN)
    
    review: CVReview = CVReview.query.get_or_404(review_id)
    
    if request.method == 'POST':
        try:
            # Validate score
            score: float = float(request.form.get('score', 0))
            score = max(0, min(100, score))  # Clamp 0-100
            
            review.job_readiness_score = score
            review.status = 'reviewed'
            review.strengths = request.form.get('strengths', '').strip() or None
            review.weaknesses = request.form.get('weaknesses', '').strip() or None
            review.recommendations = request.form.get('recommendations', '').strip() or None
            
            # Parse skills
            skills_text: str = request.form.get('suggested_skills', '')
            skills: List[str] = [s.strip() for s in skills_text.split('\n') if s.strip()]
            review.suggested_skills = json.dumps(skills)
            
            # Parse projects
            projects_text: str = request.form.get('suggested_projects', '')
            projects: List[str] = [p.strip() for p in projects_text.split('\n') if p.strip()]
            review.suggested_projects = json.dumps(projects)
            
            review.interview_tips = request.form.get('interview_tips', '').strip() or None
            review.reviewed_by = current_user.id
            review.reviewed_at = datetime.utcnow()
            
            db.session.commit()
            
            flash('CV review submitted successfully!', 'success')
            return redirect(url_for('career.advisor_reviews'))
            
        except ValueError as e:
            flash(f'Invalid score value: {str(e)}', 'danger')
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f'CV review error: {str(e)}')
            flash('Error saving review. Please try again.', 'danger')
    
    # Get student context
    student: Student = review.student
    
    return render_template(
        'advisor_cv_review.html',
        review=review,
        student=student
    )


@career_bp.route('/advisor/ai-review/<int:review_id>', methods=['POST'])
@login_required
def ai_review_cv(review_id: int) -> redirect:
    """Generate AI-powered CV review."""
    if current_user.role not in ['career_advisor', 'admin']:
        abort(HTTPStatus.FORBIDDEN)
    
    review: CVReview = CVReview.query.get_or_404(review_id)
    client = get_ai_client()
    
    if not client:
        flash('AI service unavailable. Please configure NVIDIA API key.', 'danger')
        return redirect(url_for('career.advisor_review_cv', review_id=review_id))
    
    student: Student = review.student
    
    try:
        prompt: str = f"""Analyze this student's CV and provide structured feedback.

Student Profile:
- Program: {student.program or 'Unknown'}
- Year of Study: {student.year_of_study or 'Unknown'}
- CV File: {review.file_name}

Provide analysis in this exact format:
SCORE: [0-100]
STRENGTHS:
- [strength 1]
- [strength 2]
WEAKNESSES:
- [weakness 1]
- [weakness 2]
RECOMMENDED_SKILLS:
- [skill 1]
- [skill 2]
PROJECT_SUGGESTIONS:
- [project 1]
- [project 2]
INTERVIEW_TIPS:
- [tip 1]
- [tip 2]"""
        
        response = client.chat.completions.create(
            model="nvidia/nemotron-3-super-120b-a12b",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1000,
            temperature=0.7
        )
        
        analysis: str = response.choices[0].message.content
        
        # Parse AI response
        import re
        
        # Extract score
        score_match = re.search(r'SCORE:\s*(\d+)', analysis)
        if score_match:
            review.job_readiness_score = min(100, max(0, int(score_match.group(1))))
        
        # Extract sections
        def extract_section(text: str, section_name: str) -> List[str]:
            pattern = rf'{section_name}:\s*(.*?)(?=\n\w+:|$)'
            match = re.search(pattern, text, re.DOTALL)
            if match:
                lines = match.group(1).strip().split('\n')
                return [l.strip('- ').strip() for l in lines if l.strip()]
            return []
        
        strengths: List[str] = extract_section(analysis, 'STRENGTHS')
        weaknesses: List[str] = extract_section(analysis, 'WEAKNESSES')
        skills: List[str] = extract_section(analysis, 'RECOMMENDED_SKILLS')
        projects: List[str] = extract_section(analysis, 'PROJECT_SUGGESTIONS')
        tips: List[str] = extract_section(analysis, 'INTERVIEW_TIPS')
        
        # Update review
        review.strengths = '\n'.join(strengths) if strengths else None
        review.weaknesses = '\n'.join(weaknesses) if weaknesses else None
        review.suggested_skills = json.dumps(skills) if skills else None
        review.suggested_projects = json.dumps(projects) if projects else None
        review.interview_tips = '\n'.join(tips) if tips else None
        review.recommendations = analysis[:500]  # Store truncated full analysis
        review.status = 'reviewed'
        review.reviewed_by = current_user.id
        review.reviewed_at = datetime.utcnow()
        
        db.session.commit()
        
        flash('AI review generated successfully!', 'success')
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'AI review generation error: {str(e)}')
        flash(f'Error generating AI review: {str(e)}', 'danger')
    
    return redirect(url_for('career.advisor_review_cv', review_id=review_id))