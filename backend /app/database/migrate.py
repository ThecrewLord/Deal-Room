from flask_migrate import Migrate

migrate = Migrate()


def init_migrations(app, db):
    migrate.init_app(app, db)