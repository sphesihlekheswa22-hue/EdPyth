"""
Seed data script to populate all tables with test data.
Run with: python seed_data.py
"""
import os
import sys
import json
from datetime import datetime, timedelta
import random

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db, bcrypt
from app.models import (
    User, Student, Lecturer, Course, Module, Enrollment,
    CourseMaterial, Quiz, QuizQuestion, QuizResult,
    Attendance, Mark, StudyPlan, StudyPlanItem,
    ChatSession, ChatMessage, CVReview, RiskScore
)

def seed_users():
    """Create users for admin, lecturers, career advisor, and students."""
    print("Seeding Users...")
    
    users_data = [
        # Admin
        {'email': 'admin@edumind.com', 'first_name': 'System', 'last_name': 'Admin', 'role': 'admin', 'password': 'admin123'},
        
        # Career Advisor
        {'email': 'career@edumind.com', 'first_name': 'Sarah', 'last_name': 'Johnson', 'role': 'career_advisor', 'password': 'career123'},
        
        # Lecturers
        {'email': 'john.smith@edumind.com', 'first_name': 'John', 'last_name': 'Smith', 'role': 'lecturer', 'password': 'lecturer123'},
        {'email': 'emily.davis@edumind.com', 'first_name': 'Emily', 'last_name': 'Davis', 'role': 'lecturer', 'password': 'lecturer123'},
        {'email': 'michael.brown@edumind.com', 'first_name': 'Michael', 'last_name': 'Brown', 'role': 'lecturer', 'password': 'lecturer123'},
        {'email': 'jennifer.wilson@edumind.com', 'first_name': 'Jennifer', 'last_name': 'Wilson', 'role': 'lecturer', 'password': 'lecturer123'},
        {'email': 'david.lee@edumind.com', 'first_name': 'David', 'last_name': 'Lee', 'role': 'lecturer', 'password': 'lecturer123'},
        
        # Students
        {'email': 'alex.thompson@student.edumind.com', 'first_name': 'Alex', 'last_name': 'Thompson', 'role': 'student', 'password': 'student123'},
        {'email': 'sophia.martinez@student.edumind.com', 'first_name': 'Sophia', 'last_name': 'Martinez', 'role': 'student', 'password': 'student123'},
        {'email': 'lucas.anderson@student.edumind.com', 'first_name': 'Lucas', 'last_name': 'Anderson', 'role': 'student', 'password': 'student123'},
        {'email': 'olivia.taylor@student.edumind.com', 'first_name': 'Olivia', 'last_name': 'Taylor', 'role': 'student', 'password': 'student123'},
        {'email': 'noah.white@student.edumind.com', 'first_name': 'Noah', 'last_name': 'White', 'role': 'student', 'password': 'student123'},
        {'email': 'emma.harris@student.edumind.com', 'first_name': 'Emma', 'last_name': 'Harris', 'role': 'student', 'password': 'student123'},
        {'email': 'liam.clark@student.edumind.com', 'first_name': 'Liam', 'last_name': 'Clark', 'role': 'student', 'password': 'student123'},
        {'email': 'ava.lewis@student.edumind.com', 'first_name': 'Ava', 'last_name': 'Lewis', 'role': 'student', 'password': 'student123'},
        {'email': 'mason.walker@student.edumind.com', 'first_name': 'Mason', 'last_name': 'Walker', 'role': 'student', 'password': 'student123'},
        {'email': 'isabella.hall@student.edumind.com', 'first_name': 'Isabella', 'last_name': 'Hall', 'role': 'student', 'password': 'student123'},
        {'email': 'james.allen@student.edumind.com', 'first_name': 'James', 'last_name': 'Allen', 'role': 'student', 'password': 'student123'},
    ]
    
    users = []
    for data in users_data:
        password = data.pop('password')
        user = User(**data)
        user.set_password(password)
        db.session.add(user)
        users.append(user)
    
    db.session.commit()
    print(f"  Created {len(users)} users")
    return users

