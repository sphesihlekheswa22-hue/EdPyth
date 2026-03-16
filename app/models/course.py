from datetime import datetime
from app import db


class Course(db.Model):
    """Course model representing academic courses."""
    __tablename__ = 'courses'
    
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), unique=True, nullable=False, index=True)  # e.g., CS101
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    credits = db.Column(db.Integer, default=3)
    lecturer_id = db.Column(db.Integer, db.ForeignKey('lecturers.id'), nullable=False)
    semester = db.Column(db.String(20), nullable=True)  # e.g., Fall 2024, Spring 2025
    year = db.Column(db.Integer, default=datetime.utcnow().year)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    modules = db.relationship('Module', backref='course', lazy=True, cascade='all, delete-orphan')
    enrollments = db.relationship('Enrollment', backref='course', lazy=True, cascade='all, delete-orphan')
    materials = db.relationship('CourseMaterial', backref='course', lazy=True, cascade='all, delete-orphan')
    quizzes = db.relationship('Quiz', backref='course', lazy=True, cascade='all, delete-orphan')
    attendance_records = db.relationship('Attendance', backref='course', lazy=True)
    marks = db.relationship('Mark', backref='course', lazy=True)
    
    def __repr__(self):
        return f'<Course {self.code}: {self.name}>'
    
    def get_enrolled_students(self):
        """Get all enrolled students."""
        return [e.student for e in self.enrollments if e.status == 'active']
    
    def get_student_count(self):
        """Get count of enrolled students."""
        return sum(1 for e in self.enrollments if e.status == 'active')
    
    def get_average_progress(self):
        """Calculate average progress based on attendance for enrolled students."""
        from app.models.attendance import Attendance
        from app.models.mark import Mark
        
        # Get active enrollments
        active_enrollments = [e for e in self.enrollments if e.status == 'active']
        if not active_enrollments:
            return 0
        
        # Calculate attendance-based progress
        total_attendance_records = 0
        present_count = 0
        
        for enrollment in active_enrollments:
            attendance_records = Attendance.query.filter_by(
                course_id=self.id,
                student_id=enrollment.student_id
            ).all()
            
            for record in attendance_records:
                total_attendance_records += 1
                if record.status == 'present':
                    present_count += 1
        
        # If no attendance records, fall back to mark-based progress
        if total_attendance_records == 0:
            total_marks = 0
            mark_sum = 0
            for enrollment in active_enrollments:
                marks = Mark.query.filter_by(
                    course_id=self.id,
                    student_id=enrollment.student_id
                ).all()
                for m in marks:
                    total_marks += 1
                    mark_sum += m.percentage
            
            if total_marks > 0:
                return round(mark_sum / total_marks)
            return 0
        
        return round((present_count / total_attendance_records) * 100)
    
    def to_dict(self):
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
            'description': self.description,
            'credits': self.credits,
            'lecturer': self.lecturer.full_name if self.lecturer else None,
            'semester': self.semester,
            'year': self.year,
            'is_active': self.is_active,
            'student_count': self.get_student_count()
        }


class Module(db.Model):
    """Module model representing course modules/chapters."""
    __tablename__ = 'modules'
    
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    materials = db.relationship('CourseMaterial', backref='module', lazy=True)
    quiz_questions = db.relationship('QuizQuestion', backref='module', lazy=True)
    
    def __repr__(self):
        return f'<Module {self.title}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'course_id': self.course_id,
            'title': self.title,
            'description': self.description,
            'order': self.order,
            'material_count': len(self.materials)
        }


class Enrollment(db.Model):
    """Enrollment model for student-course relationships."""
    __tablename__ = 'enrollments'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    status = db.Column(db.String(20), default='active')  # active, completed, dropped
    enrolled_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)
    
    # Ensure unique enrollment per student per course
    __table_args__ = (
        db.UniqueConstraint('student_id', 'course_id', name='unique_enrollment'),
    )
    
    def __repr__(self):
        return f'<Enrollment Student {self.student_id} - Course {self.course_id}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'student_id': self.student_id,
            'course_id': self.course_id,
            'status': self.status,
            'enrolled_at': self.enrolled_at.isoformat() if self.enrolled_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None
        }
