from flask import Blueprint
from app.api.routes.convert import convert_bp
from app.api.routes.predict import predict_bp
from app.api.routes.mol_image import mol_image_bp
from app.api.routes.load_file import load_file_bp
from app.api.routes.detect_spectrum_regions import detect_spectrum_regions_bp
from app.api.routes.simple_model_prediction import simpleModel_bp

api_routes = Blueprint("api", __name__)

api_routes.register_blueprint(convert_bp)
api_routes.register_blueprint(predict_bp)
api_routes.register_blueprint(mol_image_bp)
api_routes.register_blueprint(load_file_bp)
api_routes.register_blueprint(detect_spectrum_regions_bp)
api_routes.register_blueprint(simpleModel_bp)
