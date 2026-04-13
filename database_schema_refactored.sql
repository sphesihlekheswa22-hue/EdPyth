-- ============================================================================
-- EduMind Database Schema - REFACTORED for Module-Based LMS Architecture
-- ============================================================================
-- THIS IS THE NEW SCHEMA - All content is module-based
-- Lecturers are assigned to modules, not courses
-- Students enroll in courses, access content through modules
-- ============================================================================

-- ============================================================================
-- SECTION 1: DROP ALL EXISTING TABLES
-- ============================================================================
DROP TABLE IF EXISTS chat_messages CASCADE;
DROP TABLE IF EXISTS chat_sessions CASCADE;
DROP TABLE IF EXISTS study_plan_items CASCADE;
DROP TABLE IF EXISTS study_plans CASCADE;
DROP TABLE IF EXISTS risk_scores CASCADE;
DROP TABLE IF EXISTS cv_reviews CASCADE;
DROP TABLE IF EXISTS quiz_results CASCADE;
DROP TABLE IF EXISTS quiz_questions CASCADE;
DROP TABLE IF EXISTS quizzes CASCADE;
DROP TABLE IF EXISTS assignment_submissions CASCADE;
DROP TABLE IF EXISTS assignments CASCADE;
DROP TABLE IF EXISTS course_materials CASCADE;
DROP TABLE IF EXISTS attendances CASCADE;
DROP TABLE IF EXISTS marks CASCADE;
DROP TABLE IF EXISTS student_module_progress CASCADE;
DROP TABLE IF EXISTS lecturer_modules CASCADE;
DROP TABLE IF EXISTS enrollments CASCADE;
DROP TABLE IF EXISTS modules CASCADE;
DROP TABLE IF EXISTS courses CASCADE;
DROP TABLE IF EXISTS students CASCADE;
DROP TABLE IF EXISTS lecturers CASCADE;
DROP TABLE IF EXISTS users CASCADE;

-- ============================================================================
-- SECTION 2: USERS TABLE (Base authentication - UNCHANGED)
-- ============================================================================
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email VARCHAR(120) NOT NULL UNIQUE,
    password_hash VARCHAR(128) NOT NULL,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    role VARCHAR(20) NOT NULL CHECK (role IN ('admin', 'lecturer', 'student', 'career_advisor')),
    is_active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_notification_read TIMESTAMP,
    email_verified BOOLEAN DEFAULT 0,
    email_verification_token VARCHAR(100),
    email_verification_expires_at TIMESTAMP,
    reset_token VARCHAR(100),
    reset_token_expires_at TIMESTAMP
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role ON users(role);

-- ============================================================================
-- SECTION 3: OTPS TABLE (UNCHANGED)
-- ============================================================================
CREATE TABLE otps (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email VARCHAR(120) NOT NULL,
    otp_code VARCHAR(6) NOT NULL,
    purpose VARCHAR(20) NOT NULL CHECK (purpose IN ('registration', 'password_reset')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,
    is_used BOOLEAN DEFAULT 0
);

CREATE INDEX idx_otps_email ON otps(email);
CREATE INDEX idx_otps_purpose ON otps(purpose);
CREATE INDEX idx_otps_expires_at ON otps(expires_at);

-- ============================================================================
-- SECTION 4: LECTURERS TABLE (REMOVED course relationship)
-- ============================================================================
CREATE TABLE lecturers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL UNIQUE,
    employee_id VARCHAR(20) NOT NULL UNIQUE,
    department VARCHAR(100),
    title VARCHAR(50),
    phone VARCHAR(20),
    office VARCHAR(50),
    hire_date DATE DEFAULT (DATE('now')),
    specialization VARCHAR(200),
    
    CONSTRAINT fk_lecturers_user 
        FOREIGN KEY (user_id) REFERENCES users(id) 
        ON DELETE CASCADE
);

CREATE INDEX idx_lecturers_user_id ON lecturers(user_id);
CREATE INDEX idx_lecturers_employee_id ON lecturers(employee_id);

-- ============================================================================
-- SECTION 5: STUDENTS TABLE (UNCHANGED)
-- ============================================================================
CREATE TABLE students (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL UNIQUE,
    student_id VARCHAR(20) NOT NULL UNIQUE,
    date_of_birth DATE,
    phone VARCHAR(20),
    address TEXT,
    program VARCHAR(100),
    year_of_study INTEGER,
    enrollment_date DATE DEFAULT (DATE('now')),
    
    CONSTRAINT fk_students_user 
        FOREIGN KEY (user_id) REFERENCES users(id) 
        ON DELETE CASCADE
);

