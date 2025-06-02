from os import error
from app.models.simpleModel.H.model_utils import predict_associations, train_model
from app.models.simpleModel.H.extract_mol_features import extract_features_from_smiles
from app.models.simpleModel.H.draw_peaks_and_spectrum import (
    simulate_spectrum,
    compress_spectrum_points_zero_segments,
)
from joblib import load
from app.api.services.logger import log_with_time
import os
import pickle
import numpy as np

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "trained_model_v3.pkl")

# Charger le modèle une seule fois au démarrage du module
with open(MODEL_PATH, "rb") as f:
    model = pickle.load(f)


def predict(smiles):
    if not model:
        return None

    try:
        feats_df = extract_features_from_smiles(smiles)
        if feats_df.empty:
            print("Aucun groupe H détecté dans ce SMILES.")
            raise Exception("Aucun groupe H détecté dans ce SMILES.")

        # Préparer les features
        X_new = feats_df.drop(columns=["heavy_atom_idx"])
        if "neighbor_atomic_nums" in X_new.columns:
            X_new["neighbor_atomic_nums"] = X_new["neighbor_atomic_nums"].astype(str)

        # Prédire les associations
        heavy_atom_idx = feats_df["heavy_atom_idx"].tolist()
        associations_pred = predict_associations(model, X_new, heavy_atom_idx)

        # Trier par ppm croissant
        associations_pred_sorted = sorted(
            associations_pred, key=lambda assoc: assoc["ppm"]
        )

        pics_fusionnes = []
        for assoc in associations_pred_sorted:
            # Clé basée sur les données importantes sauf atoms
            key = (
                round(assoc["ppm"], 6),  # arrondi pour éviter petits écarts float
                assoc["nb_atoms"],
                assoc["multiplicity"],
                tuple(assoc["couplings"]),
            )

            # Chercher un pic existant avec cette clé
            found = False
            for pic in pics_fusionnes:
                pic_key = (
                    round(pic["ppm"], 6),
                    pic["nb_atoms"],
                    pic["multiplicity"],
                    tuple(pic["couplings"]),
                )
                if pic_key == key:
                    # Fusionner les atoms en set
                    pic["atoms"].update(assoc.get("atoms", []))
                    found = True
                    break
            if not found:
                # Copier et convertir atoms en set dès le départ
                new_assoc = assoc.copy()
                new_assoc["atoms"] = set(assoc.get("atoms", []))
                pics_fusionnes.append(new_assoc)

        # Transformer les sets en listes pour affichage
        for pic in pics_fusionnes:
            pic["atoms"] = list(pic["atoms"])

        # Dessiner et afficher le spectre
        x, y, atoms_ids = simulate_spectrum(pics_fusionnes)
        x_comp, y_comp, atoms_ids_comp = compress_spectrum_points_zero_segments(
            x, y, atoms_ids
        )

        # Construire la liste d'objets JSON
        spectrum_points = [
            {
                "ppm": float(ppm),
                "intensity": float(intens),
                "atomID": list(atom_ids) if atom_ids else [],
            }
            for ppm, intens, atom_ids in zip(x_comp, y_comp, atoms_ids_comp)
        ]

        return spectrum_points

    except Exception as e:
        print(f"Erreur lors du traitement du SMILES: {e}")
        return {error: e}
