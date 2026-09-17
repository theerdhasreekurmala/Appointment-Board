# Appointment Board

Simple appointment board (Flask + SQLite) implementing the features from the provided spec:

- View a list/board of appointments
- Add, edit, complete, and cancel appointments
- Filter by date and status
- Prevent overlapping appointments
- Cancelled appointments remain visible and marked cancelled


Run locally (Windows, using SQLite):

```
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Open http://127.0.0.1:5000 in your browser. The app seeds a few sample appointments on first run.

Using PostgreSQL (pgAdmin)

1. Install PostgreSQL and pgAdmin (use the installer for Windows from https://www.postgresql.org/download/windows/).
2. Create a database and user via pgAdmin or psql. Example using psql:

```psql
CREATE DATABASE appointmentdb;
CREATE USER appt_user WITH ENCRYPTED PASSWORD 'strongpassword';
GRANT ALL PRIVILEGES ON DATABASE appointmentdb TO appt_user;
```

3. Set the `DATABASE_URL` environment variable to point to your Postgres instance. Example (PowerShell):

```powershell
$env:DATABASE_URL = 'postgresql://appt_user:strongpassword@localhost:5432/appointmentdb'
python app.py
```

Alternatively set the environment variable permanently via Windows system settings or use a `.env` loader.

Notes
- The app uses `Flask-SQLAlchemy` and accepts any SQLAlchemy-compatible `DATABASE_URL`.
- For local development the app still falls back to `sqlite:///appointments.db` when `DATABASE_URL` is not set.