CREATE INDEX idx_students_user_id ON students(user_id);
CREATE INDEX idx_students_student_id ON students(student_id);

-- ============================================================================
-- SECTION 6: COURSES TABLE (REMOVED lecturer_id - courses don't have lecturers)
-- ============================================================================
CREATE TABLE courses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code VARCHAR(20) NOT NULL UNIQUE,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    credits INTEGER DEFAULT 3 CHECK (credits >= 0 AND credits <= 10),
    -- REMOVED: lecturer_id - lecturers are assigned to modules, not courses
    semester VARCHAR(20),
    year INTEGER DEFAULT (CAST(STRFTIME('%Y', 'now') AS INTEGER)),
    is_active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_courses_code ON courses(code);
CREATE INDEX idx_courses_semester ON courses(semester);

-- ============================================================================
-- SECTION 7: MODULES TABLE (Course subdivisions - lecturers assigned here)
-- ============================================================================
CREATE TABLE modules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    course_id INTEGER NOT NULL,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    module_order INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_modules_course 
        FOREIGN KEY (course_id) REFERENCES courses(id) 
        ON DELETE CASCADE
);

CREATE INDEX idx_modules_course_id ON modules(course_id);
CREATE INDEX idx_modules_order ON modules(module_order);

-- ============================================================================
-- SECTION 8: LECTURER_MODULES TABLE (NEW - Many-to-many: lecturers to modules)
-- ============================================================================
CREATE TABLE lecturer_modules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    lecturer_id INTEGER NOT NULL,
    module_id INTEGER NOT NULL,
    is_primary BOOLEAN DEFAULT 0,  -- Primary lecturer for this module
    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_lecturer_modules_lecturer 
        FOREIGN KEY (lecturer_id) REFERENCES lecturers(id) 
        ON DELETE CASCADE,
    CONSTRAINT fk_lecturer_modules_module 
        FOREIGN KEY (module_id) REFERENCES modules(id) 
        ON DELETE CASCADE,
    
    -- Prevent duplicate assignments
    CONSTRAINT uk_lecturer_module UNIQUE (lecturer_id, module_id)
);

CREATE INDEX idx_lecturer_modules_lecturer_id ON lecturer_modules(lecturer_id);
CREATE INDEX idx_lecturer_modules_module_id ON lecturer_modules(module_id);

-- ============================================================================
-- SECTION 9: ENROLLMENTS TABLE (Students enroll in courses only - UNCHANGED)
-- ============================================================================
CREATE TABLE enrollments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER NOT NULL,
    course_id INTEGER NOT NULL,
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'completed', 'dropped')),
    enrolled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    
    CONSTRAINT fk_enrollments_student 
        FOREIGN KEY (student_id) REFERENCES students(id) 
        ON DELETE CASCADE,
    CONSTRAINT fk_enrollments_course 
        FOREIGN KEY (course_id) REFERENCES courses(id) 
        ON DELETE CASCADE,
    
    CONSTRAINT uk_enrollment_student_course 
        UNIQUE (student_id, course_id)
);

CREATE INDEX idx_enrollments_student_id ON enrollments(student_id);
CREATE INDEX idx_enrollments_course_id ON enrollments(course_id);
CREATE INDEX idx_enrollments_status ON enrollments(status);

