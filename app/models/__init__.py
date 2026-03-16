from app.models.user import User
from app.models.student import Student
from app.models.lecturer import Lecturer
from app.models.course import Course, Module, Enrollment
from app.models.material import CourseMaterial
from app.models.quiz import Quiz, QuizQuestion, QuizResult
from app.models.attendance import Attendance
from app.models.mark import Mark
from app.models.study_plan import StudyPlan, StudyPlanItem
from app.models.chat import ChatSession, ChatMessage
from app.models.cv_review import CVReview
from app.models.risk_score import RiskScore

__all__ = [
    'User',
    'Student',
    'Lecturer', 
    'Course',
    'Module',
    'Enrollment',
    'CourseMaterial',
    'Quiz',
    'QuizQuestion',
    'QuizResult',
    'Attendance',
    'Mark',
    'StudyPlan',
    'StudyPlanItem',
    'ChatSession',
    'ChatMessage',
    'CVReview',
    'RiskScore'
]
