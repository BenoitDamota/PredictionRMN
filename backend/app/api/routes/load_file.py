from flask import Blueprint, request, jsonify
import jcamp
import os
import tempfile
import numpy as np

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

    try:
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            file.save(tmp.name)
            data_dict = jcamp.jcamp_readfile(tmp.name)

        os.unlink(tmp.name)

        x = data_dict["x"]
        y = data_dict["y"]

        if isinstance(x, np.ndarray):
            x = x.tolist()
        if isinstance(y, np.ndarray):
            y = y.tolist()

        if (
            isinstance(x, (list, tuple))
            and len(x) > 0
            and isinstance(y, (list, tuple))
            and len(y) > 0
        ):
            if len(x) != len(y):
                return (
                    jsonify({"error": "Malformed JCAMP file, x and y length mismatch"}),
                    400,
                )

            spectrum = [
                {"ppm": x[i], "intensity": y[i], "atomIds": []} for i in range(len(x))
            ]

            return jsonify(spectrum)
        else:
            return (
                jsonify({"error": "Malformed JCAMP file or no spectral data found"}),
                400,
            )

    except Exception as e:
        error_message = str(e)
        print(f"Error: {error_message}")

        return jsonify({"error": f"An error occurred: {error_message}"}), 500
