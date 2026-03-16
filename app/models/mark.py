from datetime import datetime
from app import db


class Mark(db.Model):
    """Mark model for storing student grades."""
    __tablename__ = 'marks'
    
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    assessment_type = db.Column(db.String(50), nullable=False)  # assignment, midterm, final, quiz, project
    assessment_name = db.Column(db.String(200), nullable=False)
    mark = db.Column(db.Float, nullable=False)
    total_marks = db.Column(db.Float, nullable=False)
    percentage = db.Column(db.Float, nullable=False)
    grade = db.Column(db.String(5), nullable=True)  # A, B, C, D, F
    recorded_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    feedback = db.Column(db.Text, nullable=True)
    marked_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    recorder = db.relationship('User', backref='recorded_marks')
    
    def __repr__(self):
        return f'<Mark {self.assessment_name} - {self.mark}/{self.total_marks}>'
    
    def calculate_grade(self):
        """Calculate letter grade based on percentage."""
        if self.percentage >= 90:
            return 'A+'
        elif self.percentage >= 85:
            return 'A'
        elif self.percentage >= 80:
            return 'A-'
        elif self.percentage >= 75:
            return 'B+'
        elif self.percentage >= 70:
            return 'B'
        elif self.percentage >= 65:
            return 'B-'
        elif self.percentage >= 60:
            return 'C+'
        elif self.percentage >= 55:
            return 'C'
        elif self.percentage >= 50:
            return 'C-'
        elif self.percentage >= 45:
            return 'D'
        else:
            return 'F'
    
    def to_dict(self):
        return {
            'id': self.id,
            'course_id': self.course_id,
            'course_name': self.course.name if self.course else None,
            'student_id': self.student_id,
            'student_name': self.student.user.full_name if self.student and self.student.user else None,
            'assessment_type': self.assessment_type,
            'assessment_name': self.assessment_name,
            'mark': self.mark,
            'total_marks': self.total_marks,
            'percentage': self.percentage,
            'grade': self.grade,
            'recorded_by': self.recorder.full_name if self.recorder else None,
            'feedback': self.feedback,
            'marked_at': self.marked_at.isoformat() if self.marked_at else None
        }
