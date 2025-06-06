import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor


class NeighborAtomStats(BaseEstimator, TransformerMixin):
    def fit(self, X, y=None):
        return self

    def transform(self, X):
        stats = []
        for val in X.iloc[:, 0]:
            if pd.isna(val):
                nums = []
            else:
                try:
                    nums = [int(x) for x in str(val).split(",")]
                except:
                    nums = []
            mean = np.mean(nums) if nums else 0
            std = np.std(nums) if nums else 0
            stats.append([mean, std, len(nums)])
        return np.array(stats)


class NeighborCountExtractor(BaseEstimator, TransformerMixin):
    def __init__(self, feature_name):
        self.feature_name = feature_name

    def fit(self, X, y=None):
        return self

    def transform(self, X):
        counts = []
        for val in X[self.feature_name]:
            if isinstance(val, dict):
                counts.append(
                    [
                        val.get("C", 0),
                        val.get("O", 0),
                        val.get("N", 0),
                        val.get("S", 0),
                        val.get("Halogen", 0),
                    ]
                )
            else:
                counts.append([0, 0, 0, 0, 0])
        return np.array(counts)


def train_model(X_train, y_train):
    numeric_features = [
        "degree",
        "in_ring",
        "is_aromatic",
        "formal_charge",
        "partial_charge",
        "num_H_neighbors",
        "num_heavy_neighbors",
        "dist_to_O",
        "dist_to_N",
        "dist_to_aromatic",
        "in_symmetric_env",
        "neighbor_C_count",
        "neighbor_O_count",
        "neighbor_N_count",
        "neighbor_S_count",
        "neighbor_Halogen_count",
    ]

    neighbor_atomic_nums_feature = ["neighbor_atomic_nums"]

    categorical_features = ["hybridization"]

    preprocessor = ColumnTransformer(
        transformers=[
            ("num", "passthrough", numeric_features),
            ("neighbor_stats", NeighborAtomStats(), neighbor_atomic_nums_feature),
            ("cat", OneHotEncoder(handle_unknown="ignore"), categorical_features),
        ]
    )

    X_proc = preprocessor.fit_transform(X_train)

    reg_ppm = RandomForestRegressor(n_estimators=100, random_state=42)
    reg_ppm.fit(X_proc, y_train["ppm"])

    return {
        "preprocessor": preprocessor,
        "reg_ppm": reg_ppm,
    }


def predict_associations(
    model_dict, X_test, heavy_atom_idx_list, merge=True, ppm_tol=0.15
):
    preprocessor = model_dict["preprocessor"]

    X_proc = preprocessor.transform(X_test)

    ppm_pred = model_dict["reg_ppm"].predict(X_proc)

    default_multiplicity = "s"

    default_couplings = []

    associations = []
    for i in range(len(X_test)):
        associations.append(
            {
                "ppm": float(ppm_pred[i]),
                "atoms": [int(heavy_atom_idx_list[i])],
                "nb_atoms": 1,
                "multiplicity": default_multiplicity,
                "couplings": default_couplings,
            }
        )

    if not merge:
        return associations

    merged = []
    associations = sorted(associations, key=lambda x: x["ppm"])
    if not associations:
        return merged

    current = associations[0].copy()
    for assoc in associations[1:]:
        if abs(assoc["ppm"] - current["ppm"]) < ppm_tol:
            nb1 = current["nb_atoms"]
            nb2 = assoc["nb_atoms"]
            total_nb = nb1 + nb2

            current["ppm"] = (current["ppm"] * nb1 + assoc["ppm"] * nb2) / total_nb
            current["nb_atoms"] = total_nb
            current["atoms"].extend(assoc["atoms"])

        else:
            merged.append(current)
            current = assoc.copy()

    merged.append(current)

    return merged
