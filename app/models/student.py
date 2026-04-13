from app import db
from app.utils.app_time import app_today


class Student(db.Model):
    """Student profile model extending User."""
    __tablename__ = 'students'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    student_id = db.Column(db.String(20), unique=True, nullable=False)  # University student ID
    date_of_birth = db.Column(db.Date, nullable=True)
    phone = db.Column(db.String(20), nullable=True)
    address = db.Column(db.Text, nullable=True)
    program = db.Column(db.String(100), nullable=True)  # e.g., Computer Science
    year_of_study = db.Column(db.Integer, nullable=True)
    enrollment_date = db.Column(db.Date, default=app_today)
    # Relative to Flask static folder, e.g. uploads/profiles/<student_db_id>/photo.jpg
    profile_image = db.Column(db.String(512), nullable=True)
    
    # Relationships
    enrollments = db.relationship('Enrollment', backref='student', lazy=True, cascade='all, delete-orphan')
    quiz_results = db.relationship('QuizResult', backref='student', lazy=True, cascade='all, delete-orphan')
    attendance_records = db.relationship('Attendance', backref='student', lazy=True, cascade='all, delete-orphan')
    marks = db.relationship('Mark', backref='student', lazy=True, cascade='all, delete-orphan')
    study_plans = db.relationship('StudyPlan', backref='student', lazy=True, cascade='all, delete-orphan')
    chat_sessions = db.relationship('ChatSession', backref='student', lazy=True, cascade='all, delete-orphan')
    cv_reviews = db.relationship('CVReview', backref='student', lazy=True, cascade='all, delete-orphan')
    risk_scores = db.relationship('RiskScore', backref='student', lazy=True, cascade='all, delete-orphan')
    interventions_received = db.relationship('InterventionMessage', back_populates='student', lazy=True)
    
    def __repr__(self):
        return f'<Student {self.student_id}>'
    
    @property
    def full_name(self):
        return self.user.full_name if self.user else None
    
    def get_enrolled_courses(self):
        """Get all courses the student is enrolled in."""
        return [e.course for e in self.enrollments if e.status == 'active']
    
    def get_average_mark(self):
        """Calculate average mark across all courses."""
        if not self.marks:
            return 0
        return sum(m.mark for m in self.marks) / len(self.marks)
    
    def get_attendance_rate(self):
        """Calculate attendance rate."""
        if not self.attendance_records:
            return 0
        present = sum(1 for a in self.attendance_records if a.status == 'present')
        return (present / len(self.attendance_records)) * 100
    
    def profile_image_url(self):
        """Public URL path for profile photo, or None."""
        if not self.profile_image:
            return None
        from flask import url_for
        try:
            return url_for('static', filename=self.profile_image)
        except RuntimeError:
            return None

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'student_id': self.student_id,
            'full_name': self.full_name,
            'program': self.program,
            'year_of_study': self.year_of_study,
            'enrollment_date': self.enrollment_date.isoformat() if self.enrollment_date else None
        }
