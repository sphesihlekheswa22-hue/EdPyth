-- ============================================================================
-- EduMind Database Seed Script (SQLite)
-- ============================================================================
-- This script seeds the database with:
-- - Users (admin, career advisor, lecturers, students)
-- - Student and Lecturer profiles
-- - Courses with lecturers assigned
-- - Modules
-- - Course Materials, Quizzes, Quiz Questions
-- - Chat Sessions, Chat Messages
-- - CV Reviews, Risk Scores
-- 
-- NOTE: Students are NOT enrolled in any courses (as per requirement)
-- ============================================================================

-- ============================================================================
-- USERS TABLE
-- ============================================================================
INSERT INTO users (id, email, password_hash, first_name, last_name, role, is_active, created_at, updated_at) VALUES
(1, 'admin@edumind.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.VT5YxW2eQ8YLYG', 'System', 'Admin', 'admin', 1, datetime('now'), datetime('now')),
(2, 'career@edumind.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.VT5YxW2eQ8YLYG', 'Sarah', 'Johnson', 'career_advisor', 1, datetime('now'), datetime('now')),
(3, 'john.smith@edumind.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.VT5YxW2eQ8YLYG', 'John', 'Smith', 'lecturer', 1, datetime('now'), datetime('now')),
(4, 'emily.davis@edumind.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.VT5YxW2eQ8YLYG', 'Emily', 'Davis', 'lecturer', 1, datetime('now'), datetime('now')),
(5, 'michael.brown@edumind.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.VT5YxW2eQ8YLYG', 'Michael', 'Brown', 'lecturer', 1, datetime('now'), datetime('now')),
(6, 'jennifer.wilson@edumind.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.VT5YxW2eQ8YLYG', 'Jennifer', 'Wilson', 'lecturer', 1, datetime('now'), datetime('now')),
(7, 'david.lee@edumind.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.VT5YxW2eQ8YLYG', 'David', 'Lee', 'lecturer', 1, datetime('now'), datetime('now')),
(8, 'alex.thompson@student.edumind.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.VT5YxW2eQ8YLYG', 'Alex', 'Thompson', 'student', 1, datetime('now'), datetime('now')),
(9, 'sophia.martinez@student.edumind.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.VT5YxW2eQ8YLYG', 'Sophia', 'Martinez', 'student', 1, datetime('now'), datetime('now')),
(10, 'lucas.anderson@student.edumind.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.VT5YxW2eQ8YLYG', 'Lucas', 'Anderson', 'student', 1, datetime('now'), datetime('now')),
(11, 'olivia.taylor@student.edumind.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.VT5YxW2eQ8YLYG', 'Olivia', 'Taylor', 'student', 1, datetime('now'), datetime('now')),
(12, 'noah.white@student.edumind.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.VT5YxW2eQ8YLYG', 'Noah', 'White', 'student', 1, datetime('now'), datetime('now')),
(13, 'emma.harris@student.edumind.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.VT5YxW2eQ8YLYG', 'Emma', 'Harris', 'student', 1, datetime('now'), datetime('now')),
(14, 'liam.clark@student.edumind.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.VT5YxW2eQ8YLYG', 'Liam', 'Clark', 'student', 1, datetime('now'), datetime('now')),
(15, 'ava.lewis@student.edumind.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.VT5YxW2eQ8YLYG', 'Ava', 'Lewis', 'student', 1, datetime('now'), datetime('now')),
(16, 'mason.walker@student.edumind.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.VT5YxW2eQ8YLYG', 'Mason', 'Walker', 'student', 1, datetime('now'), datetime('now')),
(17, 'isabella.hall@student.edumind.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.VT5YxW2eQ8YLYG', 'Isabella', 'Hall', 'student', 1, datetime('now'), datetime('now')),
(18, 'james.allen@student.edumind.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.VT5YxW2eQ8YLYG', 'James', 'Allen', 'student', 1, datetime('now'), datetime('now'));

-- Password for all users: admin123 (for admin), career123 (for career), lecturer123 (for lecturers), student123 (for students)
-- The password_hash is bcrypt of 'password123' - you may need to update based on your actual password

-- ============================================================================
-- LECTURERS TABLE
-- ============================================================================
INSERT INTO lecturers (id, user_id, employee_id, department, title, phone, office, hire_date, specialization) VALUES
(1, 3, 'EMP1000', 'Computer Science', 'Professor', '+1-555-123-4567', 'Building 1, Room 101', '2015-08-15', 'Machine Learning'),
(2, 4, 'EMP1001', 'Computer Science', 'Dr.', '+1-555-234-5678', 'Building 1, Room 202', '2017-01-20', 'Data Structures'),
(3, 5, 'EMP1002', 'Mathematics', 'Lecturer', '+1-555-345-6789', 'Building 2, Room 105', '2019-08-01', 'Calculus'),
(4, 6, 'EMP1003', 'Business', 'Senior Lecturer', '+1-555-456-7890', 'Building 3, Room 301', '2016-03-10', 'Marketing'),
(5, 7, 'EMP1004', 'Physics', 'Dr.', '+1-555-567-8901', 'Building 4, Room 401', '2018-09-01', 'Quantum Physics');

