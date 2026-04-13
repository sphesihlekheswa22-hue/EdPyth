#!/usr/bin/env python3
"""
EduMind LMS - Comprehensive QA Testing Script
Tests all user flows like a real human user using Playwright browser automation.
"""

import asyncio
import sys
import os
from datetime import datetime
from playwright.async_api import async_playwright

# Test configuration (override for CI / headed local runs)
BASE_URL = os.environ.get("PLAYWRIGHT_BASE_URL", "http://127.0.0.1:5000")
HEADLESS = os.environ.get("PLAYWRIGHT_HEADLESS", "1").lower() in ("1", "true", "yes")
SLOW_MO = int(os.environ.get("PLAYWRIGHT_SLOW_MO", "0"))

# Test credentials from seed_data.py
TEST_USERS = {
    'admin': {'email': 'admin@edumind.com', 'password': 'admin123'},
    'lecturer': {'email': 'john.smith@edumind.com', 'password': 'lecturer123'},
    'student': {'email': 'alex.thompson@student.edumind.com', 'password': 'student123'},
    'career_advisor': {'email': 'career@edumind.com', 'password': 'career123'},
}

# Bug tracking
BUGS_FOUND = []

def log_bug(title, role, steps, expected, actual, severity):
    """Log a bug report."""
    bug = {
        'title': title,
        'role': role,
        'steps': steps,
        'expected': expected,
        'actual': actual,
        'severity': severity
    }
    BUGS_FOUND.append(bug)
    print(f"\n{'='*70}")
    print(f"BUG FOUND: {title}")
    print(f"Severity: {severity}")
    print(f"Role: {role}")
    print(f"Expected: {expected}")
    print(f"Actual: {actual}")
    print(f"{'='*70}\n")

def log_test(message):
    """Log a test step."""
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")

async def wait_for_page_load(page):
    """Wait for DOM load (not networkidle — long-polling APIs would hang)."""
    await page.wait_for_load_state("load")
    await asyncio.sleep(0.35)

async def login(page, email, password):
    """Perform login action."""
    log_test(f"Logging in as {email}...")
    
    # Navigate to login page
    await page.goto(f"{BASE_URL}/auth/login")
    await wait_for_page_load(page)
    
    # Fill in credentials
    await page.fill('input[name="email"]', email)
    await page.fill('input[name="password"]', password)
    
    # Submit form
    await page.click('button[type="submit"]')
    await wait_for_page_load(page)
    
    # Check if login was successful (should redirect to dashboard)
    current_url = page.url
    if 'login' in current_url:
        # Check for error messages
        error_alert = await page.query_selector('.alert-danger')
        if error_alert:
            error_text = await error_alert.inner_text()
            return False, error_text
        return False, "Still on login page after submit"
    
    return True, "Login successful"

async def logout(page):
    """Perform logout action."""
    log_test("Logging out...")
    await page.goto(f"{BASE_URL}/auth/logout")
    await wait_for_page_load(page)

