from __future__ import annotations

from dataclasses import dataclass
from http import HTTPStatus
from typing import Optional, Tuple

from flask import abort
from flask_login import current_user

from app.models import Course, Enrollment, Lecturer, Student, Module
from app.models.lecturer import LecturerModule


@dataclass(frozen=True)
class ActiveEnrollmentContext:
    course: Course
    student: Student
    enrollment: Enrollment


@dataclass(frozen=True)
class ModuleAccessContext:
    """Context for module-level access control."""
    module: Module
    course: Course
    student: Optional[Student]
    enrollment: Optional[Enrollment]
    has_access: bool


def get_current_student_or_404() -> Student:
    """Fetch the current user's Student profile."""
    return Student.query.filter_by(user_id=current_user.id).first_or_404()


def get_current_lecturer_or_404() -> Lecturer:
    """Fetch the current user's Lecturer profile."""
    return Lecturer.query.filter_by(user_id=current_user.id).first_or_404()


def require_active_enrollment(course_id: int) -> ActiveEnrollmentContext:
    """
    Require the current user to be a student with ACTIVE enrollment in course_id.
    Returns (course, student, enrollment) context or aborts 403/404.
    """
    course: Course = Course.query.get_or_404(course_id)

    if current_user.role != "student":
        abort(HTTPStatus.FORBIDDEN)

    student = get_current_student_or_404()

    enrollment: Optional[Enrollment] = Enrollment.query.filter_by(
        student_id=student.id,
        course_id=course_id,
        status="active",
    ).first()

    if not enrollment:
        abort(HTTPStatus.FORBIDDEN, "Active enrollment required")

    return ActiveEnrollmentContext(course=course, student=student, enrollment=enrollment)


def require_module_access(module_id: int) -> ModuleAccessContext:
    """
    Require access to a specific module.
    
    For students: Must be enrolled in the course containing the module.
    For lecturers: Must be assigned to at least one module in the course.
    For admins: Always allowed.
    
    Returns ModuleAccessContext or aborts 403/404.
    """
    module: Module = Module.query.get_or_404(module_id)
    course: Course = Course.query.get_or_404(module.course_id)
    
    student = None
    enrollment = None
    has_access = False
    
    if current_user.role == "admin":
        has_access = True
        
    elif current_user.role == "student":
        student = get_current_student_or_404()
        enrollment = Enrollment.query.filter_by(
            student_id=student.id,
            course_id=course.id,
            status="active"
        ).first()
        has_access = enrollment is not None
        
    elif current_user.role == "lecturer":
        lecturer = get_current_lecturer_or_404()
        # Must be assigned to THIS module
        has_access = module.is_lecturer_assigned(lecturer.id)
    
    if not has_access:
        abort(HTTPStatus.FORBIDDEN, "Access to this module is not permitted")
    
    return ModuleAccessContext(
        module=module,
        course=course,
        student=student,
        enrollment=enrollment,
        has_access=True
    )


def require_lecturer_owns_course(course_id: int) -> Tuple[Course, Lecturer]:
    """
    DEPRECATED: Use require_lecturer_assigned_to_course instead.
    
    Require current user to be lecturer and assigned to at least one module in this course.
    """
    return require_lecturer_assigned_to_course(course_id)


def require_lecturer_assigned_to_course(course_id: int) -> Tuple[Course, Lecturer]:
    """
    Require current user to be lecturer and assigned to at least one module in this course.
    Admin bypass is NOT included here (callers can handle admin separately).
    """
    course: Course = Course.query.get_or_404(course_id)

    if current_user.role != "lecturer":
        abort(HTTPStatus.FORBIDDEN)

    lecturer = get_current_lecturer_or_404()
    
    # Check if assigned to any module in this course
    assigned = LecturerModule.query.join(Module).filter(
        LecturerModule.lecturer_id == lecturer.id,
        Module.course_id == course_id
    ).first() is not None
    
    if not assigned:
        abort(HTTPStatus.FORBIDDEN, "Not authorized for this course")

    return course, lecturer


def require_lecturer_assigned_to_module(module_id: int) -> Tuple[Module, Optional[Lecturer]]:
    """
    Require current user to be lecturer and assigned to this specific module.
    """
    module: Module = Module.query.get_or_404(module_id)

    if current_user.role == "admin":
        # Admins bypass lecturer assignment checks.
        return module, None

    if current_user.role != "lecturer":
        abort(HTTPStatus.FORBIDDEN)

    lecturer = get_current_lecturer_or_404()
    
    if not module.is_lecturer_assigned(lecturer.id):
        abort(HTTPStatus.FORBIDDEN, "Not assigned to this module")

    return module, lecturer


def can_access_course_content(course_id: int) -> bool:
    """
    Check if current user can access content for a course.
    
    Students: Must be enrolled
    Lecturers: Must be assigned to at least one module
    Admins: Always
    """
    if current_user.role == "admin":
        return True
    
    if current_user.role == "student":
        student = Student.query.filter_by(user_id=current_user.id).first()
        if not student:
            return False
        return Enrollment.query.filter_by(
            student_id=student.id,
            course_id=course_id,
            status="active"
        ).first() is not None
    
    if current_user.role == "lecturer":
        lecturer = Lecturer.query.filter_by(user_id=current_user.id).first()
        if not lecturer:
            return False
        # Check if assigned to any module in this course
        return LecturerModule.query.join(Module).filter(
            LecturerModule.lecturer_id == lecturer.id,
            Module.course_id == course_id
        ).first() is not None
    
    return False


def can_edit_module_content(module_id: int) -> bool:
    """
    Check if current user can edit content in a module.
    
    Lecturers: Must be assigned to at least one module in the course (course-level access)
    Admins: Always
    Students: Never
    """
    if current_user.role == "admin":
        return True
    
    if current_user.role != "lecturer":
        return False
    
    lecturer = Lecturer.query.filter_by(user_id=current_user.id).first()
    if not lecturer:
        return False
    
    module = Module.query.get(module_id)
    if not module:
        return False
    
    # Check if lecturer is assigned to THIS module
    return module.is_lecturer_assigned(lecturer.id)


def is_admin() -> bool:
    return bool(getattr(current_user, "is_authenticated", False) and current_user.role == "admin")


def get_student_progress_in_course(student_id: int, course_id: int) -> dict:
    """
    Get comprehensive progress data for a student in a course.
    Aggregates progress across all modules.
    """
    from app.models import StudentModuleProgress
    
    enrollment = Enrollment.query.filter_by(
        student_id=student_id,
        course_id=course_id,
        status="active"
    ).first()
    
    if not enrollment:
        return {
            "enrolled": False,
            "overall_percentage": 0,
            "modules_completed": 0,
            "total_modules": 0
        }
    
    progress_records = StudentModuleProgress.query.filter_by(
        enrollment_id=enrollment.id
    ).all()
    
    total_modules = len(progress_records)
    modules_completed = sum(1 for p in progress_records if p.completion_status == "completed")
    overall_percentage = (
        sum(p.completion_percentage for p in progress_records) / total_modules
        if total_modules > 0 else 0
    )
    
    return {
        "enrolled": True,
        "enrollment_id": enrollment.id,
        "overall_percentage": round(overall_percentage, 2),
        "modules_completed": modules_completed,
        "total_modules": total_modules,
        "module_progress": [p.to_dict() for p in progress_records]
    }
