"""Deprecated compatibility entrypoint.

Use Flask-Migrate/Alembic instead:

    flask --app run.py db upgrade

This command intentionally does not call db.create_all().
"""

print("Use 'flask --app run.py db upgrade' to apply Deal Room migrations.")