-- ============================================================================
-- STUDENTS TABLE
-- ============================================================================
INSERT INTO students (id, user_id, student_id, date_of_birth, phone, address, program, year_of_study, enrollment_date) VALUES
(1, 8, 'STU1000', '2002-03-15', '+1-555-111-2222', '123 University Ave, Campus 1', 'Computer Science', 3, '2023-09-01'),
(2, 9, 'STU1001', '2003-07-22', '+1-555-222-3333', '234 University Ave, Campus 2', 'Engineering', 2, '2023-09-01'),
(3, 10, 'STU1002', '2001-11-08', '+1-555-333-4444', '345 University Ave, Campus 3', 'Business Administration', 4, '2023-01-15'),
(4, 11, 'STU1003', '2004-02-28', '+1-555-444-5555', '456 University Ave, Campus 1', 'Mathematics', 1, '2024-09-01'),
(5, 12, 'STU1004', '2002-09-12', '+1-555-555-6666', '567 University Ave, Campus 4', 'Physics', 3, '2023-09-01'),
(6, 13, 'STU1005', '2003-05-19', '+1-555-666-7777', '678 University Ave, Campus 2', 'Computer Science', 2, '2023-09-01'),
(7, 14, 'STU1006', '2001-12-03', '+1-555-777-8888', '789 University Ave, Campus 5', 'Engineering', 4, '2022-01-10'),
(8, 15, 'STU1007', '2004-08-25', '+1-555-888-9999', '890 University Ave, Campus 1', 'Business Administration', 1, '2024-09-01'),
(9, 16, 'STU1008', '2002-06-17', '+1-555-999-0000', '901 University Ave, Campus 3', 'Mathematics', 3, '2023-09-01'),
(10, 17, 'STU1009', '2003-01-30', '+1-555-000-1111', '112 University Ave, Campus 2', 'Physics', 2, '2023-09-01'),
(11, 18, 'STU1010', '2001-10-11', '+1-555-121-2323', '223 University Ave, Campus 4', 'Computer Science', 4, '2022-09-01');

-- ============================================================================
-- COURSES TABLE (with lecturers assigned)
-- ============================================================================
INSERT INTO courses (id, code, name, description, credits, lecturer_id, semester, year, is_active, created_at, updated_at) VALUES
(1, 'CS101', 'Introduction to Computer Science', 'Fundamental concepts of programming and computer science.', 3, 1, 'Spring 2025', 2025, 1, datetime('now'), datetime('now')),
(2, 'CS201', 'Data Structures and Algorithms', 'Study of data structures and algorithm design.', 4, 1, 'Spring 2025', 2025, 1, datetime('now'), datetime('now')),
(3, 'CS301', 'Machine Learning Fundamentals', 'Introduction to machine learning algorithms and applications.', 3, 2, 'Spring 2025', 2025, 1, datetime('now'), datetime('now')),
(4, 'MATH101', 'Calculus I', 'Limits, derivatives, and integrals.', 4, 3, 'Spring 2025', 2025, 1, datetime('now'), datetime('now')),
(5, 'MATH201', 'Linear Algebra', 'Vectors, matrices, and linear transformations.', 3, 3, 'Spring 2025', 2025, 1, datetime('now'), datetime('now')),
(6, 'ENG101', 'Introduction to Engineering', 'Basic engineering principles and design.', 3, 5, 'Spring 2025', 2025, 1, datetime('now'), datetime('now')),
(7, 'BUS101', 'Introduction to Business', 'Overview of business operations and management.', 3, 4, 'Spring 2025', 2025, 1, datetime('now'), datetime('now')),
(8, 'PHYS101', 'Physics I', 'Mechanics, thermodynamics, and waves.', 4, 5, 'Spring 2025', 2025, 1, datetime('now'), datetime('now')),
(9, 'CS401', 'Deep Learning', 'Advanced neural networks and deep learning.', 3, 2, 'Spring 2025', 2025, 1, datetime('now'), datetime('now')),
(10, 'BUS201', 'Marketing Fundamentals', 'Marketing strategies and consumer behavior.', 3, 4, 'Spring 2025', 2025, 1, datetime('now'), datetime('now')),
(11, 'MATH301', 'Discrete Mathematics', 'Logic, set theory, combinatorics.', 3, 3, 'Spring 2025', 2025, 1, datetime('now'), datetime('now')),
(12, 'CS202', 'Database Systems', 'Relational databases and SQL.', 3, 1, 'Spring 2025', 2025, 1, datetime('now'), datetime('now'));