async def test_admin_flow(page):
    """Test admin user flow."""
    log_test("\n" + "="*70)
    log_test("TESTING ADMIN FLOW")
    log_test("="*70)
    
    # Login as admin
    success, message = await login(page, TEST_USERS['admin']['email'], TEST_USERS['admin']['password'])
    if not success:
        log_bug(
            title="Admin Login Failed",
            role="Admin",
            steps=["Navigate to login page", "Enter admin credentials", "Submit form"],
            expected="Successful login and redirect to dashboard",
            actual=message,
            severity="Critical"
        )
        return
    log_test("Admin login successful")
    
    # Check dashboard
    log_test("Checking admin dashboard...")
    await page.goto(f"{BASE_URL}/dashboard")
    await wait_for_page_load(page)
    
    # Verify dashboard elements
    dashboard_title = await page.title()
    log_test(f"Dashboard title: {dashboard_title}")
    
    # Check if there are any error messages on dashboard
    error_elements = await page.query_selector_all('.alert-danger')
    if error_elements:
        for elem in error_elements:
            text = await elem.inner_text()
            log_bug(
                title="Error displayed on admin dashboard",
                role="Admin",
                steps=["Login as admin", "Navigate to dashboard"],
                expected="Dashboard loads without errors",
                actual=f"Error shown: {text}",
                severity="Medium"
            )
    
    # Test course management
    log_test("Testing course management...")
    await page.goto(f"{BASE_URL}/admin/courses")
    await wait_for_page_load(page)
    
    # Check if course management page loads
    if 'courses' not in page.url and 'admin' not in page.url:
        log_bug(
            title="Course management page not accessible",
            role="Admin",
            steps=["Login as admin", "Navigate to /admin/courses"],
            expected="Course management page loads",
            actual=f"Redirected to: {page.url}",
            severity="High"
        )
    else:
        log_test("Course management page loaded successfully")
        
        # Add course entry (admin uses /admin/courses/add card link, not always "Create")
        create_btn = await page.query_selector('a[href*="courses/add"]')
        if create_btn:
            log_test("Add course entry found")
        else:
            log_bug(
                title="Add course entry not found",
                role="Admin",
                steps=["Login as admin", "Navigate to course management"],
                expected="Link or card to add a course visible",
                actual="No add-course link found on page",
                severity="Medium"
            )
    
    # Test user management
    log_test("Testing user management...")
    await page.goto(f"{BASE_URL}/admin/users")
    await wait_for_page_load(page)
    
    if 'users' not in page.url:
        log_bug(
            title="User management page not accessible",
            role="Admin",
            steps=["Login as admin", "Navigate to /admin/users"],
            expected="User management page loads",
            actual=f"Redirected to: {page.url}",
            severity="High"
        )
    else:
        log_test("User management page loaded successfully")
    
    # Logout
    await logout(page)

async def test_student_flow(page):
    """Test student user flow."""
    log_test("\n" + "="*70)
    log_test("TESTING STUDENT FLOW")
    log_test("="*70)
    
    # Login as student
    success, message = await login(page, TEST_USERS['student']['email'], TEST_USERS['student']['password'])
    if not success:
        log_bug(
            title="Student Login Failed",
            role="Student",
            steps=["Navigate to login page", "Enter student credentials", "Submit form"],
            expected="Successful login and redirect to dashboard",
            actual=message,
            severity="Critical"
        )
        return
    log_test("Student login successful")
    
    # Check dashboard
    log_test("Checking student dashboard...")
    await page.goto(f"{BASE_URL}/dashboard")
    await wait_for_page_load(page)
    
    # Check for enrolled courses
    log_test("Checking enrolled courses...")
    await page.goto(f"{BASE_URL}/courses")
    await wait_for_page_load(page)
    
    # Look for course cards or list
    course_elements = await page.query_selector_all('.course-card, .card, tr[data-course], .course-item')
    if not course_elements:
        course_elements = await page.query_selector_all('a[href*="courses/"]')
    
    if course_elements:
        log_test(f"Found {len(course_elements)} course elements")
        
        # Try to click on first course
        first_course = course_elements[0]
        await first_course.click()
        await wait_for_page_load(page)
        log_test(f"Navigated to course detail: {page.url}")
        
        # Check for modules
        module_elements = await page.query_selector_all('.module, [class*="module"], a[href*="modules"]')
        if module_elements:
            log_test(f"Found {len(module_elements)} module elements")
        else:
            log_bug(
                title="No modules visible in course",
                role="Student",
                steps=["Login as student", "Navigate to courses", "Click on a course"],
                expected="Modules should be displayed",
                actual="No module elements found",
                severity="Medium"
            )
    else:
        log_bug(
            title="No courses visible for student",
            role="Student",
            steps=["Login as student", "Navigate to courses page"],
            expected="Enrolled courses should be displayed",
            actual="No course elements found on page",
            severity="High"
        )
    
    # Test quiz access
    log_test("Testing quiz access...")
    await page.goto(f"{BASE_URL}/quizzes")
    await wait_for_page_load(page)
    
    quiz_elements = await page.query_selector_all('a[href*="quizzes/"], .quiz-item, tr[data-quiz]')
    if quiz_elements:
        log_test(f"Found {len(quiz_elements)} quiz elements")
    else:
        log_test("No quizzes visible (may be expected if none assigned)")
    
    # Test assignments
    log_test("Testing assignments...")
    await page.goto(f"{BASE_URL}/assignments")
    await wait_for_page_load(page)
    
    assignment_elements = await page.query_selector_all('a[href*="assignments/"], .assignment-item, tr[data-assignment]')
    if assignment_elements:
        log_test(f"Found {len(assignment_elements)} assignment elements")
    else:
        log_test("No assignments visible")
    
    # Test marks/grades (index /marks redirects students to courses; use summary page)
    log_test("Testing marks/grades view...")
    await page.goto(f"{BASE_URL}/marks/student")
    await wait_for_page_load(page)
    
    if "marks" not in page.url:
        log_bug(
            title="Student marks summary not accessible",
            role="Student",
            steps=["Login as student", "Navigate to /marks/student"],
            expected="Marks summary loads",
            actual=f"At URL: {page.url}",
            severity="Medium"
        )
    
    # Logout
    await logout(page)