def seed_students(users):
    """Create student profiles."""
    print("Seeding Students...")
    
    student_users = [u for u in users if u.role == 'student']
    students = []
    
    programs = ['Computer Science', 'Engineering', 'Business Administration', 'Mathematics', 'Physics']
    years = [1, 2, 3, 4]
    
    for i, user in enumerate(student_users):
        student = Student(
            user_id=user.id,
            student_id=f'STU{1000 + i}',
            date_of_birth=datetime(2000 + random.randint(0, 4), random.randint(1, 12), random.randint(1, 28)).date(),
            phone=f'+1-555-{random.randint(100, 999)}-{random.randint(1000, 9999)}',
            address=f'{random.randint(100, 999)} University Ave, Campus {random.randint(1, 5)}',
            program=random.choice(programs),
            year_of_study=random.choice(years),
            enrollment_date=datetime(2023, random.randint(1, 9), 1).date()
        )
        db.session.add(student)
        students.append(student)
    
    db.session.commit()
    print(f"  Created {len(students)} students")
    return students

def seed_lecturers(users):
    """Create lecturer profiles."""
    print("Seeding Lecturers...")
    
    lecturer_users = [u for u in users if u.role == 'lecturer']
    lecturers = []
    
    departments = ['Computer Science', 'Engineering', 'Mathematics', 'Business', 'Physics']
    titles = ['Professor', 'Dr.', 'Lecturer', 'Senior Lecturer']
    specializations = ['Machine Learning', 'Data Structures', 'Calculus', 'Marketing', 'Quantum Physics']
    
    for i, user in enumerate(lecturer_users):
        lecturer = Lecturer(
            user_id=user.id,
            employee_id=f'EMP{1000 + i}',
            department=departments[i % len(departments)],
            title=titles[i % len(titles)],
            phone=f'+1-555-{random.randint(100, 999)}-{random.randint(1000, 9999)}',
            office=f'Building {random.randint(1, 5)}, Room {random.randint(100, 599)}',
            hire_date=datetime(2015 + random.randint(0, 8), random.randint(1, 12), 1).date(),
            specialization=specializations[i % len(specializations)]
        )
        db.session.add(lecturer)
        lecturers.append(lecturer)
    
    db.session.commit()
    print(f"  Created {len(lecturers)} lecturers")
    return lecturers

def seed_courses(lecturers):
    """Create courses."""
    print("Seeding Courses...")
    
    courses_data = [
        {'code': 'CS101', 'name': 'Introduction to Computer Science', 'credits': 3, 'description': 'Fundamental concepts of programming and computer science.'},
        {'code': 'CS201', 'name': 'Data Structures and Algorithms', 'credits': 4, 'description': 'Study of data structures and algorithm design.'},
        {'code': 'CS301', 'name': 'Machine Learning Fundamentals', 'credits': 3, 'description': 'Introduction to machine learning algorithms and applications.'},
        {'code': 'MATH101', 'name': 'Calculus I', 'credits': 4, 'description': 'Limits, derivatives, and integrals.'},
        {'code': 'MATH201', 'name': 'Linear Algebra', 'credits': 3, 'description': 'Vectors, matrices, and linear transformations.'},
        {'code': 'ENG101', 'name': 'Introduction to Engineering', 'credits': 3, 'description': 'Basic engineering principles and design.'},
        {'code': 'BUS101', 'name': 'Introduction to Business', 'credits': 3, 'description': 'Overview of business operations and management.'},
        {'code': 'PHYS101', 'name': 'Physics I', 'credits': 4, 'description': 'Mechanics, thermodynamics, and waves.'},
        {'code': 'CS401', 'name': 'Deep Learning', 'credits': 3, 'description': 'Advanced neural networks and deep learning.'},
        {'code': 'BUS201', 'name': 'Marketing Fundamentals', 'credits': 3, 'description': 'Marketing strategies and consumer behavior.'},
        {'code': 'MATH301', 'name': 'Discrete Mathematics', 'credits': 3, 'description': 'Logic, set theory, combinatorics.'},
        {'code': 'CS202', 'name': 'Database Systems', 'credits': 3, 'description': 'Relational databases and SQL.'},
    ]
    
    courses = []
    for i, data in enumerate(courses_data):
        course = Course(
            code=data['code'],
            name=data['name'],
            credits=data['credits'],
            description=data['description'],
            lecturer_id=lecturers[i % len(lecturers)].id,
            semester='Spring 2025',
            year=2025,
            is_active=True
        )
        db.session.add(course)
        courses.append(course)
    
    db.session.commit()
    print(f"  Created {len(courses)} courses")
    return courses

