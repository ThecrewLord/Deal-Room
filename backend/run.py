from app import create_app
from app.models.auth.user import User

app = create_app()

if __name__ == "__main__":
    app.run(debug=True)