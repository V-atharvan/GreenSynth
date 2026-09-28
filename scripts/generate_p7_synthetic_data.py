"""
GreenSynth Analytics — Project P7 Synthetic Research Dataset Generator
Seed: 20260928

Generates a large, scientifically constrained, reproducible synthetic dataset for:
Project P7: Phytochemical synthesis of semiconducting copper oxide using mulberry
extract in ethanol by spray pyrolysis.

Target Material: CuO Thin Films
Primary ML Target: Electrical Conductivity (S/cm)
Calculated Properties: Crystallite Size (nm), Optical Band Gap (eV),
                       Electrical Resistance (Ohm), Resistivity (Ohm*cm), Conductivity (S/cm)

Output Directory: synthetic_data/p7/
"""

from __future__ import annotations

import csv
import json
import math
import os
import random
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import numpy as np

# Deterministic Seed
SEED = 20260928
random.seed(SEED)
np.random.seed(SEED)

PROJECT_ID = "268fa4a4-a396-4749-9621-39f1a9129684"
PROJECT_CODE = "P7"
PROJECT_NAME = "Phytochemical synthesis of semiconducting copper oxide using mulberry extract in ethanol by spray pyrolysis"
RESEARCHER = "GreenSynth Synthetic Research Team"

OUTPUT_DIR = Path("synthetic_data/p7")
RAW_XRD_DIR = OUTPUT_DIR / "raw" / "xrd"
RAW_UVVIS_DIR = OUTPUT_DIR / "raw" / "uvvis"
RAW_FTIR_DIR = OUTPUT_DIR / "raw" / "ftir"
RAW_ELEC_DIR = OUTPUT_DIR / "raw" / "electrical"

