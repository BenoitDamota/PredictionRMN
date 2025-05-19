import json
import numpy as np
from scipy.signal import savgol_filter, find_peaks


def guess_nmr_type(ppm, intensity):
    ppm_range = max(ppm) - min(ppm)
    if ppm_range > 100:
        return "13C"
    elif ppm_range < 15:
        return "1H"
    return "1H"  # default value


def detect_peaks(ppm, intensity, height_ratio=0.02, prominence=0.05, distance=5):
    smoothed_intensity = savgol_filter(intensity, window_length=11, polyorder=3)

    max_height = np.max(smoothed_intensity)
    height_threshold = height_ratio * max_height

    peaks, properties = find_peaks(
        smoothed_intensity,
        height=height_threshold,
        prominence=prominence * max_height,
        distance=distance,
        width=1,
    )
    return peaks


def group_peaks_into_regions(ppm, peak_indices, delta_ppm):
    peak_ppms = ppm[peak_indices]
    sorted_indices = np.argsort(peak_ppms)
    groups = []
    current_group = [peak_indices[sorted_indices[0]]]

    for i in range(1, len(sorted_indices)):
        prev_idx = peak_indices[sorted_indices[i - 1]]
        curr_idx = peak_indices[sorted_indices[i]]
        if abs(ppm[curr_idx] - ppm[prev_idx]) <= delta_ppm:
            current_group.append(curr_idx)
        else:
            groups.append(current_group)
            current_group = [curr_idx]

    if current_group:
        groups.append(current_group)

    return groups


def analyze_spectrum(ppm, intensity, atom_ids, spectrum_type="auto"):
    ppm = np.array(ppm)
    intensity = np.array(intensity)

    if spectrum_type == "auto":
        spectrum_type = guess_nmr_type(ppm, intensity)

    delta_ppm = 0.03 if spectrum_type.startswith("1H") else 0.15

    peak_indices = detect_peaks(ppm, intensity)
    grouped_regions = group_peaks_into_regions(ppm, peak_indices, delta_ppm)

    region_info = []
    for group in grouped_regions:
        region_ppm = ppm[group]
        region_intensities = intensity[group]
        center_ppm = np.mean(region_ppm)
        ppm_min = float(np.min(region_ppm)) - 0.005
        ppm_max = float(np.max(region_ppm)) + 0.005
        max_intensity = float(np.max(region_intensities))

        multiplicity = [
            {"ppm": float(ppm[i]), "intensity": float(intensity[i])} for i in group
        ]
        multiplicity.sort(key=lambda x: -x["ppm"])

        # Find atom IDs between ppmMin and ppmMax
        region_atom_ids = set()
        for i in range(len(ppm)):
            if ppm_min <= ppm[i] <= ppm_max:
                if atom_ids[i]:
                    region_atom_ids.update(atom_ids[i])

        region_info.append(
            {
                "center": center_ppm,
                "ppmMin": ppm_min,
                "ppmMax": ppm_max,
                "intensityMax": max_intensity,
                "multiplicity": multiplicity,
                "atomIds": list(region_atom_ids),
            }
        )

    # Sort by decreasing ppm
    region_info.sort(key=lambda x: -x["center"])

    formatted_regions = []
    for i, region in enumerate(region_info):
        formatted_regions.append(
            {
                "regionId": str(i),
                "ppmMin": region["ppmMin"],
                "ppmMax": region["ppmMax"],
                "intensityMax": region["intensityMax"],
                "multiplicity": region["multiplicity"],
                "atomIds": region["atomIds"],
            }
        )

    return formatted_regions
