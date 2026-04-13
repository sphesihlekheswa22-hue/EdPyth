"""
One-off SQLite helper: add students.profile_image if missing (existing DBs).

Usage (from project root):
  python add_student_profile_image_column.py
"""
import os
import sqlite3

def main():
    root = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(root, "app", "edumind_ai.db")
    if not os.path.isfile(db_path):
        print(f"No database at {db_path} — skip.")
        return
    conn = sqlite3.connect(db_path)
    try:
        cur = conn.execute("PRAGMA table_info(students)")
        cols = [row[1] for row in cur.fetchall()]
        if "profile_image" in cols:
            print("Column profile_image already exists.")
            return
        conn.execute("ALTER TABLE students ADD COLUMN profile_image VARCHAR(512)")
        conn.commit()
        print("Added students.profile_image.")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
