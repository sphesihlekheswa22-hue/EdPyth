#!/usr/bin/env python3
"""
Quick sanity check for DATABASE_URL connectivity.

Usage:
  1) Set DATABASE_URL in your environment or .env
  2) python check_database_url.py
"""

import os
import sys

from dotenv import load_dotenv

load_dotenv()


def main() -> int:
    url = (os.environ.get("DATABASE_URL") or "").strip()
    if not url:
        print("DATABASE_URL is not set. Add it to .env first.")
        return 2

    if not url.startswith(("postgresql://", "postgres://")):
        print("DATABASE_URL must start with postgresql:// (or postgres://).")
        print(f"Got: {url.split(':', 1)[0]}://...")
        return 2

    try:
        import psycopg2  # type: ignore
    except Exception as e:
        print("psycopg2 is not installed. Run: pip install -r requirements.txt")
        print(f"Import error: {e}")
        return 2

    try:
        conn = psycopg2.connect(url)
        cur = conn.cursor()
        cur.execute("select version();")
        version = cur.fetchone()[0]
        cur.close()
        conn.close()
        print("OK: Connected to Postgres.")
        print(version)
        return 0
    except Exception as e:
        print("FAILED: Could not connect using DATABASE_URL.")
        print(str(e))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

