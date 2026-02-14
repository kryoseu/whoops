import logging
import os

from dynaconf import FlaskDynaconf
from flask import Flask

from src.utils import ImportStatus

from .whoop import WhoopClient

REQUIRED_VARS = [
    "CLIENT_ID",
    "CLIENT_SECRET",
    "REDIRECT_URI",
    "SQLALCHEMY_DATABASE_URI",
]


def create_app():
    for var in REQUIRED_VARS:
        if not os.getenv(var):
            raise EnvironmentError(f"Missing required environment variable: {var}")

    logging.basicConfig(
        level=logging.INFO,
        format="[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s",
    )

    app = Flask(__name__)
    FlaskDynaconf(app)

    app.config["ImportQueue"] = set()
    app.config["LastImportStatus"] = ImportStatus.NOT_STARTED

    app.config["WhoopClient"] = WhoopClient(
        os.getenv("CLIENT_ID", ""),
        os.getenv("CLIENT_SECRET", ""),
    )
    app.config["REDIRECT_URI"] = os.getenv("REDIRECT_URI")
    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("SQLALCHEMY_DATABASE_URI")

    app.config.load_extensions()  # type: ignore

    return app


if __name__ == "__main__":
    from waitress import serve

    serve(create_app(), host="0.0.0.0", port=5000)
