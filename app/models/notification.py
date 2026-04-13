import json
from enum import Enum
from app import db
from app.utils.app_time import app_now


class NotificationType(Enum):
    INTERVENTION_SENT = "intervention_sent"
    INTERVENTION_RECEIVED = "intervention_received"
    ASSIGNMENT_DUE = "assignment_due"
    GRADE_POSTED = "grade_posted"
    COURSE_UPDATE = "course_update"
    MATERIAL_PUBLISHED = "material_published"
    QUIZ_PUBLISHED = "quiz_published"
    ASSIGNMENT_POSTED = "assignment_posted"
    AT_RISK_ALERT = "at_risk_alert"
    ENROLLMENT = "enrollment"
    QUIZ_SUBMITTED = "quiz_submitted"
    MESSAGE_RECEIVED = "message_received"
    CV_REVIEWED = "cv_reviewed"


class NotificationPriority(Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class Notification(db.Model):
    """User notification model - stores all system notifications"""
    __tablename__ = 'notifications'
    
    id = db.Column(db.Integer, primary_key=True)
    recipient_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    # Notification content
    type = db.Column(db.String(50), nullable=False)
    title = db.Column(db.String(128), nullable=False)
    message = db.Column(db.Text, nullable=False)
    priority = db.Column(db.String(20), default='normal')
    
    # Actionable notifications (e.g., click to view assignment)
    action_url = db.Column(db.String(255), nullable=True)
    action_text = db.Column(db.String(64), nullable=True)
    
    # Related entities (polymorphic reference)
    entity_type = db.Column(db.String(50), nullable=True)
    entity_id = db.Column(db.Integer, nullable=True)
    
    # Status tracking
    is_read = db.Column(db.Boolean, default=False, index=True)
    read_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=app_now, index=True)
    
    # For "intervention" specific data
    metadata_json = db.Column(db.Text, nullable=True)
    
    # Relationships
    recipient = db.relationship('User', foreign_keys=[recipient_id], backref='notifications')
    sender = db.relationship('User', foreign_keys=[sender_id])
    
    def to_dict(self):
        """Serialize notification for API/JSON"""
        return {
            'id': self.id,
            'type': self.type,
            'title': self.title,
            'message': self.message,
            'priority': self.priority,
            'is_read': self.is_read,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'action_url': self.action_url,
            'action_text': self.action_text,
            'sender': {
                'id': self.sender_id,
                'name': self.sender.full_name if self.sender else None
            } if self.sender else None,
            'metadata': json.loads(self.metadata_json) if self.metadata_json else {}
        }
    
    def mark_as_read(self):
        """Mark notification as read"""
        if not self.is_read:
            self.is_read = True
            self.read_at = app_now()
            db.session.commit()


class InterventionMessage(db.Model):
    """Specific model for lecturer-student interventions"""
    __tablename__ = 'intervention_messages'
    
    id = db.Column(db.Integer, primary_key=True)
    lecturer_id = db.Column(db.Integer, db.ForeignKey('lecturers.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=True)
    
    # Message content
    subject = db.Column(db.String(128), nullable=False)
    content = db.Column(db.Text, nullable=False)
    template_used = db.Column(db.String(50), nullable=True)
    
    # Tracking
    sent_at = db.Column(db.DateTime, default=app_now)
    opened_at = db.Column(db.DateTime, nullable=True)
    student_replied = db.Column(db.Boolean, default=False)
    
    # AI/Analysis
    risk_level_at_send = db.Column(db.String(20), nullable=True)
    recommended_actions = db.Column(db.Text, nullable=True)
    
    # Relationships
    lecturer = db.relationship('Lecturer', back_populates='interventions_sent')
    student = db.relationship('Student', back_populates='interventions_received')
    course = db.relationship('Course')
    
    def to_dict(self):
        return {
            'id': self.id,
            'lecturer_id': self.lecturer_id,
            'student_id': self.student_id,
            'course_id': self.course_id,
            'subject': self.subject,
            'content': self.content,
            'template_used': self.template_used,
            'sent_at': self.sent_at.isoformat() if self.sent_at else None,
            'opened_at': self.opened_at.isoformat() if self.opened_at else None,
            'student_replied': self.student_replied,
            'risk_level_at_send': self.risk_level_at_send
        }
