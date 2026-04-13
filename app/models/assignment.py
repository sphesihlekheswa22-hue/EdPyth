from datetime import datetime
from app import db
from app.utils.app_time import app_now


class Assignment(db.Model):
    """Assignment model - assignments belong to MODULES only.
    
    All assignments are associated with specific modules within courses.
    Students submit assignments through their enrolled course modules.
    """
    __tablename__ = 'assignments'
    
    id = db.Column(db.Integer, primary_key=True)
    # REMOVED: course_id - assignments belong to modules only
    module_id = db.Column(db.Integer, db.ForeignKey('modules.id'), nullable=False)  # NOW REQUIRED
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    due_date = db.Column(db.DateTime, nullable=True)
    total_marks = db.Column(db.Float, default=100)
    created_at = db.Column(db.DateTime, default=app_now)
    updated_at = db.Column(db.DateTime, default=app_now, onupdate=app_now)
    
    # Relationships
    submissions = db.relationship('AssignmentSubmission', backref='assignment', lazy=True, cascade='all, delete-orphan')
    attachments = db.relationship(
        'AssignmentAttachment',
        backref='assignment',
        lazy=True,
        cascade='all, delete-orphan',
    )
    
    def __repr__(self):
        return f'<Assignment {self.title} (Module: {self.module_id})>'
    
    @property
    def course_id(self):
        """Get course ID through module relationship."""
        return self.module.course_id if self.module else None
    
    def can_access(self, student):
        """Check if student can access this assignment."""
        from app.models.course import Enrollment
        
        if not student:
            return False
        
        enrollment = Enrollment.query.filter_by(
            student_id=student.id,
            course_id=self.course_id,
            status='active'
        ).first()
        
        return enrollment is not None
    
    def has_student_submitted(self, student_id):
        """Check if student has already submitted this assignment."""
        return AssignmentSubmission.query.filter_by(
            assignment_id=self.id,
            student_id=student_id
        ).first() is not None
    
    def get_student_submission(self, student_id):
        """Get student's submission for this assignment."""
        return AssignmentSubmission.query.filter_by(
            assignment_id=self.id,
            student_id=student_id
        ).first()
    
    def to_dict(self):
        return {
            'id': self.id,
            'module_id': self.module_id,
            'course_id': self.course_id,
            'title': self.title,
            'description': self.description,
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'total_marks': self.total_marks,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class AssignmentAttachment(db.Model):
    """Files attached to an assignment by the lecturer (handouts, rubrics, etc.)."""
    __tablename__ = 'assignment_attachments'

    id = db.Column(db.Integer, primary_key=True)
    assignment_id = db.Column(db.Integer, db.ForeignKey('assignments.id'), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    file_name = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=app_now)

    def __repr__(self):
        return f'<AssignmentAttachment {self.id} assignment={self.assignment_id}>'


class AssignmentSubmission(db.Model):
    """Student assignment submissions."""
    __tablename__ = 'assignment_submissions'
    
    id = db.Column(db.Integer, primary_key=True)
    assignment_id = db.Column(db.Integer, db.ForeignKey('assignments.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    file_path = db.Column(db.String(500), nullable=True)
    file_name = db.Column(db.String(255), nullable=True)
    submitted_at = db.Column(db.DateTime, default=app_now)
    status = db.Column(db.String(50), default='submitted')  # submitted, graded, late
    feedback = db.Column(db.Text, nullable=True)
    mark = db.Column(db.Float, nullable=True)
    grade = db.Column(db.String(10), nullable=True)
    graded_at = db.Column(db.DateTime, nullable=True)
    graded_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    # Relationships
    student = db.relationship('Student', backref='submissions')
    lecturer = db.relationship('User', backref='graded_submissions')
    
    def __repr__(self):
        return f'<AssignmentSubmission {self.id} - Assignment {self.assignment_id}>'
    
    def calculate_grade(self):
        """Calculate letter grade based on percentage."""
        if self.mark is None:
            return 'N/A'
        
        # Get total marks from assignment
        total = self.assignment.total_marks if self.assignment else 100
        percentage = (self.mark / total) * 100
        
        if percentage >= 90:
            return 'A'
        elif percentage >= 80:
            return 'B'
        elif percentage >= 70:
            return 'C'
        elif percentage >= 60:
            return 'D'
        else:
            return 'F'
    
    def to_dict(self):
        return {
            'id': self.id,
            'assignment_id': self.assignment_id,
            'student_id': self.student_id,
            'file_name': self.file_name,
            'submitted_at': self.submitted_at.isoformat() if self.submitted_at else None,
            'status': self.status,
            'mark': self.mark,
            'grade': self.grade,
            'feedback': self.feedback
        }
