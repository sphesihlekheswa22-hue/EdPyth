# PythonAnywhere Deployment Guide

## Prerequisites
- A PythonAnywhere account (free or paid)
- Your EduMind AI project files

## Deployment Steps

### Step 1: Upload Files to PythonAnywhere
1. Go to [PythonAnywhere](https://www.pythonanywhere.com/)
2. Log in to your account
3. Go to the **Files** tab
4. Create a new directory called `App2Python`
5. Upload all your project files to this directory

**Easier Options:**
- **Use Git** (recommended): Open a Bash console and run:
  ```bash
  cd ~ && git clone https://github.com/your-repo-url.git App2Python
  ```
- **Use ZIP upload**: Zip your project locally, then upload the ZIP file and extract it in PythonAnywhere

### Step 2: Database Setup (SQLite)
The application uses SQLite by default. The database file will be created automatically at `app/edumind_ai.db` when you first run the application.

No manual database setup is required - SQLite databases are file-based and will be created on first use.

### Step 3: Configure Environment Variables
Go to the **Web** tab and add the following in the **Environment variables** section:

```
FLASK_ENV=production
SECRET_KEY=your-secure-random-secret-key
SESSION_SECRET_KEY=your-secure-random-session-secret-key
OPENROUTER_API_KEY=your-openrouter-api-key (optional, for AI features)
```

Note: No DATABASE_URL is needed as the application uses SQLite by default.

### Step 4: Configure WSGI File
1. Go to the **Web** tab
2. Click on the WSGI configuration file link
3. Replace the content with the contents of `wsgi.py` in your project

### Step 5: Install Dependencies
Open a PythonAnywhere Bash console and run:
```bash
pip install -r ~/App2Python/requirements.txt
```

### Step 6: Initialize Database
In production, the schema should be managed via migrations (recommended).
If you are using SQLite and deploying for the first time, run migrations (or create tables once) before first request.

**Recommended (migrations):**
```bash
cd ~/App2Python
flask db upgrade
```

**Fallback (not recommended long-term):**
```bash
cd ~/App2Python
python -c "from app import create_app, db; app = create_app('production'); app.app_context().push(); db.create_all()"
```

### Step 7: Reload the App
Go to the **Web** tab and click the **Reload** button.

## Troubleshooting

### Common Issues:
1. **Database file permissions**: Ensure the app directory has write permissions for SQLite database creation
2. **Static files not loading**: Make sure to run `collectstatic` if using Flask-Staff
3. **Import errors**: Check that all files are in the correct directories

### Error Logs:
Check the **Logs** tab in PythonAnywhere for error messages.

## Important Notes:
- The app runs in production mode with `DEBUG=False`
- Session data is stored in the filesystem by default
- Make sure to set strong `SECRET_KEY` and `SESSION_SECRET_KEY` for production
