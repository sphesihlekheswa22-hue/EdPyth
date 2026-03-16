from datetime import datetime
from app import db


class Attendance(db.Model):
    """Attendance model for tracking student attendance."""
    __tablename__ = 'attendance'
    
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), nullable=False)  # present, absent, late, excused
    recorded_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    recorder = db.relationship('User', backref='recorded_attendance')
    
    # Ensure unique attendance per student per course per date
    __table_args__ = (
        db.UniqueConstraint('course_id', 'student_id', 'date', name='unique_attendance'),
    )
    
    def __repr__(self):
        return f'<Attendance Course {self.course_id} - Student {self.student_id} - {self.date}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'course_id': self.course_id,
            'student_id': self.student_id,
            'student_name': self.student.user.full_name if self.student and self.student.user else None,
            'date': self.date.isoformat() if self.date else None,
            'status': self.status,
            'recorded_by': self.recorder.full_name if self.recorder else None,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