-- ============================================================================
-- SECTION 10: STUDENT_MODULE_PROGRESS TABLE (NEW - Track progress per module)
-- ============================================================================
CREATE TABLE student_module_progress (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER NOT NULL,
    module_id INTEGER NOT NULL,
    enrollment_id INTEGER NOT NULL,
    
    -- Progress tracking
    completion_status VARCHAR(20) DEFAULT 'not_started' 
        CHECK (completion_status IN ('not_started', 'in_progress', 'completed')),
    completion_percentage INTEGER DEFAULT 0 CHECK (completion_percentage >= 0 AND completion_percentage <= 100),
    
    -- Engagement metrics
    materials_viewed INTEGER DEFAULT 0,
    quizzes_completed INTEGER DEFAULT 0,
    assignments_submitted INTEGER DEFAULT 0,
    attendance_sessions INTEGER DEFAULT 0,
    
    -- Scores
    quiz_average_score DECIMAL(5,2),
    assignment_average_score DECIMAL(5,2),
    overall_module_score DECIMAL(5,2),
    
    -- Timestamps
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    last_accessed_at TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_progress_student 
        FOREIGN KEY (student_id) REFERENCES students(id) 
        ON DELETE CASCADE,
    CONSTRAINT fk_progress_module 
        FOREIGN KEY (module_id) REFERENCES modules(id) 
        ON DELETE CASCADE,
    CONSTRAINT fk_progress_enrollment 
        FOREIGN KEY (enrollment_id) REFERENCES enrollments(id) 
        ON DELETE CASCADE,
    
    -- One progress record per student per module per enrollment
    CONSTRAINT uk_student_module_enrollment UNIQUE (student_id, module_id, enrollment_id)
);

CREATE INDEX idx_progress_student_id ON student_module_progress(student_id);
CREATE INDEX idx_progress_module_id ON student_module_progress(module_id);
CREATE INDEX idx_progress_enrollment_id ON student_module_progress(enrollment_id);
CREATE INDEX idx_progress_status ON student_module_progress(completion_status);

-- ============================================================================
-- SECTION 11: COURSE_MATERIALS TABLE (REQUIRED module_id, NO course_id)
-- ============================================================================
CREATE TABLE course_materials (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    -- REMOVED: course_id - materials belong to modules only
    module_id INTEGER NOT NULL,  -- NOW REQUIRED
    title VARCHAR(200) NOT NULL,
    description TEXT,
    file_path VARCHAR(500),
    file_name VARCHAR(255),
    file_type VARCHAR(50),
    file_size INTEGER,
    category VARCHAR(50) CHECK (category IN ('lecture', 'assignment', 'reading', 'notes', 'other')),
    uploaded_by INTEGER NOT NULL,
    is_published BOOLEAN DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_materials_module 
        FOREIGN KEY (module_id) REFERENCES modules(id) 
        ON DELETE CASCADE,
    CONSTRAINT fk_materials_uploader 
        FOREIGN KEY (uploaded_by) REFERENCES users(id) 
        ON DELETE RESTRICT
);

CREATE INDEX idx_materials_module_id ON course_materials(module_id);
CREATE INDEX idx_materials_category ON course_materials(category);

-- ============================================================================
-- SECTION 12: ASSIGNMENTS TABLE (REQUIRED module_id, NO course_id)
-- ============================================================================
CREATE TABLE assignments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    -- REMOVED: course_id - assignments belong to modules only
    module_id INTEGER NOT NULL,  -- NOW REQUIRED
    title VARCHAR(200) NOT NULL,
    description TEXT,
    due_date TIMESTAMP,
    total_marks DECIMAL(10,2) DEFAULT 100,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_assignments_module 
        FOREIGN KEY (module_id) REFERENCES modules(id) 
        ON DELETE CASCADE
);

CREATE INDEX idx_assignments_module_id ON assignments(module_id);
CREATE INDEX idx_assignments_due_date ON assignments(due_date);

-- ============================================================================
-- SECTION 13: ASSIGNMENT_SUBMISSIONS TABLE (UNCHANGED structure)
-- ============================================================================
CREATE TABLE assignment_submissions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    assignment_id INTEGER NOT NULL,
    student_id INTEGER NOT NULL,
    file_path VARCHAR(500),
    file_name VARCHAR(255),
    submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(50) DEFAULT 'submitted',
    feedback TEXT,
    mark DECIMAL(10,2),
    grade VARCHAR(10),
    graded_at TIMESTAMP,
    graded_by INTEGER,
    
    CONSTRAINT fk_submissions_assignment 
        FOREIGN KEY (assignment_id) REFERENCES assignments(id) 
        ON DELETE CASCADE,
    CONSTRAINT fk_submissions_student 
        FOREIGN KEY (student_id) REFERENCES students(id) 
        ON DELETE CASCADE,
    CONSTRAINT fk_submissions_grader 
        FOREIGN KEY (graded_by) REFERENCES users(id) 
        ON DELETE SET NULL
);