def seed_modules(courses):
    """Create course modules."""
    print("Seeding Modules...")
    
    modules = []
    module_titles = [
        'Introduction and Basics',
        'Core Concepts',
        'Advanced Topics',
        'Practical Applications',
        'Review and Assessment'
    ]
    
    for course in courses:
        for i, title in enumerate(module_titles):
            module = Module(
                course_id=course.id,
                title=f'{course.code} - {title}',
                description=f'Module {i+1} for {course.name}',
                order=i+1
            )
            db.session.add(module)
            modules.append(module)
    
    db.session.commit()
    print(f"  Created {len(modules)} modules")
    return modules

def seed_enrollments(students, courses):
    """Create enrollments."""
    print("Seeding Enrollments...")
    
    enrollments = []
    statuses = ['active', 'active', 'active', 'completed']
    
    # Enroll each student in 3-6 courses
    for student in students:
        num_courses = random.randint(3, 6)
        enrolled_courses = random.sample(courses, num_courses)
        
        for course in enrolled_courses:
            enrollment = Enrollment(
                student_id=student.id,
                course_id=course.id,
                status=random.choice(statuses),
                enrolled_at=datetime(2024, random.randint(1, 9), random.randint(1, 28))
            )
            db.session.add(enrollment)
            enrollments.append(enrollment)
    
    db.session.commit()
    print(f"  Created {len(enrollments)} enrollments")
    return enrollments

def seed_materials(courses, modules, users):
    """Create course materials."""
    print("Seeding Course Materials...")
    
    materials = []
    file_types = ['pdf', 'ppt', 'doc', 'txt']
    categories = ['lecture', 'assignment', 'reading', 'notes']
    
    material_count = 0
    for course in courses:
        # Add 2-3 materials per course
        for i in range(random.randint(2, 3)):
            material = CourseMaterial(
                course_id=course.id,
                module_id=modules[random.randint(0, len(modules)-1)].id if random.random() > 0.3 else None,
                title=f'{course.code} - {random.choice(categories).title()} {i+1}',
                description=f'Course material for {course.name}',
                file_path=f'/uploads/{course.code.lower()}_material_{i+1}.{random.choice(file_types)}',
                file_name=f'{course.code.lower()}_material_{i+1}.{random.choice(file_types)}',
                file_type=random.choice(file_types),
                file_size=random.randint(10000, 5000000),
                category=random.choice(categories),
                uploaded_by=users[0].id,  # Admin uploads
                is_published=True
            )
            db.session.add(material)
            materials.append(material)
            material_count += 1
    
    db.session.commit()
    print(f"  Created {len(materials)} course materials")
    return materials

def seed_quizzes(courses, users):
    """Create quizzes."""
    print("Seeding Quizzes...")
    
    quizzes = []
    quiz_titles = [
        'Midterm Exam',
        'Final Exam',
        'Weekly Quiz 1',
        'Weekly Quiz 2',
        'Practice Quiz'
    ]
    
    for course in courses:
        for i, title in enumerate(quiz_titles[:3]):  # 3 quizzes per course
            quiz = Quiz(
                course_id=course.id,
                title=f'{course.code} - {title}',
                description=f'{title} for {course.name}',
                created_by=users[0].id,
                time_limit=random.choice([15, 30, 45, 60]),
                passing_score=random.choice([50, 60, 70]),
                is_published=random.choice([True, False]),
                is_ai_generated=False,
                due_date=datetime(2025, random.randint(1, 6), random.randint(1, 28))
            )
            db.session.add(quiz)
            quizzes.append(quiz)
    
    db.session.commit()
    print(f"  Created {len(quizzes)} quizzes")
    return quizzes

def seed_quiz_questions(quizzes):
    """Create quiz questions."""
    print("Seeding Quiz Questions...")
    
    questions = []
    question_types = ['multiple_choice', 'true_false', 'short_answer']
    
    q_count = 0
    for quiz in quizzes:
        # Add 5-10 questions per quiz
        num_questions = random.randint(5, 10)
        
        for i in range(num_questions):
            q_type = random.choice(question_types)
            
            if q_type == 'multiple_choice':
                options = json.dumps(['Option A', 'Option B', 'Option C', 'Option D'])
                correct = random.choice(['Option A', 'Option B', 'Option C', 'Option D'])
            elif q_type == 'true_false':
                options = json.dumps(['True', 'False'])
                correct = random.choice(['True', 'False'])
            else:
                options = None
                correct = 'algorithm'
            
            question = QuizQuestion(
                quiz_id=quiz.id,
                question_text=f'Question {i+1}: What is the correct answer regarding {quiz.title}?',
                question_type=q_type,
                points=random.randint(1, 5),
                order=i+1,
                options=options,
                correct_answer=correct
            )
            db.session.add(question)
            questions.append(question)
            q_count += 1
    
    db.session.commit()
    print(f"  Created {len(questions)} quiz questions")
    return questions

