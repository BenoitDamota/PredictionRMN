from flask import Blueprint, request, jsonify
from app.api.services.logger import log_with_time
from app.models.simpleModel.H.simpleModel_predict_1h_v3 import predict as predict_1h
from app.models.simpleModel.C.simpleModel_predict_13c_v2 import predict as predict_13c

simpleModel_bp = Blueprint("simpleModel", __name__)


@simpleModel_bp.route("/simpleModelPrediction", methods=["POST"])
def simpleModel_prediction():
    data = request.get_json()
    smiles = data.get("smiles")

    if not smiles:
        return jsonify({"error": "Missing 'smiles' in simple prediction"}), 200

    spectrum_type = "1H"
    log = "Simple Prediction Parameters:"
    for key, value in data.items():
        if key == "smiles":
            continue
        if isinstance(value, dict):
            log += f"\n  - {value.get('key')}: {value.get('value')}"
            if value.get("key") == "type":
                spectrum_type = value.get("value", "1H")
    log_with_time(log)

    try:
        if spectrum_type == "13C":
            result = predict_13c(smiles)
        else:

            result = predict_1h(smiles)

        if isinstance(result, dict) and "error" in result:
            return jsonify(result), 200

        spectrum = result.get("spectrum", [])
        peaks_info = result.get("peaksInfos", [])

        if not spectrum:
            return jsonify({"error": "No spectrum predicted"}), 200

        metadata = {"nucleusType": spectrum_type}

    except Exception as e:
        return (
            jsonify({"error": f"Failed to predict simple model spectrum: {str(e)}"}),
            200,
        )

    return (
        jsonify(
            {
                "smiles": smiles,
                "peaksInfos": peaks_info,
                "spectrum": spectrum,
                "metadata": metadata,
            }
        ),
        200,
    )
