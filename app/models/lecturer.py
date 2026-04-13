from app import db
from app.utils.app_time import app_now, app_today


class Lecturer(db.Model):
    """Lecturer profile model extending User.
    
    IMPORTANT: Lecturers are NOT assigned to courses directly.
    They are assigned to MODULES (many-to-many via lecturer_modules table).
    """
    __tablename__ = 'lecturers'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    employee_id = db.Column(db.String(20), unique=True, nullable=False)
    department = db.Column(db.String(100), nullable=True)
    title = db.Column(db.String(50), nullable=True)  # e.g., Professor, Dr.
    phone = db.Column(db.String(20), nullable=True)
    office = db.Column(db.String(50), nullable=True)
    hire_date = db.Column(db.Date, default=app_today)
    specialization = db.Column(db.String(200), nullable=True)
    
    # Relationships
    user = db.relationship('User', back_populates='lecturer')
    module_assignments = db.relationship('LecturerModule', backref='lecturer', lazy=True, cascade='all, delete-orphan')
    interventions_sent = db.relationship('InterventionMessage', back_populates='lecturer', lazy=True)
    
    def __repr__(self):
        return f'<Lecturer {self.employee_id}>'
    
    @property
    def full_name(self):
        return self.user.full_name if self.user else None
    
    def get_assigned_modules(self, course_id=None):
        """Get all modules assigned to this lecturer.
        
        Args:
            course_id: Optional filter by course
            
        Returns:
            List of Module objects
        """
        from app.models.course import Module
        module_ids = [lm.module_id for lm in self.module_assignments]
        query = Module.query.filter(Module.id.in_(module_ids))
        if course_id:
            query = query.filter_by(course_id=course_id)
        return query.all()
    
    def get_teaching_courses(self):
        """Get all courses this lecturer teaches (through module assignments)."""
        from app.models.course import Course, Module
        course_ids = db.session.query(Module.course_id).join(
            LecturerModule, LecturerModule.module_id == Module.id
        ).filter(
            LecturerModule.lecturer_id == self.id
        ).distinct().all()
        return Course.query.filter(Course.id.in_([cid[0] for cid in course_ids])).all()
    
    def is_assigned_to_module(self, module_id):
        """Check if lecturer is assigned to a specific module."""
        return any(lm.module_id == module_id for lm in self.module_assignments)
    
    def is_assigned_to_course(self, course_id):
        """Check if lecturer teaches any modules in this course."""
        from app.models.course import Module
        return db.session.query(LecturerModule).join(
            Module, LecturerModule.module_id == Module.id
        ).filter(
            LecturerModule.lecturer_id == self.id,
            Module.course_id == course_id
        ).first() is not None
    
    def assign_to_module(self, module_id, is_primary=False):
        """Assign lecturer to a module."""
        if not self.is_assigned_to_module(module_id):
            lm = LecturerModule(
                lecturer_id=self.id,
                module_id=module_id,
                is_primary=is_primary
            )
            db.session.add(lm)
            return True
        return False
    
    def unassign_from_module(self, module_id):
        """Remove lecturer assignment from a module."""
        lm = next((lm for lm in self.module_assignments if lm.module_id == module_id), None)
        if lm:
            db.session.delete(lm)
            return True
        return False
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'employee_id': self.employee_id,
            'full_name': self.full_name,
            'department': self.department,
            'title': self.title,
            'specialization': self.specialization,
            'module_count': len(self.module_assignments)
        }


class LecturerModule(db.Model):
    """Association table linking lecturers to modules (many-to-many).
    
    This replaces the old pattern of assigning lecturers to courses.
    Multiple lecturers can teach the same module.
    """
    __tablename__ = 'lecturer_modules'
    
    id = db.Column(db.Integer, primary_key=True)
    lecturer_id = db.Column(db.Integer, db.ForeignKey('lecturers.id'), nullable=False)
    module_id = db.Column(db.Integer, db.ForeignKey('modules.id'), nullable=False)
    is_primary = db.Column(db.Boolean, default=False)  # Primary lecturer for this module
    assigned_at = db.Column(db.DateTime, default=app_now)
    
    # Prevent duplicate assignments
    __table_args__ = (
        db.UniqueConstraint('lecturer_id', 'module_id', name='unique_lecturer_module'),
    )
    
    def __repr__(self):
        return f'<LecturerModule Lecturer {self.lecturer_id} - Module {self.module_id}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'lecturer_id': self.lecturer_id,
            'module_id': self.module_id,
            'is_primary': self.is_primary,
            'lecturer_name': self.lecturer.full_name if self.lecturer else None,
            'module_title': self.module.title if self.module else None
        }
