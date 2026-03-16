import os
from typing import List, Optional, Set, Union
from werkzeug.utils import secure_filename
from flask import (
    Blueprint, render_template, redirect, url_for, 
    flash, request, send_from_directory, current_app, abort
)
from flask_login import login_required, current_user
from datetime import datetime
from http import HTTPStatus

from app import db
from app.models import CourseMaterial, Course, Student, Module, Enrollment, Lecturer

materials_bp = Blueprint('materials', __name__, url_prefix='/materials')


# Configuration
ALLOWED_EXTENSIONS: Set[str] = {
    'pdf', 'doc', 'docx', 'ppt', 'pptx', 'txt', 
    'jpg', 'jpeg', 'png', 'gif', 'mp4', 'zip'
}

MAX_FILE_SIZE: int = 50 * 1024 * 1024  # 50MB


class MaterialError(Exception):
    """Custom exception for material operations."""
    pass


def allowed_file(filename: str) -> bool:
    """Check if file extension is allowed."""
    return (
        '.' in filename and 
        filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
    )


def get_file_type(filename: str) -> str:
    """Determine file type category from extension."""
    ext: str = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
    
    type_map: dict = {
        'pdf': 'pdf',
        'doc': 'document', 'docx': 'document',
        'ppt': 'presentation', 'pptx': 'presentation',
        'txt': 'text',
        'jpg': 'image', 'jpeg': 'image', 'png': 'image', 'gif': 'image',
        'mp4': 'video',
        'zip': 'archive'
    }
    
    return type_map.get(ext, 'other')


def get_file_icon(file_type: str) -> str:
    """Get appropriate icon for file type."""
    icon_map: dict = {
        'pdf': 'file-text',
        'document': 'file-type',
        'presentation': 'presentation',
        'text': 'file-text',
        'image': 'image',
        'video': 'video',
        'archive': 'folder-archive',
        'other': 'file'
    }
    return icon_map.get(file_type, 'file')


def check_material_access(course_id: int, require_edit: bool = False) -> tuple:
    """
    Verify user access to course materials.
    Returns (course, student, has_edit_permission).
    """
    course: Course = Course.query.get_or_404(course_id)
    
    student: Optional[Student] = None
    can_edit: bool = False
    
    if current_user.role == 'admin':
        can_edit = True
        
    elif current_user.role == 'lecturer':
        lecturer: Lecturer = Lecturer.query.filter_by(
            user_id=current_user.id
        ).first_or_404()
        
        if course.lecturer_id != lecturer.id:
            abort(HTTPStatus.FORBIDDEN)
        
        can_edit = True
        
    elif current_user.role == 'student':
        if require_edit:
            abort(HTTPStatus.FORBIDDEN)
        
        student = Student.query.filter_by(user_id=current_user.id).first_or_404()
        
        enrollment: Optional[Enrollment] = Enrollment.query.filter_by(
            student_id=student.id,
            course_id=course_id,
            status='active'
        ).first()
        
        if not enrollment:
            abort(HTTPStatus.FORBIDDEN, 'Active enrollment required')
    
    return course, student, can_edit


def get_upload_path(course_id: int, filename: str) -> str:
    """Generate secure upload path."""
    upload_folder: str = current_app.config.get('UPLOAD_FOLDER', 'uploads')
    course_folder: str = os.path.join(upload_folder, 'materials', str(course_id))
    
    # Ensure directory exists
    os.makedirs(course_folder, exist_ok=True)
    
    return os.path.join(course_folder, secure_filename(filename))


@materials_bp.route('/course/<int:course_id>')
@login_required
def list_materials(course_id: int) -> str:
    """List materials for a course."""
    course, student, can_edit = check_material_access(course_id)
    
    # Base query - published materials for students, all for staff
    query = CourseMaterial.query.filter_by(course_id=course_id)
    
    if not can_edit:
        query = query.filter_by(is_published=True)
    
    materials: List[CourseMaterial] = query.order_by(
        CourseMaterial.category,
        CourseMaterial.created_at.desc()
    ).all()
    
    # Group by category
    categories: dict = {}
    for material in materials:
        cat: str = material.category or 'general'
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(material)
    
    # Get modules for context
    modules: List[Module] = Module.query.filter_by(course_id=course_id).all()
    module_map: dict = {m.id: m for m in modules}
    
    return render_template(
        'materials.html',
        course=course,
        materials=materials,
        categories=categories,
        module_map=module_map,
        can_edit=can_edit,
        allowed_extensions=list(ALLOWED_EXTENSIONS)
    )


