import numpy as np
from itertools import product
from scipy.stats import norm


def get_basic_pattern(m):
    patterns = {
        "s": [1],
        "d": [1, 1],
        "t": [1, 2, 1],
        "q": [1, 3, 3, 1],
        "m": [1] * 5,
    }
    return patterns.get(m, [1])  # default = singulet


def get_subpeak_shifts(multiplicity, Js, center_ppm, spectrometer_freq=500.0):
    if not multiplicity or not Js:
        return [center_ppm], [1]

    letters = list(multiplicity.lower())

    if len(letters) == 1 and len(Js) > 1:
        letters = letters * len(Js)

    if len(Js) != len(letters):
        return [center_ppm], [1]

    spacing_sets = []
    intensities_sets = []

    for letter, J in zip(letters, Js):
        base_pattern = get_basic_pattern(letter)
        base_pattern = np.array(base_pattern) / np.sum(base_pattern)
        n = len(base_pattern)
        shifts_hz = np.linspace(-J * (n - 1) / 2, J * (n - 1) / 2, n)
        spacing_sets.append(shifts_hz)
        intensities_sets.append(base_pattern)

    all_combinations = list(product(*[range(len(s)) for s in spacing_sets]))

    positions = []
    intensities = []

    for comb in all_combinations:
        pos_hz = sum(spacing_sets[i][idx] for i, idx in enumerate(comb))
        pos_ppm = pos_hz / spectrometer_freq + center_ppm

        inten = 1
        for i, idx in enumerate(comb):
            inten *= intensities_sets[i][idx]

        positions.append(pos_ppm)
        intensities.append(inten)

    intensities = np.array(intensities)
    intensities /= intensities.sum()

    return positions, intensities


def simulate_spectrum(associations, fwhm=0.004, ppm_range=(0, 10), resolution=64000):
    x = np.linspace(ppm_range[1], ppm_range[0], resolution)
    y = np.zeros_like(x)
    atoms_ids = [set() for _ in range(len(x))]

    for assoc in associations:
        ppm = assoc["ppm"]
        J = assoc.get("couplings", [])
        mult = assoc.get("multiplicity", "s") or "s"
        nb_atoms = assoc.get("nb_atoms", 1)
        atom_ids = assoc.get("atoms", [])
        positions, intensities = get_subpeak_shifts(mult.lower(), J, ppm)

        for pos, amp in zip(positions, intensities):
            peak = nb_atoms * amp * norm.pdf(x, loc=pos, scale=fwhm / 2.355) * 5e4
            y += peak
            for i in range(len(x)):
                if peak[i] > 1e-3:
                    atoms_ids[i].update(atom_ids)

    return x, y, atoms_ids


def compress_spectrum_points_zero_segments(x, y, atoms_ids):
    zero_segments = []
    in_segment = False
    start_idx = None

    for i in range(len(y)):
        if y[i] == 0:
            if not in_segment:
                start_idx = i
                in_segment = True
        else:
            if in_segment:
                end_idx = i - 1
                zero_segments.append((start_idx, end_idx))
                in_segment = False

    if in_segment:
        zero_segments.append((start_idx, len(y) - 1))

    keep_indices = set(range(len(y)))
    for start, end in zero_segments:
        if end > start:
            to_remove = range(start + 1, end)
            keep_indices.difference_update(to_remove)

    indices_sorted = sorted(keep_indices)
    x_comp = x[indices_sorted]
    y_comp = y[indices_sorted]
    atoms_ids_comp = [atoms_ids[i] for i in indices_sorted]

    return x_comp, y_comp, atoms_ids_comp
