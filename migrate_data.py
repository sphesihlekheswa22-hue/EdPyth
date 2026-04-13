#!/usr/bin/env python
"""
Data Migration Script for Course-Based Architecture Refactor

This script migrates existing data to the new Course → Module → Content hierarchy.

Migration Steps:
1. Create default modules for courses that don't have modules
2. Create lecturer_modules records from old course.lecturer_id
3. Move course-level content (materials, quizzes, assignments, attendance, marks) to modules
4. Create student_module_progress records for all enrollments

Usage:
    python migrate_data.py [--dry-run] [--backup]

Options:
    --dry-run   Preview changes without applying them
    --backup    Create a SQL backup before migration
"""

import os
import sys
import argparse
from datetime import datetime
from typing import List, Dict, Optional, Tuple

# Add the app to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import (
    Course, Module, Lecturer, LecturerModule, Enrollment,
    CourseMaterial, Quiz, Assignment, Attendance, Mark,
    StudentModuleProgress, Student
)


class DataMigrator:
    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run
        self.stats = {
            'modules_created': 0,
            'lecturer_assignments_created': 0,
            'materials_migrated': 0,
            'quizzes_migrated': 0,
            'assignments_migrated': 0,
            'attendance_migrated': 0,
            'marks_migrated': 0,
            'progress_records_created': 0,
            'errors': []
        }
    
    def log(self, message: str, level: str = 'info'):
        """Log a message with timestamp."""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        prefix = {
            'info': '[INFO]',
            'success': '[OK]',
            'warning': '[WARN]',
            'error': '[ERR]',
            'dry': '[DRY]'
        }.get(level, '[INFO]')
        
        dry_prefix = '[DRY RUN] ' if self.dry_run else ''
        print(f"{prefix} [{timestamp}] {dry_prefix}{message}")
    
    def error(self, message: str, exception: Optional[Exception] = None):
        """Log an error and add to stats."""
        self.log(message, 'error')
        if exception:
            self.stats['errors'].append(f"{message}: {str(exception)}")
    
    def create_default_modules(self) -> Dict[int, int]:
        """
        Create default modules for courses that don't have any modules.
        Returns a mapping of course_id -> module_id.
        """
        course_module_map = {}
        
        # Get all courses without modules
        courses_without_modules = db.session.query(Course).outerjoin(
            Module, Course.id == Module.course_id
        ).group_by(Course.id).having(db.func.count(Module.id) == 0).all()
        
        self.log(f"Found {len(courses_without_modules)} courses without modules", 'warning')
        
        for course in courses_without_modules:
            try:
                module = Module(
                    course_id=course.id,
                    title=f"{course.name} - Main Module",
                    description=f"Default module created during migration for {course.code}",
                    order=1
                )
                
                if not self.dry_run:
                    db.session.add(module)
                    db.session.flush()  # Get the ID without committing
                    db.session.refresh(module)
                    course_module_map[course.id] = module.id
                    self.stats['modules_created'] += 1
                else:
                    # In dry-run, use a placeholder ID
                    course_module_map[course.id] = -course.id
                
                self.log(f"Created default module for {course.code}: {module.title}", 'success')
                
            except Exception as e:
                self.error(f"Failed to create module for course {course.id}", e)
        
        if not self.dry_run:
            db.session.commit()
        
        # Also add existing modules to the map
        existing_modules = Module.query.all()
        for module in existing_modules:
            if module.course_id not in course_module_map:
                course_module_map[module.course_id] = module.id
        
        return course_module_map
    
    def migrate_lecturer_assignments(self, course_module_map: Dict[int, int]):
        """
        Create lecturer_modules records from old course.lecturer_id.
        """
        self.log("Migrating lecturer assignments...", 'info')
        
        # Get all modules and their courses
        for course_id, module_id in course_module_map.items():
            try:
                # Check if this course had a lecturer_id in the old schema
                # We need to query the raw database since the model no longer has lecturer_id
                result = db.session.execute(
                    db.text("SELECT lecturer_id FROM courses WHERE id = :course_id"),
                    {'course_id': course_id}
                ).fetchone()
                
                if result and result[0]:
                    lecturer_id = result[0]
                    
                    # Check if lecturer exists
                    lecturer = Lecturer.query.get(lecturer_id)
                    if not lecturer:
                        self.log(f"Lecturer {lecturer_id} not found for course {course_id}", 'warning')
                        continue
                    
                    # Check if assignment already exists
                    existing = LecturerModule.query.filter_by(
                        lecturer_id=lecturer_id,
                        module_id=module_id
                    ).first()
                    
                    if not existing:
                        lm = LecturerModule(
                            lecturer_id=lecturer_id,
                            module_id=module_id,
                            is_primary=True
                        )
                        
                        if not self.dry_run:
                            db.session.add(lm)
                            self.stats['lecturer_assignments_created'] += 1
                        
                        self.log(
                            f"Assigned lecturer {lecturer.employee_id} to module {module_id}",
                            'success'
                        )
                        
            except Exception as e:
                self.error(f"Failed to migrate lecturer for course {course_id}", e)
        
        if not self.dry_run:
            db.session.commit()
    
    def migrate_materials(self, course_module_map: Dict[int, int]):
        """
        Move course-level materials to the default module for each course.
        """
        self.log("Migrating materials...", 'info')
        
        # Get materials that still reference course_id directly
        # We need to check the raw database since the model now uses module_id
        try:
            # Check if there are any materials with course_id
            result = db.session.execute(
                db.text("""
                    SELECT id, course_id, title 
                    FROM course_materials 
                    WHERE course_id IS NOT NULL 
                    AND (module_id IS NULL OR module_id = 0)
                """)
            ).fetchall()
            
            for material_id, course_id, title in result:
                if course_id in course_module_map:
                    module_id = course_module_map[course_id]
                    
                    if not self.dry_run:
                        db.session.execute(
                            db.text("""
                                UPDATE course_materials 
                                SET module_id = :module_id 
                                WHERE id = :material_id
                            """),
                            {'module_id': module_id, 'material_id': material_id}
                        )
                        self.stats['materials_migrated'] += 1
                    
                    self.log(f"Migrated material '{title}' to module {module_id}", 'success')
                else:
                    self.log(f"No module found for course {course_id}, material '{title}'", 'warning')
            
            if not self.dry_run:
                db.session.commit()
                
        except Exception as e:
            self.error("Failed to migrate materials", e)
    
    def migrate_quizzes(self, course_module_map: Dict[int, int]):
        """
        Move course-level quizzes to the default module for each course.
        """
        self.log("Migrating quizzes...", 'info')
        
        try:
            result = db.session.execute(
                db.text("""
                    SELECT id, course_id, title 
                    FROM quizzes 
                    WHERE course_id IS NOT NULL 
                    AND (module_id IS NULL OR module_id = 0)
                """)
            ).fetchall()
            
            for quiz_id, course_id, title in result:
                if course_id in course_module_map:
                    module_id = course_module_map[course_id]
                    
                    if not self.dry_run:
                        db.session.execute(
                            db.text("""
                                UPDATE quizzes 
                                SET module_id = :module_id 
                                WHERE id = :quiz_id
                            """),
                            {'module_id': module_id, 'quiz_id': quiz_id}
                        )
                        self.stats['quizzes_migrated'] += 1
                    
                    self.log(f"Migrated quiz '{title}' to module {module_id}", 'success')
            
            if not self.dry_run:
                db.session.commit()
                
        except Exception as e:
            self.error("Failed to migrate quizzes", e)
    
    def migrate_assignments(self, course_module_map: Dict[int, int]):
        """
        Move course-level assignments to the default module for each course.
        """
        self.log("Migrating assignments...", 'info')
        
        try:
            result = db.session.execute(
                db.text("""
                    SELECT id, course_id, title 
                    FROM assignments 
                    WHERE course_id IS NOT NULL 
                    AND (module_id IS NULL OR module_id = 0)
                """)
            ).fetchall()
            
            for assignment_id, course_id, title in result:
                if course_id in course_module_map:
                    module_id = course_module_map[course_id]
                    
                    if not self.dry_run:
                        db.session.execute(
                            db.text("""
                                UPDATE assignments 
                                SET module_id = :module_id 
                                WHERE id = :assignment_id
                            """),
                            {'module_id': module_id, 'assignment_id': assignment_id}
                        )
                        self.stats['assignments_migrated'] += 1
                    
                    self.log(f"Migrated assignment '{title}' to module {module_id}", 'success')
            
            if not self.dry_run:
                db.session.commit()
                
        except Exception as e:
            self.error("Failed to migrate assignments", e)
    
    def migrate_attendance(self, course_module_map: Dict[int, int]):
        """
        Move course-level attendance records to the default module for each course.
        """
        self.log("Migrating attendance records...", 'info')
        
        try:
            result = db.session.execute(
                db.text("""
                    SELECT id, course_id, date, student_id
                    FROM attendance 
                    WHERE course_id IS NOT NULL 
                    AND (module_id IS NULL OR module_id = 0)
                """)
            ).fetchall()
            
            for record_id, course_id, date, student_id in result:
                if course_id in course_module_map:
                    module_id = course_module_map[course_id]
                    
                    if not self.dry_run:
                        db.session.execute(
                            db.text("""
                                UPDATE attendance 
                                SET module_id = :module_id 
                                WHERE id = :record_id
                            """),
                            {'module_id': module_id, 'record_id': record_id}
                        )
                        self.stats['attendance_migrated'] += 1
                    
                    self.log(f"Migrated attendance record {record_id} to module {module_id}", 'success')
            
            if not self.dry_run:
                db.session.commit()
                
        except Exception as e:
            self.error("Failed to migrate attendance", e)
    
    def migrate_marks(self, course_module_map: Dict[int, int]):
        """
        Move course-level marks to the default module for each course.
        """
        self.log("Migrating marks...", 'info')
        
        try:
            result = db.session.execute(
                db.text("""
                    SELECT id, course_id, assessment_name, student_id
                    FROM marks 
                    WHERE course_id IS NOT NULL 
                    AND (module_id IS NULL OR module_id = 0)
                """)
            ).fetchall()
            
            for mark_id, course_id, assessment_name, student_id in result:
                if course_id in course_module_map:
                    module_id = course_module_map[course_id]
                    
                    if not self.dry_run:
                        db.session.execute(
                            db.text("""
                                UPDATE marks 
                                SET module_id = :module_id 
                                WHERE id = :mark_id
                            """),
                            {'module_id': module_id, 'mark_id': mark_id}
                        )
                        self.stats['marks_migrated'] += 1
                    
                    self.log(f"Migrated mark '{assessment_name}' to module {module_id}", 'success')
            
            if not self.dry_run:
                db.session.commit()
                
        except Exception as e:
            self.error("Failed to migrate marks", e)
    
    def create_student_progress_records(self, course_module_map: Dict[int, int]):
        """
        Create StudentModuleProgress records for all active enrollments.
        """
        self.log("Creating student progress records...", 'info')
        
        enrollments = Enrollment.query.filter_by(status='active').all()
        
        for enrollment in enrollments:
            try:
                course_id = enrollment.course_id
                if course_id not in course_module_map:
                    continue
                
                module_id = course_module_map[course_id]
                
                # Check if progress record already exists
                existing = StudentModuleProgress.query.filter_by(
                    enrollment_id=enrollment.id,
                    module_id=module_id
                ).first()
                
                if not existing:
                    progress = StudentModuleProgress(
                        enrollment_id=enrollment.id,
                        module_id=module_id,
                        completion_status='not_started',
                        completion_percentage=0
                    )
                    
                    if not self.dry_run:
                        db.session.add(progress)
                        self.stats['progress_records_created'] += 1
                    
                    self.log(
                        f"Created progress record for student {enrollment.student_id} "
                        f"in module {module_id}",
                        'success'
                    )
                    
            except Exception as e:
                self.error(
                    f"Failed to create progress for enrollment {enrollment.id}",
                    e
                )
        
        if not self.dry_run:
            db.session.commit()
    
    def run_migration(self):
        """Run the complete migration process."""
        self.log("=" * 60)
        self.log("STARTING DATA MIGRATION")
        self.log("=" * 60)
        
        if self.dry_run:
            self.log("RUNNING IN DRY-RUN MODE - No changes will be saved", 'dry')
        
        try:
            # Step 1: Create default modules
            self.log("Step 1: Creating default modules for courses...")
            course_module_map = self.create_default_modules()
            self.log(f"Course to Module mapping: {course_module_map}", 'info')
            
            if not course_module_map:
                self.log("No modules to process. Migration complete.")
                return
            
            # Step 2: Migrate lecturer assignments
            self.log("Step 2: Migrating lecturer assignments...")
            self.migrate_lecturer_assignments(course_module_map)
            
            # Step 3: Migrate content
            self.log("Step 3: Migrating course content...")
            self.migrate_materials(course_module_map)
            self.migrate_quizzes(course_module_map)
            self.migrate_assignments(course_module_map)
            self.migrate_attendance(course_module_map)
            self.migrate_marks(course_module_map)
            
            # Step 4: Create progress records
            self.log("Step 4: Creating student progress records...")
            self.create_student_progress_records(course_module_map)
            
            # Print summary
            self.print_summary()
            
        except Exception as e:
            self.error("Migration failed", e)
            if not self.dry_run:
                db.session.rollback()
            raise
    
    def print_summary(self):
        """Print migration summary."""
        self.log("=" * 60)
        self.log("MIGRATION SUMMARY")
        self.log("=" * 60)
        
        summary = [
            f"Modules created: {self.stats['modules_created']}",
            f"Lecturer assignments created: {self.stats['lecturer_assignments_created']}",
            f"Materials migrated: {self.stats['materials_migrated']}",
            f"Quizzes migrated: {self.stats['quizzes_migrated']}",
            f"Assignments migrated: {self.stats['assignments_migrated']}",
            f"Attendance records migrated: {self.stats['attendance_migrated']}",
            f"Marks migrated: {self.stats['marks_migrated']}",
            f"Progress records created: {self.stats['progress_records_created']}",
        ]
        
        for item in summary:
            self.log(item, 'success')
        
        if self.stats['errors']:
            self.log(f"\nErrors encountered: {len(self.stats['errors'])}", 'error')
            for error in self.stats['errors'][:10]:  # Show first 10 errors
                self.log(f"  - {error}", 'error')
            if len(self.stats['errors']) > 10:
                self.log(f"  ... and {len(self.stats['errors']) - 10} more", 'error')