@materials_bp.route('/course/<int:course_id>/upload', methods=['GET', 'POST'])
@login_required
def upload_material(course_id: int) -> Union[str, redirect]:
    """Upload material to course."""
    course, _, can_edit = check_material_access(course_id, require_edit=True)
    
    if not can_edit:
        abort(HTTPStatus.FORBIDDEN)
    
    if request.method == 'POST':
        # Debug: Log what's received
        current_app.logger.info(f"POST request.files keys: {list(request.files.keys())}")
        current_app.logger.info(f"POST request.form keys: {list(request.form.keys())}")
        
        # Validate file presence
        if 'file' not in request.files:
            flash('No file selected.', 'danger')
            return redirect(request.url)
        
        file = request.files['file']
        
        if file.filename == '':
            flash('No file selected.', 'danger')
            return redirect(request.url)
        
        if not allowed_file(file.filename):
            flash(
                f'Invalid file type. Allowed: {", ".join(sorted(ALLOWED_EXTENSIONS))}', 
                'danger'
            )
            return redirect(request.url)
        
        try:
            # Secure filename and save
            filename: str = secure_filename(file.filename)
            file_path: str = get_upload_path(course_id, filename)
            
            # Check for duplicate
            existing: Optional[CourseMaterial] = CourseMaterial.query.filter_by(
                course_id=course_id,
                file_name=filename
            ).first()
            
            if existing:
                # Append timestamp to make unique
                name, ext = os.path.splitext(filename)
                filename = f"{name}_{int(datetime.utcnow().timestamp())}{ext}"
                file_path = get_upload_path(course_id, filename)
            
            file.save(file_path)
            
            # Get file size
            file_size: int = os.path.getsize(file_path)
            
            if file_size > MAX_FILE_SIZE:
                os.remove(file_path)
                flash(f'File too large. Maximum size: {MAX_FILE_SIZE // (1024*1024)}MB', 'danger')
                return redirect(request.url)
            
            # Determine publish status from checkbox (default to True if not present)
            is_published = request.form.get('is_published') == 'on'
            
            # Create database record
            material = CourseMaterial(
                course_id=course_id,
                module_id=request.form.get('module_id') or None,
                title=request.form.get('title', '').strip() or filename,
                description=request.form.get('description', '').strip() or None,
                file_path=f'/static/uploads/materials/{course_id}/{filename}',
                file_name=filename,
                file_type=get_file_type(filename),
                file_size=file_size,
                category=request.form.get('category', 'general').strip(),
                is_published=is_published,
                uploaded_by=current_user.id
            )
            
            db.session.add(material)
            db.session.commit()
            
            flash(f'Material "{material.title}" uploaded successfully!', 'success')
            return redirect(url_for('materials.list_materials', course_id=course_id))
            
        except Exception as e:
            db.session.rollback()
            # Cleanup file if saved
            if 'file_path' in locals() and os.path.exists(file_path):
                os.remove(file_path)
            
            current_app.logger.error(f'Material upload error: {str(e)}')
            flash('Error uploading material. Please try again.', 'danger')
            return redirect(request.url)
    
    # GET request
    modules: List[Module] = Module.query.filter_by(
        course_id=course_id
    ).order_by(Module.order).all()
    
    categories: List[str] = db.session.query(
        CourseMaterial.category
    ).filter_by(course_id=course_id).distinct().all()
    
    return render_template(
        'material_upload.html',
        course=course,
        modules=modules,
        existing_categories=[c[0] for c in categories if c[0]]
    )


@materials_bp.route('/download/<int:material_id>')
@login_required
def download_material(material_id: int):
    """Download material file."""
    material: CourseMaterial = CourseMaterial.query.get_or_404(material_id)
    
    # Access check for students
    if current_user.role == 'student':
        student: Student = Student.query.filter_by(
            user_id=current_user.id
        ).first_or_404()
        
        enrollment: Optional[Enrollment] = Enrollment.query.filter_by(
            student_id=student.id,
            course_id=material.course_id,
            status='active'
        ).first()
        
        if not enrollment or not material.is_published:
            abort(HTTPStatus.FORBIDDEN)
    
    upload_folder: str = current_app.config.get('UPLOAD_FOLDER', 'uploads')
    course_folder: str = os.path.join(
        upload_folder, 'materials', str(material.course_id)
    )
    
    # Track download (optional analytics)
    try:
        material.download_count = (material.download_count or 0) + 1
        db.session.commit()
    except:
        db.session.rollback()
    
    return send_from_directory(
        course_folder,
        material.file_name,
        as_attachment=True,
        download_name=material.title or material.file_name
    )


@materials_bp.route('/delete/<int:material_id>', methods=['POST'])
@login_required
def delete_material(material_id: int) -> redirect:
    """Delete material."""
    material: CourseMaterial = CourseMaterial.query.get_or_404(material_id)
    course_id: int = material.course_id
    
    # Permission check
    can_delete: bool = False
    
    if current_user.role == 'admin':
        can_delete = True
    elif current_user.role == 'lecturer':
        lecturer: Lecturer = Lecturer.query.filter_by(
            user_id=current_user.id
        ).first_or_404()
        can_delete = material.course.lecturer_id == lecturer.id
    
    if not can_delete:
        abort(HTTPStatus.FORBIDDEN)
    
    try:
        # Delete physical file
        upload_folder: str = current_app.config.get('UPLOAD_FOLDER', 'uploads')
        file_path: str = os.path.join(
            upload_folder, 'materials', str(course_id), material.file_name
        )
        
        if os.path.exists(file_path):
            os.remove(file_path)
        
        # Delete database record
        db.session.delete(material)
        db.session.commit()
        
        flash('Material deleted successfully.', 'success')
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Material deletion error: {str(e)}')
        flash('Error deleting material.', 'danger')
    
    return redirect(url_for('materials.list_materials', course_id=course_id))


@materials_bp.route('/<int:material_id>/toggle-publish', methods=['POST'])
@login_required
def toggle_publish(material_id: int) -> redirect:
    """Toggle material published status."""
    material: CourseMaterial = CourseMaterial.query.get_or_404(material_id)
    
    # Permission check
    can_edit: bool = False
    
    if current_user.role == 'admin':
        can_edit = True
    elif current_user.role == 'lecturer':
        lecturer: Lecturer = Lecturer.query.filter_by(
            user_id=current_user.id
        ).first_or_404()
        can_edit = material.course.lecturer_id == lecturer.id
    
    if not can_edit:
        abort(HTTPStatus.FORBIDDEN)
    
    try:
        material.is_published = not material.is_published
        db.session.commit()
        
        status: str = 'published' if material.is_published else 'unpublished'
        flash(f'Material {status}.', 'success')
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Publish toggle error: {str(e)}')
        flash('Error updating material.', 'danger')
    
    return redirect(url_for('materials.list_materials', course_id=material.course_id))
