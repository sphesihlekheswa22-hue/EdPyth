from app import db
from app.utils.app_time import app_now


class StudentModuleProgress(db.Model):
    """Track student progress at the module level.
    
    This model ensures students can only access modules through their
    enrolled courses and tracks their engagement and completion.
    """
    __tablename__ = 'student_module_progress'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    module_id = db.Column(db.Integer, db.ForeignKey('modules.id'), nullable=False)
    enrollment_id = db.Column(db.Integer, db.ForeignKey('enrollments.id'), nullable=False)
    
    # Progress tracking
    completion_status = db.Column(
        db.String(20), 
        default='not_started'
    )  # not_started, in_progress, completed
    completion_percentage = db.Column(db.Integer, default=0)  # 0-100
    
    # Engagement metrics
    materials_viewed = db.Column(db.Integer, default=0)
    quizzes_completed = db.Column(db.Integer, default=0)
    assignments_submitted = db.Column(db.Integer, default=0)
    attendance_sessions = db.Column(db.Integer, default=0)
    
    # Scores
    quiz_average_score = db.Column(db.Float, nullable=True)
    assignment_average_score = db.Column(db.Float, nullable=True)
    overall_module_score = db.Column(db.Float, nullable=True)
    
    # Timestamps
    started_at = db.Column(db.DateTime, nullable=True)
    completed_at = db.Column(db.DateTime, nullable=True)
    last_accessed_at = db.Column(db.DateTime, nullable=True)
    updated_at = db.Column(db.DateTime, default=app_now, onupdate=app_now)
    
    # Ensure one progress record per student per module per enrollment
    __table_args__ = (
        db.UniqueConstraint('student_id', 'module_id', 'enrollment_id', 
                          name='unique_student_module_progress'),
    )
    
    def __repr__(self):
        return f'<StudentModuleProgress Student {self.student_id} - Module {self.module_id}: {self.completion_percentage}%>'
    
    def mark_started(self):
        """Mark module as started."""
        if not self.started_at:
            self.started_at = app_now()
        if self.completion_status == 'not_started':
            self.completion_status = 'in_progress'
        self.last_accessed_at = app_now()
    
    def mark_completed(self):
        """Mark module as completed."""
        self.completion_status = 'completed'
        self.completion_percentage = 100
        self.completed_at = app_now()
        self.last_accessed_at = app_now()
    
    def update_completion(self, percentage):
        """Update completion percentage."""
        self.completion_percentage = min(100, max(0, percentage))
        if self.completion_percentage > 0 and not self.started_at:
            self.started_at = app_now()
        if self.completion_percentage >= 100:
            self.mark_completed()
        elif self.completion_percentage > 0:
            self.completion_status = 'in_progress'
        self.last_accessed_at = app_now()
    
    def record_material_viewed(self):
        """Increment materials viewed counter."""
        self.materials_viewed += 1
        self.last_accessed_at = app_now()
        self._update_progress()
    
    def record_quiz_completed(self, score):
        """Record quiz completion."""
        self.quizzes_completed += 1
        self._update_quiz_average(score)
        self.last_accessed_at = app_now()
        self._update_progress()
    
    def record_assignment_submitted(self, score=None):
        """Record assignment submission."""
        self.assignments_submitted += 1
        if score is not None:
            self._update_assignment_average(score)
        self.last_accessed_at = app_now()
        self._update_progress()
    
    def record_attendance(self):
        """Record attendance session."""
        self.attendance_sessions += 1
        self.last_accessed_at = app_now()
        self._update_progress()
    
    def _update_quiz_average(self, new_score):
        """Update quiz average score."""
        if self.quiz_average_score is None:
            self.quiz_average_score = new_score
        else:
            # Weighted average
            total = self.quiz_average_score * (self.quizzes_completed - 1) + new_score
            self.quiz_average_score = total / self.quizzes_completed
    
    def _update_assignment_average(self, new_score):
        """Update assignment average score."""
        if self.assignment_average_score is None:
            self.assignment_average_score = new_score
        else:
            # Weighted average
            total = self.assignment_average_score * (self.assignments_submitted - 1) + new_score
            self.assignment_average_score = total / self.assignments_submitted
    
    def _update_progress(self):
        """Calculate overall progress based on activities."""
        module = self.module
        if not module:
            return
        
        # Calculate based on available content
        total_items = 0
        completed_items = 0
        
        # Materials (published only for students)
        published_materials = [m for m in module.materials if getattr(m, "is_published", True)]
        if published_materials:
            total_items += 1
            if self.materials_viewed >= len(published_materials):
                completed_items += 1
        
        # Quizzes (published only)
        published_quizzes = [q for q in module.quizzes if getattr(q, "is_published", False)]
        if published_quizzes:
            total_items += 1
            if self.quizzes_completed >= len(published_quizzes):
                completed_items += 1
        
        # Assignments (if any exist)
        if module.assignments:
            total_items += 1
            if self.assignments_submitted >= len(module.assignments):
                completed_items += 1
        
        if total_items > 0:
            self.completion_percentage = int((completed_items / total_items) * 100)
            if self.completion_percentage >= 100:
                self.completion_status = 'completed'
            elif self.completion_percentage > 0:
                self.completion_status = 'in_progress'
        
        # Calculate overall score
        scores = []
        if self.quiz_average_score is not None:
            scores.append(self.quiz_average_score)
        if self.assignment_average_score is not None:
            scores.append(self.assignment_average_score)
        
        if scores:
            self.overall_module_score = sum(scores) / len(scores)
    
    def to_dict(self):
        return {
            'id': self.id,
            'student_id': self.student_id,
            'module_id': self.module_id,
            'enrollment_id': self.enrollment_id,
            'completion_status': self.completion_status,
            'completion_percentage': self.completion_percentage,
            'materials_viewed': self.materials_viewed,
            'quizzes_completed': self.quizzes_completed,
            'assignments_submitted': self.assignments_submitted,
            'attendance_sessions': self.attendance_sessions,
            'quiz_average_score': self.quiz_average_score,
            'assignment_average_score': self.assignment_average_score,
            'overall_module_score': self.overall_module_score,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'last_accessed_at': self.last_accessed_at.isoformat() if self.last_accessed_at else None
        }