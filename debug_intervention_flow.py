import re
import requests


def get_csrf_from_html(html: str) -> str | None:
    # base.html: <meta name="csrf-token" content="...">
    m = re.search(r'<meta\\s+name="csrf-token"\\s+content="([^"]+)"', html)
    if m:
        return m.group(1)
    # fallback: hidden input
    m = re.search(r'name="csrf_token"[^>]*value="([^"]+)"', html)
    return m.group(1) if m else None


def login(session: requests.Session, base: str, email: str, password: str) -> None:
    lg = session.get(f"{base}/auth/login", timeout=10)
    csrf = get_csrf_from_html(lg.text)
    if not csrf:
        raise RuntimeError("No CSRF token on login page")
    session.post(
        f"{base}/auth/login",
        data={"email": email, "password": password, "csrf_token": csrf},
        allow_redirects=True,
        timeout=10,
    )
    # Ensure we're actually logged in by hitting dashboard
    dash = session.get(f"{base}/dashboard", allow_redirects=False, timeout=10)
    if dash.status_code in (301, 302) and dash.headers.get("Location", "").startswith("/auth/login"):
        raise RuntimeError("Login failed (redirected back to login)")
    return None


def main() -> None:
    base = "http://127.0.0.1:5000"

    # Lecturer session
    lec = requests.Session()
    # CSRF is exempt for intervention APIs, so token is not required here.
    login(lec, base, "john.smith@edumind.com", "lecturer123")

    # Student session
    stu = requests.Session()
    login(stu, base, "alex.thompson@student.edumind.com", "student123")

    before = stu.get(f"{base}/notifications/api/notifications/unread-count", timeout=10).json()["count"]

    payload = {"student_id": 1, "message": "TEST intervention message", "template": "custom", "course_id": 1}
    send = lec.post(
        f"{base}/notifications/api/interventions/send",
        json=payload,
        timeout=10,
    )
    print("send_status", send.status_code, send.text[:200])

    after = stu.get(f"{base}/notifications/api/notifications/unread-count", timeout=10).json()["count"]
    poll = stu.get(f"{base}/notifications/api/notifications/poll", timeout=10).json()

    print("student_unread_before", before)
    print("student_unread_after", after)
    print("poll_has_new", poll.get("has_new"), "new_count", len(poll.get("notifications") or []))


if __name__ == "__main__":
    main()

