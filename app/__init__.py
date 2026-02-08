from flask import Flask

from app.auth import auth_bp
from app.db import init_db


def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = "dev-secret-key-change-me"
    app.config["DATABASE"] = "medismart.db"
    app.config["OTP_EXPIRY_SECONDS"] = 30
    app.config["OTP_MAX_ATTEMPTS"] = 3

    init_db(app)

    app.register_blueprint(auth_bp)

    return app
