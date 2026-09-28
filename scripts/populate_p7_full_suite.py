"""
GreenSynth Analytics — Project P7 Full 5-Technique Suite & Curve Enrichment Script
Seed: 20260928

Ensures that every experiment / sample in Project P7 has:
  1. All 5 Characterization Techniques (XRD, UV_VIS, FTIR, SEM, ELECTRICAL)
  2. Full Raw Files on disk (data/raw/ and backend/data/raw/) with SHA-256 validation
     - XRD: 2theta vs intensity CSV
     - UV-Vis: wavelength vs absorbance CSV
     - FTIR: wavenumber vs %T CSV
     - Electrical: voltage vs current CSV
     - SEM: High-resolution realistic CuO micrograph PNG with calibrated 500 nm scale bar
  3. Preprocessed Curve Files on disk (data/processed/ and backend/data/processed/)
  4. ProcessedFile database records linking AnalysisRun to processed curves
  5. XRD and FTIR Peak records in xrd_peaks table
  6. Calculated Properties for all techniques (Crystallite Size, Band Gap, Vibration Frequency,
     Resistance, Resistivity, Conductivity, Sheet Resistance, Average Grain Size)
  7. SEM Metadata, Annotations, and Scale Measurements for all SEM images
  8. Sanitizes any file_extension with leading dot to plain extension (e.g. 'csv', 'png')
"""

from __future__ import annotations

import asyncio
import hashlib
import io
import logging
import os
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Ensure backend in python path
sys.path.insert(0, "backend")

import numpy as np
import pandas as pd
from PIL import Image, ImageDraw
from scipy.ndimage import gaussian_filter
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import AsyncSessionLocal
from app.models.analysis import (
    AnalysisRun,
    AnalysisStatus,
    CalculatedProperty,
    FTIRAnnotation,
    ProcessedFile,
    SEMAnnotation,
    SEMMeasurement,
    SEMMetadata,
    XRDPeak,
)
from app.models.characterization import Characterization, RawFile, RawFileStatus
from app.models.experiment import Experiment
from app.models.project import Project
from app.models.sample import Sample

# Silence noisy SQL echo
logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("p7_full_suite")

ROOT_DIR = Path(__file__).resolve().parent.parent
RAW_DIRS = [ROOT_DIR / "data" / "raw", ROOT_DIR / "backend" / "data" / "raw"]
PROCESSED_DIRS = [ROOT_DIR / "data" / "processed", ROOT_DIR / "backend" / "data" / "processed"]

SEED = 20260928


def save_file_to_storage(rel_path: str, data_bytes: bytes, target_dirs: list[Path]) -> tuple[int, str]:
    """Write bytes to all target directories, return (size, sha256)."""
    sha256 = hashlib.sha256(data_bytes).hexdigest()
    size = len(data_bytes)
    for d in target_dirs:
        dest = d / rel_path
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data_bytes)
    return size, sha256


def generate_xrd_curves(crystallite_size_nm: float, seed: int) -> tuple[bytes, bytes, list[dict[str, Any]]]:
    """Generate raw and processed XRD curve CSVs and peak records."""
    rng = np.random.default_rng(seed)
    theta = np.linspace(20.0, 70.0, 1001)

    # Monoclinic tenorite CuO peaks
    peaks_info = [
        {"hkl": "(110)", "pos": 32.52, "rel_int": 250.0},
        {"hkl": "(-111)", "pos": 35.54, "rel_int": 1000.0},
        {"hkl": "(111)", "pos": 38.73, "rel_int": 820.0},
        {"hkl": "(-202)", "pos": 48.72, "rel_int": 310.0},
        {"hkl": "(020)", "pos": 53.49, "rel_int": 160.0},
        {"hkl": "(202)", "pos": 58.28, "rel_int": 190.0},
        {"hkl": "(-113)", "pos": 61.54, "rel_int": 240.0},
        {"hkl": "(-311)", "pos": 66.23, "rel_int": 270.0},
        {"hkl": "(220)", "pos": 68.12, "rel_int": 210.0},
    ]

    # Scherrer formula for FWHM
    k = 0.94
    wavelength = 0.15406  # nm Cu K-alpha
    detected_peaks = []
    y_proc = np.zeros_like(theta)

    for p in peaks_info:
        theta_rad = np.radians(p["pos"] / 2.0)
        fwhm_rad = (k * wavelength) / (crystallite_size_nm * np.cos(theta_rad))
        fwhm_deg = float(np.degrees(fwhm_rad))
        peak_intensity = float(p["rel_int"] * (crystallite_size_nm / 25.0) ** 0.3)
        peak_shape = peak_intensity * np.exp(-4.0 * np.log(2.0) * ((theta - p["pos"]) ** 2) / (fwhm_deg ** 2))
        y_proc += peak_shape
        detected_peaks.append({
            "peak_position": round(p["pos"], 2),
            "intensity": round(peak_intensity, 2),
            "fwhm": round(fwhm_deg, 4),
            "prominence": round(peak_intensity * 0.9, 2),
            "width": round(fwhm_deg, 4),
            "detection_parameters": {"hkl": p["hkl"], "wavelength_nm": wavelength},
        })

    bg = 150.0 + 80.0 * np.exp(-(theta - 20.0) / 18.0)
    noise = rng.normal(0, 12.0, size=len(theta))
    y_raw = y_proc + bg + noise

    df_raw = pd.DataFrame({"two_theta": np.round(theta, 3), "intensity": np.round(y_raw, 2)})
    buf_raw = io.StringIO()
    df_raw.to_csv(buf_raw, index=False)
    raw_bytes = buf_raw.getvalue().encode("utf-8")

    df_proc = pd.DataFrame({
        "two_theta": np.round(theta, 3),
        "raw_intensity": np.round(y_raw, 2),
        "processed_intensity": np.round(y_proc, 2),
    })
    buf_proc = io.StringIO()
    df_proc.to_csv(buf_proc, index=False)
    proc_bytes = buf_proc.getvalue().encode("utf-8")

    return raw_bytes, proc_bytes, detected_peaks


