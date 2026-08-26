# Deal Room Backend

## Run

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
flask --app run.py db upgrade
python seed_test_data.py
python run.py
```

Health endpoint:

```text
GET http://localhost:5000/health
```

## Database

PostgreSQL is expected at the `DATABASE_URL` configured in `.env`.

Migrations are Flask-Migrate/Alembic. The current chain has a single head:

```text
e6f7a8b9c0d1
```

Do not use `db.drop_all()` as part of normal development setup.

## Tests

```bash
pytest -q
```

## Compile

```bash
python -m compileall app tests migrations seed_test_data.py run.py
```
