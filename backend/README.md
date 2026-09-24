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
Run `flask --app run.py db upgrade` after replacing the backend so the stakeholder primary-key sequence repair is applied.

## Tests

```bash
pytest -q
```

## Compile

```bash
python -m compileall app tests migrations seed_test_data.py run.py
```

## A2 database cutover requirement

A2 adds authoritative opportunity state columns (`lifecycle_stage`, `outcome`,
`operational_status`, `review_status`, `row_version`, and Closed Lost fields).
Before starting the API against an existing database, run the Alembic upgrade:

```bash
flask --app run.py db upgrade
```

If this project uses the Alembic CLI directly, the equivalent is:

```bash
alembic upgrade head
```

Do not manually alter the PostgreSQL schema. The A2 migration is
`j1k2l3m4n5o6_phase2_lifecycle_transition_engine`.
