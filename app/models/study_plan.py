from app import db
from app.utils.app_time import app_now


class StudyPlan(db.Model):
    """Study plan model for AI-generated personalized study plans."""
    __tablename__ = 'study_plans'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=True)
    is_ai_generated = db.Column(db.Boolean, default=True)
    start_date = db.Column(db.Date, nullable=True)
    end_date = db.Column(db.Date, nullable=True)
    status = db.Column(db.String(20), default='active')  # active, completed, cancelled
    created_at = db.Column(db.DateTime, default=app_now)
    updated_at = db.Column(db.DateTime, default=app_now, onupdate=app_now)
    
    # Relationships
    course = db.relationship('Course', backref='study_plans')
    items = db.relationship('StudyPlanItem', backref='study_plan', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<StudyPlan {self.title}>'
    
    @property
    def completion_percentage(self):
        """Calculate completion percentage."""
        if not self.items:
            return 0
        completed = sum(1 for item in self.items if item.status == 'completed')
        return round((completed / len(self.items)) * 100, 2)
    
    def to_dict(self):
        return {
            'id': self.id,
            'student_id': self.student_id,
            'title': self.title,
            'description': self.description,
            'course_id': self.course_id,
            'course_name': self.course.name if self.course else None,
            'is_ai_generated': self.is_ai_generated,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'status': self.status,
            'completion_percentage': self.completion_percentage,
            'item_count': len(self.items),
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class StudyPlanItem(db.Model):
    """Study plan item model for individual study tasks."""
    __tablename__ = 'study_plan_items'
    
    id = db.Column(db.Integer, primary_key=True)
    study_plan_id = db.Column(db.Integer, db.ForeignKey('study_plans.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    task_type = db.Column(db.String(50), nullable=True)  # reading, practice, review, assignment
    order = db.Column(db.Integer, default=0)
    status = db.Column(db.String(20), default='pending')  # pending, in_progress, completed
    priority = db.Column(db.String(20), default='medium')  # low, medium, high
    due_date = db.Column(db.Date, nullable=True)
    estimated_time = db.Column(db.Integer, nullable=True)  # in minutes
    completed_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=app_now)
    updated_at = db.Column(db.DateTime, default=app_now, onupdate=app_now)
    
    def __repr__(self):
        return f'<StudyPlanItem {self.title}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'study_plan_id': self.study_plan_id,
            'title': self.title,
            'description': self.description,
            'task_type': self.task_type,
            'order': self.order,
            'status': self.status,
            'priority': self.priority,
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'estimated_time': self.estimated_time,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None
        }
