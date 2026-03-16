from datetime import datetime
from app import db


class RiskScore(db.Model):
    """Risk score model for academic performance monitoring."""
    __tablename__ = 'risk_scores'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=True)
    risk_level = db.Column(db.String(20), nullable=False)  # low, medium, high, critical
    risk_score = db.Column(db.Float, nullable=False)  # 0-100
    attendance_score = db.Column(db.Float, nullable=True)
    quiz_score = db.Column(db.Float, nullable=True)
    assignment_score = db.Column(db.Float, nullable=True)
    overall_score = db.Column(db.Float, nullable=True)
    risk_factors = db.Column(db.Text, nullable=True)  # JSON array of risk factors
    recommendations = db.Column(db.Text, nullable=True)
    calculated_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    course = db.relationship('Course', backref='risk_scores')
    
    def __repr__(self):
        return f'<RiskScore Student {self.student_id} - Level {self.risk_level}>'
    
    def calculate_risk_level(self):
        """Calculate risk level based on score."""
        if self.risk_score >= 80:
            return 'low'
        elif self.risk_score >= 60:
            return 'medium'
        elif self.risk_score >= 40:
            return 'high'
        else:
            return 'critical'
    
    def to_dict(self):
        import json
        return {
            'id': self.id,
            'student_id': self.student_id,
            'student_name': self.student.user.full_name if self.student and self.student.user else None,
            'course_id': self.course_id,
            'course_name': self.course.name if self.course else 'Overall',
            'risk_level': self.risk_level,
            'risk_score': self.risk_score,
            'attendance_score': self.attendance_score,
            'quiz_score': self.quiz_score,
            'assignment_score': self.assignment_score,
            'overall_score': self.overall_score,
            'risk_factors': json.loads(self.risk_factors) if self.risk_factors else [],
            'recommendations': self.recommendations,
            'calculated_at': self.calculated_at.isoformat() if self.calculated_at else None
        }
