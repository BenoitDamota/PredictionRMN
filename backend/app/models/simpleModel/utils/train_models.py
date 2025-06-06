import pandas as pd
import ast
import os
from sklearn.model_selection import train_test_split
from app.models.simpleModel.H.model_utils_1h_v3 import train_model as train_model_1h
from app.models.simpleModel.C.model_utils_13c_v2 import train_model as train_model_13c
from joblib import dump

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TRAIN_DATASET_1H_PATH = os.path.join(BASE_DIR, "dataset_features_labels_1000_1h_v3.csv")
TRAIN_DATASET_13C_PATH = os.path.join(
    BASE_DIR, "dataset_features_labels_1000_13c_v2.csv"
)
MODEL_1H_PATH = os.path.join(BASE_DIR, "..", "H", "trained_model_1h_v3.joblib")
MODEL_13C_PATH = os.path.join(BASE_DIR, "..", "C", "trained_model_13c_v2.joblib")


def train_1h():
    df = pd.read_csv(TRAIN_DATASET_1H_PATH)

    df = df.dropna(subset=["ppm", "nb_atoms", "multiplicity"])

    df["couplings"] = df["couplings"].apply(
        lambda x: ast.literal_eval(x) if pd.notna(x) else []
    )

    X = df.drop(
        columns=["ppm", "nb_atoms", "multiplicity", "couplings", "heavy_atom_idx"]
    )
    X["neighbor_atomic_nums"] = X["neighbor_atomic_nums"].astype(str)
    y = df[["ppm", "nb_atoms", "multiplicity", "couplings"]]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    model_1h = train_model_1h(X_train, y_train)
    dump(model_1h, MODEL_1H_PATH, compress=3)


def train_13c():

    df = pd.read_csv(TRAIN_DATASET_13C_PATH)
    df = df.dropna(subset=["ppm", "nb_atoms", "multiplicity"])

    df["couplings"] = df["couplings"].apply(
        lambda x: ast.literal_eval(x) if pd.notna(x) else []
    )

    X = df.drop(
        columns=["ppm", "nb_atoms", "multiplicity", "couplings", "heavy_atom_idx"]
    )
    X["neighbor_atomic_nums"] = X["neighbor_atomic_nums"].astype(str)
    y = df[["ppm", "nb_atoms", "multiplicity", "couplings"]]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    model_13c = train_model_13c(X_train, y_train)
    dump(model_13c, MODEL_13C_PATH, compress=3)


def train_models():
    train_1h()
    train_13c()