def seed_quiz_results(quizzes, students):
    """Create quiz results."""
    print("Seeding Quiz Results...")
    
    results = []
    
    for quiz in quizzes:
        # Add results for 3-6 random students
        num_results = random.randint(3, min(6, len(students)))
        attempted_students = random.sample(students, num_results)
        
        for student in attempted_students:
            score = random.randint(30, 100)
            total = random.randint(50, 100)
            percentage = (score / total) * 100
            
            result = QuizResult(
                quiz_id=quiz.id,
                student_id=student.id,
                score=score,
                total_points=total,
                percentage=percentage,
                passed=percentage >= quiz.passing_score,
                time_taken=random.randint(300, 3600),
                started_at=datetime.now() - timedelta(days=random.randint(1, 30)),
                completed_at=datetime.now() - timedelta(days=random.randint(0, 29))
            )
            db.session.add(result)
            results.append(result)
    
    db.session.commit()
    print(f"  Created {len(results)} quiz results")
    return results

def seed_attendance(courses, students, users):
    """Create attendance records."""
    print("Seeding Attendance...")
    
    attendance_records = []
    statuses = ['present', 'present', 'present', 'absent', 'late']
    
    # Create attendance for past 10 days
    for days_ago in range(10):
        date = datetime.now().date() - timedelta(days=days_ago)
        
        for course in courses[:5]:  # First 5 courses
            # Random 5-8 students per course per day
            num_students = random.randint(5, min(8, len(students)))
            attending_students = random.sample(students, num_students)
            
            for student in attending_students:
                attendance = Attendance(
                    course_id=course.id,
                    student_id=student.id,
                    date=date,
                    status=random.choice(statuses),
                    recorded_by=users[0].id,
                    notes=None
                )
                db.session.add(attendance)
                attendance_records.append(attendance)
    
    db.session.commit()
    print(f"  Created {len(attendance_records)} attendance records")
    return attendance_records

def seed_marks(courses, students, users):
    """Create marks/grades."""
    print("Seeding Marks...")
    
    marks = []
    assessment_types = ['assignment', 'midterm', 'final', 'quiz', 'project']
    
    for course in courses:
        # 5-8 marks per course
        num_marks = random.randint(5, 8)
        
        for i in range(num_marks):
            student = random.choice(students)
            assessment_type = random.choice(assessment_types)
            total = random.choice([100, 50, 20, 10])
            mark_score = random.randint(int(total * 0.4), total)
            percentage = (mark_score / total) * 100
            
            mark = Mark(
                course_id=course.id,
                student_id=student.id,
                assessment_type=assessment_type,
                assessment_name=f'{assessment_type.title()} {i+1}',
                mark=mark_score,
                total_marks=total,
                percentage=percentage,
                grade=calculate_grade(percentage),
                recorded_by=users[0].id,
                feedback='Good work!' if percentage >= 60 else 'Needs improvement.',
                marked_at=datetime.now() - timedelta(days=random.randint(1, 60))
            )
            db.session.add(mark)
            marks.append(mark)
    
    db.session.commit()
    print(f"  Created {len(marks)} marks")
    return marks

def calculate_grade(percentage):
    """Calculate letter grade."""
    if percentage >= 90:
        return 'A+'
    elif percentage >= 85:
        return 'A'
    elif percentage >= 80:
        return 'A-'
    elif percentage >= 75:
        return 'B+'
    elif percentage >= 70:
        return 'B'
    elif percentage >= 65:
        return 'B-'
    elif percentage >= 60:
        return 'C+'
    elif percentage >= 55:
        return 'C'
    elif percentage >= 50:
        return 'C-'
    elif percentage >= 45:
        return 'D'
    else:
        return 'F'