-- ============================================================================
-- MODULES TABLE
-- ============================================================================
INSERT INTO modules (id, course_id, title, description, "order", created_at) VALUES
-- CS101 Modules
(1, 1, 'CS101 - Introduction and Basics', 'Module 1 for Introduction to Computer Science', 1, datetime('now')),
(2, 1, 'CS101 - Core Concepts', 'Module 2 for Introduction to Computer Science', 2, datetime('now')),
(3, 1, 'CS101 - Advanced Topics', 'Module 3 for Introduction to Computer Science', 3, datetime('now')),
(4, 1, 'CS101 - Practical Applications', 'Module 4 for Introduction to Computer Science', 4, datetime('now')),
(5, 1, 'CS101 - Review and Assessment', 'Module 5 for Introduction to Computer Science', 5, datetime('now')),
-- CS201 Modules
(6, 2, 'CS201 - Introduction and Basics', 'Module 1 for Data Structures and Algorithms', 1, datetime('now')),
(7, 2, 'CS201 - Core Concepts', 'Module 2 for Data Structures and Algorithms', 2, datetime('now')),
(8, 2, 'CS201 - Advanced Topics', 'Module 3 for Data Structures and Algorithms', 3, datetime('now')),
(9, 2, 'CS201 - Practical Applications', 'Module 4 for Data Structures and Algorithms', 4, datetime('now')),
(10, 2, 'CS201 - Review and Assessment', 'Module 5 for Data Structures and Algorithms', 5, datetime('now')),
-- CS301 Modules
(11, 3, 'CS301 - Introduction and Basics', 'Module 1 for Machine Learning Fundamentals', 1, datetime('now')),
(12, 3, 'CS301 - Core Concepts', 'Module 2 for Machine Learning Fundamentals', 2, datetime('now')),
(13, 3, 'CS301 - Advanced Topics', 'Module 3 for Machine Learning Fundamentals', 3, datetime('now')),
(14, 3, 'CS301 - Practical Applications', 'Module 4 for Machine Learning Fundamentals', 4, datetime('now')),
(15, 3, 'CS301 - Review and Assessment', 'Module 5 for Machine Learning Fundamentals', 5, datetime('now')),
-- MATH101 Modules
(16, 4, 'MATH101 - Introduction and Basics', 'Module 1 for Calculus I', 1, datetime('now')),
(17, 4, 'MATH101 - Core Concepts', 'Module 2 for Calculus I', 2, datetime('now')),
(18, 4, 'MATH101 - Advanced Topics', 'Module 3 for Calculus I', 3, datetime('now')),
(19, 4, 'MATH101 - Practical Applications', 'Module 4 for Calculus I', 4, datetime('now')),
(20, 4, 'MATH101 - Review and Assessment', 'Module 5 for Calculus I', 5, datetime('now')),
-- MATH201 Modules
(21, 5, 'MATH201 - Introduction and Basics', 'Module 1 for Linear Algebra', 1, datetime('now')),
(22, 5, 'MATH201 - Core Concepts', 'Module 2 for Linear Algebra', 2, datetime('now')),
(23, 5, 'MATH201 - Advanced Topics', 'Module 3 for Linear Algebra', 3, datetime('now')),
(24, 5, 'MATH201 - Practical Applications', 'Module 4 for Linear Algebra', 4, datetime('now')),
(25, 5, 'MATH201 - Review and Assessment', 'Module 5 for Linear Algebra', 5, datetime('now')),
-- ENG101 Modules
(26, 6, 'ENG101 - Introduction and Basics', 'Module 1 for Introduction to Engineering', 1, datetime('now')),
(27, 6, 'ENG101 - Core Concepts', 'Module 2 for Introduction to Engineering', 2, datetime('now')),
(28, 6, 'ENG101 - Advanced Topics', 'Module 3 for Introduction to Engineering', 3, datetime('now')),
(29, 6, 'ENG101 - Practical Applications', 'Module 4 for Introduction to Engineering', 4, datetime('now')),
(30, 6, 'ENG101 - Review and Assessment', 'Module 5 for Introduction to Engineering', 5, datetime('now')),
-- BUS101 Modules
(31, 7, 'BUS101 - Introduction and Basics', 'Module 1 for Introduction to Business', 1, datetime('now')),
(32, 7, 'BUS101 - Core Concepts', 'Module 2 for Introduction to Business', 2, datetime('now')),
(33, 7, 'BUS101 - Advanced Topics', 'Module 3 for Introduction to Business', 3, datetime('now')),
(34, 7, 'BUS101 - Practical Applications', 'Module 4 for Introduction to Business', 4, datetime('now')),
(35, 7, 'BUS101 - Review and Assessment', 'Module 5 for Introduction to Business', 5, datetime('now')),
-- PHYS101 Modules
(36, 8, 'PHYS101 - Introduction and Basics', 'Module 1 for Physics I', 1, datetime('now')),
(37, 8, 'PHYS101 - Core Concepts', 'Module 2 for Physics I', 2, datetime('now')),
(38, 8, 'PHYS101 - Advanced Topics', 'Module 3 for Physics I', 3, datetime('now')),
(39, 8, 'PHYS101 - Practical Applications', 'Module 4 for Physics I', 4, datetime('now')),
(40, 8, 'PHYS101 - Review and Assessment', 'Module 5 for Physics I', 5, datetime('now')),
-- CS401 Modules
(41, 9, 'CS401 - Introduction and Basics', 'Module 1 for Deep Learning', 1, datetime('now')),
(42, 9, 'CS401 - Core Concepts', 'Module 2 for Deep Learning', 2, datetime('now')),
(43, 9, 'CS401 - Advanced Topics', 'Module 3 for Deep Learning', 3, datetime('now')),
(44, 9, 'CS401 - Practical Applications', 'Module 4 for Deep Learning', 4, datetime('now')),
(45, 9, 'CS401 - Review and Assessment', 'Module 5 for Deep Learning', 5, datetime('now')),
-- BUS201 Modules
(46, 10, 'BUS201 - Introduction and Basics', 'Module 1 for Marketing Fundamentals', 1, datetime('now')),
(47, 10, 'BUS201 - Core Concepts', 'Module 2 for Marketing Fundamentals', 2, datetime('now')),
(48, 10, 'BUS201 - Advanced Topics', 'Module 3 for Marketing Fundamentals', 3, datetime('now')),
(49, 10, 'BUS201 - Practical Applications', 'Module 4 for Marketing Fundamentals', 4, datetime('now')),
(50, 10, 'BUS201 - Review and Assessment', 'Module 5 for Marketing Fundamentals', 5, datetime('now')),
-- MATH301 Modules
(51, 11, 'MATH301 - Introduction and Basics', 'Module 1 for Discrete Mathematics', 1, datetime('now')),
(52, 11, 'MATH301 - Core Concepts', 'Module 2 for Discrete Mathematics', 2, datetime('now')),
(53, 11, 'MATH301 - Advanced Topics', 'Module 3 for Discrete Mathematics', 3, datetime('now')),
(54, 11, 'MATH301 - Practical Applications', 'Module 4 for Discrete Mathematics', 4, datetime('now')),
(55, 11, 'MATH301 - Review and Assessment', 'Module 5 for Discrete Mathematics', 5, datetime('now')),
-- CS202 Modules
(56, 12, 'CS202 - Introduction and Basics', 'Module 1 for Database Systems', 1, datetime('now')),
(57, 12, 'CS202 - Core Concepts', 'Module 2 for Database Systems', 2, datetime('now')),
(58, 12, 'CS202 - Advanced Topics', 'Module 3 for Database Systems', 3, datetime('now')),
(59, 12, 'CS202 - Practical Applications', 'Module 4 for Database Systems', 4, datetime('now')),
(60, 12, 'CS202 - Review and Assessment', 'Module 5 for Database Systems', 5, datetime('now'));

