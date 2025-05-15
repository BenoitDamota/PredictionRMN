from rdkit import Chem
from rdkit.Chem import Draw
from rdkit.Chem.Draw import rdMolDraw2D
from io import BytesIO
from rdkit.Chem import rdchem


def generate_molecule_image_with_atom_ids(smiles: str) -> BytesIO:
    mol = Chem.MolFromSmiles(smiles)
    if not mol:
        raise ValueError("Invalid SMILES string")

    try:
        Chem.Kekulize(mol, clearAromaticFlags=True)
    except rdchem.KekulizationError as e:
        raise ValueError(f"Kekulization failed: {str(e)}")

    drawer = rdMolDraw2D.MolDraw2DCairo(400, 400)
    drawer.drawOptions().addAtomIndices = True
    drawer.DrawMolecule(mol)
    drawer.FinishDrawing()

    img_bytes = drawer.GetDrawingText()
    img_io = BytesIO(img_bytes)
    img_io.seek(0)
    return img_io