async def test_lecturer_flow(page):
    """Test lecturer user flow."""
    log_test("\n" + "="*70)
    log_test("TESTING LECTURER FLOW")
    log_test("="*70)
    
    # Login as lecturer
    success, message = await login(page, TEST_USERS['lecturer']['email'], TEST_USERS['lecturer']['password'])
    if not success:
        log_bug(
            title="Lecturer Login Failed",
            role="Lecturer",
            steps=["Navigate to login page", "Enter lecturer credentials", "Submit form"],
            expected="Successful login and redirect to dashboard",
            actual=message,
            severity="Critical"
        )
        return
    log_test("Lecturer login successful")
    
    # Check dashboard
    log_test("Checking lecturer dashboard...")
    await page.goto(f"{BASE_URL}/dashboard")
    await wait_for_page_load(page)
    
    # Check for assigned modules
    log_test("Checking assigned modules...")
    await page.goto(f"{BASE_URL}/materials")
    await wait_for_page_load(page)
    
    module_elements = await page.query_selector_all('a[href*="modules/"], .module-item, tr[data-module]')
    if module_elements:
        log_test(f"Found {len(module_elements)} module elements")
    else:
        log_bug(
            title="No modules visible for lecturer",
            role="Lecturer",
            steps=["Login as lecturer", "Navigate to materials"],
            expected="Assigned modules should be displayed",
            actual="No module elements found",
            severity="High"
        )
    
    # Test attendance (/attendance redirects lecturers to dashboard; use course entry)
    log_test("Testing attendance...")
    await page.goto(f"{BASE_URL}/attendance/course/1")
    await wait_for_page_load(page)
    
    if "attendance" not in page.url:
        log_bug(
            title="Lecturer attendance (course) not reachable",
            role="Lecturer",
            steps=["Login as lecturer", "Navigate to /attendance/course/1"],
            expected="Attendance UI loads (module view or redirect within attendance)",
            actual=f"At URL: {page.url}",
            severity="Medium"
        )
    
    # Test marks entry
    log_test("Testing marks entry...")
    await page.goto(f"{BASE_URL}/marks/course/1")
    await wait_for_page_load(page)
    
    if "marks" not in page.url:
        log_bug(
            title="Lecturer marks (course) not reachable",
            role="Lecturer",
            steps=["Login as lecturer", "Navigate to /marks/course/1"],
            expected="Marks UI loads (module view or redirect within marks)",
            actual=f"At URL: {page.url}",
            severity="Medium"
        )
    
    # Logout
    await logout(page)

