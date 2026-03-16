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

### Step 2: Create MySQL Database
1. Go to the **Databases** tab
2. Create a new MySQL database:
   - Database name: `yourusername$edumind` (or whatever you prefer)
   - Username and password: Note these down
3. Initialize the database tables using the PythonAnywhere console

### Step 3: Configure Environment Variables
Go to the **Web** tab and add the following in the **Environment variables** section:

```
FLASK_ENV=production
SECRET_KEY=your-secure-random-secret-key
DATABASE_URL=mysql://username:password@localhost/databasename
NVIDIA_API_KEY=your-nvidia-api-key (optional)
```

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
Run the following in a PythonAnywhere console:
```bash
cd ~/App2Python
python -c "from app import create_app, db; app = create_app('production'); app.app_context().push(); db.create_all()"
```

### Step 7: Reload the App
Go to the **Web** tab and click the **Reload** button.

## Troubleshooting

### Common Issues:
1. **Database connection errors**: Check your DATABASE_URL format
2. **Static files not loading**: Make sure to run `collectstatic` if using Flask-Staff
3. **Import errors**: Check that all files are in the correct directories

### Error Logs:
Check the **Logs** tab in PythonAnywhere for error messages.

## Important Notes:
- The app runs in production mode with `DEBUG=False`
- Session data is stored in the filesystem by default
- Make sure to set a strong SECRET_KEY for production
