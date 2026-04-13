# EduMind LMS - Course-Based Architecture Migration Guide

## Overview

This migration transforms EduMind from a course-centric model to a strict **Course → Module → Content** hierarchy where:

- **Courses** are containers that students enroll in
- **Modules** contain all learning content (materials, quizzes, assignments, attendance, marks)
- **Lecturers** are assigned to modules (many-to-many), NOT to courses
- **Students** access all content through their enrolled course modules

## Architecture Changes

### Before (Old Model)
```
Student → Enrollment → Course → Content (materials, quizzes, marks, attendance)
                          ↓
                       Lecturer (single)
```

### After (New Model)
```
Student → Enrollment → Course → Modules → Content (materials, quizzes, assignments, marks, attendance)
                                      ↓
                                   Lecturers (many-to-many via lecturer_modules)
```

## Database Schema Changes

### 1. REMOVED Fields (Course-Level Content References)
| Table | Removed Column | Reason |
|-------|---------------|--------|
| `courses` | `lecturer_id` | Lecturers assigned to modules, not courses |
| `course_materials` | `course_id` (required) | Materials belong to modules only |
| `quizzes` | `course_id` | Quizzes belong to modules only |
| `assignments` | `course_id` | Assignments belong to modules only |
| `attendances` | `course_id` | Attendance tracked at module level |
| `marks` | `course_id` | Marks recorded at module level |
| `quiz_questions` | `module_id` | Questions belong to quizzes |

### 2. NEW Tables

#### `lecturer_modules` - Lecturer-to-Module Assignments
```sql
CREATE TABLE lecturer_modules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    lecturer_id INTEGER NOT NULL,
    module_id INTEGER NOT NULL,
    is_primary BOOLEAN DEFAULT 0,
    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(lecturer_id, module_id)
);
```

#### `student_module_progress` - Module-Level Progress Tracking
```sql
CREATE TABLE student_module_progress (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER NOT NULL,
    module_id INTEGER NOT NULL,
    enrollment_id INTEGER NOT NULL,
    completion_status VARCHAR(20), -- not_started, in_progress, completed
    completion_percentage INTEGER DEFAULT 0,
    materials_viewed INTEGER DEFAULT 0,
    quizzes_completed INTEGER DEFAULT 0,
    assignments_submitted INTEGER DEFAULT 0,
    attendance_sessions INTEGER DEFAULT 0,
    quiz_average_score DECIMAL(5,2),
    assignment_average_score DECIMAL(5,2),
    overall_module_score DECIMAL(5,2),
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    last_accessed_at TIMESTAMP,
    UNIQUE(student_id, module_id, enrollment_id)
);
```

### 3. MODIFIED Tables

#### `course_materials`
- **REMOVED**: `course_id` foreign key
- **CHANGED**: `module_id` is now REQUIRED (NOT NULL)

#### `quizzes`
- **REMOVED**: `course_id` foreign key  
- **CHANGED**: `module_id` is now REQUIRED (NOT NULL)

#### `assignments`
- **REMOVED**: `course_id` foreign key
- **REMOVED**: `module_id` was optional, now REQUIRED

#### `attendances`
- **REMOVED**: `course_id` foreign key
- **ADDED**: `module_id` REQUIRED (NOT NULL)
- **CHANGED**: Unique constraint now `(module_id, student_id, date)`

#### `marks`
- **REMOVED**: `course_id` foreign key
- **ADDED**: `module_id` REQUIRED (NOT NULL)

#### `study_plans`
- **ADDED**: `module_id` (optional) for module-specific study plans

#### `chat_sessions`
- **ADDED**: `module_id` (optional) for module-specific chat sessions

#### `risk_scores`
- **ADDED**: `module_id` (optional) for module-level risk tracking

## Data Migration Strategy

### Step 1: Backup Existing Data
```bash
# Create backup before migration
sqlite3 edumind.db ".backup edumind_backup_pre_migration.db"
```

### Step 2: Create New Schema
```bash
# Use the new schema file
sqlite3 edumind.db < database_schema_refactored.sql
```

### Step 3: Migrate Existing Data

