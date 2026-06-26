# Education ROI Calculator

Production-ready MVP skeleton for an async FastAPI service with PostgreSQL, SQLAlchemy 2.0 async, Alembic, JWT auth, Jinja2, HTMX, and TailwindCSS.

## Run

```bash
docker compose up -d
docker compose exec api alembic upgrade head
```

Open `http://localhost:8000`.

For local development without Docker:

```bash
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload
```

## Migration commands

```bash
alembic revision --autogenerate -m "message"
alembic upgrade head
alembic downgrade -1
```
