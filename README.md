# Deal Room Backend

Flask + SQLAlchemy + PostgreSQL backend for the Deal Room / Collaborating Opportunities platform.

## Run locally

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

## Database / migrations

This repository uses a **fresh V2 Alembic baseline**. The previous migration
history is intentionally not part of the active chain.

Active migration:

```text
60ba9620bb40  Deal Room V2 baseline
```

The active chain must have exactly one head:

```bash
flask --app run.py db heads
flask --app run.py db current
flask --app run.py db check
```

For a new empty PostgreSQL database:

```bash
flask --app run.py db upgrade
```

The legacy migration files, if retained for historical reference, are not used
by the active Alembic environment.

### Fresh local database

For the disposable local `dealroom2` database, recreate the database first,
then run the migration:

```bash
flask --app run.py db upgrade
```

Do not run `db.drop_all()` against a database containing data you need to keep.
The old database can remain untouched as a fallback until the new baseline has
been verified.

## POC architecture

`poc_tracker` is the only authoritative POC record. POC request, team
assignment, submission, completion, retrieval and report generation delegate to
the canonical Phase2 service/report service.

The retired standalone `poc` table/model and the old duplicate POC service,
repository, controller and schemas have been removed. A small `/api/poc/*`
compatibility facade remains only for existing clients and delegates to the
canonical Phase2 implementation; it does not maintain a second POC domain.

POC records support multiple cycles per opportunity, submitted results are
immutable, normal POC deletion is not exposed, and POC rows carry a
`row_version` for concurrency tracking.

## Delivery project suggestions

When a Closed Won opportunity creates a Delivery Project, the latest completed
POC team's members may be copied as **suggestions** (`is_suggested=true`). The
Delivery Manager or Leadership must explicitly confirm/reassign project
membership. Suggested members are not treated as final assignment.

## Tests

```bash
pytest -q
```

## Static compile check

```bash
python -m compileall app tests migrations seed_test_data.py run.py
```

## Security

Do not commit `.env` files or production secrets. Use `.env.example` as the
local template and provide a random JWT secret of at least 32 bytes in the real
environment.