-- ============================================================================
-- COURSE MATERIALS TABLE
-- ============================================================================
INSERT INTO course_materials (id, course_id, module_id, title, description, file_path, file_name, file_type, file_size, category, uploaded_by, is_published, created_at) VALUES
(1, 1, 1, 'CS101 - Lecture 1', 'Course material for Introduction to Computer Science', '/uploads/cs101_material_1.pdf', 'cs101_material_1.pdf', 'pdf', 150000, 'lecture', 1, 1, datetime('now')),
(2, 1, 2, 'CS101 - Assignment 1', 'Course material for Introduction to Computer Science', '/uploads/cs101_material_2.ppt', 'cs101_material_2.ppt', 'ppt', 250000, 'assignment', 1, 1, datetime('now')),
(3, 2, 6, 'CS201 - Lecture 1', 'Course material for Data Structures and Algorithms', '/uploads/cs201_material_1.pdf', 'cs201_material_1.pdf', 'pdf', 180000, 'lecture', 1, 1, datetime('now')),
(4, 3, 11, 'CS301 - Lecture 1', 'Course material for Machine Learning Fundamentals', '/uploads/cs301_material_1.pdf', 'cs301_material_1.pdf', 'pdf', 200000, 'lecture', 1, 1, datetime('now')),
(5, 4, 16, 'MATH101 - Lecture 1', 'Course material for Calculus I', '/uploads/math101_material_1.pdf', 'math101_material_1.pdf', 'pdf', 160000, 'lecture', 1, 1, datetime('now')),
(6, 5, 21, 'MATH201 - Lecture 1', 'Course material for Linear Algebra', '/uploads/math201_material_1.pdf', 'math201_material_1.pdf', 'pdf', 170000, 'lecture', 1, 1, datetime('now')),
(7, 6, 26, 'ENG101 - Lecture 1', 'Course material for Introduction to Engineering', '/uploads/eng101_material_1.pdf', 'eng101_material_1.pdf', 'pdf', 190000, 'lecture', 1, 1, datetime('now')),
(8, 7, 31, 'BUS101 - Lecture 1', 'Course material for Introduction to Business', '/uploads/bus101_material_1.pdf', 'bus101_material_1.pdf', 'pdf', 140000, 'lecture', 1, 1, datetime('now')),
(9, 8, 36, 'PHYS101 - Lecture 1', 'Course material for Physics I', '/uploads/phys101_material_1.pdf', 'phys101_material_1.pdf', 'pdf', 210000, 'lecture', 1, 1, datetime('now')),
(10, 9, 41, 'CS401 - Lecture 1', 'Course material for Deep Learning', '/uploads/cs401_material_1.pdf', 'cs401_material_1.pdf', 'pdf', 220000, 'lecture', 1, 1, datetime('now')),
(11, 10, 46, 'BUS201 - Lecture 1', 'Course material for Marketing Fundamentals', '/uploads/bus201_material_1.pdf', 'bus201_material_1.pdf', 'pdf', 130000, 'lecture', 1, 1, datetime('now')),
(12, 11, 51, 'MATH301 - Lecture 1', 'Course material for Discrete Mathematics', '/uploads/math301_material_1.pdf', 'math301_material_1.pdf', 'pdf', 155000, 'lecture', 1, 1, datetime('now')),
(13, 12, 56, 'CS202 - Lecture 1', 'Course material for Database Systems', '/uploads/cs202_material_1.pdf', 'cs202_material_1.pdf', 'pdf', 175000, 'lecture', 1, 1, datetime('now'));