def create_backup():
    """Create a SQL backup of the database."""
    import subprocess
    from app.config import Config
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_file = f"backup_{timestamp}.sql"
    
    # Get database URL from config
    db_url = Config.SQLALCHEMY_DATABASE_URI
    
    print(f"Creating backup: {backup_file}")
    
    try:
        # This is a simple example - adjust based on your database type
        if 'sqlite' in db_url:
            # For SQLite, just copy the file
            import shutil
            db_path = db_url.replace('sqlite:///', '')
            shutil.copy2(db_path, backup_file)
        else:
            # For PostgreSQL/MySQL, use appropriate dump command
            print("Backup for non-SQLite databases not implemented in this script.")
            print("Please manually backup your database before running migration.")
            return None
        
        print(f"Backup created: {backup_file}")
        return backup_file
        
    except Exception as e:
        print(f"Backup failed: {e}")
        return None


def main():
    parser = argparse.ArgumentParser(
        description='Migrate data to new Course → Module → Content hierarchy'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Preview changes without applying them'
    )
    parser.add_argument(
        '--backup',
        action='store_true',
        help='Create a database backup before migration'
    )
    
    args = parser.parse_args()
    
    # Create Flask app context
    app = create_app()
    
    with app.app_context():
        if args.backup:
            create_backup()
        
        migrator = DataMigrator(dry_run=args.dry_run)
        migrator.run_migration()


if __name__ == '__main__':
    main()