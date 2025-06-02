from flask import Blueprint, request, jsonify
from app.api.services.logger import log_with_time
from app.models.simpleModel.H.simpleModel_predict import predict

simpleModel_bp = Blueprint("simpleModel", __name__)


@simpleModel_bp.route("/simpleModelPrediction", methods=["POST"])
def simpleModel_prediction():
    data = request.get_json()
    smiles = data.get("smiles")

    if not smiles:
        return jsonify({"error": "Missing 'smiles' in simple prediction"}), 400

    log = "Simple Prediction Parameters:"
    for key, value in data.items():
        if key != "smiles":
            log += f"\n  - {key}: {value}"
    log_with_time(log)

    try:
        spectrum = predict(smiles)
        if not spectrum:
            raise Exception("No Model Founnd")
    except Exception as e:
        return (
            jsonify({"error": f"Failed to predict simple model spectrum: {str(e)}"}),
            500,
        )

    return jsonify({"smiles": smiles, "spectrum": spectrum}), 200