def generate_uvvis_curves(band_gap_ev: float, thickness_nm: float, seed: int) -> tuple[bytes, bytes, dict[str, float]]:
    """Generate raw absorbance and processed Tauc curve CSVs."""
    rng = np.random.default_rng(seed)
    wavelength = np.linspace(300.0, 1000.0, 701)
    photon_energy = 1239.84193 / wavelength

    slope_constant = 4.5e8  # cm^-2 * eV^-1
    d_cm = thickness_nm * 1e-7

    alpha = np.zeros_like(photon_energy)
    for idx, e in enumerate(photon_energy):
        if e > band_gap_ev:
            tauc_val = slope_constant * (e - band_gap_ev)
            alpha[idx] = np.sqrt(max(0.0, tauc_val)) / e
        else:
            alpha[idx] = 120.0 * np.exp((e - band_gap_ev) / 0.08)

    absorbance = (alpha * d_cm) / 2.303 + rng.normal(0, 0.003, size=len(wavelength))
    absorbance = np.clip(absorbance, 0.001, 4.0)

    tauc_y = (alpha * photon_energy) ** 2

    slope = float(slope_constant)
    intercept = float(-slope_constant * band_gap_ev)
    fit_meta = {"r_squared": 0.9942, "slope": slope, "intercept": intercept}

    df_raw = pd.DataFrame({"wavelength_nm": np.round(wavelength, 1), "absorbance": np.round(absorbance, 4)})
    buf_raw = io.StringIO()
    df_raw.to_csv(buf_raw, index=False)
    raw_bytes = buf_raw.getvalue().encode("utf-8")

    df_proc = pd.DataFrame({
        "wavelength_nm": np.round(wavelength, 1),
        "absorbance": np.round(absorbance, 4),
        "photon_energy_ev": np.round(photon_energy, 4),
        "tauc_y": np.round(tauc_y, 2),
    })
    buf_proc = io.StringIO()
    df_proc.to_csv(buf_proc, index=False)
    proc_bytes = buf_proc.getvalue().encode("utf-8")

    return raw_bytes, proc_bytes, fit_meta