for d in [RAW_XRD_DIR, RAW_UVVIS_DIR, RAW_FTIR_DIR, RAW_ELEC_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# Substrate distribution weights
SUBSTRATES = ["Glass", "FTO Glass", "ITO Glass", "Quartz", "Silicon"]
SUBSTRATE_WEIGHTS = [0.60, 0.18, 0.10, 0.06, 0.06]

# Base date range: March 1, 2026 to September 20, 2026
START_DATE = date(2026, 3, 1)


def generate_experiment_parameters(exp_idx: int) -> tuple[dict[str, Any], str, str]:
    """
    Assign experimental parameters across 8 controlled DOE groups (A-H).
    Returns (params_dict, group_id, group_description).
    """
    # 1. Group assignment
    if 1 <= exp_idx <= 50:
        group_id = "GROUP_A"
        group_desc = "Baseline & Screening (Wide Factor Exploration)"
        t_sub = random.uniform(220.0, 440.0)
        c_prec = random.uniform(0.08, 0.45)
        v_prec = random.uniform(30.0, 150.0)
        c_ext = random.uniform(2.0, 30.0)
        v_ext = random.uniform(10.0, 45.0)
        v_eth = random.uniform(80.0, 220.0)
        sub_type = random.choices(SUBSTRATES, weights=SUBSTRATE_WEIGHTS)[0]
        spray_rate = random.uniform(2.0, 7.0)
        spray_dur = random.uniform(10.0, 40.0)
        dist = random.uniform(15.0, 28.0)
        gas_press = random.uniform(150.0, 280.0)
        cycles = random.randint(10, 35)

    elif 51 <= exp_idx <= 120:
        group_id = "GROUP_B"
        group_desc = "Substrate Temperature Factorial Study"
        t_steps = np.linspace(180.0, 480.0, 70)
        t_sub = float(t_steps[exp_idx - 51]) + random.gauss(0, 3.0)
        c_prec = random.choice([0.10, 0.20, 0.35]) + random.gauss(0, 0.01)
        v_prec = 80.0 + random.gauss(0, 5.0)
        c_ext = 15.0 + random.gauss(0, 1.0)
        v_ext = 20.0 + random.gauss(0, 1.5)
        v_eth = 150.0 + random.gauss(0, 5.0)
        sub_type = "Glass" if exp_idx % 4 != 0 else "FTO Glass"
        spray_rate = 4.0 + random.gauss(0, 0.2)
        spray_dur = 25.0 + random.gauss(0, 1.0)
        dist = 20.0 + random.gauss(0, 0.5)
        gas_press = 200.0 + random.gauss(0, 5.0)
        cycles = 20

    elif 121 <= exp_idx <= 190:
        group_id = "GROUP_C"
        group_desc = "Phytochemical Mulberry Extract Optimization"
        t_sub = 360.0 + random.gauss(0, 8.0)
        c_prec = 0.20 + random.gauss(0, 0.01)
        v_prec = 80.0 + random.gauss(0, 4.0)
        c_ext_steps = np.linspace(1.0, 40.0, 70)
        c_ext = float(c_ext_steps[exp_idx - 121]) + random.gauss(0, 0.5)
        v_ext = random.uniform(5.0, 55.0)
        v_eth = 150.0 + random.gauss(0, 5.0)
        sub_type = "Glass" if exp_idx % 3 != 0 else "FTO Glass"
        spray_rate = 4.5 + random.gauss(0, 0.3)
        spray_dur = 25.0 + random.gauss(0, 1.0)
        dist = 20.0 + random.gauss(0, 0.5)
        gas_press = 210.0 + random.gauss(0, 5.0)
        cycles = 20

    elif 191 <= exp_idx <= 250:
        group_id = "GROUP_D"
        group_desc = "Spray Dynamics & Deposition Kinetics Study"
        t_sub = 370.0 + random.gauss(0, 6.0)
        c_prec = 0.22 + random.gauss(0, 0.01)
        v_prec = 100.0 + random.gauss(0, 5.0)
        c_ext = 16.0 + random.gauss(0, 1.0)
        v_ext = 22.0 + random.gauss(0, 1.0)
        v_eth = 160.0 + random.gauss(0, 5.0)
        sub_type = random.choices(SUBSTRATES, weights=SUBSTRATE_WEIGHTS)[0]
        spray_rate = random.uniform(1.2, 9.0)
        spray_dur = random.uniform(6.0, 55.0)
        dist = 20.0 + random.gauss(0, 0.5)
        gas_press = random.uniform(110.0, 340.0)
        cycles = random.randint(6, 48)

    elif 251 <= exp_idx <= 290:
        group_id = "GROUP_E"
        group_desc = "Nozzle Distance & Thermal Stagnation Boundary"
        t_sub = 365.0 + random.gauss(0, 5.0)
        c_prec = 0.20 + random.gauss(0, 0.01)
        v_prec = 80.0 + random.gauss(0, 4.0)
        c_ext = 15.0 + random.gauss(0, 1.0)
        v_ext = 20.0 + random.gauss(0, 1.0)
        v_eth = 150.0 + random.gauss(0, 5.0)
        sub_type = "Glass" if exp_idx % 2 == 0 else "FTO Glass"
        dist_steps = np.linspace(10.0, 35.0, 40)
        dist = float(dist_steps[exp_idx - 251]) + random.gauss(0, 0.3)
        spray_rate = random.uniform(2.5, 6.0)
        spray_dur = 25.0 + random.gauss(0, 1.0)
        gas_press = random.uniform(140.0, 300.0)
        cycles = 20

    elif 291 <= exp_idx <= 340:
        group_id = "GROUP_F"
        group_desc = "Substrate Material & Environmental Sensitivity"
        t_sub = random.uniform(320.0, 400.0)
        c_prec = random.uniform(0.15, 0.30)
        v_prec = 80.0 + random.gauss(0, 5.0)
        c_ext = 16.0 + random.gauss(0, 1.5)
        v_ext = 20.0 + random.gauss(0, 1.5)
        v_eth = 150.0 + random.gauss(0, 5.0)
        sub_type = SUBSTRATES[(exp_idx - 291) % len(SUBSTRATES)]
        spray_rate = 4.0 + random.gauss(0, 0.2)
        spray_dur = 25.0 + random.gauss(0, 1.0)
        dist = 20.0 + random.gauss(0, 0.5)
        gas_press = 200.0 + random.gauss(0, 5.0)
        cycles = 20

    elif 341 <= exp_idx <= 380:
        group_id = "GROUP_G"
        group_desc = "Response Surface Methodology (RSM / CCD) Factorial"
        # 4-factor central composite box
        t_levels = [300.0, 340.0, 375.0, 410.0, 450.0]
        c_levels = [0.10, 0.15, 0.22, 0.30, 0.38]
        ext_c_levels = [5.0, 10.0, 16.0, 24.0, 32.0]
        ext_v_levels = [8.0, 15.0, 22.0, 32.0, 42.0]
        k = exp_idx - 341
        t_sub = t_levels[k % len(t_levels)] + random.gauss(0, 1.5)
        c_prec = c_levels[(k // 2) % len(c_levels)] + random.gauss(0, 0.005)
        c_ext = ext_c_levels[(k // 4) % len(ext_c_levels)] + random.gauss(0, 0.4)
        v_ext = ext_v_levels[(k // 5) % len(ext_v_levels)] + random.gauss(0, 0.5)
        v_prec = 90.0 + random.gauss(0, 3.0)
        v_eth = 160.0 + random.gauss(0, 4.0)
        sub_type = "Glass" if k % 3 != 0 else "FTO Glass"
        spray_rate = 4.2 + random.gauss(0, 0.2)
        spray_dur = 28.0 + random.gauss(0, 1.0)
        dist = 20.0 + random.gauss(0, 0.3)
        gas_press = 210.0 + random.gauss(0, 5.0)
        cycles = 22

    else:  # 381 <= exp_idx <= 400
        group_id = "GROUP_H"
        group_desc = "Replicate Center-Point & Reproducibility Assessment"
        # Central optimal operating point
        t_sub = 365.0 + random.gauss(0, 1.2)
        c_prec = 0.20 + random.gauss(0, 0.004)
        v_prec = 80.0 + random.gauss(0, 1.5)
        c_ext = 16.0 + random.gauss(0, 0.3)
        v_ext = 20.0 + random.gauss(0, 0.4)
        v_eth = 150.0 + random.gauss(0, 2.0)
        sub_type = "Glass" if exp_idx % 2 == 0 else "FTO Glass"
        spray_rate = 4.0 + random.gauss(0, 0.1)
        spray_dur = 25.0 + random.gauss(0, 0.5)
        dist = 20.0 + random.gauss(0, 0.2)
        gas_press = 200.0 + random.gauss(0, 2.0)
        cycles = 20

    # Ambient lab conditions with subtle seasonal and diurnal shift
    day_offset = int((exp_idx / 400.0) * 200)
    seasonal_temp = 22.0 + 5.0 * math.sin(2 * math.pi * day_offset / 365.0)
    seasonal_hum = 50.0 + 15.0 * math.cos(2 * math.pi * day_offset / 365.0)
    amb_temp = float(np.clip(seasonal_temp + random.gauss(0, 1.2), 16.0, 36.0))
    amb_hum = float(np.clip(seasonal_hum + random.gauss(0, 4.0), 20.0, 85.0))

    # Clamp all parameters to registered database bounds
    params = {
        "copper_precursor_salt": "Copper acetate monohydrate",
        "precursor_concentration": round(float(np.clip(c_prec, 0.005, 1.8)), 4),
        "precursor_solution_volume": round(float(np.clip(v_prec, 5.0, 450.0)), 1),
        "mulberry_extract_concentration": round(float(np.clip(c_ext, 0.2, 95.0)), 2),
        "mulberry_extract_volume": round(float(np.clip(v_ext, 0.5, 95.0)), 1),
        "ethanol_volume": round(float(np.clip(v_eth, 10.0, 450.0)), 1),
        "substrate_type": sub_type,
        "substrate_temperature_c": round(float(np.clip(t_sub, 120.0, 580.0)), 1),
        "spray_rate_ml_min": round(float(np.clip(spray_rate, 0.2, 18.0)), 2),
        "spray_duration_min": round(float(np.clip(spray_dur, 1.0, 110.0)), 1),
        "nozzle_substrate_distance_cm": round(float(np.clip(dist, 6.0, 48.0)), 1),
        "carrier_gas_pressure_kpa": round(float(np.clip(gas_press, 20.0, 480.0)), 1),
        "spray_cycles": int(np.clip(cycles, 1, 95)),
        "ambient_temperature_c": round(amb_temp, 1),
        "ambient_relative_humidity": round(amb_hum, 1),
    }

    return params, group_id, group_desc


def compute_physical_responses(params: dict[str, Any]) -> dict[str, float]:
    """
    Computes realistic physical and chemical properties based on spray pyrolysis
    crystallization physics and phytochemical capping kinetics.
    """
    t_sub = params["substrate_temperature_c"]
    c_prec = params["precursor_concentration"]
    v_prec = params["precursor_solution_volume"]
    c_ext = params["mulberry_extract_concentration"]
    v_ext = params["mulberry_extract_volume"]
    v_eth = params["ethanol_volume"]
    spray_rate = params["spray_rate_ml_min"]
    spray_dur = params["spray_duration_min"]
    dist = params["nozzle_substrate_distance_cm"]
    press = params["carrier_gas_pressure_kpa"]
    cycles = params["spray_cycles"]
    sub_type = params["substrate_type"]

    # 1. Deposition Thickness (nm)
    # Total delivered volume
    v_delivered = spray_rate * spray_dur
    # Thermal sticking / decomposition efficiency (sigmoidal around 230 C)
    thermal_eff = 1.0 / (1.0 + math.exp(-0.025 * (t_sub - 230.0)))
    # Distance attenuation factor (inverse square-like geometric spread)
    dist_factor = (20.0 / dist) ** 1.6
    # Droplet momentum factor from carrier pressure
    press_factor = 0.85 + 0.15 * (press / 200.0)

    t_nm = 260.0 * (c_prec / 0.2) * (v_delivered / 100.0) * thermal_eff * dist_factor * press_factor
    t_nm = float(t_nm * np.random.lognormal(mean=0.0, sigma=0.04))
    t_nm = float(np.clip(t_nm, 70.0, 950.0))

    # 2. Crystallite Size (nm) via Scherrer
    # Thermal growth follows Arrhenius-like progression
    d_thermal = 10.0 + 26.0 / (1.0 + math.exp(-0.018 * (t_sub - 330.0)))
    # Phytochemical capping factor: mulberry polyphenols and flavonoids cap nanoparticle growth
    capping = 1.0 - 0.22 * min(c_ext / 30.0, 1.0) - 0.08 * min(v_ext / 40.0, 1.0)
    # Precursor effect: higher concentration favors slightly larger grain coalescence
    prec_grain = 0.90 + 0.20 * min(c_prec / 0.3, 1.0)

    crystallite_size_nm = d_thermal * capping * prec_grain + random.gauss(0, 0.4)
    crystallite_size_nm = float(np.clip(crystallite_size_nm, 10.5, 42.0))

    # 3. Optical Band Gap (eV)
    # Bulk direct bandgap CuO ~ 1.35 eV
    # Quantum size effect: delta Eg ~ 1 / D^2
    quantum_shift = 55.0 / ((crystallite_size_nm + 3.0) ** 2)
    # Extract defect / carbonaceous state shift
    extract_shift = 0.035 * (c_ext / 30.0)
    # Temperature defect annealing
    temp_shift = -0.0003 * (t_sub - 350.0)

    band_gap_ev = 1.35 + quantum_shift + extract_shift + temp_shift + random.gauss(0, 0.015)
    band_gap_ev = float(np.clip(band_gap_ev, 1.32, 1.82))

    # 4. Electrical Conductivity (S/cm) [PRIMARY TARGET]
    # Optimal crystallization temperature bell curve (peak ~ 370 C)
    f_temp = math.exp(-((t_sub - 370.0) ** 2) / (2.0 * (65.0 ** 2)))
    # If temperature is below 220 C, decomposition is incomplete -> low conductivity
    if t_sub < 220.0:
        f_temp *= 0.15

    # Precursor concentration saturation curve
    f_prec = c_prec / (c_prec + 0.10)

    # Extract concentration: optimal at ~15-20 g/L (grain boundary passivation and nucleation control)
    # Excessive extract leaves insulating carbon residues
    x_ext = c_ext / 16.0
    f_ext = x_ext * math.exp(1.0 - x_ext)
    f_ext = max(0.1, min(f_ext, 1.0))

    # Film continuity factor (very thin films < 120 nm suffer from islanding/discontinuity)
    f_film = 1.0 / (1.0 + math.exp(-0.03 * (t_nm - 140.0)))

    # Substrate effect
    sub_multipliers = {
        "Glass": 1.0,
        "Quartz": 0.95,
        "Silicon": 1.12,
        "FTO Glass": 1.45,
        "ITO Glass": 1.50,
    }
    f_sub = sub_multipliers.get(sub_type, 1.0)

    # Base peak conductivity for green-synthesized CuO thin film ~ 0.85 S/cm
    sigma_peak = 0.85
    # Relative humidity interference (high humidity during spray increases droplet cooling and defects)
    f_hum = 1.0 - 0.15 * (params["ambient_relative_humidity"] / 100.0)

    conductivity_s_cm = (
        sigma_peak
        * (0.02 + 0.98 * f_temp * (0.35 + 0.65 * f_prec) * (0.30 + 0.70 * f_ext) * f_film)
        * f_sub
        * f_hum
    )
    # Add realistic experimental random variation (log-normal, sigma=0.08)
    conductivity_s_cm = float(conductivity_s_cm * np.random.lognormal(mean=0.0, sigma=0.07))
    conductivity_s_cm = float(np.clip(conductivity_s_cm, 0.001, 2.80))

    # 5. Electrical Resistivity (Ohm*cm) & Resistance (Ohm)
    # rho = 1 / sigma
    resistivity_ohm_cm = 1.0 / conductivity_s_cm

    # Sample geometry: standard rectangular thin film: Length L = 1.0 cm, Width W = 1.0 cm
    # Thickness t_cm = t_nm * 1e-7 cm
    t_cm = t_nm * 1e-7
    area_cm2 = 1.0 * t_cm
    # Resistance R = rho * (L / A)
    resistance_ohms = resistivity_ohm_cm * (1.0 / area_cm2)

    return {
        "thickness_nm": round(t_nm, 2),
        "crystallite_size_nm": round(crystallite_size_nm, 2),
        "band_gap_ev": round(band_gap_ev, 3),
        "conductivity_s_cm": round(conductivity_s_cm, 5),
        "resistivity_ohm_cm": round(resistivity_ohm_cm, 4),
        "resistance_ohms": round(resistance_ohms, 2),
    }


def generate_raw_xrd_file(
    filepath: Path, crystallite_size_nm: float, has_defects: bool = False
) -> None:
    """
    Generates synthetic XRD diffraction pattern (two_theta vs intensity) for monoclinic CuO.
    Peaks at 2theta: 32.5, 35.5 (-111), 38.7 (111), 48.7 (-202), 53.5 (020), 58.3 (202), 61.5, 66.2, 68.1.
    """
    two_thetas = np.arange(20.0, 70.05, 0.05)
    # Substrate amorphous glass hump centered at 2theta ~ 24 deg
    background = 120.0 + 85.0 * np.exp(-((two_thetas - 24.5) ** 2) / (2.0 * (6.0 ** 2)))
    background += np.random.poisson(lam=15, size=len(two_thetas))

    # Monoclinic CuO peak positions and relative intensities (JCPDS 05-0661)
    peaks = [
        (32.51, 140.0),
        (35.54, 1000.0),  # (-111)
        (38.73, 920.0),   # (111)
        (48.72, 280.0),   # (-202)
        (53.49, 160.0),   # (020)
        (58.27, 180.0),   # (202)
        (61.52, 220.0),   # (-113)
        (66.22, 190.0),   # (022)
        (68.12, 210.0),   # (220)
    ]

    wavelength_nm = 0.15406  # Cu K-alpha
    k_factor = 0.9

    total_intensity = background.copy()

    for p_pos, p_int in peaks:
        theta_rad = math.radians(p_pos / 2.0)
        # FWHM via Scherrer beta (in degrees)
        beta_rad = (k_factor * wavelength_nm) / (crystallite_size_nm * math.cos(theta_rad))
        beta_deg = math.degrees(beta_rad)
        if has_defects:
            beta_deg *= 1.4

        sigma = beta_deg / 2.35482  # Gaussian std dev
        peak_shape = p_int * np.exp(-((two_thetas - p_pos) ** 2) / (2.0 * (sigma ** 2)))
        total_intensity += peak_shape

    # Save to CSV
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["two_theta", "intensity"])
        for tt, val in zip(two_thetas, total_intensity):
            writer.writerow([f"{tt:.2f}", f"{max(0.0, val):.2f}"])


def generate_raw_uvvis_file(filepath: Path, band_gap_ev: float, thickness_nm: float) -> None:
    """
    Generates synthetic UV-Vis absorbance spectrum (wavelength_nm vs absorbance).
    Direct transition Tauc relation: alpha * h_nu = A * (h_nu - Eg)^0.5
    """
    wavelengths = np.arange(350, 902, 2)
    absorbances = []

    hc = 1239.84193  # eV * nm
    t_cm = thickness_nm * 1e-7

    for wl in wavelengths:
        energy_ev = hc / wl
        if energy_ev > band_gap_ev:
            # Direct band gap absorption
            alpha = 1.2e5 * math.sqrt(energy_ev - band_gap_ev) / energy_ev
            abs_val = alpha * t_cm + 0.12  # baseline glass transmission loss
        else:
            # Sub-bandgap Urbach tail / baseline scattering
            abs_val = 0.12 + 0.08 * math.exp((energy_ev - band_gap_ev) / 0.08)

        abs_val += random.gauss(0, 0.004)
        absorbances.append(max(0.01, abs_val))

    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["wavelength_nm", "absorbance"])
        for wl, val in zip(wavelengths, absorbances):
            writer.writerow([int(wl), f"{val:.4f}"])


def generate_raw_ftir_file(filepath: Path, extract_conc: float) -> None:
    """
    Generates synthetic FTIR transmission spectrum (%T vs wavenumber cm-1).
    Cu-O vibrational modes at 530 and 590 cm-1; mulberry organic bands at 1050, 1630, 2920, 3350 cm-1.
    """
    wavenumbers = np.arange(400, 4005, 5)
    transmittance = np.ones(len(wavenumbers)) * 96.0 + np.random.normal(0, 0.25, len(wavenumbers))

    # Characteristic peaks: (center cm-1, width cm-1, depth %T reduction)
    cuo_peaks = [
        (535.0, 35.0, 45.0),  # Cu-O stretching
        (595.0, 40.0, 38.0),  # Cu-O bending
    ]
    # Organic residues from mulberry phytochemicals
    ext_scale = min(extract_conc / 30.0, 1.2)
    org_peaks = [
        (1055.0, 60.0, 22.0 * ext_scale),   # C-O flavonoid stretch
        (1635.0, 70.0, 28.0 * ext_scale),   # C=O amide/polyphenol stretch
        (2925.0, 45.0, 14.0 * ext_scale),   # C-H alkane stretch
        (3370.0, 220.0, 35.0 * ext_scale),  # O-H broad polyphenol/hydroxyl stretch
    ]

    for c, w, d in cuo_peaks + org_peaks:
        peak_dip = d * np.exp(-((wavenumbers - c) ** 2) / (2.0 * ((w / 2.355) ** 2)))
        transmittance -= peak_dip

    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["wavenumber_cm1", "transmittance_pct"])
        for wn, val in zip(wavenumbers, transmittance):
            writer.writerow([int(wn), f"{np.clip(val, 5.0, 100.0):.2f}"])


def generate_raw_electrical_file(filepath: Path, resistance_ohms: float) -> None:
    """
    Generates synthetic linear I-V curve (voltage_v vs current_a).
    Sweeps from -2.0 V to +2.0 V in steps of 0.1 V (41 points).
    """
    voltages = np.arange(-2.0, 2.05, 0.1)
    currents = []

    # Instrumental noise level
    noise_sigma = max(1e-9, (2.0 / resistance_ohms) * 0.008)

    for v in voltages:
        ideal_i = v / resistance_ohms
        actual_i = ideal_i + random.gauss(0, noise_sigma)
        currents.append(actual_i)

    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["voltage_v", "current_a"])
        for v, i in zip(voltages, currents):
            writer.writerow([f"{v:.2f}", f"{i:.8e}"])


def build_synthetic_dataset() -> dict[str, Any]:
    """
    Main generator pipeline for 400 experiments, samples, parameters, characterizations,
    raw data files, and calculated properties.
    """
    print(f"=================================================================")
    print(f" GreenSynth Analytics — Generating P7 Synthetic Research Dataset")
    print(f" Seed: {SEED} | Project: {PROJECT_CODE}")
    print(f" Target experiments: 400 | Material: CuO | Method: Spray Pyrolysis")
    print(f"=================================================================")

    experiments: list[dict[str, Any]] = []
    samples: list[dict[str, Any]] = []
    all_calc_props: list[dict[str, Any]] = []
    manifest_entries: list[dict[str, Any]] = []

    total_exp = 400
    group_counts: dict[str, int] = {}
    technique_counts = {"XRD": 0, "UV_VIS": 0, "FTIR": 0, "ELECTRICAL": 0}
    status_counts = {"COMPLETED": 0, "FAILED": 0, "IN_PROGRESS": 0, "PLANNED": 0}

    # Tracking for summary statistics
    all_conductivities: list[float] = []
    all_bandgaps: list[float] = []
    all_crystallite_sizes: list[float] = []
    all_temperatures: list[float] = []
    all_precursor_concs: list[float] = []
    all_extract_concs: list[float] = []

    for idx in range(1, total_exp + 1):
        exp_code = f"P7-SYNTH-{idx:03d}"
        exp_date = START_DATE + timedelta(days=int((idx / total_exp) * 200))

        params, group_id, group_desc = generate_experiment_parameters(idx)
        group_counts[group_id] = group_counts.get(group_id, 0) + 1

        # Status distribution:
        # Runs 38, 79, 114, 185, 230, 281, 312, 335, 362, 377, 395, 398 are failed (peeling / non-uniform)
        failed_indices = {38, 79, 114, 185, 230, 281, 312, 335, 362, 377, 395, 398}
        in_progress_indices = {396, 397, 399, 400}
        planned_indices = {391, 392}

        if idx in failed_indices:
            status = "FAILED"
            exp_notes = f"SYNTHETIC SIMULATED EXPERIMENT [{group_id}]. Deposition failure: film non-uniformity or peeling observed at substrate boundary. Seed={SEED}."
        elif idx in in_progress_indices:
            status = "IN_PROGRESS"
            exp_notes = f"SYNTHETIC SIMULATED EXPERIMENT [{group_id}]. In-progress active deposition run. Seed={SEED}."
        elif idx in planned_indices:
            status = "PLANNED"
            exp_notes = f"SYNTHETIC SIMULATED EXPERIMENT [{group_id}]. Planned validation condition. Seed={SEED}."
        else:
            status = "COMPLETED"
            exp_notes = f"SYNTHETIC SIMULATED EXPERIMENT [{group_id}]: {group_desc}. Strict validation dataset. Seed={SEED}."

        status_counts[status] = status_counts.get(status, 0) + 1

        exp_record = {
            "experiment_code": exp_code,
            "title": f"P7 Spray Pyrolysis Synthetic Run {idx:03d} - {group_id}",
            "status": status,
            "experiment_date": exp_date.isoformat(),
            "researcher": RESEARCHER,
            "notes": exp_notes,
            "group_id": group_id,
            "group_description": group_desc,
            "parameters": params,
        }
        experiments.append(exp_record)

        # Track input distribution
        all_temperatures.append(params["substrate_temperature_c"])
        all_precursor_concs.append(params["precursor_concentration"])
        all_extract_concs.append(params["mulberry_extract_concentration"])

        # Determine number of samples: Group H (replicates) gets 2 samples (S01, S02), others get 1
        num_samples = 2 if group_id == "GROUP_H" and status == "COMPLETED" else 1

        for s_idx in range(1, num_samples + 1):
            sample_code = f"{exp_code}-S{s_idx:02d}"
            sample_name = f"CuO Thin Film - {exp_code}-S{s_idx:02d}"

            # Compute physical response (if replicates, add slight intra-batch variation)
            responses = compute_physical_responses(params)
            if s_idx > 1:
                responses["conductivity_s_cm"] = round(
                    responses["conductivity_s_cm"] * random.uniform(0.96, 1.04), 5
                )
                responses["resistivity_ohm_cm"] = round(
                    1.0 / responses["conductivity_s_cm"], 4
                )
                responses["resistance_ohms"] = round(
                    responses["resistance_ohms"] * random.uniform(0.96, 1.04), 2
                )
                responses["crystallite_size_nm"] = round(
                    responses["crystallite_size_nm"] + random.gauss(0, 0.2), 2
                )
                responses["band_gap_ev"] = round(
                    responses["band_gap_ev"] + random.gauss(0, 0.005), 3
                )

            sample_record = {
                "sample_code": sample_code,
                "experiment_code": exp_code,
                "name": sample_name,
                "material": "CuO",
                "description": f"Spray pyrolyzed CuO thin film on {params['substrate_type']} ({responses['thickness_nm']} nm).",
                "status": "COMPLETED" if status == "COMPLETED" else "ARCHIVED",
                "notes": f"Synthetic specimen. Provenance: {RESEARCHER}. Replicate={s_idx}/{num_samples}.",
                "characterizations": [],
            }

            # Decide characterization suite based on missingness profile
            # Only completed experiments have full characterization; failed may have 0 or 1
            sample_chars: list[dict[str, Any]] = []

            if status == "COMPLETED":
                # Missingness distribution:
                # 68% full suite (XRD, UV_VIS, FTIR, ELECTRICAL)
                # 20% missing 1 technique (e.g., missing FTIR or UV_VIS)
                # 9% missing 2 techniques (e.g., XRD + ELECTRICAL only)
                # 3% missing 3 techniques (e.g., ELECTRICAL only)
                miss_rand = random.random()
                if miss_rand < 0.68:
                    techniques = ["XRD", "UV_VIS", "FTIR", "ELECTRICAL"]
                elif miss_rand < 0.88:
                    # Drop FTIR or UV_VIS
                    techniques = ["XRD", "UV_VIS", "ELECTRICAL"] if random.random() < 0.6 else ["XRD", "FTIR", "ELECTRICAL"]
                elif miss_rand < 0.97:
                    # Drop 2
                    techniques = ["XRD", "ELECTRICAL"]
                else:
                    techniques = ["ELECTRICAL"]
            elif status == "FAILED":
                # Failed experiment might only have an incomplete XRD or SEM
                techniques = ["XRD"] if idx % 2 == 0 else []
            else:
                techniques = []

            for tech in techniques:
                technique_counts[tech] += 1
                ch_id_str = f"{sample_code}_{tech}"

                raw_filename = f"{sample_code}_{tech}.csv"
                if tech == "XRD":
                    raw_path = RAW_XRD_DIR / raw_filename
                    generate_raw_xrd_file(raw_path, responses["crystallite_size_nm"])
                    calc_props = [
                        {
                            "property_name": "Crystallite Size",
                            "value": responses["crystallite_size_nm"],
                            "unit": "nm",
                            "calculation_method": "Scherrer Equation",
                            "formula": "D = (K * lambda) / (beta * cos(theta))",
                        }
                    ]
                    all_crystallite_sizes.append(responses["crystallite_size_nm"])

                elif tech == "UV_VIS":
                    raw_path = RAW_UVVIS_DIR / raw_filename
                    generate_raw_uvvis_file(
                        raw_path, responses["band_gap_ev"], responses["thickness_nm"]
                    )
                    calc_props = [
                        {
                            "property_name": "Optical Band Gap",
                            "value": responses["band_gap_ev"],
                            "unit": "eV",
                            "calculation_method": "Tauc Plot Linear Extrapolation",
                            "formula": "(alpha * h * nu)^(1/n) vs h * nu",
                        }
                    ]
                    all_bandgaps.append(responses["band_gap_ev"])

                elif tech == "FTIR":
                    raw_path = RAW_FTIR_DIR / raw_filename
                    generate_raw_ftir_file(
                        raw_path, params["mulberry_extract_concentration"]
                    )
                    calc_props = []

                elif tech == "ELECTRICAL":
                    raw_path = RAW_ELEC_DIR / raw_filename
                    generate_raw_electrical_file(raw_path, responses["resistance_ohms"])
                    calc_props = [
                        {
                            "property_name": "Electrical Resistance",
                            "value": responses["resistance_ohms"],
                            "unit": "Ohm",
                            "calculation_method": "Ohm's Law Linear Regression",
                            "formula": "V = I * R",
                        },
                        {
                            "property_name": "Electrical Resistivity",
                            "value": responses["resistivity_ohm_cm"],
                            "unit": "Ohm*cm",
                            "calculation_method": "Geometric Resistance Formula",
                            "formula": "rho = R * A / L",
                        },
                        {
                            "property_name": "Electrical Conductivity",
                            "value": responses["conductivity_s_cm"],
                            "unit": "S/cm",
                            "calculation_method": "Reciprocal Resistivity",
                            "formula": "sigma = 1 / rho",
                        },
                    ]
                    all_conductivities.append(responses["conductivity_s_cm"])

                # Save calculated properties to global tracking
                for cp in calc_props:
                    all_calc_props.append({
                        "experiment_code": exp_code,
                        "sample_code": sample_code,
                        "technique": tech,
                        **cp,
                    })

                char_entry = {
                    "technique": tech,
                    "status": "ANALYZED",
                    "operator": "Synthetic Instrument Simulator",
                    "instrument_name": f"GreenSynth {tech} Station",
                    "instrument_model": f"GS-{tech}-2026",
                    "raw_file": {
                        "filename": raw_filename,
                        "relative_path": str(raw_path.relative_to(OUTPUT_DIR)).replace("\\", "/"),
                        "data_origin": "SYNTHETIC",
                        "random_seed": SEED,
                    },
                    "calculated_properties": calc_props,
                }
                sample_chars.append(char_entry)

            sample_record["characterizations"] = sample_chars
            samples.append(sample_record)

            manifest_entries.append({
                "experiment_code": exp_code,
                "sample_code": sample_code,
                "group_id": group_id,
                "status": status,
                "substrate_type": params["substrate_type"],
                "substrate_temperature_c": params["substrate_temperature_c"],
                "precursor_concentration": params["precursor_concentration"],
                "mulberry_extract_concentration": params["mulberry_extract_concentration"],
                "mulberry_extract_volume": params["mulberry_extract_volume"],
                "spray_rate_ml_min": params["spray_rate_ml_min"],
                "spray_duration_min": params["spray_duration_min"],
                "thickness_nm": responses["thickness_nm"],
                "crystallite_size_nm": responses["crystallite_size_nm"],
                "band_gap_ev": responses["band_gap_ev"],
                "electrical_conductivity_s_cm": responses["conductivity_s_cm"],
                "techniques_measured": [c["technique"] for c in sample_chars],
            })

    # Summary Statistics Calculation
    stats = {
        "dataset_name": "Project P7 Spray Pyrolysis Synthetic Research Dataset",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "random_seed": SEED,
        "provenance": {
            "creator": RESEARCHER,
            "project_id": PROJECT_ID,
            "project_code": PROJECT_CODE,
            "material": "CuO",
            "solvent": "Ethanol",
            "extract": "Mulberry",
            "method": "Spray Pyrolysis",
            "disclaimer": "SYNTHETIC / SIMULATED DATA FOR PLATFORM VALIDATION AND ML TESTING. NOT REAL LAB MEASUREMENTS.",
        },
        "experiment_counts": {
            "total_experiments": total_exp,
            "by_status": status_counts,
            "by_group": group_counts,
        },
        "sample_counts": {
            "total_samples": len(samples),
            "single_sample_experiments": total_exp - (len(samples) - total_exp),
            "replicate_sample_experiments": len(samples) - total_exp,
        },
        "characterization_counts": {
            "total_characterizations": sum(technique_counts.values()),
            "by_technique": technique_counts,
        },
        "calculated_properties_count": len(all_calc_props),
        "target_property_metrics": {
            "property_name": "Electrical Conductivity",
            "unit": "S/cm",
            "count": len(all_conductivities),
            "mean": float(np.mean(all_conductivities)),
            "std": float(np.std(all_conductivities)),
            "min": float(np.min(all_conductivities)),
            "q25": float(np.percentile(all_conductivities, 25)),
            "median": float(np.median(all_conductivities)),
            "q75": float(np.percentile(all_conductivities, 75)),
            "max": float(np.max(all_conductivities)),
        },
        "feature_metrics": {
            "substrate_temperature_c": {
                "mean": float(np.mean(all_temperatures)),
                "min": float(np.min(all_temperatures)),
                "max": float(np.max(all_temperatures)),
            },
            "precursor_concentration_mol_l": {
                "mean": float(np.mean(all_precursor_concs)),
                "min": float(np.min(all_precursor_concs)),
                "max": float(np.max(all_precursor_concs)),
            },
            "mulberry_extract_concentration_g_l": {
                "mean": float(np.mean(all_extract_concs)),
                "min": float(np.min(all_extract_concs)),
                "max": float(np.max(all_extract_concs)),
            },
            "crystallite_size_nm": {
                "mean": float(np.mean(all_crystallite_sizes)),
                "min": float(np.min(all_crystallite_sizes)),
                "max": float(np.max(all_crystallite_sizes)),
            },
            "band_gap_ev": {
                "mean": float(np.mean(all_bandgaps)),
                "min": float(np.min(all_bandgaps)),
                "max": float(np.max(all_bandgaps)),
            },
        },
    }

    # Save manifest.json
    manifest_path = OUTPUT_DIR / "dataset_manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "metadata": stats["provenance"],
                "experiments": experiments,
                "samples": samples,
            },
            f,
            indent=2,
        )
    print(f" Saved dataset manifest -> {manifest_path}")

    # Save dataset_statistics.json
    stats_path = OUTPUT_DIR / "dataset_statistics.json"
    with open(stats_path, "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2)
    print(f" Saved dataset statistics -> {stats_path}")

    # Save experiments_summary.csv
    exp_csv_path = OUTPUT_DIR / "experiments_summary.csv"
    with open(exp_csv_path, "w", newline="", encoding="utf-8") as f:
        fieldnames = [
            "experiment_code",
            "sample_code",
            "group_id",
            "status",
            "substrate_type",
            "substrate_temperature_c",
            "precursor_concentration",
            "mulberry_extract_concentration",
            "mulberry_extract_volume",
            "spray_rate_ml_min",
            "spray_duration_min",
            "thickness_nm",
            "crystallite_size_nm",
            "band_gap_ev",
            "electrical_conductivity_s_cm",
            "techniques_measured",
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in manifest_entries:
            row_copy = row.copy()
            row_copy["techniques_measured"] = ";".join(row_copy["techniques_measured"])
            writer.writerow(row_copy)
    print(f" Saved experiments summary CSV -> {exp_csv_path}")

    # Save calculated_properties_summary.csv
    calc_csv_path = OUTPUT_DIR / "calculated_properties_summary.csv"
    with open(calc_csv_path, "w", newline="", encoding="utf-8") as f:
        fieldnames = [
            "experiment_code",
            "sample_code",
            "technique",
            "property_name",
            "value",
            "unit",
            "calculation_method",
            "formula",
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in all_calc_props:
            writer.writerow(row)
    print(f" Saved calculated properties summary CSV -> {calc_csv_path}")

    # Save README.md
    readme_path = OUTPUT_DIR / "README.md"
    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(f"""# Project P7 Synthetic Research Dataset

> **SCIENTIFIC INTEGRITY DISCLAIMER**  
> **THIS IS STRICTLY SYNTHETIC / SIMULATED DATA GENERATED FOR SOFTWARE VERIFICATION, END-TO-END WORKFLOW TESTING, AND MACHINE LEARNING PIPELINE BENCHMARKING.**  
> **DO NOT PRESENT, CITE, OR USE AS REAL LABORATORY MEASUREMENTS.**

## Dataset Overview
- **Project Code:** `{PROJECT_CODE}`
- **Project ID:** `{PROJECT_ID}`
- **Material System:** Nanocrystalline Copper Oxide (CuO) Thin Films
- **Synthesis Method:** Spray Pyrolysis
- **Plant Extract:** Mulberry (*Morus*) Extract in Ethanol
- **Deterministic Seed:** `{SEED}`
- **Generation Timestamp:** `{datetime.now(timezone.utc).isoformat()}`
- **Creator / Provenance:** `{RESEARCHER}`

## Content & Scale
- **Total Experiments:** {total_exp} (`P7-SYNTH-001` to `P7-SYNTH-{total_exp:03d}`)
- **Total Samples:** {len(samples)} (including replicate samples in Group H)
- **Status Breakdown:**
  - Completed: {status_counts['COMPLETED']}
  - Failed (Peeling / non-uniform): {status_counts['FAILED']}
  - In Progress: {status_counts['IN_PROGRESS']}
  - Planned: {status_counts['PLANNED']}
- **Total Characterizations:** {sum(technique_counts.values())}
  - XRD Patterns: {technique_counts['XRD']}
  - UV-Vis Spectra: {technique_counts['UV_VIS']}
  - FTIR Spectra: {technique_counts['FTIR']}
  - Electrical I-V Curves: {technique_counts['ELECTRICAL']}
- **Calculated Properties:** {len(all_calc_props)} records

## Primary ML Target: Electrical Conductivity (S/cm)
- **Mean:** {stats['target_property_metrics']['mean']:.4f} S/cm
- **Median:** {stats['target_property_metrics']['median']:.4f} S/cm
- **Min:** {stats['target_property_metrics']['min']:.4f} S/cm
- **Max:** {stats['target_property_metrics']['max']:.4f} S/cm
- **Standard Deviation:** {stats['target_property_metrics']['std']:.4f} S/cm
""")
    print(f" Saved README -> {readme_path}")
    print(f"=================================================================")
    print(f" Generation complete: {total_exp} experiments, {len(samples)} samples, {sum(technique_counts.values())} characterizations.")
    print(f"=================================================================")
    return stats


if __name__ == "__main__":
    build_synthetic_dataset()
