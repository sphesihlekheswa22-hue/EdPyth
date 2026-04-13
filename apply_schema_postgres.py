#!/usr/bin/env python3
"""
Apply database_schema_postgres.sql to the DATABASE_URL Postgres database.

Usage:
  1) Set DATABASE_URL in .env
  2) python apply_schema_postgres.py
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


def main() -> int:
    url = (os.environ.get("DATABASE_URL") or "").strip()
    if not url:
        print("DATABASE_URL is not set. Add it to .env first.")
        return 2

    schema_path = Path(__file__).with_name("database_schema_postgres.sql")
    if not schema_path.exists():
        print(f"Missing schema file: {schema_path}")
        return 2

    try:
        import psycopg2  # type: ignore
    except Exception as e:
        print("psycopg2 is not installed. Run: pip install -r requirements.txt")
        print(f"Import error: {e}")
        return 2

    sql = schema_path.read_text(encoding="utf-8")
    try:
        conn = psycopg2.connect(url)
        conn.autocommit = True
        cur = conn.cursor()
        cur.execute(sql)
        cur.close()
        conn.close()
        print("OK: Schema applied to Postgres.")
        return 0
    except Exception as e:
        print("FAILED: Could not apply schema.")
        print(str(e))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

