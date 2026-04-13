"""
One-off SQLite helper: create assignment_attachments for lecturer-uploaded assignment files.

Usage (from project root):
  python add_assignment_attachments_table.py
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
        row = conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='assignment_attachments'"
        ).fetchone()
        if row:
            print("Table assignment_attachments already exists.")
            return
        conn.execute(
            """
            CREATE TABLE assignment_attachments (
                id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                assignment_id INTEGER NOT NULL,
                file_path VARCHAR(500) NOT NULL,
                file_name VARCHAR(255) NOT NULL,
                created_at DATETIME,
                FOREIGN KEY (assignment_id) REFERENCES assignments (id) ON DELETE CASCADE
            )
            """
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_assignment_attachments_assignment_id "
            "ON assignment_attachments(assignment_id)"
        )
        conn.commit()
        print("Created assignment_attachments table.")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
