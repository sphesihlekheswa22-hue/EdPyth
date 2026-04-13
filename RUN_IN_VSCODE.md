# Run this app in VS Code (Windows) — step by step

This project is a Flask app. The simplest local entrypoint is `run.py`, which calls `create_app()` and starts the dev server.

## Prerequisites

- VS Code
- Python 3.10+ installed (3.11 recommended)
- (Recommended) VS Code extension: **Python** (by Microsoft)

## 1) Open the project in VS Code

1. Open VS Code
2. **File → Open Folder…**
3. Select this folder: `App2Python`

## 2) Create and activate a virtual environment

Open VS Code terminal (**Terminal → New Terminal**) and run:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
```

If PowerShell blocks activation, run this once (then try activating again):

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

## 3) Install dependencies

With the venv activated:

```powershell
pip install -r requirements.txt
```

## 4) Create your local `.env`

This project loads environment variables from a `.env` file automatically (see `app/config.py`).

1. Copy `.env.example` to a new file named `.env` in the project root.

In PowerShell:

```powershell
Copy-Item .env.example .env
```

2. Edit `.env` and set at least:

- `FLASK_ENV=development` (recommended locally)
- `SECRET_KEY=...` (any random string is fine for local dev)
- `SESSION_SECRET_KEY=...` (any random string is fine for local dev)

Optional:

- `OPENROUTER_API_KEY=...` (only needed for AI features)
- Email variables (`MAIL_SERVER`, `MAIL_USERNAME`, etc.) if you want password reset / verification emails to work.

## 5) Database (SQLite)

By default, the app uses SQLite and will create a DB file automatically.

- **Default DB path**: `app/edumind_ai.db`
- You can override with: `SQLITE_DB_PATH=...` in `.env`

In development, the app will run `db.create_all()` automatically (see `app/__init__.py`), so you usually don’t need to run migrations just to start.

If you want to use migrations anyway (recommended once your schema stabilizes):

```powershell
flask db upgrade
```

Note: `flask` commands require the correct app context. If `flask db upgrade` fails due to missing app configuration, just run the app first using `python run.py` (next step) and we can set up a proper `FLASK_APP` value afterward.

## 6) Run the app (dev server)

With the venv activated:

```powershell
python run.py
```

Then open:

- `http://127.0.0.1:5000`

If port 5000 is busy, set a different port:

```powershell
$env:PORT=5001
python run.py
```

## 7) Debug the app with F5 (recommended)

### Option A (quickest): use a `launch.json`

1. In VS Code, open **Run and Debug**
2. Click **create a launch.json file**
3. Choose **Python**
4. Replace the generated config with this (or add a new config):

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Flask (run.py)",
      "type": "python",
      "request": "launch",
      "program": "${workspaceFolder}/run.py",
      "console": "integratedTerminal",
      "env": {
        "FLASK_ENV": "development",
        "PORT": "5000"
      }
    }
  ]
}
```

5. Press **F5** and select **Flask (run.py)**

### Option B: debug from terminal

You can also run:

```powershell
python -m debugpy --listen 5678 --wait-for-client run.py
```

Then attach a debugger to port `5678`.

## 8) Common problems

### “ModuleNotFoundError …”

- Ensure the venv is activated: `.\.venv\Scripts\Activate.ps1`
- Ensure you installed deps: `pip install -r requirements.txt`

### “Missing production secrets…”

That happens if you run with `FLASK_ENV=production` without secrets.

- For local dev set `FLASK_ENV=development` in `.env`

### Static/uploads folder issues

Uploads are stored under the app’s configured upload folder (see `app/config.py`). If you get file-not-found errors for uploads, check which uploads directory exists in your repo:

- `app/static/uploads` or
- `app/app/static/uploads`

## 9) Production note (not for local VS Code runs)

In production this repo uses Gunicorn with `wsgi:application` (see `Procfile`).

