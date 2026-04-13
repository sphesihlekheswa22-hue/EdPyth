"""
End-to-end sanity check for student ↔ career advisor CV review flow.

Flow:
- Student uploads CV (creates CVReview pending)
- Career advisor opens review queue and review page
- Career advisor submits feedback (marks reviewed)
- Student can view review detail page and dashboards without 403/500

Run:
  python debug_e2e_career_flow.py
"""

from __future__ import annotations

import io
from app import create_app, db
from app.utils.app_time import app_now
from app.models import CVReview, User
from app.models.notification import Notification


STUDENT_EMAIL = "alex.thompson@student.edumind.com"
STUDENT_PASSWORD = "student123"

ADVISOR_EMAIL = "career@edumind.com"
ADVISOR_PASSWORD = "career123"


def _login(client, email: str, password: str) -> None:
    r = client.post("/auth/login", data={"email": email, "password": password}, follow_redirects=False)
    assert r.status_code in (302, 303), f"Login failed for {email}: {r.status_code}"


def main() -> None:
    app = create_app("development")
    app.config.update(TESTING=True, WTF_CSRF_ENABLED=False)

    # --- Student uploads CV ---
    client = app.test_client()
    _login(client, STUDENT_EMAIL, STUDENT_PASSWORD)

    # Page loads
    r = client.get("/career/upload-cv")
    assert r.status_code == 200, f"Upload CV page failed: {r.status_code}"

    cv_bytes = io.BytesIO(b"%PDF-1.4\n% e2e cv\n")
    cv_bytes.name = "e2e_cv.pdf"
    r = client.post(
        "/career/upload-cv",
        data={"notes": "E2E upload", "file": (cv_bytes, "e2e_cv.pdf")},
        content_type="multipart/form-data",
        follow_redirects=False,
    )
    assert r.status_code in (302, 303), f"CV upload failed: {r.status_code}"

    with app.app_context():
        student_user = User.query.filter_by(email=STUDENT_EMAIL).first()
        assert student_user, "Student user not found"
        review = (
            CVReview.query.join(CVReview.student)
            .filter(CVReview.student.has(user_id=student_user.id))
            .order_by(CVReview.id.desc())
            .first()
        )
        assert review, "CVReview not created"
        review_id = review.id

    # Student dashboard loads and shows no server error
    r = client.get("/career/dashboard")
    assert r.status_code == 200, f"Student career dashboard failed: {r.status_code}"

    # --- Advisor reviews CV ---
    client = app.test_client()
    _login(client, ADVISOR_EMAIL, ADVISOR_PASSWORD)

    r = client.get("/career/advisor/reviews")
    assert r.status_code == 200, f"Advisor review queue failed: {r.status_code}"

    r = client.get(f"/career/advisor/review/{review_id}")
    assert r.status_code == 200, f"Advisor review page failed: {r.status_code}"

    r = client.post(
        f"/career/advisor/review/{review_id}",
        data={
            "score": "78",
            "strengths": "Clear layout\nGood projects",
            "weaknesses": "Add metrics\nImprove summary",
            "recommendations": "Tailor CV to roles",
            "suggested_skills": "Python\nSQL\nCommunication",
            "suggested_projects": "Portfolio website\nData dashboard",
            "interview_tips": "Prepare STAR stories",
        },
        follow_redirects=False,
    )
    assert r.status_code in (302, 303), f"Advisor submit review failed: {r.status_code}"

    with app.app_context():
        updated = CVReview.query.get(review_id)
        assert updated is not None
        assert updated.status == "reviewed", f"Review status not updated: {updated.status}"
        assert updated.reviewed_at is not None, "reviewed_at not set"
        assert updated.reviewed_by is not None, "reviewed_by not set"
        student_user = User.query.filter_by(email=STUDENT_EMAIL).first()
        assert student_user is not None
        notif = (
            Notification.query.filter_by(recipient_id=student_user.id, type="cv_reviewed")
            .order_by(Notification.created_at.desc())
            .first()
        )
        assert notif is not None, "Missing cv_reviewed notification for student"

    # --- Student sees reviewed CV ---
    client = app.test_client()
    _login(client, STUDENT_EMAIL, STUDENT_PASSWORD)

    # Notification bell API includes cv_reviewed
    r = client.get("/notifications/api/notifications?per_page=10")
    assert r.status_code == 200, f"Notifications API failed: {r.status_code}"
    data = r.get_json() or {}
    types = {n.get("type") for n in (data.get("notifications") or [])}
    assert "cv_reviewed" in types, "Bell API missing cv_reviewed"

    r = client.get(f"/career/cv/{review_id}")
    assert r.status_code == 200, f"Student review detail failed: {r.status_code}"

    r = client.get("/career/job-readiness")
    assert r.status_code == 200, f"Job readiness page failed: {r.status_code}"

    r = client.get("/career/skills-suggestions")
    assert r.status_code == 200, f"Skills suggestions page failed: {r.status_code}"

    print(f"E2E career flow OK (review_id={review_id}) at {app_now().isoformat()}")


if __name__ == "__main__":
    main()