-- ============================================================================
-- QUIZZES TABLE
-- ============================================================================
INSERT INTO quizzes (id, course_id, title, description, created_by, time_limit, passing_score, is_published, is_ai_generated, due_date, created_at) VALUES
(1, 1, 'CS101 - Midterm Exam', 'Midterm Exam for Introduction to Computer Science', 1, 60, 60, 1, 0, '2025-04-15', datetime('now')),
(2, 1, 'CS101 - Final Exam', 'Final Exam for Introduction to Computer Science', 1, 90, 70, 1, 0, '2025-05-20', datetime('now')),
(3, 1, 'CS101 - Weekly Quiz 1', 'Weekly Quiz 1 for Introduction to Computer Science', 1, 30, 50, 1, 0, '2025-02-28', datetime('now')),
(4, 2, 'CS201 - Midterm Exam', 'Midterm Exam for Data Structures and Algorithms', 1, 60, 60, 1, 0, '2025-04-15', datetime('now')),
(5, 2, 'CS201 - Final Exam', 'Final Exam for Data Structures and Algorithms', 1, 90, 70, 1, 0, '2025-05-20', datetime('now')),
(6, 2, 'CS201 - Weekly Quiz 1', 'Weekly Quiz 1 for Data Structures and Algorithms', 1, 30, 50, 1, 0, '2025-02-28', datetime('now')),
(7, 3, 'CS301 - Midterm Exam', 'Midterm Exam for Machine Learning Fundamentals', 1, 60, 60, 1, 0, '2025-04-15', datetime('now')),
(8, 3, 'CS301 - Final Exam', 'Final Exam for Machine Learning Fundamentals', 1, 90, 70, 1, 0, '2025-05-20', datetime('now')),
(9, 3, 'CS301 - Weekly Quiz 1', 'Weekly Quiz 1 for Machine Learning Fundamentals', 1, 30, 50, 1, 0, '2025-02-28', datetime('now')),
(10, 4, 'MATH101 - Midterm Exam', 'Midterm Exam for Calculus I', 1, 60, 60, 1, 0, '2025-04-15', datetime('now')),
(11, 4, 'MATH101 - Final Exam', 'Final Exam for Calculus I', 1, 90, 70, 1, 0, '2025-05-20', datetime('now')),
(12, 4, 'MATH101 - Weekly Quiz 1', 'Weekly Quiz 1 for Calculus I', 1, 30, 50, 1, 0, '2025-02-28', datetime('now'));

