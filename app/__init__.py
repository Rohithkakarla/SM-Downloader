from flask import Flask

from os import path, environ


def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = environ.get("SECRET_KEY", "dev")

    from .youtube import youtube

    app.register_blueprint(youtube, url_prefix="/youtube")

    return app