def seed_study_plans(students, courses):
    """Create study plans."""
    print("Seeding Study Plans...")
    
    study_plans = []
    
    for student in students:
        # 1-3 study plans per student
        num_plans = random.randint(1, 3)
        
        for i in range(num_plans):
            plan = StudyPlan(
                student_id=student.id,
                course_id=random.choice(courses).id if random.random() > 0.3 else None,
                title=f'{student.user.first_name}\'s Study Plan {i+1}',
                description='Personalized AI-generated study plan',
                is_ai_generated=random.choice([True, False]),
                start_date=datetime.now().date(),
                end_date=datetime.now().date() + timedelta(weeks=random.randint(2, 8)),
                status=random.choice(['active', 'active', 'completed'])
            )
            db.session.add(plan)
            study_plans.append(plan)
    
    db.session.commit()
    print(f"  Created {len(study_plans)} study plans")
    return study_plans

def seed_study_plan_items(study_plans):
    """Create study plan items."""
    print("Seeding Study Plan Items...")
    
    items = []
    task_types = ['reading', 'practice', 'review', 'assignment', 'project']
    item_statuses = ['pending', 'in_progress', 'completed']
    priorities = ['low', 'medium', 'high']
    
    for plan in study_plans:
        # 5-10 items per plan
        num_items = random.randint(5, 10)
        
        for i in range(num_items):
            item = StudyPlanItem(
                study_plan_id=plan.id,
                title=f'Task {i+1}: {random.choice(task_types).title()} session',
                description=f'Complete {random.choice(task_types)} for the course',
                task_type=random.choice(task_types),
                order=i+1,
                status=random.choice(item_statuses),
                priority=random.choice(priorities),
                due_date=datetime.now().date() + timedelta(days=random.randint(1, 30)),
                estimated_time=random.randint(30, 180)
            )
            db.session.add(item)
            items.append(item)
    
    db.session.commit()
    print(f"  Created {len(items)} study plan items")
    return items

def seed_chat_sessions(students, courses):
    """Create chat sessions."""
    print("Seeding Chat Sessions...")
    
    sessions = []
    topics = ['Homework Help', 'Exam Preparation', 'Concept Review', 'Practice Problems', 'General Questions']
    
    for student in students:
        # 1-3 chat sessions per student
        num_sessions = random.randint(1, 3)
        
        for i in range(num_sessions):
            session = ChatSession(
                student_id=student.id,
                title=f'Chat: {random.choice(topics)}',
                course_id=random.choice(courses).id if random.random() > 0.4 else None,
                topic=random.choice(topics),
                is_active=random.choice([True, False]),
                created_at=datetime.now() - timedelta(days=random.randint(1, 30))
            )
            db.session.add(session)
            sessions.append(session)
    
    db.session.commit()
    print(f"  Created {len(sessions)} chat sessions")
    return sessions

def seed_chat_messages(sessions):
    """Create chat messages."""
    print("Seeding Chat Messages...")
    
    messages = []
    
    for session in sessions:
        # 2-8 messages per session
        num_messages = random.randint(2, 8)
        
        for i in range(num_messages):
            message = ChatMessage(
                session_id=session.id,
                role='user' if i % 2 == 0 else 'assistant',
                content=f'This is message {i+1} in the chat session. ' + ('How can I help you?' if i % 2 == 1 else 'I need help with this topic.'),
                is_ai=(i % 2 == 1),
                created_at=session.created_at + timedelta(minutes=i*5)
            )
            db.session.add(message)
            messages.append(message)
    
    db.session.commit()
    print(f"  Created {len(messages)} chat messages")
    return messages

def seed_cv_reviews(students):
    """Create CV reviews."""
    print("Seeding CV Reviews...")
    
    reviews = []
    statuses = ['pending', 'reviewed', 'needs_revision']
    
    for student in students[:10]:  # First 10 students
        review = CVReview(
            student_id=student.id,
            file_path=f'/uploads/cv_{student.student_id}.pdf',
            file_name=f'cv_{student.student_id}.pdf',
            job_readiness_score=random.randint(40, 95) if random.random() > 0.3 else None,
            status=random.choice(statuses),
            strengths='Strong technical skills, good communication, proactive learning',
            weaknesses='Could improve presentation skills, needs more industry experience',
            recommendations='Continue building projects, consider internships',
            suggested_skills=json.dumps(['Python', 'Machine Learning', 'Data Analysis']),
            suggested_projects=json.dumps(['Web App', 'Mobile App', 'Data Visualization']),
            interview_tips='Practice coding problems, research company culture, prepare STAR stories',
            reviewed_by=None,
            reviewed_at=datetime.now() - timedelta(days=random.randint(1, 30)) if random.random() > 0.3 else None,
            created_at=datetime.now() - timedelta(days=random.randint(30, 90))
        )
        db.session.add(review)
        reviews.append(review)
    
    db.session.commit()
    print(f"  Created {len(reviews)} CV reviews")
    return reviews

