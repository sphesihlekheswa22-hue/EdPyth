"""
End-to-end sanity check for lecturer ↔ student learning content flows.

Covers:
- Lecturer uploads material (published) → student can view
- Lecturer creates assignment → student can view + submit → lecturer can grade
- Lecturer creates quiz + adds question + publishes → student can take + submit → result view works

Run:
  python debug_e2e_content_flow.py
"""

from __future__ import annotations

import io
from datetime import timedelta

from app import create_app, db
from app.utils.app_time import app_now
from app.models import Course, Module, Enrollment, Quiz, QuizQuestion
from app.models.assignment import Assignment, AssignmentSubmission


LECTURER_EMAIL = "john.smith@edumind.com"
LECTURER_PASSWORD = "lecturer123"

STUDENT_EMAIL = "alex.thompson@student.edumind.com"
STUDENT_PASSWORD = "student123"


def _login(client, email: str, password: str) -> None:
    r = client.post(
        "/auth/login",
        data={"email": email, "password": password},
        follow_redirects=False,
    )
    assert r.status_code in (302, 303), f"Login failed for {email}: {r.status_code}"


def _pick_assigned_module_for_lecturer(app) -> Module:
    with app.app_context():
        from app.models import Lecturer
        from app.models.lecturer import LecturerModule

        lecturer = Lecturer.query.join(Lecturer.user).filter_by(email=LECTURER_EMAIL).first()
        if not lecturer:
            lecturer = Lecturer.query.filter(Lecturer.user.has(email=LECTURER_EMAIL)).first()
        assert lecturer, "Seed lecturer not found"

        module = (
            Module.query.join(LecturerModule, LecturerModule.module_id == Module.id)
            .filter(LecturerModule.lecturer_id == lecturer.id)
            .order_by(Module.id.asc())
            .first()
        )
        assert module, "Lecturer has no assigned modules"
        return module


def _ensure_student_enrolled_in_course(app, course_id: int) -> None:
    with app.app_context():
        from app.models import Student

        student = Student.query.filter(Student.user.has(email=STUDENT_EMAIL)).first()
        assert student, "Seed student not found"
        existing = Enrollment.query.filter_by(student_id=student.id, course_id=course_id, status="active").first()
        if existing:
            return
        db.session.add(Enrollment(student_id=student.id, course_id=course_id, status="active"))
        db.session.commit()


