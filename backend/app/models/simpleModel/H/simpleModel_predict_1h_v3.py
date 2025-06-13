from os import error
from app.models.simpleModel.H.model_utils_1h_v3 import predict_associations
from app.models.simpleModel.H.extract_mol_features_1h_v3 import (
    extract_features_from_smiles,
)
from app.models.simpleModel.utils.draw_peaks_and_spectrum import (
    simulate_spectrum,
    compress_spectrum_points_zero_segments,
)
import os
from joblib import load
import numpy as np
from app.api.services.logger import log_with_time

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "trained_model_1h_v3.joblib")

model = load(MODEL_PATH)

from app.models.simpleModel.utils.train_models import train_models


def predict(smiles):

    if not model:
        return {"error": "Error during the 1H prediction"}

    try:
        feats_df = extract_features_from_smiles(smiles)
        if feats_df.empty:
            log_with_time(f"No H groups detected in the SMILES : {smiles}")
            return {
                "spectrum": [
                    {"ppm": 0, "intensity": 0, "atomID": []},
                    {"ppm": 10, "intensity": 0, "atomID": []},
                ],
                "peaksInfos": [],
            }

        X_new = feats_df.drop(columns=["heavy_atom_idx"])
        if "neighbor_atomic_nums" in X_new.columns:
            X_new["neighbor_atomic_nums"] = X_new["neighbor_atomic_nums"].astype(str)

        heavy_atom_idx = feats_df["heavy_atom_idx"].tolist()
        associations_pred = predict_associations(model, X_new, heavy_atom_idx)

        associations_pred_sorted = sorted(
            associations_pred, key=lambda assoc: assoc["ppm"]
        )

        merged_peaks = []
        for assoc in associations_pred_sorted:
            key = (
                round(assoc["ppm"], 6),
                assoc["nb_atoms"],
                assoc["multiplicity"],
                tuple(assoc["couplings"]),
            )

            found = False
            for peak in merged_peaks:
                peak_keys = (
                    round(peak["ppm"], 6),
                    peak["nb_atoms"],
                    peak["multiplicity"],
                    tuple(peak["couplings"]),
                )
                if peak_keys == key:
                    peak["atoms"].update(assoc.get("atoms", []))
                    found = True
                    break
            if not found:
                new_assoc = assoc.copy()
                new_assoc["atoms"] = set(assoc.get("atoms", []))
                merged_peaks.append(new_assoc)

        for peak in merged_peaks:
            peak["atoms"] = list(peak["atoms"])

        x, y, atoms_ids = simulate_spectrum(merged_peaks, 0.004, (0, 10), 64000)
        x_comp, y_comp, atoms_ids_comp = compress_spectrum_points_zero_segments(
            x, y, atoms_ids
        )

        spectrum_points = [
            {
                "ppm": float(ppm),
                "intensity": float(intens),
                "atomID": list(atom_ids) if atom_ids else [],
            }
            for ppm, intens, atom_ids in zip(x_comp, y_comp, atoms_ids_comp)
        ]

        peaksInfos = [
            {
                "assignement": peak["atoms"],
                "delta": peak["ppm"],
                "nbAtoms": peak["nb_atoms"],
                "multiplicity": peak["multiplicity"],
                "coupling": peak["couplings"],
            }
            for peak in merged_peaks
        ]

        return {"spectrum": spectrum_points, "peaksInfos": peaksInfos}

    except Exception as e:
        log_with_time(f"Error during the processing of the SMILES: {e}")
        return {"error": "Error during the 1H prediction"}