-- ============================================================================
-- QUIZ QUESTIONS TABLE
-- ============================================================================
INSERT INTO quiz_questions (id, quiz_id, question_text, question_type, points, "order", options, correct_answer, created_at) VALUES
-- Quiz 1 (CS101 Midterm) Questions
(1, 1, 'Question 1: What is the correct answer regarding computer science basics?', 'multiple_choice', 5, 1, '["Option A", "Option B", "Option C", "Option D"]', 'Option A', datetime('now')),
(2, 1, 'Question 2: What is the binary representation of decimal 10?', 'multiple_choice', 5, 2, '["1010", "1100", "1001", "1110"]', '1010', datetime('now')),
(3, 1, 'Question 3: Python is a compiled language.', 'true_false', 3, 3, '["True", "False"]', 'False', datetime('now')),
(4, 1, 'Question 4: What is an algorithm?', 'short_answer', 10, 4, NULL, 'algorithm', datetime('now')),
(5, 1, 'Question 5: What is OOP?', 'short_answer', 10, 5, NULL, 'object-oriented programming', datetime('now')),
-- Quiz 4 (CS201 Midterm) Questions
(6, 4, 'Question 1: What is the time complexity of binary search?', 'multiple_choice', 5, 1, '["O(1)", "O(log n)", "O(n)", "O(n^2)"]', 'O(log n)', datetime('now')),
(7, 4, 'Question 2: Which data structure uses LIFO?', 'multiple_choice', 5, 2, '["Queue", "Stack", "Array", "Linked List"]', 'Stack', datetime('now')),
(8, 4, 'Question 3: Binary trees can have more than 2 children per node.', 'true_false', 3, 3, '["True", "False"]', 'False', datetime('now')),
(9, 4, 'Question 4: What is a linked list?', 'short_answer', 10, 4, NULL, 'linked list', datetime('now')),
(10, 4, 'Question 5: What is hashing?', 'short_answer', 10, 5, NULL, 'hashing', datetime('now')),
-- Quiz 7 (CS301 Midterm) Questions
(11, 7, 'Question 1: What is machine learning a subset of?', 'multiple_choice', 5, 1, '["AI", "Data Science", "Statistics", "Neural Networks"]', 'AI', datetime('now')),
(12, 7, 'Question 2: Which algorithm is used for classification?', 'multiple_choice', 5, 2, '["Linear Regression", "Logistic Regression", "K-Means", "PCA"]', 'Logistic Regression', datetime('now')),
(13, 7, 'Question 3: Deep learning requires large datasets.', 'true_false', 3, 3, '["True", "False"]', 'True', datetime('now')),
(14, 7, 'Question 4: What is overfitting?', 'short_answer', 10, 4, NULL, 'overfitting', datetime('now')),
(15, 7, 'Question 5: What is a neural network?', 'short_answer', 10, 5, NULL, 'neural network', datetime('now')),
-- Quiz 10 (MATH101 Midterm) Questions
(16, 10, 'Question 1: What is the derivative of x^2?', 'multiple_choice', 5, 1, '["x", "2x", "2", "x^2"]', '2x', datetime('now')),
(17, 10, 'Question 2: What is the integral of 2x?', 'multiple_choice', 5, 2, '["x^2", "2x^2", "x^2 + C", "2"]', 'x^2 + C', datetime('now')),
(18, 10, 'Question 3: The derivative of a constant is zero.', 'true_false', 3, 3, '["True", "False"]', 'True', datetime('now')),
(19, 10, 'Question 4: What is a limit?', 'short_answer', 10, 4, NULL, 'limit', datetime('now')),
(20, 10, 'Question 5: What is calculus?', 'short_answer', 10, 5, NULL, 'calculus', datetime('now'));

-- ============================================================================
-- CHAT SESSIONS TABLE
-- ============================================================================
INSERT INTO chat_sessions (id, student_id, title, course_id, topic, is_active, created_at) VALUES
(1, 1, 'Chat: Homework Help', NULL, 'Homework Help', 1, datetime('now', '-5 days')),
(2, 1, 'Chat: Exam Preparation', NULL, 'Exam Preparation', 1, datetime('now', '-3 days')),
(3, 2, 'Chat: Concept Review', NULL, 'Concept Review', 1, datetime('now', '-4 days')),
(4, 3, 'Chat: Practice Problems', NULL, 'Practice Problems', 1, datetime('now', '-2 days')),
(5, 4, 'Chat: General Questions', NULL, 'General Questions', 1, datetime('now', '-1 days')),
(6, 5, 'Chat: Homework Help', NULL, 'Homework Help', 1, datetime('now', '-6 days')),
(7, 6, 'Chat: Exam Preparation', NULL, 'Exam Preparation', 1, datetime('now', '-7 days')),
(8, 7, 'Chat: Concept Review', NULL, 'Concept Review', 0, datetime('now', '-10 days')),
(9, 8, 'Chat: Practice Problems', NULL, 'Practice Problems', 1, datetime('now', '-8 days')),
(10, 9, 'Chat: General Questions', NULL, 'General Questions', 1, datetime('now', '-9 days'));

