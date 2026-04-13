import re

import requests


def main() -> None:
    base = "http://127.0.0.1:5000"
    s = requests.Session()

    lg = s.get(f"{base}/auth/login", timeout=10)
    m = re.search(r'name="csrf_token"[^>]*value="([^"]+)"', lg.text)
    if not m:
        print("Could not find csrf_token on login page")
        return

    csrf = m.group(1)
    resp = s.post(
        f"{base}/auth/login",
        data={"email": "alex.thompson@student.edumind.com", "password": "student123", "csrf_token": csrf},
        allow_redirects=False,
        timeout=10,
    )
    print("login_post", resp.status_code, resp.headers.get("Location"))

    if resp.is_redirect and resp.headers.get("Location"):
        s.get(f"{base}{resp.headers['Location']}", timeout=10)

    for p in ["/materials/module/2", "/quizzes/module/2", "/assignments/module/2"]:
        r = s.get(f"{base}{p}", allow_redirects=False, timeout=10)
        print(p, r.status_code)


if __name__ == "__main__":
    main()

