from flask import Blueprint, request, jsonify
import json
import os
import sys
from app.api.services.logger import log_with_time

mock_bp = Blueprint("mock", __name__)


def load_mock_spectrum():
    if getattr(sys, "frozen", False):
        base_path = sys._MEIPASS
    else:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        base_path = os.path.abspath(os.path.join(current_dir, "..", "services"))

    path = os.path.join(base_path, "mock", "mockSpectrum.json")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


@mock_bp.route("/mockPredictionModel", methods=["POST"])
def mock_prediction_model():
    data = request.get_json()
    smiles = data.get("smiles")

    if not smiles:
        return jsonify({"error": "Missing 'smiles' in mock prediction"}), 400

    log = "Mock Prediction Parameters:"
    for key, value in data.items():
        if key != "smiles":
            log += f"\n  - {key}: {value}"
    log_with_time(log)

    try:
        spectre = load_mock_spectrum()
    except Exception as e:
        return jsonify({"error": f"Failed to load mock spectrum: {str(e)}"}), 500

    # Mock spectrum data for the corresponding molecules
    return jsonify({"smiles": "CCOC1=CC=C(C(C)=O)C=C1", "spectrum": spectre}), 200