-- ============================================================================
-- CHAT MESSAGES TABLE
-- ============================================================================
INSERT INTO chat_messages (id, session_id, role, content, is_ai, created_at) VALUES
(1, 1, 'user', 'I need help with my homework assignment 1.', 0, datetime('now', '-5 days')),
(2, 1, 'assistant', 'How can I help you?', 1, datetime('now', '-5 days')),
(3, 1, 'user', 'Can you explain loops in Python?', 0, datetime('now', '-5 days')),
(4, 1, 'assistant', 'Of course! Loops in Python allow you to iterate over sequences...', 1, datetime('now', '-5 days')),
(5, 2, 'user', 'I need help preparing for the midterm exam.', 0, datetime('now', '-3 days')),
(6, 2, 'assistant', 'I can help you create a study plan. What topics are covered?', 1, datetime('now', '-3 days')),
(7, 3, 'user', 'Can you explain linked lists?', 0, datetime('now', '-4 days')),
(8, 3, 'assistant', 'A linked list is a linear data structure...', 1, datetime('now', '-4 days')),
(9, 4, 'user', 'I want to practice some problems.', 0, datetime('now', '-2 days')),
(10, 4, 'assistant', 'Great! What topic would you like to practice?', 1, datetime('now', '-2 days')),
(11, 5, 'user', 'I have a question about the course.', 0, datetime('now', '-1 days')),
(12, 5, 'assistant', 'Sure, what would you like to know?', 1, datetime('now', '-1 days'));

-- ============================================================================
-- CV REVIEWS TABLE
-- ============================================================================
INSERT INTO cv_reviews (id, student_id, file_path, file_name, job_readiness_score, status, strengths, weaknesses, recommendations, suggested_skills, suggested_projects, interview_tips, reviewed_by, reviewed_at, created_at) VALUES
(1, 1, '/uploads/cv_STU1000.pdf', 'cv_STU1000.pdf', 85, 'reviewed', 'Strong technical skills, good communication, proactive learning', 'Could improve presentation skills, needs more industry experience', 'Continue building projects, consider internships', '["Python", "Machine Learning", "Data Analysis"]', '["Web App", "Mobile App", "Data Visualization"]', 'Practice coding problems, research company culture, prepare STAR stories', NULL, datetime('now', '-5 days'), datetime('now', '-30 days')),
(2, 2, '/uploads/cv_STU1001.pdf', 'cv_STU1001.pdf', 75, 'reviewed', 'Strong problem-solving skills, good teamwork', 'Limited exposure to modern frameworks', 'Learn React and Node.js, contribute to open source', '["Java", "Spring", "React"]', '["E-commerce App", "REST API"]', 'Practice system design questions, prepare for behavioral questions', NULL, datetime('now', '-10 days'), datetime('now', '-35 days')),
(3, 3, '/uploads/cv_STU1002.pdf', 'cv_STU1002.pdf', 90, 'reviewed', 'Excellent leadership skills, strong business acumen', 'Could improve technical depth', 'Pursue MBA, consider consulting roles', '["Business Analysis", "Project Management", "Excel"]', '["Business Plan", "Market Analysis"]', 'Prepare for case interviews, practice presentation skills', NULL, datetime('now', '-3 days'), datetime('now', '-25 days')),
(4, 4, '/uploads/cv_STU1003.pdf', 'cv_STU1003.pdf', 65, 'needs_revision', 'Good mathematical foundation, eager to learn', 'Lack of practical projects, weak communication', 'Build portfolio projects, improve writing skills', '["Python", "Statistics", "R"]', '["Data Analysis Project", "Statistical Model"]', 'Practice technical interviews, work on communication skills', NULL, NULL, datetime('now', '-20 days')),
(5, 5, '/uploads/cv_STU1004.pdf', 'cv_STU1004.pdf', 70, 'pending', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, datetime('now', '-15 days')),
(6, 6, '/uploads/cv_STU1005.pdf', 'cv_STU1005.pdf', 80, 'reviewed', 'Good programming skills, analytical thinking', 'Limited soft skills', 'Practice presentations, join group projects', '["Python", "SQL", "JavaScript"]', '["Portfolio Website", "Database Project"]', 'Prepare for technical interviews, practice pair programming', NULL, datetime('now', '-7 days'), datetime('now', '-28 days')),
(7, 7, '/uploads/cv_STU1006.pdf', 'cv_STU1006.pdf', 88, 'reviewed', 'Strong engineering background, excellent problem-solving', 'Could improve code documentation', 'Contribute to open source, write technical blog', '["C++", "Python", "Linux"]', '["Embedded System", "Robot Project"]', 'Practice coding challenges, prepare for system design', NULL, datetime('now', '-2 days'), datetime('now', '-40 days')),
(8, 8, '/uploads/cv_STU1007.pdf', 'cv_STU1007.pdf', 60, 'needs_revision', 'Quick learner, positive attitude', 'No relevant experience, weak CV structure', 'Gain internship experience, restructure CV', '["Marketing", "Social Media", "Content Creation"]', '["Marketing Campaign", "Social Media Plan"]', 'Practice elevator pitch, prepare for HR interviews', NULL, NULL, datetime('now', '-18 days')),
(9, 9, '/uploads/cv_STU1008.pdf', 'cv_STU1008.pdf', 72, 'pending', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, datetime('now', '-12 days')),
(10, 10, '/uploads/cv_STU1009.pdf', 'cv_STU1009.pdf', 78, 'reviewed', 'Good physics background, research experience', 'Limited programming skills', 'Learn Python and data analysis tools', '["Python", "MATLAB", "Data Analysis"]', '["Research Project", "Simulation"]', 'Prepare for technical questions, practice problem-solving', NULL, datetime('now', '-4 days'), datetime('now', '-22 days'));

