from datetime import datetime
from app import db


class Lecturer(db.Model):
    """Lecturer profile model extending User."""
    __tablename__ = 'lecturers'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    employee_id = db.Column(db.String(20), unique=True, nullable=False)  # University employee ID
    department = db.Column(db.String(100), nullable=True)
    title = db.Column(db.String(50), nullable=True)  # e.g., Professor, Dr.
    phone = db.Column(db.String(20), nullable=True)
    office = db.Column(db.String(50), nullable=True)
    hire_date = db.Column(db.Date, default=datetime.utcnow)
    specialization = db.Column(db.String(200), nullable=True)
    
    # Relationships
    courses = db.relationship('Course', backref='lecturer', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Lecturer {self.employee_id}>'
    
    @property
    def full_name(self):
        return self.user.full_name if self.user else None
    
    def get_teaching_courses(self):
        """Get all courses taught by this lecturer."""
        return self.courses
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'employee_id': self.employee_id,
            'full_name': self.full_name,
            'department': self.department,
            'title': self.title,
            'specialization': self.specialization
        }