CREATE INDEX idx_submissions_assignment_id ON assignment_submissions(assignment_id);
CREATE INDEX idx_submissions_student_id ON assignment_submissions(student_id);

-- ============================================================================
-- SECTION 13b: ASSIGNMENT_ATTACHMENTS (lecturer handouts / spec files)
-- ============================================================================
CREATE TABLE assignment_attachments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    assignment_id INTEGER NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    file_name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_assignment_attachments_assignment
        FOREIGN KEY (assignment_id) REFERENCES assignments(id)
        ON DELETE CASCADE
);

CREATE INDEX idx_assignment_attachments_assignment_id ON assignment_attachments(assignment_id);

-- ============================================================================
-- SECTION 14: QUIZZES TABLE (REQUIRED module_id, NO course_id)
-- ============================================================================
CREATE TABLE quizzes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    -- REMOVED: course_id - quizzes belong to modules only
    module_id INTEGER NOT NULL,  -- NOW REQUIRED
    title VARCHAR(200) NOT NULL,
    description TEXT,
    created_by INTEGER NOT NULL,
    time_limit INTEGER,
    passing_score INTEGER DEFAULT 50 CHECK (passing_score >= 0 AND passing_score <= 100),
    is_published BOOLEAN DEFAULT 0,
    is_ai_generated BOOLEAN DEFAULT 0,
    due_date TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_quizzes_module 
        FOREIGN KEY (module_id) REFERENCES modules(id) 
        ON DELETE CASCADE,
    CONSTRAINT fk_quizzes_creator 
        FOREIGN KEY (created_by) REFERENCES users(id) 
        ON DELETE RESTRICT
);

CREATE INDEX idx_quizzes_module_id ON quizzes(module_id);
CREATE INDEX idx_quizzes_published ON quizzes(is_published);

-- ============================================================================
-- SECTION 15: QUIZ_QUESTIONS TABLE (module_id now references module, not optional context)
-- ============================================================================
CREATE TABLE quiz_questions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    quiz_id INTEGER NOT NULL,
    question_text TEXT NOT NULL,
    question_type VARCHAR(20) CHECK (question_type IN ('multiple_choice', 'true_false', 'short_answer')),
    points INTEGER DEFAULT 1,
    question_order INTEGER DEFAULT 0,
    options TEXT,
    correct_answer TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_questions_quiz 
        FOREIGN KEY (quiz_id) REFERENCES quizzes(id) 
        ON DELETE CASCADE
);

CREATE INDEX idx_questions_quiz_id ON quiz_questions(quiz_id);

-- ============================================================================
-- SECTION 16: QUIZ_RESULTS TABLE (UNCHANGED structure)
-- ============================================================================
CREATE TABLE quiz_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    quiz_id INTEGER NOT NULL,
    student_id INTEGER NOT NULL,
    score DECIMAL(10,2),
    total_points DECIMAL(10,2),
    percentage DECIMAL(5,2),
    passed BOOLEAN DEFAULT 0,
    time_taken INTEGER,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    
    CONSTRAINT fk_results_quiz 
        FOREIGN KEY (quiz_id) REFERENCES quizzes(id) 
        ON DELETE CASCADE,
    CONSTRAINT fk_results_student 
        FOREIGN KEY (student_id) REFERENCES students(id) 
        ON DELETE CASCADE
);

CREATE INDEX idx_results_quiz_id ON quiz_results(quiz_id);
CREATE INDEX idx_results_student_id ON quiz_results(student_id);

-- ============================================================================
-- SECTION 17: ATTENDANCES TABLE (REQUIRED module_id, NO course_id)
-- ============================================================================
CREATE TABLE attendances (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    -- REMOVED: course_id - attendance is tracked at module level
    module_id INTEGER NOT NULL,  -- NOW REQUIRED
    student_id INTEGER NOT NULL,
    date DATE NOT NULL,
    status VARCHAR(20) CHECK (status IN ('present', 'absent', 'late', 'excused')),
    recorded_by INTEGER NOT NULL,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_attendances_module 
        FOREIGN KEY (module_id) REFERENCES modules(id) 
        ON DELETE CASCADE,
    CONSTRAINT fk_attendances_student 
        FOREIGN KEY (student_id) REFERENCES students(id) 
        ON DELETE CASCADE,
    CONSTRAINT fk_attendances_recorder 
        FOREIGN KEY (recorded_by) REFERENCES users(id) 
        ON DELETE RESTRICT,
    
    -- Unique attendance per student per module per date
    CONSTRAINT uk_attendance_student_module_date UNIQUE (student_id, module_id, date)
);