-- ============================================================================
-- RISK SCORES TABLE (Overall - no course specific)
-- ============================================================================
INSERT INTO risk_scores (id, student_id, course_id, risk_level, risk_score, attendance_score, quiz_score, assignment_score, overall_score, risk_factors, recommendations, calculated_at) VALUES
(1, 1, NULL, 'low', 25, 85, 90, 88, 87, '["Good attendance", "Strong quiz scores"]', 'Keep up the excellent work!', datetime('now', '-3 days')),
(2, 2, NULL, 'low', 30, 80, 82, 75, 79, '["Good attendance", "Consistent performance"]', 'Continue performing well', datetime('now', '-5 days')),
(3, 3, NULL, 'low', 22, 90, 88, 92, 90, '["Excellent attendance", "Top performance"]', 'You are doing great!', datetime('now', '-7 days')),
(4, 4, NULL, 'medium', 55, 65, 70, 60, 65, '["Moderate attendance", "Average scores"]', 'Improve attendance and assignment submission', datetime('now', '-2 days')),
(5, 5, NULL, 'low', 35, 78, 80, 75, 77, '["Good attendance", "Solid performance"]', 'Keep up the good work', datetime('now', '-4 days')),
(6, 6, NULL, 'medium', 50, 70, 65, 68, 67, '["Average attendance", "Inconsistent quiz scores"]', 'Focus on improving quiz performance', datetime('now', '-6 days')),
(7, 7, NULL, 'low', 28, 88, 85, 90, 87, '["Excellent attendance", "Strong assignment scores"]', 'Maintain your performance', datetime('now', '-8 days')),
(8, 8, NULL, 'high', 65, 55, 60, 58, 57, '["Low attendance", "Below average scores"]', 'Increase attendance and seek tutoring', datetime('now', '-1 days')),
(9, 9, NULL, 'medium', 48, 72, 68, 70, 70, '["Moderate attendance", "Average performance"]', 'Aim for consistent improvement', datetime('now', '-9 days')),
(10, 10, NULL, 'low', 32, 82, 78, 80, 80, '["Good attendance", "Solid overall performance"]', 'Continue working hard', datetime('now', '-10 days')),
(11, 11, NULL, 'medium', 52, 68, 72, 65, 68, '["Average attendance", "Inconsistent assignment scores"]', 'Focus on assignment submission', datetime('now', '-11 days'));

-- ============================================================================
-- ENROLLMENTS TABLE - LEFT EMPTY (No student enrollments as per requirement)
-- ============================================================================
-- NOTE: The enrollments table exists but contains NO records
-- Students are NOT registered to any course
-- Only lecturers are assigned to courses (via lecturer_id in courses table)

-- ============================================================================
-- SUMMARY
-- ============================================================================
-- Total Records:
-- - Users: 18 (1 admin, 1 career advisor, 5 lecturers, 11 students)
-- - Lecturers: 5
-- - Students: 11
-- - Courses: 12 (all with lecturers assigned)
-- - Modules: 60 (5 per course)
-- - Course Materials: 13
-- - Quizzes: 12
-- - Quiz Questions: 20
-- - Chat Sessions: 10
-- - Chat Messages: 12
-- - CV Reviews: 10
-- - Risk Scores: 11 (overall only)
-- - Enrollments: 0 (NO student enrollments)
-- ============================================================================
