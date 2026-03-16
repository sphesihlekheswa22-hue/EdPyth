from datetime import datetime
from app import db


class ChatSession(db.Model):
    """Chat session model for AI tutoring."""
    __tablename__ = 'chat_sessions'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    title = db.Column(db.String(200), nullable=True)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=True)
    topic = db.Column(db.String(100), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    course = db.relationship('Course', backref='chat_sessions')
    messages = db.relationship('ChatMessage', backref='session', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<ChatSession {self.id}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'student_id': self.student_id,
            'title': self.title,
            'course_id': self.course_id,
            'course_name': self.course.name if self.course else None,
            'topic': self.topic,
            'is_active': self.is_active,
            'message_count': len(self.messages),
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class ChatMessage(db.Model):
    """Chat message model for AI tutoring conversations."""
    __tablename__ = 'chat_messages'
    
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('chat_sessions.id'), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # user, assistant
    content = db.Column(db.Text, nullable=False)
    is_ai = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<ChatMessage {self.id}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'session_id': self.session_id,
            'role': self.role,
            'content': self.content,
            'is_ai': self.is_ai,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
