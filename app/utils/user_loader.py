from flask_login import LoginManager
from app.models import User

login_manager = LoginManager()


@login_manager.user_loader
def load_user(user_id):
    """Load user by ID for Flask-Login."""
    return User.query.get(int(user_id))
