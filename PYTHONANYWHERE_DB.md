# PythonAnywhere Database Configuration

## SQLite Configuration (Default)

The application uses SQLite by default. No manual database setup is required.

## How It Works

- The SQLite database file is automatically created at `app/edumind_ai.db` when you first run the application
- SQLite is file-based, so no separate database server is needed
- The database file will be created in your application directory

## Environment Variables to Set (in Web tab)

| Variable | Value |
|----------|-------|
| FLASK_ENV | production |
| SECRET_KEY | any-random-string-like-this-x8k9j2h4 |

## Where to Set

1. Go to **Web** tab
2. Scroll down to **Environment variables**
3. Add the 2 variables above

## Important Notes

- **No DATABASE_URL needed**: The application automatically uses SQLite
- **No database creation required**: SQLite database is created automatically on first run
- **File permissions**: Ensure your app directory has write permissions for the database file

## Database Location

The SQLite database will be created at:
```
~/App2Python/app/edumind_ai.db
```

## Backup

To backup your SQLite database, simply copy the `edumind_ai.db` file from your application directory.
