"""
GreenSynth Analytics — Integration Tests: SEM Image Metadata, Scale Calibration & Manual Measurements
"""

from __future__ import annotations

import pytest
from httpx import AsyncClient

PROJECTS_API = "/api/v1/projects"
EXPERIMENTS_API = "/api/v1/experiments"
SAMPLES_API = "/api/v1/samples"
CHAR_API = "/api/v1/characterizations"
FILES_API = "/api/v1/files"


async def setup_sem_characterization_with_file(client: AsyncClient, suffix: str) -> tuple[str, str]:
    """Helper: create Project → Exp → Sample → SEM Characterization → Raw File."""
    p_resp = await client.post(
        f"{PROJECTS_API}/",
        json={
            "project_code": f"P-SEM-{suffix}",
            "name": f"SEM Test Project {suffix}",
            "material": "CuO",
            "extract": "Mulberry",
            "solvent": "Ethanol",
            "synthesis_method": "Spray Pyrolysis",
        },
    )
    p_id = p_resp.json()["id"]

    e_resp = await client.post(
        f"{EXPERIMENTS_API}/",
        json={
            "project_id": p_id,
            "experiment_code": f"EXP-SEM-{suffix}",
            "title": f"SEM Exp {suffix}",
        },
    )
    e_id = e_resp.json()["id"]

    s_resp = await client.post(
        f"{SAMPLES_API}/",
        json={
            "experiment_id": e_id,
            "sample_code": f"S-SEM-{suffix}",
            "name": f"CuO Nanoparticles {suffix}",
            "material": "CuO",
        },
    )
    s_id = s_resp.json()["id"]

    c_resp = await client.post(
        CHAR_API,
        json={
            "sample_id": s_id,
            "technique": "SEM",
            "operator": "Dr. Electron Microscopist",
            "instrument_name": "JEOL JSM-7600F FE-SEM",
        },
    )
    ch_id = c_resp.json()["id"]

    # Upload synthetic PNG raw file
    dummy_png_bytes = (
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x10\x00\x00\x00\x10\x08\x06\x00\x00\x00\x1f\xf3\xffa"
    )
    files = {"file": ("cuo_sem_micrograph.png", dummy_png_bytes, "image/png")}

    up_resp = await client.post(f"{CHAR_API}/{ch_id}/files", files=files)
    assert up_resp.status_code == 201
    file_id = up_resp.json()["id"]

    return ch_id, file_id


@pytest.mark.asyncio
async def test_sem_metadata_calibration_measurements_pipeline(client: AsyncClient) -> None:
    """Update SEM metadata, calibrate scale bar, add visual annotation, and record manual length measurement."""
    _, file_id = await setup_sem_characterization_with_file(client, "FULL1")

    # 1. Update metadata & scale bar calibration (500 nm scale bar = 100 pixels)
    meta_resp = await client.post(
        f"{FILES_API}/{file_id}/sem-metadata",
        json={
            "magnification": 50000.0,
            "accelerating_voltage_kv": 15.0,
            "working_distance_mm": 8.0,
            "detector": "SE",
            "scale_bar_nm": 500.0,
            "scale_bar_pixels": 100.0,
            "notes": "CuO spherical nanoparticles FE-SEM image",
        },
    )
    assert meta_resp.status_code == 200
    meta_data = meta_resp.json()
    assert meta_data["nm_per_pixel"] == 5.0

    # 2. Add visual annotation
    ann_resp = await client.post(
        f"{FILES_API}/{file_id}/sem-annotations",
        json={
            "annotation_type": "rectangle",
            "coordinates_json": {"x": 50, "y": 50, "width": 100, "height": 100},
            "label": "Aggregated Nanoparticles Cluster",
            "notes": "Spherical morphology region",
        },
    )
    assert ann_resp.status_code == 201
    ann_data = ann_resp.json()
    assert ann_data["label"] == "Aggregated Nanoparticles Cluster"

    # 3. Add manual physical measurement (40 pixels => 40 * 5 = 200 nm)
    meas_resp = await client.post(
        f"{FILES_API}/{file_id}/sem-measurements",
        json={
            "pixel_distance": 40.0,
            "label": "Nanoparticle Diameter #1",
        },
    )
    assert meas_resp.status_code == 201
    meas_data = meas_resp.json()
    assert meas_data["pixel_distance"] == 40.0
    assert meas_data["physical_distance_nm"] == 200.0
    assert meas_data["unit"] == "nm"

    # 4. Query measurements list
    list_meas_resp = await client.get(f"{FILES_API}/{file_id}/sem-measurements")
    assert list_meas_resp.status_code == 200
    meass = list_meas_resp.json()
    assert len(meass) == 1
    assert meass[0]["physical_distance_nm"] == 200.0
