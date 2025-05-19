from flask import Blueprint, request, jsonify
from app.api.services.detect_nmr_peaks import analyze_spectrum
from app.api.services.logger import log_with_time
import traceback

detect_spectrum_regions_bp = Blueprint("detect_spectrum_regions_bp", __name__)


@detect_spectrum_regions_bp.route("/detectSpectrumRegions", methods=["POST"])
def detect_peaks_nmr():
    data = request.get_json()

    if not data or "spectrum" not in data:
        return jsonify({"error": "Missing 'spectrum' in request body"}), 400

    spectrum = data["spectrum"]
    ppm = [point["ppm"] for point in spectrum]
    intensity = [point["intensity"] for point in spectrum]
    atom_ids = [point.get("atomID", []) for point in spectrum]

    spectrum_type = data.get("type", "auto")

    try:
        result = analyze_spectrum(ppm, intensity, atom_ids, spectrum_type)
        return jsonify({"regions": result}), 200
    except Exception as e:
        log_with_time(f"Error during spectrum analysis: {e}")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500