async def test_career_advisor_flow(page):
    """Test career advisor user flow."""
    log_test("\n" + "="*70)
    log_test("TESTING CAREER ADVISOR FLOW")
    log_test("="*70)
    
    # Login as career advisor
    success, message = await login(page, TEST_USERS['career_advisor']['email'], TEST_USERS['career_advisor']['password'])
    if not success:
        log_bug(
            title="Career Advisor Login Failed",
            role="Career Advisor",
            steps=["Navigate to login page", "Enter career advisor credentials", "Submit form"],
            expected="Successful login and redirect to dashboard",
            actual=message,
            severity="Critical"
        )
        return
    log_test("Career Advisor login successful")
    
    # Check dashboard
    log_test("Checking career advisor dashboard...")
    await page.goto(f"{BASE_URL}/dashboard")
    await wait_for_page_load(page)
    
    # Check CV reviews
    log_test("Checking CV reviews...")
    await page.goto(f"{BASE_URL}/career/advisor/reviews")
    await wait_for_page_load(page)
    
    if "career" not in page.url or "review" not in page.url:
        log_bug(
            title="CV reviews page not accessible for career advisor",
            role="Career Advisor",
            steps=["Login as career advisor", "Navigate to /career/advisor/reviews"],
            expected="Advisor review queue loads",
            actual=f"At URL: {page.url}",
            severity="High"
        )
    else:
        # Check for CV elements
        cv_elements = await page.query_selector_all('a[href*="cv"], .cv-item, tr[data-cv], .review-item')
        if cv_elements:
            log_test(f"Found {len(cv_elements)} CV/review elements")
        else:
            log_test("No CV reviews visible (may be expected if none submitted)")
    
    # Logout
    await logout(page)

async def test_edge_cases(page):
    """Test edge cases and error handling."""
    log_test("\n" + "="*70)
    log_test("TESTING EDGE CASES")
    log_test("="*70)
    
    # Test invalid login
    log_test("Testing invalid login...")
    await page.goto(f"{BASE_URL}/auth/login")
    await wait_for_page_load(page)
    
    await page.fill('input[name="email"]', 'invalid@test.com')
    await page.fill('input[name="password"]', 'wrongpassword')
    await page.click('button[type="submit"]')
    await wait_for_page_load(page)
    
    # Should still be on login page with error (flashes use Tailwind, not .alert-danger)
    if "login" in page.url:
        invalid_msg = page.get_by_text("Invalid email or password", exact=False)
        try:
            await invalid_msg.first.wait_for(state="visible", timeout=5000)
            log_test("Invalid login shows error message (correct behavior)")
        except Exception:
            log_bug(
                title="No error message for invalid login",
                role="Any",
                steps=["Navigate to login page", "Enter invalid credentials", "Submit form"],
                expected="Flash error displayed (e.g. Invalid email or password)",
                actual="Message not visible within timeout",
                severity="Low"
            )
    else:
        log_bug(
            title="Invalid login redirects away from login page",
            role="Any",
            steps=["Navigate to login page", "Enter invalid credentials", "Submit form"],
            expected="Stay on login page with error",
            actual=f"Redirected to: {page.url}",
            severity="Medium"
        )
    
    # Test empty form submission
    log_test("Testing empty login form submission...")
    await page.goto(f"{BASE_URL}/auth/login")
    await wait_for_page_load(page)
    
    await page.click('button[type="submit"]')
    await wait_for_page_load(page)
    
    if 'login' in page.url:
        log_test("Empty form stays on login page (correct)")
    else:
        log_bug(
            title="Empty login form causes redirect",
            role="Any",
            steps=["Navigate to login page", "Submit empty form"],
            expected="Stay on login page with validation errors",
            actual=f"Redirected to: {page.url}",
            severity="Low"
        )
    
    # Test accessing protected routes without login
    log_test("Testing unauthorized access to protected routes...")
    protected_routes = [
        '/admin/courses',
        '/admin/users',
        '/materials',
        '/quizzes',
        '/assignments',
        '/attendance',
        '/marks',
        '/career/advisor/reviews',
    ]
    
    for route in protected_routes:
        response = await page.goto(f"{BASE_URL}{route}")
        await wait_for_page_load(page)
        
        status = response.status if response else 0
        current_url = page.url
        
        # Check if redirected to login (302/301 redirect)
        if 'login' in current_url:
            log_test(f"{route} - Redirects to login (correct)")
        # Check for 404 - route doesn't exist (not a security bug, just missing route)
        elif status == 404:
            log_test(f"{route} - Returns 404 (route doesn't exist - UX issue)")
            log_bug(
                title=f"Missing index route for {route}",
                role="Any",
                steps=[f"Navigate to {route}"],
                expected="Should have an index page or redirect to a default view",
                actual=f"Returns 404 Not Found",
                severity="Low"
            )
        # Check if page loaded with 200 but shouldn't have
        elif status == 200 and 'login' not in current_url:
            log_bug(
                title=f"Protected route {route} accessible without login",
                role="Unauthenticated",
                steps=[f"Navigate to {route} without being logged in"],
                expected="Redirect to login page",
                actual=f"Page loaded with status 200: {current_url}",
                severity="High"
            )
        else:
            log_test(f"{route} - Status: {status}, URL: {current_url}")
    
    # Test registration flow
    log_test("Testing registration page...")
    await page.goto(f"{BASE_URL}/auth/register")
    await wait_for_page_load(page)
    
    if 'register' in page.url:
        log_test("Registration page loads successfully")
        
        # Check required fields
        email_field = await page.query_selector('input[name="email"]')
        password_field = await page.query_selector('input[name="password"]')
        first_name_field = await page.query_selector('input[name="first_name"]')
        last_name_field = await page.query_selector('input[name="last_name"]')
        
        if not all([email_field, password_field, first_name_field, last_name_field]):
            log_bug(
                title="Missing required fields on registration form",
                role="Unauthenticated",
                steps=["Navigate to registration page"],
                expected="All required fields present (email, password, first_name, last_name)",
                actual="Some fields missing",
                severity="High"
            )
    else:
        log_bug(
            title="Registration page not accessible",
            role="Unauthenticated",
            steps=["Navigate to /auth/register"],
            expected="Registration form loads",
            actual=f"Redirected to: {page.url}",
            severity="Medium"
        )