def generate_ftir_curves(extract_conc: float, seed: int) -> tuple[bytes, bytes, list[dict[str, Any]], float]:
    """Generate raw and processed FTIR spectrum (%T vs wavenumber) and detected peaks."""
    rng = np.random.default_rng(seed)
    wn = np.linspace(400.0, 4000.0, 1801)

    t_signal = np.full_like(wn, 92.0)
    cuo_peak_wn = float(532.0 + rng.normal(0, 1.5))
    cuo_dip = 48.0
    t_signal -= cuo_dip * np.exp(-((wn - cuo_peak_wn) ** 2) / (2 * (16.0 ** 2)))
    t_signal -= 22.0 * np.exp(-((wn - 482.0) ** 2) / (2 * (14.0 ** 2)))

    ext_scale = min(1.0, max(0.2, extract_conc / 30.0))
    t_signal -= 15.0 * ext_scale * np.exp(-((wn - 1050.0) ** 2) / (2 * (25.0 ** 2)))
    t_signal -= 25.0 * ext_scale * np.exp(-((wn - 1630.0) ** 2) / (2 * (30.0 ** 2)))
    t_signal -= 18.0 * ext_scale * np.exp(-((wn - 2920.0) ** 2) / (2 * (20.0 ** 2)))
    t_signal -= 32.0 * ext_scale * np.exp(-((wn - 3400.0) ** 2) / (2 * (70.0 ** 2)))

    noise = rng.normal(0, 0.4, size=len(wn))
    t_raw = np.clip(t_signal + noise, 5.0, 100.0)
    t_proc = np.clip(t_signal, 5.0, 100.0)

    peaks = [
        {"peak_position": round(cuo_peak_wn, 1), "intensity": round(float(t_proc[np.argmin(np.abs(wn - cuo_peak_wn))]), 2), "prominence": 46.0, "width": 16.0},
        {"peak_position": 482.0, "intensity": round(float(t_proc[np.argmin(np.abs(wn - 482.0))]), 2), "prominence": 20.0, "width": 14.0},
        {"peak_position": 1630.0, "intensity": round(float(t_proc[np.argmin(np.abs(wn - 1630.0))]), 2), "prominence": 24.0, "width": 30.0},
        {"peak_position": 3400.0, "intensity": round(float(t_proc[np.argmin(np.abs(wn - 3400.0))]), 2), "prominence": 30.0, "width": 70.0},
    ]

    df_raw = pd.DataFrame({"wavenumber_cm1": np.round(wn, 1), "signal": np.round(t_raw, 2)})
    buf_raw = io.StringIO()
    df_raw.to_csv(buf_raw, index=False)
    raw_bytes = buf_raw.getvalue().encode("utf-8")

    df_proc = pd.DataFrame({"wavenumber_cm1": np.round(wn, 1), "signal": np.round(t_proc, 2)})
    buf_proc = io.StringIO()
    df_proc.to_csv(buf_proc, index=False)
    proc_bytes = buf_proc.getvalue().encode("utf-8")

    return raw_bytes, proc_bytes, peaks, cuo_peak_wn


def generate_electrical_curves(resistance_ohms: float, seed: int) -> tuple[bytes, bytes, dict[str, float]]:
    """Generate raw and processed I-V curve CSVs and linear fit parameters."""
    rng = np.random.default_rng(seed)
    voltages = np.linspace(-5.0, 5.0, 101)
    noise_sigma = max(1e-9, (2.0 / resistance_ohms) * 0.008)

    ideal_i = voltages / resistance_ohms
    actual_i = ideal_i + rng.normal(0, noise_sigma, size=len(voltages))

    df_raw = pd.DataFrame({"voltage_v": np.round(voltages, 2), "current_a": actual_i})
    buf_raw = io.StringIO()
    df_raw.to_csv(buf_raw, index=False)
    raw_bytes = buf_raw.getvalue().encode("utf-8")

    df_proc = pd.DataFrame({"voltage_v": np.round(voltages, 2), "current_a": ideal_i})
    buf_proc = io.StringIO()
    df_proc.to_csv(buf_proc, index=False)
    proc_bytes = buf_proc.getvalue().encode("utf-8")

    fit_meta = {
        "r_squared": 0.9998,
        "slope": float(1.0 / resistance_ohms),
        "intercept": 0.0,
    }
    return raw_bytes, proc_bytes, fit_meta


def generate_sem_micrograph(grain_size_nm: float, seed: int) -> tuple[bytes, dict[str, Any]]:
    """Generate realistic secondary-electron SEM micrograph image (640x480) with scale bar databar."""
    w, h = 640, 480
    rng = np.random.default_rng(seed)
    grain_px = max(6.0, grain_size_nm / 5.0)

    n1 = rng.normal(128, 40, (h - 36, w))
    smooth1 = gaussian_filter(n1, sigma=grain_px * 0.4)
    smooth2 = gaussian_filter(n1, sigma=grain_px * 0.8)
    roughness = rng.normal(0, 15, (h - 36, w))

    grad_y, grad_x = np.gradient(smooth1)
    relief = grad_x * 4.0 + grad_y * 2.0
    film = smooth2 + relief + roughness
    film = ((film - film.min()) / (film.max() - film.min()) * 210 + 20).astype(np.uint8)

    img = Image.new("L", (w, h), 0)
    img.paste(Image.fromarray(film, mode="L"), (0, 0))

    draw = ImageDraw.Draw(img)
    draw.rectangle([(0, h - 36), (w, h)], fill=0)
    draw.line([(0, h - 36), (w, h - 36)], fill=60, width=1)
    draw.text((16, h - 25), "15.0 kV  x50,000  WD 8.0 mm  SE  GreenSynth FE-SEM", fill=220)

    sb_x = w - 145
    sb_y = h - 14
    draw.line([(sb_x, sb_y), (sb_x + 100, sb_y)], fill=255, width=3)
    draw.line([(sb_x, sb_y - 4), (sb_x, sb_y + 4)], fill=255, width=2)
    draw.line([(sb_x + 100, sb_y - 4), (sb_x + 100, sb_y + 4)], fill=255, width=2)
    draw.text((sb_x + 26, sb_y - 15), "500 nm", fill=255)

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    png_bytes = buf.getvalue()

    sem_info = {
        "magnification": 50000.0,
        "accelerating_voltage_kv": 15.0,
        "working_distance_mm": 8.0,
        "detector": "SE",
        "scale_bar_nm": 500.0,
        "scale_bar_pixels": 100.0,
        "nm_per_pixel": 5.0,
        "measured_grain_size_nm": round(grain_size_nm, 1),
        "pixel_distance": round(grain_size_nm / 5.0, 1),
    }
    return png_bytes, sem_info


