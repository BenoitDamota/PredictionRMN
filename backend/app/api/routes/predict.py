from flask import Blueprint, request, jsonify
import requests
from app.api.services.kekule_converter import convert_smiles_to_kekule
from app.config import Config
import time

predict_bp = Blueprint("predict", __name__)


@predict_bp.route("/predict", methods=["POST"])
def predict():
    data = request.get_json()

    if not data:
        return jsonify({"error": "Missing JSON body"}), 400

    smiles = data.get("smiles")
    endpoint = data.get("endpoint")

    if not smiles:
        return jsonify({"error": "Missing 'smiles' in request body"}), 400
    if not endpoint:
        return jsonify({"error": "Missing 'endpoint' (prediction API URL)"}), 400

    try:
        kekule_smiles = convert_smiles_to_kekule(smiles)
    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 400

    payload = {
        key: value for key, value in data.items() if key not in ["smiles", "endpoint"]
    }
    payload["smiles"] = kekule_smiles

    if endpoint.startswith("http://") or endpoint.startswith("https://"):
        target_url = endpoint
    else:
        base_url = "http://127.0.0.1:52586"
        target_url = f"{base_url}/{endpoint.lstrip('/')}"

    try:
        response = requests.post(
            target_url, json=payload, timeout=Config.PREDICTION_MODEL_TIMEOUT_IN_SECONDS
        )
        response.raise_for_status()
        response_data = response.json()

        checked_response = {
            "smiles": response_data.get("smiles", smiles),
            "peaksInfos": response_data.get("peaksInfos", []),
            "spectrum": response_data.get("spectrum", []),
            "metadata": response_data.get("metadata", {}),
        }

        if "nucleusType" not in checked_response["metadata"]:
            checked_response["metadata"]["nucleusType"] = "Unknown"

        return jsonify(checked_response), 200

    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"Prediction request failed: {str(e)}"}), 500
