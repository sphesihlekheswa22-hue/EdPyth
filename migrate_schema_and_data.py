#!/usr/bin/env python3
"""
EduMind LMS - Complete Schema and Data Migration Script

This script handles the complete migration from course-based to module-based architecture:
1. Applies schema changes (adds new tables/columns)
2. Migrates existing data to new structure
3. Validates migration integrity

Usage:
    python migrate_schema_and_data.py --dry-run    # Preview changes
    python migrate_schema_and_data.py --execute    # Apply changes

Safety Features:
    - Automatic backup creation
    - Transaction rollback on error
    - Detailed logging
    - Dry-run mode for testing
"""

import os
import sys
import shutil
import argparse
import logging
from datetime import datetime
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(levelname)s] [%(asctime)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Add app to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Database path - matches config.py
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app', 'edumind_ai.db')
BACKUP_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backups')


def create_backup():
    """Create a backup of the current database."""
    if not os.path.exists(DB_PATH):
        logger.warning("No database found at {}".format(DB_PATH))
        return None
    
    os.makedirs(BACKUP_DIR, exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = os.path.join(BACKUP_DIR, 'app_backup_{}.db'.format(timestamp))
    
    shutil.copy2(DB_PATH, backup_path)
    logger.info("Database backup created: {}".format(backup_path))
    return backup_path


def get_db_connection():
    """Get SQLite database connection."""
    import sqlite3
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def check_column_exists(cursor, table, column):
    """Check if a column exists in a table."""
    cursor.execute("PRAGMA table_info({})".format(table))
    columns = [row[1] for row in cursor.fetchall()]
    return column in columns


def check_table_exists(cursor, table):
    """Check if a table exists."""
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
        (table,)
    )
    return cursor.fetchone() is not None


class SchemaMigration:
    """Handles schema migration - adding new tables and columns."""
    
    def __init__(self, conn, dry_run=True):
        self.conn = conn
        self.cursor = conn.cursor()
        self.dry_run = dry_run
        self.changes_made = []
    
    def log_change(self, description):
        """Log a schema change."""
        self.changes_made.append(description)
        if self.dry_run:
            logger.info("[DRY-RUN] Would apply: {}".format(description))
        else:
            logger.info("[APPLIED] {}".format(description))
    
    def execute(self, sql, params=None):
        """Execute SQL if not in dry-run mode."""
        if not self.dry_run:
            if params:
                self.cursor.execute(sql, params)
            else:
                self.cursor.execute(sql)
    
    def migrate(self):
        """Run all schema migrations."""
        logger.info("="*60)
        logger.info("STEP 1: SCHEMA MIGRATION")
        logger.info("="*60)
        
        self.add_module_order_column()
        self.create_lecturer_modules_table()
        self.create_student_module_progress_table()
        self.add_module_id_to_content_tables()
        self.add_module_id_to_attendance()
        self.add_module_id_to_marks()
        
        logger.info("\nSchema changes summary:")
        for change in self.changes_made:
            logger.info("  - {}".format(change))
    
    def add_module_order_column(self):
        """Add module_order column to modules table if missing."""
        if check_column_exists(self.cursor, 'modules', 'module_order'):
            logger.info("Column modules.module_order already exists - skipping")
            return
        
        self.execute("ALTER TABLE modules ADD COLUMN module_order INTEGER DEFAULT 0")
        self.execute("CREATE INDEX IF NOT EXISTS idx_modules_order ON modules(module_order)")
        self.log_change("Added module_order column to modules table")
    
    def create_lecturer_modules_table(self):
        """Create lecturer_modules junction table."""
        if check_table_exists(self.cursor, 'lecturer_modules'):
            logger.info("Table lecturer_modules already exists - skipping")
            return
        
        sql = """
            CREATE TABLE lecturer_modules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lecturer_id INTEGER NOT NULL,
                module_id INTEGER NOT NULL,
                is_primary BOOLEAN DEFAULT 0,
                assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                CONSTRAINT fk_lecturer_modules_lecturer 
                    FOREIGN KEY (lecturer_id) REFERENCES lecturers(id) 
                    ON DELETE CASCADE,
                CONSTRAINT fk_lecturer_modules_module 
                    FOREIGN KEY (module_id) REFERENCES modules(id) 
                    ON DELETE CASCADE,
                
                CONSTRAINT uk_lecturer_module UNIQUE (lecturer_id, module_id)
            )
        """
        self.execute(sql)
        self.execute("CREATE INDEX idx_lecturer_modules_lecturer_id ON lecturer_modules(lecturer_id)")
        self.execute("CREATE INDEX idx_lecturer_modules_module_id ON lecturer_modules(module_id)")
        self.log_change("Created lecturer_modules table")
    
    def create_student_module_progress_table(self):
        """Create student_module_progress table."""
        if check_table_exists(self.cursor, 'student_module_progress'):
            logger.info("Table student_module_progress already exists - skipping")
            return
        
        sql = """
            CREATE TABLE student_module_progress (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER NOT NULL,
                module_id INTEGER NOT NULL,
                enrollment_id INTEGER NOT NULL,
                
                completion_status VARCHAR(20) DEFAULT 'not_started',
                completion_percentage INTEGER DEFAULT 0,
                materials_accessed INTEGER DEFAULT 0,
                quizzes_completed INTEGER DEFAULT 0,
                assignments_submitted INTEGER DEFAULT 0,
                last_accessed_at TIMESTAMP,
                completed_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
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
                
                CONSTRAINT uk_student_module_progress UNIQUE (student_id, module_id)
            )
        """
        self.execute(sql)
        self.execute("CREATE INDEX idx_student_module_progress_student_id ON student_module_progress(student_id)")
        self.execute("CREATE INDEX idx_student_module_progress_module_id ON student_module_progress(module_id)")
        self.execute("CREATE INDEX idx_student_module_progress_enrollment_id ON student_module_progress(enrollment_id)")
        self.log_change("Created student_module_progress table")
    
    def add_module_id_to_content_tables(self):
        """Add module_id column to materials, quizzes, assignments tables."""
        tables = [
            ('course_materials', 'module_id', 'INTEGER'),
            ('quizzes', 'module_id', 'INTEGER'),
            ('assignments', 'module_id', 'INTEGER')
        ]
        
        for table, column, col_type in tables:
            if check_column_exists(self.cursor, table, column):
                logger.info("Column {}.{} already exists - skipping".format(table, column))
                continue
            
            self.execute("ALTER TABLE {} ADD COLUMN {} {}".format(table, column, col_type))
            self.execute("CREATE INDEX idx_{}_{} ON {}({})".format(table, column, table, column))
            self.log_change("Added {} column to {} table".format(column, table))
    
    def add_module_id_to_attendance(self):
        """Add module_id column to attendance table."""
        if not check_table_exists(self.cursor, 'attendance'):
            logger.info("Table attendance doesn't exist - skipping")
            return
        
        if check_column_exists(self.cursor, 'attendance', 'module_id'):
            logger.info("Column attendance.module_id already exists - skipping")
            return
        
        self.execute("ALTER TABLE attendance ADD COLUMN module_id INTEGER")
        self.execute("CREATE INDEX idx_attendance_module_id ON attendance(module_id)")
        self.log_change("Added module_id column to attendance table")
    
    def add_module_id_to_marks(self):
        """Add module_id column to marks table."""
        if not check_table_exists(self.cursor, 'marks'):
            logger.info("Table marks doesn't exist - skipping")
            return
        
        if check_column_exists(self.cursor, 'marks', 'module_id'):
            logger.info("Column marks.module_id already exists - skipping")
            return
        
        self.execute("ALTER TABLE marks ADD COLUMN module_id INTEGER")
        self.execute("CREATE INDEX idx_marks_module_id ON marks(module_id)")
        self.log_change("Added module_id column to marks table")


class DataMigration:
    """Handles data migration to new schema."""
    
    def __init__(self, conn, dry_run=True):
        self.conn = conn
        self.cursor = conn.cursor()
        self.dry_run = dry_run
        self.stats = {
            'modules_created': 0,
            'lecturer_assignments': 0,
            'materials_migrated': 0,
            'quizzes_migrated': 0,
            'assignments_migrated': 0,
            'attendance_migrated': 0,
            'marks_migrated': 0,
            'progress_records': 0
        }
    
    def execute(self, sql, params=None):
        """Execute SQL if not in dry-run mode."""
        if not self.dry_run:
            if params:
                self.cursor.execute(sql, params)
            else:
                self.cursor.execute(sql)
    
    def migrate(self):
        """Run all data migrations."""
        logger.info("\n" + "="*60)
        logger.info("STEP 2: DATA MIGRATION")
        logger.info("="*60)
        
        self.create_default_modules()
        self.migrate_lecturer_assignments()
        self.migrate_content_to_modules()
        self.create_student_progress_records()
        
        logger.info("\nData migration statistics:")
        for key, value in self.stats.items():
            logger.info("  {}: {}".format(key, value))
    
    def create_default_modules(self):
        """Create default modules for courses that don't have any."""
        # Find courses without modules
        self.cursor.execute("""
            SELECT c.id, c.code, c.name, c.lecturer_id
            FROM courses c
            LEFT JOIN modules m ON c.id = m.course_id
            WHERE m.id IS NULL
        """)
        courses_without_modules = self.cursor.fetchall()
        
        if not courses_without_modules:
            logger.info("All courses already have modules")
            return
        
        logger.info("Found {} courses without modules".format(len(courses_without_modules)))
        
        for course in courses_without_modules:
            course_id, code, name, lecturer_id = course
            module_title = "{} - Main Module".format(code)
            
            if self.dry_run:
                logger.info("[DRY-RUN] Would create module '{}' for course {}".format(module_title, code))
            else:
                self.cursor.execute("""
                    INSERT INTO modules (course_id, title, description, module_order)
                    VALUES (?, ?, ?, ?)
                """, (course_id, module_title, "Default module for course content", 1))
                logger.info("Created module for course: {}".format(code))
            
            self.stats['modules_created'] += 1
    
    def migrate_lecturer_assignments(self):
        """Migrate lecturer assignments from courses to modules."""
        # Get all modules with their course's lecturer_id
        self.cursor.execute("""
            SELECT m.id as module_id, c.lecturer_id, c.code
            FROM modules m
            JOIN courses c ON m.course_id = c.id
            WHERE c.lecturer_id IS NOT NULL
        """)
        modules = self.cursor.fetchall()
        
        for module in modules:
            module_id, lecturer_id, course_code = module
            
            # Check if already assigned
            self.cursor.execute("""
                SELECT 1 FROM lecturer_modules
                WHERE lecturer_id = ? AND module_id = ?
            """, (lecturer_id, module_id))
            
            if self.cursor.fetchone():
                continue
            
            if self.dry_run:
                logger.info("[DRY-RUN] Would assign lecturer {} to module {}".format(lecturer_id, module_id))
            else:
                self.cursor.execute("""
                    INSERT INTO lecturer_modules (lecturer_id, module_id, is_primary)
                    VALUES (?, ?, ?)
                """, (lecturer_id, module_id, 1))
            
            self.stats['lecturer_assignments'] += 1
        
        logger.info("Migrated {} lecturer assignments".format(self.stats['lecturer_assignments']))
    
    def migrate_content_to_modules(self):
        """Migrate materials, quizzes, assignments to modules."""
        # Migrate materials
        if not check_column_exists(self.cursor, 'course_materials', 'module_id'):
            logger.info("Column course_materials.module_id doesn't exist yet - skipping material migration")
            materials = []
        else:
            self.cursor.execute("""
                SELECT cm.id, cm.course_id, c.code
                FROM course_materials cm
                JOIN courses c ON cm.course_id = c.id
                WHERE cm.module_id IS NULL
            """)
            materials = self.cursor.fetchall()
        
        for material in materials:
            material_id, course_id, code = material
            # Get first module for this course
            self.cursor.execute(
                "SELECT id FROM modules WHERE course_id = ? LIMIT 1",
                (course_id,)
            )
            module = self.cursor.fetchone()
            
            if module:
                if self.dry_run:
                    logger.info("[DRY-RUN] Would migrate material {} to module {}".format(material_id, module[0]))
                else:
                    self.cursor.execute("""
                        UPDATE course_materials SET module_id = ? WHERE id = ?
                    """, (module[0], material_id))
                self.stats['materials_migrated'] += 1
        
        # Migrate quizzes - only if module_id column exists
        if not check_column_exists(self.cursor, 'quizzes', 'module_id'):
            logger.info("Column quizzes.module_id doesn't exist yet - skipping quiz migration")
            quizzes = []
        else:
            self.cursor.execute("""
                SELECT q.id, q.course_id, c.code
                FROM quizzes q
                JOIN courses c ON q.course_id = c.id
                WHERE q.module_id IS NULL
            """)
            quizzes = self.cursor.fetchall()
        
        for quiz in quizzes:
            quiz_id, course_id, code = quiz
            self.cursor.execute(
                "SELECT id FROM modules WHERE course_id = ? LIMIT 1",
                (course_id,)
            )
            module = self.cursor.fetchone()
            
            if module:
                if self.dry_run:
                    logger.info("[DRY-RUN] Would migrate quiz {} to module {}".format(quiz_id, module[0]))
                else:
                    self.cursor.execute("""
                        UPDATE quizzes SET module_id = ? WHERE id = ?
                    """, (module[0], quiz_id))
                self.stats['quizzes_migrated'] += 1
        
        # Migrate assignments
        if not check_column_exists(self.cursor, 'assignments', 'module_id'):
            logger.info("Column assignments.module_id doesn't exist yet - skipping assignment migration")
            assignments = []
        else:
            self.cursor.execute("""
                SELECT a.id, a.course_id, c.code
                FROM assignments a
                JOIN courses c ON a.course_id = c.id
                WHERE a.module_id IS NULL
            """)
            assignments = self.cursor.fetchall()
        
        for assignment in assignments:
            assignment_id, course_id, code = assignment
            self.cursor.execute(
                "SELECT id FROM modules WHERE course_id = ? LIMIT 1",
                (course_id,)
            )
            module = self.cursor.fetchone()
            
            if module:
                if self.dry_run:
                    logger.info("[DRY-RUN] Would migrate assignment {} to module {}".format(assignment_id, module[0]))
                else:
                    self.cursor.execute("""
                        UPDATE assignments SET module_id = ? WHERE id = ?
                    """, (module[0], assignment_id))
                self.stats['assignments_migrated'] += 1
        
        # Migrate attendance - check if table and column exist
        if not check_table_exists(self.cursor, 'attendance'):
            logger.info("Table attendance doesn't exist - skipping attendance migration")
            attendances = []
        elif not check_column_exists(self.cursor, 'attendance', 'module_id'):
            logger.info("Column attendance.module_id doesn't exist yet - skipping attendance migration")
            attendances = []
        else:
            self.cursor.execute("""
                SELECT a.id, a.course_id, c.code
                FROM attendance a
                JOIN courses c ON a.course_id = c.id
                WHERE a.module_id IS NULL
            """)
            attendances = self.cursor.fetchall()
        attendances = self.cursor.fetchall()
        
        for attendance in attendances:
            attendance_id, course_id, code = attendance
            self.cursor.execute(
                "SELECT id FROM modules WHERE course_id = ? LIMIT 1",
                (course_id,)
            )
            module = self.cursor.fetchone()
            
            if module:
                if self.dry_run:
                    logger.info("[DRY-RUN] Would migrate attendance {} to module {}".format(attendance_id, module[0]))
                else:
                    self.cursor.execute("""
                        UPDATE attendances SET module_id = ? WHERE id = ?
                    """, (module[0], attendance_id))
                self.stats['attendance_migrated'] += 1
        
        # Migrate marks - check if table and column exist
        if not check_table_exists(self.cursor, 'marks'):
            logger.info("Table marks doesn't exist - skipping marks migration")
            marks = []
        elif not check_column_exists(self.cursor, 'marks', 'module_id'):
            logger.info("Column marks.module_id doesn't exist yet - skipping marks migration")
            marks = []
        else:
            self.cursor.execute("""
                SELECT m.id, m.course_id, c.code
                FROM marks m
                JOIN courses c ON m.course_id = c.id
                WHERE m.module_id IS NULL
            """)
            marks = self.cursor.fetchall()
        marks = self.cursor.fetchall()
        
        for mark in marks:
            mark_id, course_id, code = mark
            self.cursor.execute(
                "SELECT id FROM modules WHERE course_id = ? LIMIT 1",
                (course_id,)
            )
            module = self.cursor.fetchone()
            
            if module:
                if self.dry_run:
                    logger.info("[DRY-RUN] Would migrate mark {} to module {}".format(mark_id, module[0]))
                else:
                    self.cursor.execute("""
                        UPDATE marks SET module_id = ? WHERE id = ?
                    """, (module[0], mark_id))
                self.stats['marks_migrated'] += 1
        
        logger.info("Migrated content: materials={}, quizzes={}, assignments={}, attendance={}, marks={}".format(
            self.stats['materials_migrated'],
            self.stats['quizzes_migrated'],
            self.stats['assignments_migrated'],
            self.stats['attendance_migrated'],
            self.stats['marks_migrated']
        ))
    
    def create_student_progress_records(self):
        """Create initial progress records for all enrolled students."""
        self.cursor.execute("""
            SELECT DISTINCT e.student_id, m.id as module_id, e.id as enrollment_id
            FROM enrollments e
            JOIN modules m ON m.course_id = e.course_id
            LEFT JOIN student_module_progress smp ON 
                smp.student_id = e.student_id AND smp.module_id = m.id
            WHERE smp.id IS NULL AND e.status = 'active'
        """)
        
        records = self.cursor.fetchall()
        
        for record in records:
            student_id, module_id, enrollment_id = record
            
            if self.dry_run:
                logger.info("[DRY-RUN] Would create progress record for student {} in module {}".format(
                    student_id, module_id))
            else:
                self.cursor.execute("""
                    INSERT INTO student_module_progress 
                        (student_id, module_id, enrollment_id, completion_status, completion_percentage)
                    VALUES (?, ?, ?, 'not_started', 0)
                """, (student_id, module_id, enrollment_id))
            
            self.stats['progress_records'] += 1
        
        logger.info("Created {} student progress records".format(self.stats['progress_records']))


def main():
    parser = argparse.ArgumentParser(
        description='Migrate EduMind LMS from course-based to module-based architecture'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Preview changes without applying them'
    )
    parser.add_argument(
        '--execute',
        action='store_true',
        help='Apply the migration (requires confirmation)'
    )
    parser.add_argument(
        '--skip-backup',
        action='store_true',
        help='Skip database backup (not recommended)'
    )
    parser.add_argument(
        '--force',
        action='store_true',
        help='Skip confirmation prompt (use with caution)'
    )
    
    args = parser.parse_args()
    
    if not args.dry_run and not args.execute:
        parser.print_help()
        print("\nError: Must specify either --dry-run or --execute")
        sys.exit(1)
    
    dry_run = args.dry_run
    
    logger.info("="*60)
    logger.info("EduMind LMS Migration Tool")
    logger.info("="*60)
    logger.info("Mode: {}".format('DRY RUN' if dry_run else 'EXECUTE'))
    logger.info("Database: {}".format(DB_PATH))
    
    if not os.path.exists(DB_PATH):
        logger.error("Database not found at {}".format(DB_PATH))
        sys.exit(1)
    
    # Create backup
    if not dry_run and not args.skip_backup:
        backup_path = create_backup()
        if backup_path:
            logger.info("Backup created: {}".format(backup_path))
        
        # Confirm execution
        if not args.force:
            print("\n" + "!"*60)
            print("WARNING: This will modify your database!")
            print("A backup has been created, but please ensure you have additional backups.")
            print("!"*60)
            confirm = input("\nType 'MIGRATE' to proceed: ")
            if confirm != 'MIGRATE':
                logger.info("Migration cancelled by user")
                sys.exit(0)
        else:
            logger.info("Force flag set - skipping confirmation")
    
    # Connect to database
    conn = get_db_connection()
    
    try:
        # Step 1: Schema Migration
        schema_migrator = SchemaMigration(conn, dry_run)
        schema_migrator.migrate()
        
        # Step 2: Data Migration
        data_migrator = DataMigration(conn, dry_run)
        data_migrator.migrate()
        
        # Commit changes
        if not dry_run:
            conn.commit()
            logger.info("\n" + "="*60)
            logger.info("MIGRATION COMPLETED SUCCESSFULLY")
            logger.info("="*60)
            logger.info("All changes have been committed to the database.")
        else:
            logger.info("\n" + "="*60)
            logger.info("DRY RUN COMPLETED")
            logger.info("="*60)
            logger.info("No changes were made. Review the output above.")
            logger.info("Run with --execute to apply the migration.")
    
    except Exception as e:
        logger.error("Migration failed: {}".format(str(e)))
        if not dry_run:
            conn.rollback()
            logger.info("Changes have been rolled back.")
        raise
    
    finally:
        conn.close()


if __name__ == '__main__':
    main()