#### Migrate Lecturer Assignments
```sql
-- For each existing course with a lecturer, assign that lecturer 
-- to all modules in that course as primary lecturer
INSERT INTO lecturer_modules (lecturer_id, module_id, is_primary)
SELECT c.lecturer_id, m.id, 1
FROM courses c
JOIN modules m ON m.course_id = c.id
WHERE c.lecturer_id IS NOT NULL;
```

#### Migrate Content to Modules
```sql
-- For content that was at course level but had module_id set
-- Already correct - no migration needed

-- For content that was at course level without module_id:
-- Option A: Create a "General" module for each course and move content there
INSERT INTO modules (course_id, title, description, module_order)
SELECT id, 'General Content', 'Auto-created for migration', 0
FROM courses;

-- Then update content to point to these general modules
-- (requires mapping old course_id to new module_id)
```

#### Create Module Progress Records
```sql
-- For each active enrollment, create progress records for all modules
INSERT INTO student_module_progress (
    student_id, module_id, enrollment_id, 
    completion_status, completion_percentage
)
SELECT 
    e.student_id,
    m.id,
    e.id,
    'not_started',
    0
FROM enrollments e
JOIN modules m ON m.course_id = e.course_id
WHERE e.status = 'active';
```

## API Changes

### Updated Endpoints

#### Course Routes (`/courses`)
- **REMOVED**: `lecturer_id` from course creation/editing
- **ADDED**: `/courses/<id>/modules/create` - Create module in course
- **ADDED**: `/courses/modules/<id>/assign-lecturer` - Assign lecturer to module
- **ADDED**: `/courses/modules/<id>/remove-lecturer/<lecturer_id>` - Remove lecturer from module

#### Content Routes (All Module-Based)

| Old Endpoint | New Endpoint | Notes |
|-------------|--------------|-------|
| `/materials/course/<course_id>` | `/materials/module/<module_id>` | Materials now module-based |
| `/quizzes/course/<course_id>` | `/quizzes/module/<module_id>` | Quizzes now module-based |
| `/attendance/course/<course_id>` | `/attendance/module/<module_id>` | Attendance now module-based |
| `/marks/course/<course_id>` | `/marks/module/<module_id>` | Marks now module-based |
| `/assignments/course/<course_id>/create` | `/assignments/module/<module_id>/create` | Assignments now module-based |

### Access Control Changes

#### New Permission Functions
```python
# Check module-level access (replaces course-level checks)
require_module_access(module_id)

# Check lecturer is assigned to specific module
require_lecturer_assigned_to_module(module_id)

# Check if user can edit content in module
can_edit_module_content(module_id)
```

#### Modified Permission Functions
```python
# Now checks if lecturer is assigned to ANY module in the course
require_lecturer_assigned_to_course(course_id)

# Returns ModuleAccessContext instead of just boolean
require_module_access(module_id)
```

## Frontend Changes

### URL Structure Changes

| Old Pattern | New Pattern |
|-------------|-------------|
| `/courses/<id>/materials` | `/modules/<id>/materials` |
| `/courses/<id>/quizzes` | `/modules/<id>/quizzes` |
| `/courses/<id>/attendance` | `/modules/<id>/attendance` |
| `/courses/<id>/marks` | `/modules/<id>/marks` |

### Template Changes Required

#### Course Detail Page
- **ADD**: Module list with lecturer assignments
- **REMOVE**: Direct content listing (moved to module pages)
- **ADD**: Progress overview across all modules

#### Module Pages (New/Updated)
- `/modules/<id>/` - Module overview
- `/modules/<id>/materials` - Module materials
- `/modules/<id>/quizzes` - Module quizzes  
- `/modules/<id>/assignments` - Module assignments
- `/modules/<id>/attendance` - Module attendance
- `/modules/<id>/marks` - Module marks

### Access Control in Templates
```jinja2
{# Old - check if lecturer owns course #}
{% if course.lecturer_id == current_user.lecturer.id %}

{# New - check if lecturer is assigned to module #}
{% if module.is_lecturer_assigned(current_user.lecturer.id) %}
```

## Model Changes Summary

