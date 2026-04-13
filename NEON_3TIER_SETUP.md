# Neon 3‑tier setup (fast rubric‑friendly)

This turns your project into a true **3‑tier** demo:

- **Tier 1 (Client)**: Browser on another device (phone/PC)
- **Tier 2 (Web server)**: Flask app on your PC
- **Tier 3 (Database)**: Neon Postgres (remote machine)

## 1) Create Neon database (Tier 3)

1. Create a Neon account/project
2. Create a database
3. Copy the connection string (it looks like):

`postgresql://USER:PASSWORD@HOST/DBNAME?sslmode=require`

## 2) Set `.env` on the web server machine (your PC)

In the project root, set:

```env
FLASK_ENV=development
DATABASE_URL=postgresql://USER:PASSWORD@HOST/DBNAME?sslmode=require
SECRET_KEY=anything-random
SESSION_SECRET_KEY=anything-random
```

## 3) Install dependencies

```powershell
pip install -r requirements.txt
```

## 4) Verify the DB connection

```powershell
python check_database_url.py
```

## 5) Create tables in Neon

```powershell
python apply_schema_postgres.py
```

## 6) Seed sample data (for marking)

```powershell
python seed_data.py
```

## 7) Run the web app (Tier 2)

```powershell
python run.py
```

## 8) Prove the 3 tiers in your demo

- Open the site on another device (Tier 1 → Tier 2): `http://<your-pc-ip>:5000`
- In Neon dashboard, show tables/rows changing when you insert/update/delete in the app (Tier 2 → Tier 3).

