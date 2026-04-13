from app import db
from app.utils.app_time import app_now


class Attendance(db.Model):
    """Attendance model - attendance is tracked at MODULE level.
    
    Attendance is recorded for specific modules within courses.
    Students must be enrolled in the course to have attendance recorded.
    """
    __tablename__ = 'attendance'
    
    id = db.Column(db.Integer, primary_key=True)
    # REMOVED: course_id - attendance is at module level
    module_id = db.Column(db.Integer, db.ForeignKey('modules.id'), nullable=False)  # NOW REQUIRED
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), nullable=False)  # present, absent, late, excused
    recorded_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=app_now)
    updated_at = db.Column(db.DateTime, default=app_now, onupdate=app_now)
    
    # Relationships
    recorder = db.relationship('User', backref='recorded_attendance')
    
    # Ensure unique attendance per student per module per date
    __table_args__ = (
        db.UniqueConstraint('module_id', 'student_id', 'date', name='unique_attendance'),
    )
    
    def __repr__(self):
        return f'<Attendance Module {self.module_id} - Student {self.student_id} - {self.date}>'
    
    @property
    def course_id(self):
        """Get course ID through module relationship."""
        return self.module.course_id if self.module else None
    
    def can_record(self, user):
        """Check if user can record attendance for this module."""
        from app.models.lecturer import LecturerModule
        
        if not user:
            return False
        
        if user.role == 'admin':
            return True
        
        if user.role == 'lecturer':
            lecturer = user.lecturer
            if not lecturer:
                return False
            # Must be assigned to the module
            return LecturerModule.query.filter_by(
                lecturer_id=lecturer.id,
                module_id=self.module_id
            ).first() is not None
        
        return False
    
    def to_dict(self):
        return {
            'id': self.id,
            'module_id': self.module_id,
            'course_id': self.course_id,
            'student_id': self.student_id,
            'student_name': self.student.user.full_name if self.student and self.student.user else None,
            'date': self.date.isoformat() if self.date else None,
            'status': self.status,
            'recorded_by': self.recorder.full_name if self.recorder else None,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