CREATE INDEX idx_attendances_module_id ON attendances(module_id);
CREATE INDEX idx_attendances_student_id ON attendances(student_id);
CREATE INDEX idx_attendances_date ON attendances(date);

-- ============================================================================
-- SECTION 18: MARKS TABLE (REQUIRED module_id, NO course_id)
-- ============================================================================
CREATE TABLE marks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    -- REMOVED: course_id - marks are recorded at module level
    module_id INTEGER NOT NULL,  -- NOW REQUIRED
    student_id INTEGER NOT NULL,
    assessment_type VARCHAR(50) CHECK (assessment_type IN ('assignment', 'quiz', 'participation', 'project', 'other')),
    assessment_name VARCHAR(200),
    mark DECIMAL(10,2),
    total_marks DECIMAL(10,2),
    percentage DECIMAL(5,2),
    grade VARCHAR(5),
    recorded_by INTEGER NOT NULL,
    feedback TEXT,
    marked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_marks_module 
        FOREIGN KEY (module_id) REFERENCES modules(id) 
        ON DELETE CASCADE,
    CONSTRAINT fk_marks_student 
        FOREIGN KEY (student_id) REFERENCES students(id) 
        ON DELETE CASCADE,
    CONSTRAINT fk_marks_recorder 
        FOREIGN KEY (recorded_by) REFERENCES users(id) 
        ON DELETE RESTRICT
);

CREATE INDEX idx_marks_module_id ON marks(module_id);
CREATE INDEX idx_marks_student_id ON marks(student_id);
CREATE INDEX idx_marks_assessment_type ON marks(assessment_type);

-- ============================================================================
-- SECTION 19: STUDY_PLANS TABLE (course_id now OPTIONAL - can be module-specific)
-- ============================================================================
CREATE TABLE study_plans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER NOT NULL,
    course_id INTEGER,  -- Optional - NULL for cross-course or module-specific plans
    module_id INTEGER,  -- NEW - can link to specific module
    title VARCHAR(200) NOT NULL,
    description TEXT,
    is_ai_generated BOOLEAN DEFAULT 0,
    start_date DATE,
    end_date DATE,
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'completed', 'cancelled')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_plans_student 
        FOREIGN KEY (student_id) REFERENCES students(id) 
        ON DELETE CASCADE,
    CONSTRAINT fk_plans_course 
        FOREIGN KEY (course_id) REFERENCES courses(id) 
        ON DELETE SET NULL,
    CONSTRAINT fk_plans_module 
        FOREIGN KEY (module_id) REFERENCES modules(id) 
        ON DELETE SET NULL
);

CREATE INDEX idx_plans_student_id ON study_plans(student_id);
CREATE INDEX idx_plans_course_id ON study_plans(course_id);
CREATE INDEX idx_plans_module_id ON study_plans(module_id);

-- ============================================================================
-- SECTION 20: STUDY_PLAN_ITEMS TABLE (UNCHANGED)
-- ============================================================================
CREATE TABLE study_plan_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    study_plan_id INTEGER NOT NULL,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    task_type VARCHAR(50) CHECK (task_type IN ('reading', 'practice', 'review', 'assignment', 'project', 'other')),
    item_order INTEGER DEFAULT 0,
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'in_progress', 'completed', 'cancelled')),
    priority VARCHAR(20) DEFAULT 'medium' CHECK (priority IN ('low', 'medium', 'high')),
    due_date DATE,
    estimated_time INTEGER,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_items_plan 
        FOREIGN KEY (study_plan_id) REFERENCES study_plans(id) 
        ON DELETE CASCADE
);

CREATE INDEX idx_items_plan_id ON study_plan_items(study_plan_id);