async def populate_p7_suite() -> None:
    logger.info("Starting P7 5-Technique & Processed Curves Population...")

    summary_path = ROOT_DIR / "synthetic_data" / "p7" / "experiments_summary.csv"
    if not summary_path.exists():
        raise FileNotFoundError(f"Missing summary CSV at {summary_path}")
    summary_df = pd.read_csv(summary_path)
    summary_map = {row["sample_code"]: row for _, row in summary_df.iterrows()}
    logger.info(f"Loaded summary metadata for {len(summary_map)} synthetic samples.")

    async with AsyncSessionLocal() as session:
        # Step 1: Normalize any double-dot '.csv' extensions
        logger.info("Normalizing file_extension in database (stripping leading dots)...")
        await session.execute(
            update(RawFile)
            .where(RawFile.file_extension == ".csv")
            .values(file_extension="csv")
        )
        await session.commit()

        # Step 2: Fetch Project P7
        proj_res = await session.execute(select(Project).where(Project.project_code == "P7"))
        project = proj_res.scalars().first()
        if not project:
            raise RuntimeError("Project P7 not found!")

        logger.info(f"Target Project: {project.project_code} ({project.id})")

        # Step 3: Fetch all samples without deep selectinload (avoiding greenlet issues)
        samples_res = await session.execute(
            select(Sample, Experiment)
            .join(Experiment, Sample.experiment_id == Experiment.id)
            .where(Experiment.project_id == project.id)
            .order_by(Experiment.experiment_code, Sample.sample_code)
        )
        sample_rows = samples_res.all()
        logger.info(f"Loaded {len(sample_rows)} total samples for Project P7.")

        batch_size = 20
        total_samples = len(sample_rows)
        all_techniques = ["XRD", "UV_VIS", "FTIR", "SEM", "ELECTRICAL"]

        for b_start in range(0, total_samples, batch_size):
            b_end = min(b_start + batch_size, total_samples)
            batch = sample_rows[b_start:b_end]
            logger.info(f"Processing samples {b_start + 1} to {b_end} of {total_samples}...")

            for sample, experiment in batch:
                s_code = sample.sample_code
                e_code = experiment.experiment_code
                meta_row = summary_map.get(s_code)

                cryst_nm = float(meta_row["crystallite_size_nm"]) if meta_row is not None and pd.notna(meta_row.get("crystallite_size_nm")) else 22.5
                bg_ev = float(meta_row["band_gap_ev"]) if meta_row is not None and pd.notna(meta_row.get("band_gap_ev")) else 1.55
                cond_s_cm = float(meta_row["electrical_conductivity_s_cm"]) if meta_row is not None and pd.notna(meta_row.get("electrical_conductivity_s_cm")) else 0.45
                thick_nm = float(meta_row["thickness_nm"]) if meta_row is not None and pd.notna(meta_row.get("thickness_nm")) else 800.0
                ext_conc = float(meta_row["mulberry_extract_concentration"]) if meta_row is not None and pd.notna(meta_row.get("mulberry_extract_concentration")) else 15.0

                seed_int = SEED + int(hashlib.md5(s_code.encode()).hexdigest()[:6], 16) % 100000
                grain_size_nm = cryst_nm * (1.8 + 0.3 * (cryst_nm / 25.0))

                rho_ohm_cm = 1.0 / max(1e-6, cond_s_cm)
                area_cm2 = (thick_nm * 1e-7) * 1.0
                length_cm = 0.5
                resistance_ohms = (rho_ohm_cm * length_cm) / area_cm2

                # Fetch characterizations for this sample explicitly
                chars_res = await session.execute(
                    select(Characterization).where(Characterization.sample_id == sample.id)
                )
                chars = chars_res.scalars().all()
                existing_chars = {c.technique: c for c in chars}

                for tech in all_techniques:
                    # 1. Ensure Characterization exists
                    char = existing_chars.get(tech)
                    if char is None:
                        char = Characterization(
                            id=uuid.uuid4(),
                            sample_id=sample.id,
                            technique=tech,
                            status="ANALYZED",
                            operator="Dr. V. Atharvan",
                            instrument_name=f"GreenSynth {tech} Station",
                            instrument_model=f"GS-{tech}-2026",
                            notes=f"Synthetic full-suite {tech} run",
                        )
                        session.add(char)
                        await session.flush()
                        existing_chars[tech] = char

                    # 2. Ensure RawFile exists & stored on disk
                    ext = "png" if tech == "SEM" else "csv"
                    mime = "image/png" if tech == "SEM" else "text/csv"
                    orig_filename = f"{s_code}_{tech}.{ext}"

                    rf_res = await session.execute(
                        select(RawFile).where(RawFile.characterization_id == char.id)
                    )
                    raw_file = rf_res.scalars().first()

                    if raw_file is None:
                        raw_file_id = uuid.uuid4()
                        stored_filename = f"{raw_file_id!s}.{ext}"
                        rel_raw_path = f"projects/P7/experiments/{e_code}/samples/{s_code}/{char.id!s}/{stored_filename}"

                        if tech == "XRD":
                            raw_b, _, _ = generate_xrd_curves(cryst_nm, seed_int)
                        elif tech == "UV_VIS":
                            raw_b, _, _ = generate_uvvis_curves(bg_ev, thick_nm, seed_int)
                        elif tech == "FTIR":
                            raw_b, _, _, _ = generate_ftir_curves(ext_conc, seed_int)
                        elif tech == "ELECTRICAL":
                            raw_b, _, _ = generate_electrical_curves(resistance_ohms, seed_int)
                        elif tech == "SEM":
                            raw_b, _ = generate_sem_micrograph(grain_size_nm, seed_int)

                        f_size, f_sha256 = save_file_to_storage(rel_raw_path, raw_b, RAW_DIRS)

                        raw_file = RawFile(
                            id=raw_file_id,
                            characterization_id=char.id,
                            sample_id=sample.id,
                            original_filename=orig_filename,
                            stored_filename=stored_filename,
                            file_extension=ext,
                            mime_type=mime,
                            file_size=f_size,
                            checksum=f_sha256,
                            storage_path=rel_raw_path,
                            storage_backend="local",
                            file_metadata={"data_origin": "SYNTHETIC", "technique": tech},
                            status=RawFileStatus.ACTIVE.value,
                        )
                        session.add(raw_file)
                        await session.flush()
                    else:
                        if raw_file.file_extension != ext:
                            raw_file.file_extension = ext

                    # 3. SEM Specifics (Metadata, Annotations, Measurements)
                    if tech == "SEM":
                        raw_disk_path = RAW_DIRS[0] / raw_file.storage_path
                        if not raw_disk_path.exists() or raw_disk_path.stat().st_size < 1000:
                            raw_b, _ = generate_sem_micrograph(grain_size_nm, seed_int)
                            save_file_to_storage(raw_file.storage_path, raw_b, RAW_DIRS)

                        meta_res = await session.execute(
                            select(SEMMetadata).where(SEMMetadata.raw_file_id == raw_file.id)
                        )
                        sem_meta = meta_res.scalar_one_or_none()
                        if sem_meta is None:
                            sem_meta = SEMMetadata(
                                id=uuid.uuid4(),
                                raw_file_id=raw_file.id,
                                magnification=50000.0,
                                accelerating_voltage_kv=15.0,
                                working_distance_mm=8.0,
                                detector="SE",
                                scale_bar_nm=500.0,
                                scale_bar_pixels=100.0,
                                nm_per_pixel=5.0,
                                notes="Polycrystalline CuO thin film surface micrograph with grain boundary structure",
                            )
                            session.add(sem_meta)

                        ann_res = await session.execute(
                            select(SEMAnnotation).where(SEMAnnotation.raw_file_id == raw_file.id)
                        )
                        if not ann_res.scalars().all():
                            ann = SEMAnnotation(
                                id=uuid.uuid4(),
                                raw_file_id=raw_file.id,
                                annotation_type="rectangle",
                                coordinates_json={"x": 60, "y": 60, "width": 80, "height": 80},
                                label="Representative CuO Grain Cluster",
                                notes="Sub-micron faceted polycrystalline grain domain",
                                created_by="Dr. V. Atharvan",
                            )
                            session.add(ann)

                        meas_res = await session.execute(
                            select(SEMMeasurement).where(SEMMeasurement.raw_file_id == raw_file.id)
                        )
                        if not meas_res.scalars().all():
                            px_len = round(grain_size_nm / 5.0, 1)
                            meas = SEMMeasurement(
                                id=uuid.uuid4(),
                                raw_file_id=raw_file.id,
                                pixel_distance=px_len,
                                physical_distance_nm=round(grain_size_nm, 1),
                                unit="nm",
                                label="Average Grain Diameter",
                                calibration_info={"scale_bar_nm": 500.0, "scale_bar_pixels": 100.0, "nm_per_pixel": 5.0},
                                created_by="Automated SEM Scale Measurement",
                            )
                            session.add(meas)

                        # Ensure Average Grain Size calculated property
                        grain_prop_res = await session.execute(
                            select(CalculatedProperty)
                            .where(CalculatedProperty.sample_id == sample.id)
                            .where(CalculatedProperty.property_name == "Average Grain Size")
                        )
                        if not grain_prop_res.scalars().all():
                            run_res = await session.execute(
                                select(AnalysisRun).where(AnalysisRun.characterization_id == char.id)
                            )
                            sem_run = run_res.scalars().first()
                            if sem_run is None:
                                sem_run = AnalysisRun(
                                    id=uuid.uuid4(),
                                    characterization_id=char.id,
                                    input_file_id=raw_file.id,
                                    analysis_type="SEM",
                                    status=AnalysisStatus.COMPLETED.value,
                                    software_version="0.1.0",
                                    notes="SEM micrograph grain size intercept analysis",
                                    completed_at=datetime.now(timezone.utc),
                                )
                                session.add(sem_run)
                                await session.flush()

                            prop_sem = CalculatedProperty(
                                id=uuid.uuid4(),
                                sample_id=sample.id,
                                analysis_run_id=sem_run.id,
                                property_name="Average Grain Size",
                                value=round(grain_size_nm, 1),
                                unit="nm",
                                calculation_method="SEM Micrograph Intercept Analysis",
                                formula="D_grain = Pixel_distance * nm_per_pixel",
                                assumptions={"magnification": 50000.0, "nm_per_pixel": 5.0},
                            )
                            session.add(prop_sem)

                    # 4. Handle 1D Techniques (XRD, UV_VIS, FTIR, ELECTRICAL)
                    else:
                        run_res = await session.execute(
                            select(AnalysisRun).where(AnalysisRun.characterization_id == char.id)
                        )
                        run = run_res.scalars().first()
                        if run is None:
                            run = AnalysisRun(
                                id=uuid.uuid4(),
                                characterization_id=char.id,
                                input_file_id=raw_file.id,
                                analysis_type=tech,
                                status=AnalysisStatus.COMPLETED.value,
                                software_version="0.1.0",
                                notes=f"GreenSynth synthetic {tech} analysis run",
                                completed_at=datetime.now(timezone.utc),
                            )
                            session.add(run)
                            await session.flush()

                        proc_res = await session.execute(
                            select(ProcessedFile).where(ProcessedFile.analysis_run_id == run.id)
                        )
                        proc_file = proc_res.scalars().first()

                        tech_folder = tech.lower().replace("-", "_")
                        rel_proc_path = f"projects/P7/{e_code}/{s_code}/{tech_folder}/{run.id!s}_processed.csv"

                        need_generate = False
                        if proc_file is None:
                            need_generate = True
                        else:
                            disk_proc = PROCESSED_DIRS[0] / proc_file.stored_path
                            if not disk_proc.exists() or disk_proc.stat().st_size < 50:
                                need_generate = True

                        if need_generate:
                            if tech == "XRD":
                                raw_b, proc_b, detected_peaks = generate_xrd_curves(cryst_nm, seed_int)
                                save_file_to_storage(raw_file.storage_path, raw_b, RAW_DIRS)
                                save_file_to_storage(rel_proc_path, proc_b, PROCESSED_DIRS)

                                if proc_file is None:
                                    proc_file = ProcessedFile(
                                        id=uuid.uuid4(),
                                        analysis_run_id=run.id,
                                        raw_file_id=raw_file.id,
                                        stored_path=rel_proc_path,
                                        processing_method="Baseline subtraction + Savitzky-Golay smoothing",
                                    )
                                    session.add(proc_file)

                                # Populate XRD peaks if missing
                                peaks_res = await session.execute(
                                    select(XRDPeak).where(XRDPeak.analysis_run_id == run.id)
                                )
                                if not peaks_res.scalars().all():
                                    for dp in detected_peaks:
                                        peak_obj = XRDPeak(
                                            id=uuid.uuid4(),
                                            analysis_run_id=run.id,
                                            peak_position=dp["peak_position"],
                                            intensity=dp["intensity"],
                                            fwhm=dp["fwhm"],
                                            prominence=dp["prominence"],
                                            width=dp["width"],
                                            detection_parameters=dp["detection_parameters"],
                                        )
                                        session.add(peak_obj)

                                # Ensure Crystallite Size property
                                cp_res = await session.execute(
                                    select(CalculatedProperty)
                                    .where(CalculatedProperty.analysis_run_id == run.id)
                                    .where(CalculatedProperty.property_name == "Crystallite Size")
                                )
                                if not cp_res.scalars().all():
                                    cp = CalculatedProperty(
                                        id=uuid.uuid4(),
                                        sample_id=sample.id,
                                        analysis_run_id=run.id,
                                        property_name="Crystallite Size",
                                        value=cryst_nm,
                                        unit="nm",
                                        calculation_method="Scherrer Equation",
                                        formula="D = (K * lambda) / (beta * cos(theta))",
                                        input_values={"peak_position_2theta": 35.54, "fwhm_deg": detected_peaks[1]["fwhm"]},
                                    )
                                    session.add(cp)

                            elif tech == "UV_VIS":
                                raw_b, proc_b, fit_meta = generate_uvvis_curves(bg_ev, thick_nm, seed_int)
                                save_file_to_storage(raw_file.storage_path, raw_b, RAW_DIRS)
                                save_file_to_storage(rel_proc_path, proc_b, PROCESSED_DIRS)

                                run.parameters = {
                                    "tauc": {
                                        "transition_type": "DIRECT_ALLOWED",
                                        "sample_thickness_cm": thick_nm * 1e-7,
                                    }
                                }

                                if proc_file is None:
                                    proc_file = ProcessedFile(
                                        id=uuid.uuid4(),
                                        analysis_run_id=run.id,
                                        raw_file_id=raw_file.id,
                                        stored_path=rel_proc_path,
                                        processing_method="Tauc plot transformation ((alpha * h * nu)^2 vs h * nu)",
                                    )
                                    session.add(proc_file)

                                cp_res = await session.execute(
                                    select(CalculatedProperty)
                                    .where(CalculatedProperty.analysis_run_id == run.id)
                                    .where(CalculatedProperty.property_name == "Optical Band Gap")
                                )
                                bg_prop = cp_res.scalars().first()
                                if bg_prop is None:
                                    cp = CalculatedProperty(
                                        id=uuid.uuid4(),
                                        sample_id=sample.id,
                                        analysis_run_id=run.id,
                                        property_name="Optical Band Gap",
                                        value=bg_ev,
                                        unit="eV",
                                        calculation_method="Tauc Plot",
                                        formula="(alpha * h * nu)^2 vs h * nu",
                                        input_values=fit_meta,
                                    )
                                    session.add(cp)
                                else:
                                    bg_prop.input_values = fit_meta

                            elif tech == "FTIR":
                                raw_b, proc_b, peaks, cuo_wn = generate_ftir_curves(ext_conc, seed_int)
                                save_file_to_storage(raw_file.storage_path, raw_b, RAW_DIRS)
                                save_file_to_storage(rel_proc_path, proc_b, PROCESSED_DIRS)

                                if proc_file is None:
                                    proc_file = ProcessedFile(
                                        id=uuid.uuid4(),
                                        analysis_run_id=run.id,
                                        raw_file_id=raw_file.id,
                                        stored_path=rel_proc_path,
                                        processing_method="Transmittance baseline normalization",
                                    )
                                    session.add(proc_file)

                                ftir_peaks_res = await session.execute(
                                    select(XRDPeak).where(XRDPeak.analysis_run_id == run.id)
                                )
                                if not ftir_peaks_res.scalars().all():
                                    for p in peaks:
                                        peak_obj = XRDPeak(
                                            id=uuid.uuid4(),
                                            analysis_run_id=run.id,
                                            peak_position=p["peak_position"],
                                            intensity=p["intensity"],
                                            fwhm=p["width"],
                                            prominence=p["prominence"],
                                            width=p["width"],
                                        )
                                        session.add(peak_obj)

                                ftir_ann_res = await session.execute(
                                    select(FTIRAnnotation).where(FTIRAnnotation.analysis_run_id == run.id)
                                )
                                if not ftir_ann_res.scalars().all():
                                    f_ann = FTIRAnnotation(
                                        id=uuid.uuid4(),
                                        analysis_run_id=run.id,
                                        wavenumber_cm1=cuo_wn,
                                        label="Cu-O stretching mode",
                                        interpretation="Characteristic monoclinic tenorite CuO lattice vibration",
                                        confidence="Confirmed",
                                        created_by="Dr. V. Atharvan",
                                    )
                                    session.add(f_ann)

                                ftir_cp_res = await session.execute(
                                    select(CalculatedProperty)
                                    .where(CalculatedProperty.analysis_run_id == run.id)
                                    .where(CalculatedProperty.property_name == "Cu-O Vibration Frequency")
                                )
                                if not ftir_cp_res.scalars().all():
                                    cp = CalculatedProperty(
                                        id=uuid.uuid4(),
                                        sample_id=sample.id,
                                        analysis_run_id=run.id,
                                        property_name="Cu-O Vibration Frequency",
                                        value=round(cuo_wn, 1),
                                        unit="cm⁻¹",
                                        calculation_method="FTIR Peak Absorption Minimum",
                                    )
                                    session.add(cp)

                            elif tech == "ELECTRICAL":
                                raw_b, proc_b, fit_meta = generate_electrical_curves(resistance_ohms, seed_int)
                                save_file_to_storage(raw_file.storage_path, raw_b, RAW_DIRS)
                                save_file_to_storage(rel_proc_path, proc_b, PROCESSED_DIRS)

                                if proc_file is None:
                                    proc_file = ProcessedFile(
                                        id=uuid.uuid4(),
                                        analysis_run_id=run.id,
                                        raw_file_id=raw_file.id,
                                        stored_path=rel_proc_path,
                                        processing_method="Ohm's Law Linear Regression",
                                    )
                                    session.add(proc_file)

                                elec_props_res = await session.execute(
                                    select(CalculatedProperty).where(CalculatedProperty.analysis_run_id == run.id)
                                )
                                ep_map = {cp.property_name: cp for cp in elec_props_res.scalars().all()}

                                if "Electrical Resistance" not in ep_map:
                                    cp = CalculatedProperty(
                                        id=uuid.uuid4(),
                                        sample_id=sample.id,
                                        analysis_run_id=run.id,
                                        property_name="Electrical Resistance",
                                        value=round(resistance_ohms, 2),
                                        unit="Ω",
                                        calculation_method="Ohm's Law Linear Regression",
                                        formula="V = I * R",
                                        input_values=fit_meta,
                                    )
                                    session.add(cp)
                                else:
                                    ep_map["Electrical Resistance"].input_values = fit_meta

                                if "Electrical Resistivity" not in ep_map:
                                    cp = CalculatedProperty(
                                        id=uuid.uuid4(),
                                        sample_id=sample.id,
                                        analysis_run_id=run.id,
                                        property_name="Electrical Resistivity",
                                        value=round(rho_ohm_cm, 4),
                                        unit="Ω·cm",
                                        calculation_method="Geometric Resistance Formula",
                                        formula="rho = R * A / L",
                                    )
                                    session.add(cp)

                                if "Electrical Conductivity" not in ep_map:
                                    cp = CalculatedProperty(
                                        id=uuid.uuid4(),
                                        sample_id=sample.id,
                                        analysis_run_id=run.id,
                                        property_name="Electrical Conductivity",
                                        value=round(cond_s_cm, 5),
                                        unit="S/cm",
                                        calculation_method="Reciprocal Resistivity",
                                        formula="sigma = 1 / rho",
                                    )
                                    session.add(cp)

            # Commit batch
            await session.commit()
            logger.info(f"Committed batch {b_start + 1} - {b_end}.")

        # Final Verification Queries
        p_id = project.id
        final_chars = (await session.execute(
            select(Characterization.technique, func.count(Characterization.id))
            .join(Sample).join(Experiment).where(Experiment.project_id == p_id)
            .group_by(Characterization.technique)
        )).all()

        final_raw = (await session.execute(
            select(func.count(RawFile.id))
            .join(Characterization).join(Sample).join(Experiment).where(Experiment.project_id == p_id)
        )).scalar()

        final_proc = (await session.execute(
            select(func.count(ProcessedFile.id))
            .join(AnalysisRun).join(Characterization).join(Sample).join(Experiment).where(Experiment.project_id == p_id)
        )).scalar()

        final_peaks = (await session.execute(
            select(func.count(XRDPeak.id))
            .join(AnalysisRun).join(Characterization).join(Sample).join(Experiment).where(Experiment.project_id == p_id)
        )).scalar()

        final_sem_meta = (await session.execute(
            select(func.count(SEMMetadata.id))
            .join(RawFile).join(Characterization).join(Sample).join(Experiment).where(Experiment.project_id == p_id)
        )).scalar()

        logger.info("======================================================")
        logger.info("P7 POPULATION & ENRICHMENT COMPLETE")
        logger.info(f"Characterizations by technique: {dict(final_chars)}")
        logger.info(f"Raw Files: {final_raw}")
        logger.info(f"Processed Files: {final_proc}")
        logger.info(f"Peak Records: {final_peaks}")
        logger.info(f"SEM Metadata Records: {final_sem_meta}")
        logger.info("======================================================")


if __name__ == "__main__":
    asyncio.run(populate_p7_suite())
