# Using the app like a real user

## 1. One-time setup

1. Follow `RUN_IN_VSCODE.md` (venv, `pip install -r requirements.txt`, `.env` with `FLASK_ENV=development`).
2. Load demo data (creates users, courses, modules, enrollments, etc.):

   ```powershell
   python seed_data.py
   ```

3. Start the server:

   ```powershell
   python run.py
   ```

4. Open [http://127.0.0.1:5000](http://127.0.0.1:5000) and sign in at `/auth/login`.

## 2. Demo accounts (from `seed_data.py`)

| Role           | Email                               | Password     |
|----------------|-------------------------------------|--------------|
| Admin          | `admin@edumind.com`                 | `admin123`   |
| Lecturer       | `john.smith@edumind.com`            | `lecturer123`|
| Student        | `alex.thompson@student.edumind.com` | `student123` |
| Career advisor | `career@edumind.com`                | `career123`  |

Other seeded lecturers use `lecturer123`; other students use `student123`.

## 3. What to click through (smoke test)

- **Student:** Dashboard → Courses → open a course → module hub → materials, quizzes, assignments, marks, attendance (read-only where expected).
- **Lecturer:** Same module URLs plus create/upload flows (assignments, quizzes, attendance record, **enter marks**).
- **Admin:** `/admin/courses`, user management, analytics as linked from the nav.

## 4. Automated “user flow” check (no browser)

This hits login, dashboards, lecturer module pages, legacy redirects, and admin pages using Flask’s test client:

```powershell
python test_end_to_end.py
```

You should see **END-TO-END TESTING COMPLETE** with no traceback.  
(Login passwords in that script match `seed_data.py`.)

## 5. Optional: browser automation

If you install Playwright (`pip install playwright` then `playwright install`), you can run:

```powershell
python qa_test_playwright.py
```

Start `python run.py` in another terminal first; the script expects `http://localhost:5000` and uses the same demo accounts as the table above.