-- ============================================================================
-- SECTION 21: CHAT_SESSIONS TABLE (course_id optional, can reference module)
-- ============================================================================
CREATE TABLE chat_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER NOT NULL,
    course_id INTEGER,
    module_id INTEGER,  -- NEW - can link to specific module
    title VARCHAR(200) NOT NULL,
    topic VARCHAR(100),
    is_active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_sessions_student 
        FOREIGN KEY (student_id) REFERENCES students(id) 
        ON DELETE CASCADE,
    CONSTRAINT fk_sessions_course 
        FOREIGN KEY (course_id) REFERENCES courses(id) 
        ON DELETE SET NULL,
    CONSTRAINT fk_sessions_module 
        FOREIGN KEY (module_id) REFERENCES modules(id) 
        ON DELETE SET NULL
);

CREATE INDEX idx_sessions_student_id ON chat_sessions(student_id);
CREATE INDEX idx_sessions_course_id ON chat_sessions(course_id);
CREATE INDEX idx_sessions_module_id ON chat_sessions(module_id);

-- ============================================================================
-- SECTION 22: CHAT_MESSAGES TABLE (UNCHANGED)
-- ============================================================================
CREATE TABLE chat_messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL,
    role VARCHAR(20) CHECK (role IN ('user', 'assistant', 'system')),
    content TEXT NOT NULL,
    is_ai BOOLEAN DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_messages_session 
        FOREIGN KEY (session_id) REFERENCES chat_sessions(id) 
        ON DELETE CASCADE
);

CREATE INDEX idx_messages_session_id ON chat_messages(session_id);

-- ============================================================================
-- SECTION 23: CV_REVIEWS TABLE (UNCHANGED)
-- ============================================================================
CREATE TABLE cv_reviews (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER NOT NULL,
    file_path VARCHAR(500),
    file_name VARCHAR(255),
    job_readiness_score INTEGER CHECK (job_readiness_score >= 0 AND job_readiness_score <= 100),
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'reviewed', 'needs_revision')),
    strengths TEXT,
    weaknesses TEXT,
    recommendations TEXT,
    suggested_skills TEXT,
    suggested_projects TEXT,
    interview_tips TEXT,
    reviewed_by INTEGER,
    reviewed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_reviews_student 
        FOREIGN KEY (student_id) REFERENCES students(id) 
        ON DELETE CASCADE,
    CONSTRAINT fk_reviews_reviewer 
        FOREIGN KEY (reviewed_by) REFERENCES users(id) 
        ON DELETE SET NULL
);

CREATE INDEX idx_reviews_student_id ON cv_reviews(student_id);
CREATE INDEX idx_reviews_status ON cv_reviews(status);

-- ============================================================================
-- SECTION 24: RISK_SCORES TABLE (module_id added)
-- ============================================================================
CREATE TABLE risk_scores (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER NOT NULL,
    course_id INTEGER,
    module_id INTEGER,  -- NEW - can track risk at module level
    risk_level VARCHAR(20) CHECK (risk_level IN ('low', 'medium', 'high', 'critical')),
    risk_score INTEGER CHECK (risk_score >= 0 AND risk_score <= 100),
    attendance_score INTEGER CHECK (attendance_score >= 0 AND attendance_score <= 100),
    quiz_score INTEGER CHECK (quiz_score >= 0 AND quiz_score <= 100),
    assignment_score INTEGER CHECK (assignment_score >= 0 AND assignment_score <= 100),
    overall_score INTEGER CHECK (overall_score >= 0 AND overall_score <= 100),
    risk_factors TEXT,
    recommendations TEXT,
    calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_risk_student 
        FOREIGN KEY (student_id) REFERENCES students(id) 
        ON DELETE CASCADE,
    CONSTRAINT fk_risk_course 
        FOREIGN KEY (course_id) REFERENCES courses(id) 
        ON DELETE SET NULL,
    CONSTRAINT fk_risk_module 
        FOREIGN KEY (module_id) REFERENCES modules(id) 
        ON DELETE SET NULL
);

CREATE INDEX idx_risk_student_id ON risk_scores(student_id);
CREATE INDEX idx_risk_course_id ON risk_scores(course_id);
CREATE INDEX idx_risk_module_id ON risk_scores(module_id);

-- ============================================================================
-- SECTION 25: NOTIFICATIONS & INTERVENTIONS (UNCHANGED)
-- ============================================================================
CREATE TABLE IF NOT EXISTS notifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    title VARCHAR(200) NOT NULL,
    message TEXT NOT NULL,
    notification_type VARCHAR(50) DEFAULT 'general',
    is_read BOOLEAN DEFAULT 0,
    related_type VARCHAR(50),
    related_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_notifications_user 
        FOREIGN KEY (user_id) REFERENCES users(id) 
        ON DELETE CASCADE
);

