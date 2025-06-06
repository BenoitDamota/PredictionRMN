from rdkit import Chem
from rdkit.Chem import rdPartialCharges, AllChem


def extract_features_for_C_atom(mol, carbon_idx):
    carbon_atom = mol.GetAtomWithIdx(carbon_idx)
    neighbors = carbon_atom.GetNeighbors()

    if not mol.HasProp("_GasteigerChargesComputed"):
        rdPartialCharges.ComputeGasteigerCharges(mol)
        mol.SetProp("_GasteigerChargesComputed", "1")

    try:
        charge = float(carbon_atom.GetProp("_GasteigerCharge"))
    except:
        charge = 0.0

    symmetry_classes = Chem.CanonicalRankAtoms(mol, breakTies=False)
    in_symmetric_env = symmetry_classes[carbon_idx]

    heavy_neighbors = [a for a in neighbors if a.GetAtomicNum() > 1]

    num_H_neighbors = sum(1 for a in neighbors if a.GetAtomicNum() == 1)

    hybridization = str(carbon_atom.GetHybridization())

    in_ring = int(carbon_atom.IsInRing())
    is_aromatic = int(carbon_atom.GetIsAromatic())
    formal_charge = carbon_atom.GetFormalCharge()

    degree = carbon_atom.GetDegree()

    neighbor_atomic_nums = ",".join(str(a.GetAtomicNum()) for a in heavy_neighbors)

    neighbor_types_count = {
        "C": sum(1 for a in heavy_neighbors if a.GetAtomicNum() == 6),
        "O": sum(1 for a in heavy_neighbors if a.GetAtomicNum() == 8),
        "N": sum(1 for a in heavy_neighbors if a.GetAtomicNum() == 7),
        "S": sum(1 for a in heavy_neighbors if a.GetAtomicNum() == 16),
        "Halogen": sum(
            1 for a in heavy_neighbors if a.GetAtomicNum() in [9, 17, 35, 53]
        ),
    }

    def shortest_distance_to_atom_type(atom_type):
        dists = []
        for atom in mol.GetAtoms():
            if atom.GetAtomicNum() == atom_type and atom.GetIdx() != carbon_idx:
                try:
                    path = Chem.rdmolops.GetShortestPath(mol, carbon_idx, atom.GetIdx())
                    dists.append(len(path) - 1)
                except:
                    continue
        return min(dists) if dists else -1

    dist_to_O = shortest_distance_to_atom_type(8)
    dist_to_N = shortest_distance_to_atom_type(7)
    aromatic_dists = [
        len(Chem.rdmolops.GetShortestPath(mol, carbon_idx, a.GetIdx())) - 1
        for a in mol.GetAtoms()
        if a.GetIdx() != carbon_idx and a.IsInRing() and a.GetIsAromatic()
    ]
    dist_to_aromatic = min(aromatic_dists) if aromatic_dists else -1

    feature_dict = {
        "heavy_atom_idx": carbon_idx,
        "degree": degree,
        "hybridization": hybridization,
        "in_ring": in_ring,
        "is_aromatic": is_aromatic,
        "formal_charge": formal_charge,
        "partial_charge": charge,
        "num_H_neighbors": num_H_neighbors,
        "num_heavy_neighbors": len(heavy_neighbors),
        "neighbor_atomic_nums": neighbor_atomic_nums,
        "neighbor_C_count": neighbor_types_count["C"],
        "neighbor_O_count": neighbor_types_count["O"],
        "neighbor_N_count": neighbor_types_count["N"],
        "neighbor_S_count": neighbor_types_count["S"],
        "neighbor_Halogen_count": neighbor_types_count["Halogen"],
        "dist_to_O": dist_to_O,
        "dist_to_N": dist_to_N,
        "dist_to_aromatic": dist_to_aromatic,
        "in_symmetric_env": int(in_symmetric_env),
    }

    return feature_dict


def extract_features_from_smiles(smiles):
    mol = Chem.MolFromSmiles(smiles)
    mol = Chem.AddHs(mol)
    AllChem.EmbedMolecule(mol, AllChem.ETKDG())

    all_features = []
    for atom in mol.GetAtoms():
        if atom.GetAtomicNum() == 6:
            feat = extract_features_for_C_atom(mol, atom.GetIdx())
            all_features.append(feat)

    import pandas as pd

    return pd.DataFrame(all_features)