### Course Model
```python
# REMOVED
lecturer_id = db.Column(db.Integer, db.ForeignKey('lecturers.id'))

# REMOVED Relationships
lecturer = db.relationship('Lecturer', backref='courses')  # OLD
materials = db.relationship('CourseMaterial', ...)  # MOVED to Module
quizzes = db.relationship('Quiz', ...)  # MOVED to Module

# ADDED Methods
def get_lecturers(self):  # Get lecturers through modules
def get_average_progress(self):  # Aggregated from module progress
```

### Module Model (Enhanced)
```python
# ADDED Relationships
materials = db.relationship('CourseMaterial', ...)
quizzes = db.relationship('Quiz', ...)
assignments = db.relationship('Assignment', ...)
attendances = db.relationship('Attendance', ...)
marks = db.relationship('Mark', ...)
lecturer_assignments = db.relationship('LecturerModule', ...)
student_progress = db.relationship('StudentModuleProgress', ...)

# ADDED Properties
@property
def lecturers(self):  # All assigned lecturers
@property  
def primary_lecturer(self):  # Primary lecturer

# ADDED Methods
def is_lecturer_assigned(self, lecturer_id):
```

### Lecturer Model (Enhanced)
```python
# REMOVED Relationships
courses = db.relationship('Course', ...)  # OLD - now through modules

# ADDED Relationships
module_assignments = db.relationship('LecturerModule', ...)

# ADDED Methods
def get_assigned_modules(self, course_id=None):
def get_teaching_courses(self):  # Through module assignments
def is_assigned_to_module(self, module_id):
def is_assigned_to_course(self, course_id):
def assign_to_module(self, module_id, is_primary=False):
def unassign_from_module(self, module_id):
```

## Security & Validation

### New Data Integrity Rules

1. **Student Access**: Students can only access modules in courses they're enrolled in
2. **Lecturer Assignment**: Lecturers must be explicitly assigned to modules
3. **Content Creation**: Content can only be created in modules where lecturer is assigned
4. **Progress Tracking**: Module progress records are auto-created on enrollment

### Validation Functions
```python
# In models
def can_access(self, student):  # For content items
def can_record(self, user):  # For marks/attendance

# In access_control utility
def require_module_access(module_id):
def can_edit_module_content(module_id):
```

## Rollback Plan

If migration fails:

1. Stop application
2. Restore from backup:
   ```bash
   cp edumind_backup_pre_migration.db edumind.db
   ```
3. Revert code to previous version (git)
4. Restart application

## Testing Checklist

### Enrollment Flow
- [ ] Student can enroll in course
- [ ] Module progress records auto-created
- [ ] Student can view enrolled course modules
- [ ] Student cannot access modules in non-enrolled courses

### Lecturer Assignment
- [ ] Admin can assign lecturers to modules
- [ ] Lecturer can only access assigned modules
- [ ] Lecturer can create content in assigned modules
- [ ] Lecturer cannot access unassigned modules

### Content Creation
- [ ] Materials can be uploaded to modules
- [ ] Quizzes can be created in modules
- [ ] Assignments can be created in modules
- [ ] Attendance can be recorded for modules
- [ ] Marks can be entered for module assessments

### Progress Tracking
- [ ] Module progress updates when student views materials
- [ ] Module progress updates when student completes quiz
- [ ] Module progress updates when student submits assignment
- [ ] Overall course progress aggregates module progress

## Post-Migration Verification

Run these queries to verify migration:

```sql
-- Verify lecturer assignments migrated
SELECT COUNT(*) as lecturer_module_assignments FROM lecturer_modules;

-- Verify no orphaned content
SELECT 'Materials without modules' as check_item, COUNT(*) as count 
FROM course_materials WHERE module_id IS NULL
UNION ALL
SELECT 'Quizzes without modules', COUNT(*) FROM quizzes WHERE module_id IS NULL
UNION ALL
SELECT 'Assignments without modules', COUNT(*) FROM assignments WHERE module_id IS NULL;

-- Verify progress records created
SELECT COUNT(*) as progress_records FROM student_module_progress;
```

## Support

For issues during migration:
1. Check application logs
2. Verify database schema matches new models
3. Ensure all foreign key constraints are satisfied
4. Review data migration scripts for completeness

---

**Migration Date**: 2026-04-02  
**Schema Version**: 2.0 - Module-Based Architecture  
**Compatible With**: EduMind v2.0+