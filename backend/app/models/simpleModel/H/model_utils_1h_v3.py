import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.multioutput import MultiOutputRegressor
from sklearn.preprocessing import OneHotEncoder, LabelEncoder
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.compose import ColumnTransformer


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


class NeighborHCountsStats(BaseEstimator, TransformerMixin):
    def fit(self, X, y=None):
        return self

    def transform(self, X):
        stats = []
        for val in X.iloc[:, 0]:
            if pd.isna(val):
                counts = []
            else:
                try:
                    counts = [int(x) for x in str(val).split(",")]
                except:
                    counts = []
            mean = np.mean(counts) if counts else 0
            std = np.std(counts) if counts else 0
            stats.append([mean, std, len(counts)])
        return np.array(stats)


class HCouplingTypeEncoder(BaseEstimator, TransformerMixin):
    def __init__(self):
        self.encoder = OneHotEncoder(handle_unknown="ignore", sparse_output=False)

    def fit(self, X, y=None):
        self.encoder.fit(X.values.reshape(-1, 1))
        return self

    def transform(self, X):
        return self.encoder.transform(X.values.reshape(-1, 1))


MAX_COUPLINGS = 3


def prepare_couplings(couplings_series):
    couplings_padded = []
    for c in couplings_series:
        c_list = c if isinstance(c, list) else []
        c_list_padded = c_list[:MAX_COUPLINGS] + [0.0] * (MAX_COUPLINGS - len(c_list))
        couplings_padded.append(c_list_padded)
    return np.array(couplings_padded)


def train_model(X_train, y_train):
    numeric_features = [
        "num_H",
        "heavy_atomic_num",
        "heavy_degree",
        "heavy_in_ring",
        "heavy_is_aromatic",
        "heavy_formal_charge",
        "heavy_partial_charge",
        "num_heavy_neighbors",
        "num_H_neighbors",
        "num_couplable_H_neighbors",
        "distance_to_nearest_non_equivalent_H",
        "in_symmetric_env",
        "is_in_CH3",
        "is_in_CH2",
        "is_terminal_CH",
    ]

    neighbor_atomic_nums_feature = ["neighbor_atomic_nums"]
    neighbor_H_counts_feature = ["neighbor_H_counts_per_atom"]

    categorical_features = ["heavy_hybridization"]

    h_coupling_feature = X_train["H_coupling_type"]

    preprocessor = ColumnTransformer(
        transformers=[
            ("num", "passthrough", numeric_features),
            ("neighbor_stats", NeighborAtomStats(), neighbor_atomic_nums_feature),
            ("neighbor_H_stats", NeighborHCountsStats(), neighbor_H_counts_feature),
            ("cat", OneHotEncoder(handle_unknown="ignore"), categorical_features),
        ]
    )

    label_multiplicity = LabelEncoder()
    y_multiplicity = label_multiplicity.fit_transform(
        y_train["multiplicity"].fillna("None")
    )

    X_num_cat = preprocessor.fit_transform(X_train)

    h_coupling_enc = HCouplingTypeEncoder()
    h_coupling_enc.fit(h_coupling_feature)
    h_coupling_encoded = h_coupling_enc.transform(h_coupling_feature)

    X_proc = np.hstack([X_num_cat, h_coupling_encoded])

    y_couplings = prepare_couplings(y_train["couplings"])

    reg_ppm = RandomForestRegressor(n_estimators=100, random_state=42)
    clf_multiplicity = RandomForestClassifier(n_estimators=100, random_state=42)
    reg_couplings = MultiOutputRegressor(
        RandomForestRegressor(n_estimators=100, random_state=42)
    )

    reg_ppm.fit(X_proc, y_train["ppm"])
    clf_multiplicity.fit(X_proc, y_multiplicity)
    reg_couplings.fit(X_proc, y_couplings)

    return {
        "preprocessor": preprocessor,
        "reg_ppm": reg_ppm,
        "clf_multiplicity": clf_multiplicity,
        "reg_couplings": reg_couplings,
        "label_multiplicity": label_multiplicity,
        "h_coupling_encoder": h_coupling_enc,
    }


def multiplicity_complexity(m):
    if m is None:
        return 0
    return len(m)


def predict_associations(
    model_dict, X_test, heavy_atom_idx_list, merge=True, ppm_tol=0.15
):
    preprocessor = model_dict["preprocessor"]
    h_coupling_enc = model_dict["h_coupling_encoder"]

    X_num_cat = preprocessor.transform(X_test)
    h_coupling_encoded = h_coupling_enc.transform(X_test["H_coupling_type"])

    X_proc = np.hstack([X_num_cat, h_coupling_encoded])

    ppm_pred = model_dict["reg_ppm"].predict(X_proc)
    multiplicity_pred_enc = model_dict["clf_multiplicity"].predict(X_proc)
    multiplicity_pred = model_dict["label_multiplicity"].inverse_transform(
        multiplicity_pred_enc
    )

    couplings_pred_raw = model_dict["reg_couplings"].predict(X_proc)

    associations = []
    for i in range(len(X_test)):
        multiplicity = multiplicity_pred[i]
        num_H = X_test.iloc[i]["num_H"]
        nb_atoms = int(num_H) if not pd.isna(num_H) else None

        couplings = [float(c) for c in couplings_pred_raw[i] if c > 0.01]

        if multiplicity is not None:
            length = len(multiplicity)
            if len(couplings) > length:
                couplings = couplings[:length]
            elif len(couplings) < length:
                couplings += [0.0] * (length - len(couplings))

        associations.append(
            {
                "ppm": float(ppm_pred[i]),
                "atoms": [int(heavy_atom_idx_list[i])],
                "nb_atoms": nb_atoms,
                "multiplicity": multiplicity if multiplicity != "None" else None,
                "couplings": couplings,
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
            nb1 = current["nb_atoms"] or 1
            nb2 = assoc["nb_atoms"] or 1
            total_nb = nb1 + nb2

            current["ppm"] = (current["ppm"] * nb1 + assoc["ppm"] * nb2) / total_nb
            current["nb_atoms"] = total_nb
            current["atoms"].extend(assoc["atoms"])

            if multiplicity_complexity(assoc["multiplicity"]) > multiplicity_complexity(
                current["multiplicity"]
            ):
                current["multiplicity"] = assoc["multiplicity"]
                current["couplings"] = assoc["couplings"]

        else:
            merged.append(current)
            current = assoc.copy()

    merged.append(current)

    return merged
