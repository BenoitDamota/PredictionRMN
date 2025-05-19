import jcamp
import os
import tempfile
import numpy as np


def get_observe_frequency(data_dict):
    possible_keys = [
        ".observe frequency",
        "observe frequency",
        "obsfreq",
        "bf1",
        "$bf1",
        "sfo1",
        "freq",
        ".spectrometer frequency",
        "spectrometer frequency",
    ]

    for key in data_dict:
        normalized_key = key.strip().lower()
        for target in possible_keys:
            if normalized_key == target.lower():
                try:
                    return float(data_dict[key])
                except (ValueError, TypeError):
                    continue
    return None


def parse_jcamp(file_storage):
    try:
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            file_storage.save(tmp.name)
            data_dict = jcamp.jcamp_readfile(tmp.name)
        os.unlink(tmp.name)

        x = np.array(data_dict["x"])
        y = np.array(data_dict["y"])

        # Convert xUnit to ppm if necessary
        x_unit = data_dict.get("xunits", "").lower()
        if x_unit != "ppm":
            obs_freq = get_observe_frequency(data_dict)
            if obs_freq:
                if x_unit in ["hz", "khz"]:
                    factor = 1e-3 if x_unit == "khz" else 1
                    x = x * factor / obs_freq
                    x_unit = "ppm"
                else:
                    return None, f"Unsupported x-unit: {x_unit}"
            else:
                return (
                    None,
                    f"Cannot convert to ppm: missing spectrometer frequency. Metadata: {data_dict}",
                )

        # Check x and y lenght
        if len(x) != len(y):
            return None, "Malformed JCAMP file: x and y length mismatch"

        spectrum = [
            {"ppm": float(x[i]), "intensity": float(y[i]), "atomIds": []}
            for i in range(len(x))
        ]

        if len(x) < 100:
            return {
                "spectrum": spectrum,
                "warning": "JCAMP data is sparse; consider using an uncompressed version",
            }, None

        else:
            return {"spectrum": spectrum}, None

    except Exception as e:
        return None, str(e)
