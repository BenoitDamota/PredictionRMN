from flask import Blueprint, request, jsonify
from app.api.services.jcampdxLoader import parse_jcamp

load_file_bp = Blueprint("load_file_bp", __name__)


@load_file_bp.route("/loadJCAMP", methods=["POST"])
def load_jcamp():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]
    if not file.filename.endswith((".jdx", ".jcamp")):
        return (
            jsonify(
                {"error": "Invalid file type. Please upload a .jdx or .jcamp file"}
            ),
            400,
        )

    data, error = parse_jcamp(file)

    if error:
        return jsonify({"error": error}), 400

    return jsonify(data)
