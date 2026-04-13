import re

import requests


def main() -> None:
    base = "http://127.0.0.1:5000"
    s = requests.Session()

    lg = s.get(f"{base}/auth/login", timeout=10)
    # WTForms may render attributes in any order; match name="csrf_token" then value="..."
    m = re.search(r'name="csrf_token"[^>]*value="([^"]+)"', lg.text)
    if not m:
        print("Could not find csrf_token on login page")
        return

    csrf = m.group(1)
    resp = s.post(
        f"{base}/auth/login",
        data={"email": "john.smith@edumind.com", "password": "lecturer123", "csrf_token": csrf},
        allow_redirects=False,
        timeout=10,
    )
    print("login_post", resp.status_code, resp.headers.get("Location"))

    if resp.is_redirect and resp.headers.get("Location"):
        s.get(f"{base}{resp.headers['Location']}", timeout=10)

    paths = [
        "/dashboard/lecturer",
        "/courses/modules/content-management",
        "/materials/course/1",
        "/quizzes/course/1",
        "/attendance/course/1",
        "/marks/course/1",
        "/materials/module/2/upload",
        "/quizzes/module/2/create",
        "/assignments/module/2/manage",
        "/assignments/module/2/create",
        "/notifications/api/notifications/unread-count",
    ]

    for p in paths:
        r = s.get(f"{base}{p}", allow_redirects=False, timeout=10)
        print(p, r.status_code, r.headers.get("Location"))

    # Probe an unassigned module (403 expected)
    for p in ["/materials/module/1", "/quizzes/module/1"]:
        r = s.get(f"{base}{p}", allow_redirects=False, timeout=10)
        print(p, r.status_code)


if __name__ == "__main__":
    main()