def seed_risk_scores(students, courses):
    """Create risk scores."""
    print("Seeding Risk Scores...")
    
    risk_scores = []
    risk_levels = ['low', 'medium', 'high', 'critical']
    
    for student in students:
        # 1-2 risk scores per student (overall + per course)
        num_scores = random.randint(1, 2)
        
        for i in range(num_scores):
            risk_score_value = random.randint(20, 95)
            
            if risk_score_value >= 80:
                risk_level = 'low'
            elif risk_score_value >= 60:
                risk_level = 'medium'
            elif risk_score_value >= 40:
                risk_level = 'high'
            else:
                risk_level = 'critical'
            
            risk = RiskScore(
                student_id=student.id,
                course_id=random.choice(courses).id if i == 1 else None,
                risk_level=risk_level,
                risk_score=risk_score_value,
                attendance_score=random.randint(50, 100),
                quiz_score=random.randint(40, 100),
                assignment_score=random.randint(45, 100),
                overall_score=random.randint(50, 95),
                risk_factors=json.dumps(['Low attendance', 'Missed assignments', 'Low quiz scores'][:random.randint(1, 3)]),
                recommendations='Increase attendance, submit assignments on time, seek tutoring',
                calculated_at=datetime.now() - timedelta(days=random.randint(1, 14))
            )
            db.session.add(risk)
            risk_scores.append(risk)
    
    db.session.commit()
    print(f"  Created {len(risk_scores)} risk scores")
    return risk_scores

def main():
    """Main function to seed all data."""
    print("=" * 50)
    print("Starting database seeding...")
    print("=" * 50)
    
    # Create app context
    app = create_app('development')
    
    with app.app_context():
        # Use existing database - don't drop tables
        print("\nUsing existing database structure...")
        db.create_all()
        print("Database tables verified.")
        
        # Seed all tables
        users = seed_users()
        students = seed_students(users)
        lecturers = seed_lecturers(users)
        courses = seed_courses(lecturers)
        modules = seed_modules(courses)
        enrollments = seed_enrollments(students, courses)
        materials = seed_materials(courses, modules, users)
        quizzes = seed_quizzes(courses, users)
        quiz_questions = seed_quiz_questions(quizzes)
        quiz_results = seed_quiz_results(quizzes, students)
        attendance_records = seed_attendance(courses, students, users)
        marks = seed_marks(courses, students, users)
        study_plans = seed_study_plans(students, courses)
        study_plan_items = seed_study_plan_items(study_plans)
        chat_sessions = seed_chat_sessions(students, courses)
        chat_messages = seed_chat_messages(chat_sessions)
        cv_reviews = seed_cv_reviews(students)
        risk_scores = seed_risk_scores(students, courses)
        
        print("\n" + "=" * 50)
        print("Database seeding completed successfully!")
        print("=" * 50)
        
        print("\nSummary:")
        print(f"  Users: {len(users)}")
        print(f"  Students: {len(students)}")
        print(f"  Lecturers: {len(lecturers)}")
        print(f"  Courses: {len(courses)}")
        print(f"  Modules: {len(modules)}")
        print(f"  Enrollments: {len(enrollments)}")
        print(f"  Course Materials: {len(materials)}")
        print(f"  Quizzes: {len(quizzes)}")
        print(f"  Quiz Questions: {len(quiz_questions)}")
        print(f"  Quiz Results: {len(quiz_results)}")
        print(f"  Attendance Records: {len(attendance_records)}")
        print(f"  Marks: {len(marks)}")
        print(f"  Study Plans: {len(study_plans)}")
        print(f"  Study Plan Items: {len(study_plan_items)}")
        print(f"  Chat Sessions: {len(chat_sessions)}")
        print(f"  Chat Messages: {len(chat_messages)}")
        print(f"  CV Reviews: {len(cv_reviews)}")
        print(f"  Risk Scores: {len(risk_scores)}")

if __name__ == '__main__':
    main()
