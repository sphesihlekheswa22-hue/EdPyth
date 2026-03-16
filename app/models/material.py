from datetime import datetime
from app import db
import os


class CourseMaterial(db.Model):
    """Course material model for storing course-related files."""
    __tablename__ = 'course_materials'
    
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    module_id = db.Column(db.Integer, db.ForeignKey('modules.id'), nullable=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    file_path = db.Column(db.String(500), nullable=False)
    file_name = db.Column(db.String(255), nullable=False)
    file_type = db.Column(db.String(50), nullable=False)  # pdf, doc, docx, ppt, pptx, etc.
    file_size = db.Column(db.Integer, nullable=False)  # in bytes
    category = db.Column(db.String(50), default='general')  # lecture, assignment, reading, etc.
    uploaded_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    is_published = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    uploader = db.relationship('User', backref='uploaded_materials')
    
    def __repr__(self):
        return f'<CourseMaterial {self.title}>'
    
    @property
    def file_extension(self):
        """Get file extension."""
        return os.path.splitext(self.file_name)[1].lower()
    
    @property
    def file_size_mb(self):
        """Get file size in MB."""
        return round(self.file_size / (1024 * 1024), 2)
    
    def to_dict(self):
        return {
            'id': self.id,
            'course_id': self.course_id,
            'module_id': self.module_id,
            'title': self.title,
            'description': self.description,
            'file_name': self.file_name,
            'file_type': self.file_type,
            'file_size_mb': self.file_size_mb,
            'category': self.category,
            'uploaded_by': self.uploader.full_name if self.uploader else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
