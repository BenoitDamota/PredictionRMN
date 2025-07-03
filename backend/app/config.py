import os
import sys
from platformdirs import user_config_dir


class Config:
    IS_FROZEN = getattr(sys, "frozen", False)
    DEBUG = not IS_FROZEN

    if IS_FROZEN:
        CORS_ORIGINS = []
    else:
        CORS_ORIGINS = ["http://localhost:5173"]

    if IS_FROZEN:
        STATIC_FOLDER = os.path.join(sys._MEIPASS, "frontend", "build")
    else:
        STATIC_FOLDER = os.path.join(os.path.dirname(__file__), "../../frontend/build")

    APP_NAME = "PredictionRMN"
    APP_AUTHOR = "LERIA"
    PREDICTION_MODEL_TIMEOUT_IN_SECONDS = 300