async def run_tests():
    """Run all tests."""
    log_test("="*70)
    log_test("EduMind LMS - QA Testing Starting")
    log_test(f"Base URL: {BASE_URL}")
    log_test("="*70)
    
    async with async_playwright() as p:
        # Launch browser
        browser = await p.chromium.launch(
            headless=HEADLESS,
            slow_mo=SLOW_MO
        )
        
        context = await browser.new_context(
            viewport={'width': 1280, 'height': 720},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        
        page = await context.new_page()
        
        try:
            # Test home page first
            log_test("Testing home page...")
            await page.goto(BASE_URL)
            await wait_for_page_load(page)
            
            home_title = await page.title()
            log_test(f"Home page title: {home_title}")
            
            # Run all test flows
            await test_admin_flow(page)
            await test_student_flow(page)
            await test_lecturer_flow(page)
            await test_career_advisor_flow(page)
            await test_edge_cases(page)
            
        except Exception as e:
            log_test(f"Error during testing: {str(e)}")
        finally:
            await browser.close()
    
    # Print summary
    print("\n" + "="*70)
    print("QA TESTING COMPLETE")
    print("="*70)
    print(f"Total bugs found: {len(BUGS_FOUND)}")
    
    # Group by severity
    severity_counts = {'Critical': 0, 'High': 0, 'Medium': 0, 'Low': 0}
    for bug in BUGS_FOUND:
        severity_counts[bug['severity']] += 1
    
    print(f"\nSeverity Breakdown:")
    print(f"  Critical: {severity_counts['Critical']}")
    print(f"  High: {severity_counts['High']}")
    print(f"  Medium: {severity_counts['Medium']}")
    print(f"  Low: {severity_counts['Low']}")
    
    # Print all bugs
    if BUGS_FOUND:
        print("\n" + "="*70)
        print("BUG REPORTS")
        print("="*70)
        
        for i, bug in enumerate(BUGS_FOUND, 1):
            print(f"\n--- BUG #{i} ---")
            print(f"Title: {bug['title']}")
            print(f"Role: {bug['role']}")
            print(f"Severity: {bug['severity']}")
            print(f"Steps to Reproduce:")
            for step in bug['steps']:
                print(f"  - {step}")
            print(f"Expected: {bug['expected']}")
            print(f"Actual: {bug['actual']}")

if __name__ == '__main__':
    asyncio.run(run_tests())