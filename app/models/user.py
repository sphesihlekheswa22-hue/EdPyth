from datetime import datetime
from flask_login import UserMixin
from app import db, bcrypt


class User(db.Model, UserMixin):
    """User model for authentication and base user information."""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(128), nullable=False)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # student, lecturer, admin, career_advisor
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    student = db.relationship('Student', backref='user', uselist=False, lazy=True)
    lecturer = db.relationship('Lecturer', backref='user', uselist=False, lazy=True)
    
    def set_password(self, password):
        """Hash and set the user password."""
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
    
    def check_password(self, password):
        """Verify the password."""
        return bcrypt.check_password_hash(self.password_hash, password)
    
    @property
    def full_name(self):
        """Return the user's full name."""
        return f"{self.first_name} {self.last_name}"
    
    def __repr__(self):
        return f'<User {self.email} ({self.role})>'
    
    def to_dict(self):
        """Convert user to dictionary."""
        return {
            'id': self.id,
            'email': self.email,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'full_name': self.full_name,
            'role': self.role,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
