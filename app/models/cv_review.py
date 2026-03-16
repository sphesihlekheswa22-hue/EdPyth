from datetime import datetime
from app import db


class CVReview(db.Model):
    """CV review model for career development module."""
    __tablename__ = 'cv_reviews'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    file_name = db.Column(db.String(255), nullable=False)
    job_readiness_score = db.Column(db.Float, nullable=True)  # 0-100
    status = db.Column(db.String(20), default='pending')  # pending, reviewed, needs_revision
    strengths = db.Column(db.Text, nullable=True)
    weaknesses = db.Column(db.Text, nullable=True)
    recommendations = db.Column(db.Text, nullable=True)
    suggested_skills = db.Column(db.Text, nullable=True)  # JSON array
    suggested_projects = db.Column(db.Text, nullable=True)  # JSON array
    interview_tips = db.Column(db.Text, nullable=True)
    reviewed_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    reviewed_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    reviewer = db.relationship('User', backref='cv_reviews')
    
    def __repr__(self):
        return f'<CVReview {self.id}>'
    
    def to_dict(self):
        import json
        return {
            'id': self.id,
            'student_id': self.student_id,
            'student_name': self.student.user.full_name if self.student and self.student.user else None,
            'file_name': self.file_name,
            'job_readiness_score': self.job_readiness_score,
            'status': self.status,
            'strengths': self.strengths,
            'weaknesses': self.weaknesses,
            'recommendations': self.recommendations,
            'suggested_skills': json.loads(self.suggested_skills) if self.suggested_skills else [],
            'suggested_projects': json.loads(self.suggested_projects) if self.suggested_projects else [],
            'interview_tips': self.interview_tips,
            'reviewed_by': self.reviewer.full_name if self.reviewer else None,
            'reviewed_at': self.reviewed_at.isoformat() if self.reviewed_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