def main() -> None:
    app = create_app("development")
    app.config.update(TESTING=True, WTF_CSRF_ENABLED=False)

    client = app.test_client()

    # Pick scope
    module = _pick_assigned_module_for_lecturer(app)
    with app.app_context():
        course = Course.query.get(module.course_id)
        assert course, "Module missing course"
    _ensure_student_enrolled_in_course(app, course.id)

    print(f"Using course={course.code}({course.id}) module={module.title}({module.id})")

    # -------- Lecturer creates content --------
    _login(client, LECTURER_EMAIL, LECTURER_PASSWORD)

    # 1) Upload material (published)
    material_title = f"E2E Material {app_now().isoformat()}"
    file_bytes = io.BytesIO(b"%PDF-1.4\n%fake pdf\n")
    file_bytes.name = "e2e_material.pdf"
    r = client.post(
        f"/materials/module/{module.id}/upload",
        data={
            "title": material_title,
            "description": "E2E upload",
            "category": "general",
            "is_published": "on",
            "file": (file_bytes, "e2e_material.pdf"),
        },
        content_type="multipart/form-data",
        follow_redirects=False,
    )
    assert r.status_code in (302, 303), f"Material upload failed: {r.status_code}"

    # 2) Create assignment
    assignment_title = f"E2E Assignment {app_now().isoformat()}"
    due = (app_now() + timedelta(days=7)).strftime("%Y-%m-%dT%H:%M")
    r = client.post(
        f"/assignments/module/{module.id}/create",
        data={
            "title": assignment_title,
            "description": "E2E assignment",
            "due_date": due,
            "total_marks": "100",
        },
        follow_redirects=False,
    )
    assert r.status_code in (302, 303), f"Assignment create failed: {r.status_code}"

    with app.app_context():
        assignment = (
            Assignment.query.filter_by(module_id=module.id, title=assignment_title)
            .order_by(Assignment.id.desc())
            .first()
        )
        assert assignment, "Assignment not found after create"

    # 3) Create quiz + add question + publish
    quiz_title = f"E2E Quiz {app_now().isoformat()}"
    r = client.post(
        f"/quizzes/module/{module.id}/create",
        data={
            "title": quiz_title,
            "description": "E2E quiz",
            "time_limit": "10",
            "passing_score": "60",
        },
        follow_redirects=False,
    )
    assert r.status_code in (302, 303), f"Quiz create failed: {r.status_code}"

    with app.app_context():
        quiz = Quiz.query.filter_by(module_id=module.id, title=quiz_title).order_by(Quiz.id.desc()).first()
        assert quiz, "Quiz not found after create"

    # Add a MCQ question
    r = client.post(
        f"/quizzes/{quiz.id}/edit",
        data={
            "question_text": "What is 2+2?",
            "question_type": "multiple_choice",
            "points": "1",
            "options[]": ["3", "4", "5", ""],
            "correct_option": "1",
        },
        follow_redirects=False,
    )
    assert r.status_code in (302, 303), f"Quiz add question failed: {r.status_code}"

    # Publish quiz
    r = client.post(f"/quizzes/{quiz.id}/publish", data={}, follow_redirects=False)
    assert r.status_code in (302, 303), f"Quiz publish failed: {r.status_code}"

    # Verify notifications are created for student for material/assignment/quiz
    with app.app_context():
        from app.models import User
        from app.models.notification import Notification

        student_user = User.query.filter_by(email=STUDENT_EMAIL).first()
        assert student_user, "Student user not found"

        notif_types = {
            n.type
            for n in Notification.query.filter_by(recipient_id=student_user.id)
            .order_by(Notification.created_at.desc())
            .limit(50)
            .all()
        }
        assert "material_published" in notif_types, "Missing material_published notification"
        assert "assignment_posted" in notif_types, "Missing assignment_posted notification"
        assert "quiz_published" in notif_types, "Missing quiz_published notification"

    # -------- Student views and submits --------
    client = app.test_client()  # new session
    _login(client, STUDENT_EMAIL, STUDENT_PASSWORD)

    # Notification bell APIs + View all page
    r = client.get("/notifications/api/notifications?per_page=10")
    assert r.status_code == 200, f"Notifications API failed: {r.status_code}"
    data = r.get_json() or {}
    api_types = {n.get("type") for n in (data.get("notifications") or [])}
    assert "material_published" in api_types, "Bell API missing material_published"
    assert "assignment_posted" in api_types, "Bell API missing assignment_posted"
    assert "quiz_published" in api_types, "Bell API missing quiz_published"

    r = client.get("/notifications/")
    assert r.status_code == 200, f"Notifications page failed: {r.status_code}"

    # Materials visible
    r = client.get(f"/materials/module/{module.id}")
    assert r.status_code == 200, f"Student materials view failed: {r.status_code}"

    # Assignments visible
    r = client.get(f"/assignments/module/{module.id}")
    assert r.status_code in (200, 302, 303), f"Student assignments list failed: {r.status_code}"

    # Submit assignment
    sub_file = io.BytesIO(b"hello assignment")
    sub_file.name = "e2e_submission.txt"
    r = client.post(
        f"/assignments/{assignment.id}/submit",
        data={"file": (sub_file, "e2e_submission.txt")},
        content_type="multipart/form-data",
        follow_redirects=False,
    )
    assert r.status_code in (302, 303), f"Assignment submit failed: {r.status_code}"

    with app.app_context():
        submission = (
            AssignmentSubmission.query.filter_by(assignment_id=assignment.id)
            .order_by(AssignmentSubmission.id.desc())
            .first()
        )
        assert submission, "Submission not found after submit"

    # Take quiz page
    r = client.get(f"/quizzes/{quiz.id}/take", follow_redirects=False)
    assert r.status_code in (200, 302, 303), f"Quiz take page failed: {r.status_code}"

    with app.app_context():
        q = QuizQuestion.query.filter_by(quiz_id=quiz.id).order_by(QuizQuestion.order).first()
        assert q, "Quiz question missing"
        correct = q.correct_answer

    r = client.post(
        f"/quizzes/{quiz.id}/submit",
        data={f"question_{q.id}": correct, "started_at": app_now().isoformat()},
        follow_redirects=False,
    )
    assert r.status_code in (302, 303), f"Quiz submit failed: {r.status_code}"

    # -------- Lecturer grades submission --------
    client = app.test_client()
    _login(client, LECTURER_EMAIL, LECTURER_PASSWORD)

    r = client.get(f"/assignments/submissions/{assignment.id}")
    assert r.status_code == 200, f"Lecturer submissions view failed: {r.status_code}"

    r = client.post(
        f"/assignments/submissions/{submission.id}/grade",
        data={"mark": "85", "feedback": "Good job"},
        follow_redirects=False,
    )
    assert r.status_code in (302, 303), f"Grade submission failed: {r.status_code}"

    # Lecturer exports: marks + attendance CSV download
    r = client.get(f"/marks/module/{module.id}/export.csv")
    assert r.status_code == 200, f"Marks export failed: {r.status_code}"

    r = client.get(f"/attendance/module/{module.id}/export.csv")
    assert r.status_code == 200, f"Attendance export failed: {r.status_code}"

    print("E2E flow OK: materials, assignment submit+grade, quiz take+submit")


if __name__ == "__main__":
    main()