CREATE INDEX idx_notifications_user_id ON notifications(user_id);
CREATE INDEX idx_notifications_is_read ON notifications(is_read);

CREATE TABLE IF NOT EXISTS intervention_messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sender_id INTEGER NOT NULL,
    sender_role VARCHAR(20) NOT NULL,
    student_id INTEGER NOT NULL,
    course_id INTEGER,
    message TEXT NOT NULL,
    intervention_type VARCHAR(50) DEFAULT 'general',
    priority VARCHAR(20) DEFAULT 'medium',
    is_read BOOLEAN DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_interventions_sender 
        FOREIGN KEY (sender_id) REFERENCES users(id) 
        ON DELETE CASCADE,
    CONSTRAINT fk_interventions_student 
        FOREIGN KEY (student_id) REFERENCES students(id) 
        ON DELETE CASCADE,
    CONSTRAINT fk_interventions_course 
        FOREIGN KEY (course_id) REFERENCES courses(id) 
        ON DELETE SET NULL
);

CREATE INDEX idx_interventions_student_id ON intervention_messages(student_id);
CREATE INDEX idx_interventions_sender_id ON intervention_messages(sender_id);

-- ============================================================================
-- SECTION 26: VIEWS FOR CONVENIENCE
-- ============================================================================

-- View: Student course access (validates enrollment)
CREATE VIEW IF NOT EXISTS v_student_course_access AS
SELECT 
    s.id as student_id,
    s.user_id,
    e.id as enrollment_id,
    e.course_id,
    e.status as enrollment_status,
    c.code as course_code,
    c.name as course_name
FROM students s
JOIN enrollments e ON s.id = e.student_id
JOIN courses c ON e.course_id = c.id
WHERE e.status = 'active';

-- View: Student module access (validates enrollment through course)
CREATE VIEW IF NOT EXISTS v_student_module_access AS
SELECT 
    s.id as student_id,
    s.user_id,
    m.id as module_id,
    m.course_id,
    m.title as module_title,
    m.module_order,
    e.id as enrollment_id,
    e.status as enrollment_status
FROM students s
JOIN enrollments e ON s.id = e.student_id
JOIN courses c ON e.course_id = c.id
JOIN modules m ON c.id = m.course_id
WHERE e.status = 'active';

-- View: Lecturer module assignments
CREATE VIEW IF NOT EXISTS v_lecturer_modules AS
SELECT 
    l.id as lecturer_id,
    l.user_id,
    l.employee_id,
    lm.module_id,
    lm.is_primary,
    m.title as module_title,
    m.course_id,
    c.code as course_code,
    c.name as course_name
FROM lecturers l
JOIN lecturer_modules lm ON l.id = lm.lecturer_id
JOIN modules m ON lm.module_id = m.id
JOIN courses c ON m.course_id = c.id;

-- ============================================================================
-- SECTION 27: TRIGGERS FOR DATA INTEGRITY
-- ============================================================================

-- Trigger: Auto-create module progress when student enrolls
CREATE TRIGGER IF NOT EXISTS trg_create_module_progress
AFTER INSERT ON enrollments
WHEN NEW.status = 'active'
BEGIN
    INSERT INTO student_module_progress (
        student_id, 
        module_id, 
        enrollment_id,
        completion_status,
        started_at
    )
    SELECT 
        NEW.student_id,
        m.id,
        NEW.id,
        'not_started',
        CURRENT_TIMESTAMP
    FROM modules m
    WHERE m.course_id = NEW.course_id;
END;

-- Trigger: Prevent direct module access without enrollment
-- (Enforced at application level, this is a safety net)
CREATE TRIGGER IF NOT EXISTS trg_validate_module_access
BEFORE INSERT ON student_module_progress
BEGIN
    SELECT CASE
        WHEN NOT EXISTS (
            SELECT 1 FROM enrollments e
            WHERE e.id = NEW.enrollment_id
            AND e.student_id = NEW.student_id
            AND e.status = 'active'
        ) THEN
            RAISE(ABORT, 'Student must have active enrollment to track module progress')
    END;
END;

-- ============================================================================
-- END OF REFACTORED DATABASE SCHEMA
-- ============================================================================