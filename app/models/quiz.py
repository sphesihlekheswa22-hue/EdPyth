from datetime import datetime
from app import db
import json


class Quiz(db.Model):
    """Quiz model for course quizzes."""
    __tablename__ = 'quizzes'
    
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    time_limit = db.Column(db.Integer, default=30)  # in minutes
    passing_score = db.Column(db.Integer, default=60)  # percentage
    is_published = db.Column(db.Boolean, default=False)
    is_ai_generated = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    due_date = db.Column(db.DateTime, nullable=True)
    
    # Relationships
    questions = db.relationship('QuizQuestion', backref='quiz', lazy=True, cascade='all, delete-orphan')
    results = db.relationship('QuizResult', backref='quiz', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Quiz {self.title}>'
    
    @property
    def question_count(self):
        """Get total number of questions."""
        return len(self.questions)
    
    @property
    def total_points(self):
        """Get total points for the quiz."""
        return sum(q.points for q in self.questions)
    
    def to_dict(self):
        return {
            'id': self.id,
            'course_id': self.course_id,
            'title': self.title,
            'description': self.description,
            'time_limit': self.time_limit,
            'passing_score': self.passing_score,
            'question_count': self.question_count,
            'total_points': self.total_points,
            'is_published': self.is_published,
            'is_ai_generated': self.is_ai_generated,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'due_date': self.due_date.isoformat() if self.due_date else None
        }


class QuizQuestion(db.Model):
    """Quiz question model."""
    __tablename__ = 'quiz_questions'
    
    id = db.Column(db.Integer, primary_key=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quizzes.id'), nullable=False)
    module_id = db.Column(db.Integer, db.ForeignKey('modules.id'), nullable=True)
    question_text = db.Column(db.Text, nullable=False)
    question_type = db.Column(db.String(20), default='multiple_choice')  # multiple_choice, true_false, short_answer
    points = db.Column(db.Integer, default=1)
    order = db.Column(db.Integer, default=0)
    
    # For multiple choice and true/false
    options = db.Column(db.Text, nullable=True)  # JSON string of options
    correct_answer = db.Column(db.Text, nullable=True)
    
    # For short answer
    acceptable_answers = db.Column(db.Text, nullable=True)  # JSON array of acceptable answers
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<QuizQuestion {self.id}>'
    
    def set_options(self, options_list):
        """Set options as JSON string."""
        self.options = json.dumps(options_list)
    
    def get_options(self):
        """Get options as list."""
        if self.options:
            return json.loads(self.options)
        return []
    
    def set_acceptable_answers(self, answers_list):
        """Set acceptable answers as JSON string."""
        self.acceptable_answers = json.dumps(answers_list)
    
    def get_acceptable_answers(self):
        """Get acceptable answers as list."""
        if self.acceptable_answers:
            return json.loads(self.acceptable_answers)
        return []
    
    def check_answer(self, answer):
        """Check if the given answer is correct."""
        if self.question_type in ['multiple_choice', 'true_false']:
            return answer and answer.lower().strip() == self.correct_answer.lower().strip()
        elif self.question_type == 'short_answer':
            acceptable = self.get_acceptable_answers()
            return any(answer and answer.lower().strip() == a.lower().strip() for a in acceptable)
        return False
    
    def to_dict(self, include_correct=False):
        data = {
            'id': self.id,
            'quiz_id': self.quiz_id,
            'module_id': self.module_id,
            'question_text': self.question_text,
            'question_type': self.question_type,
            'points': self.points,
            'order': self.order,
            'options': self.get_options() if self.question_type in ['multiple_choice', 'true_false'] else None
        }
        if include_correct:
            data['correct_answer'] = self.correct_answer
            data['acceptable_answers'] = self.get_acceptable_answers()
        return data


class QuizResult(db.Model):
    """Quiz result model for storing student quiz attempts."""
    __tablename__ = 'quiz_results'
    
    id = db.Column(db.Integer, primary_key=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quizzes.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    score = db.Column(db.Float, nullable=False)
    total_points = db.Column(db.Float, nullable=False)
    percentage = db.Column(db.Float, nullable=False)
    passed = db.Column(db.Boolean, default=False)
    time_taken = db.Column(db.Integer, nullable=True)  # in seconds
    answers = db.Column(db.Text, nullable=True)  # JSON string of answers
    started_at = db.Column(db.DateTime, nullable=True)
    completed_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<QuizResult Quiz {self.quiz_id} - Student {self.student_id}>'
    
    def set_answers(self, answers_dict):
        """Set answers as JSON string."""
        self.answers = json.dumps(answers_dict)
    
    def get_answers(self):
        """Get answers as dictionary."""
        if self.answers:
            return json.loads(self.answers)
        return {}
    
    def to_dict(self):
        return {
            'id': self.id,
            'quiz_id': self.quiz_id,
            'student_id': self.student_id,
            'score': self.score,
            'total_points': self.total_points,
            'percentage': self.percentage,
            'passed': self.passed,
            'time_taken': self.time_taken,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None
        }
