from flask import Flask
from flask_cors import CORS
from app.config import Config
from app.routes import main_routes
from app.api import api_routes


def create_app(serve_frontend=True):
    # Create a flask instance
    app = Flask(__name__, static_folder=Config.STATIC_FOLDER)

    # Load config
    app.config.from_object(Config)

    CORS(app, origins=app.config["CORS_ORIGINS"])

    # Handle blueprints
    if serve_frontend:
        app.register_blueprint(main_routes)
    app.register_blueprint(api_routes, url_prefix="/api")

    return app
