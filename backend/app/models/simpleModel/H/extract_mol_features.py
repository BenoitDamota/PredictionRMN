from rdkit import Chem
from rdkit.Chem import rdPartialCharges, AllChem
from collections import defaultdict
import pandas as pd


def get_equivalent_H_groups(mol):
    try:
        Chem.Kekulize(mol, clearAromaticFlags=True)
    except:
        # Si Kekulize échoue, on continue sans arrêt (mol peut rester aromatique)
        pass

    atom_to_H = defaultdict(list)
    for atom in mol.GetAtoms():
        if atom.GetAtomicNum() == 1:
            neighbor = atom.GetNeighbors()[0].GetIdx()
            atom_to_H[neighbor].append(atom.GetIdx())
    return atom_to_H


from rdkit.Chem import rdMolDescriptors


def extract_features_for_H_group(mol, heavy_idx, H_indices, groups):
    heavy_atom = mol.GetAtomWithIdx(heavy_idx)
    neighbors = [a for a in heavy_atom.GetNeighbors() if a.GetAtomicNum() > 1]

    if not mol.HasProp("_GasteigerChargesComputed"):
        rdPartialCharges.ComputeGasteigerCharges(mol)
        mol.SetProp("_GasteigerChargesComputed", "1")

    try:
        charge = float(heavy_atom.GetProp("_GasteigerCharge"))
    except:
        charge = 0.0

    # Utilisation de CanonicalRankAtoms pour la symétrie
    symmetry_classes = Chem.CanonicalRankAtoms(mol, breakTies=False)
    in_symmetric_env = symmetry_classes[heavy_idx]  # même classe signifie symétrie

    # Nombre de voisins H par atome voisin
    neighbor_H_counts = []
    for nbr in neighbors:
        nbr_H = sum(1 for a in nbr.GetNeighbors() if a.GetAtomicNum() == 1)
        neighbor_H_counts.append(nbr_H)
    neighbor_H_counts_str = ",".join(map(str, neighbor_H_counts))

    # Nombre de protons couplables (non équivalents à 2-3 liaisons)
    def is_non_equivalent_H(h_idx):
        for g_heavy, g_H in groups.items():
            if h_idx in g_H and g_heavy != heavy_idx:
                return True
        return False

    num_couplable_H_neighbors = 0
    for atom in mol.GetAtoms():
        if atom.GetAtomicNum() == 1 and is_non_equivalent_H(atom.GetIdx()):
            dist = Chem.rdmolops.GetShortestPath(
                mol, heavy_idx, atom.GetNeighbors()[0].GetIdx()
            )
            if 2 <= len(dist) - 1 <= 3:
                num_couplable_H_neighbors += 1

    # Distance au proton non équivalent le plus proche
    distances = []
    for atom in mol.GetAtoms():
        if atom.GetAtomicNum() == 1 and is_non_equivalent_H(atom.GetIdx()):
            path = Chem.rdmolops.GetShortestPath(
                mol, heavy_idx, atom.GetNeighbors()[0].GetIdx()
            )
            distances.append(len(path) - 1)
    distance_to_nearest_non_equivalent_H = min(distances) if distances else -1

    # Type de couplage (simplifié)
    if distance_to_nearest_non_equivalent_H == 2:
        H_coupling_type = "geminal"
    elif distance_to_nearest_non_equivalent_H == 3:
        H_coupling_type = "vicinal"
    elif distance_to_nearest_non_equivalent_H > 3:
        H_coupling_type = "long-range"
    else:
        H_coupling_type = "none"

    # Position structurale simple
    is_in_CH3 = heavy_atom.GetDegree() == 1 and len(H_indices) == 3
    is_in_CH2 = heavy_atom.GetDegree() == 2 and len(H_indices) == 2
    is_terminal_CH = heavy_atom.GetDegree() == 1 and len(H_indices) == 1

    feature_dict = {
        "heavy_atom_idx": heavy_idx,
        "num_H": len(H_indices),
        "heavy_atomic_num": heavy_atom.GetAtomicNum(),
        "heavy_degree": heavy_atom.GetDegree(),
        "heavy_hybridization": str(heavy_atom.GetHybridization()),
        "heavy_in_ring": int(heavy_atom.IsInRing()),
        "heavy_is_aromatic": int(heavy_atom.GetIsAromatic()),
        "heavy_formal_charge": heavy_atom.GetFormalCharge(),
        "heavy_partial_charge": charge,
        "num_heavy_neighbors": len(neighbors),
        "neighbor_atomic_nums": ",".join(str(n.GetAtomicNum()) for n in neighbors),
        "num_H_neighbors": sum(
            1 for n in heavy_atom.GetNeighbors() if n.GetAtomicNum() == 1
        ),
        "neighbor_H_counts_per_atom": neighbor_H_counts_str,
        "num_couplable_H_neighbors": num_couplable_H_neighbors,
        "distance_to_nearest_non_equivalent_H": distance_to_nearest_non_equivalent_H,
        "in_symmetric_env": int(in_symmetric_env),
        "H_coupling_type": H_coupling_type,
        "is_in_CH3": int(is_in_CH3),
        "is_in_CH2": int(is_in_CH2),
        "is_terminal_CH": int(is_terminal_CH),
    }

    return feature_dict


def extract_features_from_smiles(smiles):
    mol = Chem.MolFromSmiles(smiles)
    mol = Chem.AddHs(mol)
    AllChem.EmbedMolecule(mol, AllChem.ETKDG())

    groups = get_equivalent_H_groups(mol)
    all_features = []

    for heavy_idx, H_indices in groups.items():
        feat = extract_features_for_H_group(mol, heavy_idx, H_indices, groups)
        all_features.append(feat)

    return pd.DataFrame(all_features)
