"""
Repair missing material files on disk.

Why this exists:
- Some CourseMaterial rows may reference filenames/paths that don't exist on disk
  (often from older seed/demo data or refactors that moved uploads folders).
- The app now avoids hard 404s, but you still want downloads to work.

What this script does:
- Scans CourseMaterial records and checks whether the file exists in the canonical location:
    <UPLOAD_FOLDER>/materials/<module_id>/<file_name>
- If missing, it can copy a fallback PDF (e.g. sample.pdf) into that location
  and optionally normalize the DB `file_path` to `/static/uploads/materials/<module_id>/<file_name>`.

Usage (PowerShell):
  python repair_missing_material_files.py --dry-run
  python repair_missing_material_files.py --copy-from "app/app/static/uploads/sample.pdf" --apply
"""

from __future__ import annotations

import argparse
import os
import shutil
from typing import Optional

from app import create_app, db
from app.models import CourseMaterial


def _resolve_copy_source(path: Optional[str], app_root: str) -> Optional[str]:
    if not path:
        return None
    if os.path.isabs(path):
        return path if os.path.exists(path) else None
    candidate = os.path.join(app_root, path)
    return candidate if os.path.exists(candidate) else None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--env", default="development", choices=["development", "production", "testing"])
    parser.add_argument("--dry-run", action="store_true", help="Only print what would change.")
    parser.add_argument("--apply", action="store_true", help="Actually write files and update DB.")
    parser.add_argument(
        "--copy-from",
        default=None,
        help="Path to a fallback file to copy into missing material locations (relative to repo root or absolute).",
    )
    parser.add_argument(
        "--normalize-db-paths",
        action="store_true",
        help="Update CourseMaterial.file_path to canonical /static/uploads/materials/<module_id>/<file_name>.",
    )
    args = parser.parse_args()

    if args.apply and args.dry_run:
        raise SystemExit("Use either --dry-run or --apply, not both.")
    if not args.apply and not args.dry_run:
        raise SystemExit("Pick one: --dry-run or --apply")

    app = create_app(args.env)

    with app.app_context():
        upload_root = app.config.get("UPLOAD_FOLDER")
        if not upload_root:
            raise SystemExit("UPLOAD_FOLDER is not configured.")

        copy_source = _resolve_copy_source(args.copy_from, app.root_path) if args.copy_from else None
        if args.copy_from and not copy_source:
            raise SystemExit(f'--copy-from "{args.copy_from}" does not exist.')

        materials = CourseMaterial.query.order_by(CourseMaterial.id.asc()).all()
        missing = []

        for m in materials:
            canonical_path = os.path.join(upload_root, "materials", str(m.module_id), m.file_name)
            if not os.path.exists(canonical_path):
                missing.append((m, canonical_path))

        print(f"UPLOAD_FOLDER: {upload_root}")
        print(f"Total materials: {len(materials)}")
        print(f"Missing files: {len(missing)}")

        if not missing:
            return 0

        for (m, canonical_path) in missing:
            print(f"- material_id={m.id} module_id={m.module_id} file_name={m.file_name}")
            print(f"  expected: {canonical_path}")
            print(f"  db.file_path: {m.file_path}")

            if copy_source:
                print(f"  will_copy_from: {copy_source}")
            if args.normalize_db_paths:
                print(f"  will_set_db_file_path: /static/uploads/materials/{m.module_id}/{m.file_name}")

            if args.apply:
                os.makedirs(os.path.dirname(canonical_path), exist_ok=True)
                if copy_source:
                    shutil.copy2(copy_source, canonical_path)
                if args.normalize_db_paths:
                    m.file_path = f"/static/uploads/materials/{m.module_id}/{m.file_name}"

        if args.apply and args.normalize_db_paths:
            db.session.commit()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

