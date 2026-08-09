"""
GreenSynth Analytics — Integration Tests: UV-Vis Tauc Analysis Workflow
"""

from __future__ import annotations

import numpy as np
import pytest
from httpx import AsyncClient

PROJECTS_API = "/api/v1/projects"
EXPERIMENTS_API = "/api/v1/experiments"
SAMPLES_API = "/api/v1/samples"
CHAR_API = "/api/v1/characterizations"
ANALYSIS_API = "/api/v1"


async def setup_uvvis_characterization_with_file(client: AsyncClient, suffix: str) -> tuple[str, str]:
    """Helper: create Project → Exp → Sample → UV-Vis Characterization → Raw File."""
    p_resp = await client.post(
        f"{PROJECTS_API}/",
        json={
            "project_code": f"P-UV-{suffix}",
            "name": f"UV-Vis Test Project {suffix}",
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
            "experiment_code": f"EXP-UV-{suffix}",
            "title": f"UV-Vis Exp {suffix}",
        },
    )
    e_id = e_resp.json()["id"]

    s_resp = await client.post(
        f"{SAMPLES_API}/",
        json={
            "experiment_id": e_id,
            "sample_code": f"S-UV-{suffix}",
            "name": f"CuO Film {suffix}",
            "material": "CuO",
        },
    )
    s_id = s_resp.json()["id"]

    c_resp = await client.post(
        CHAR_API,
        json={
            "sample_id": s_id,
            "technique": "UV_VIS",
            "operator": "Dr. UV Spectroscopist",
            "instrument_name": "Shimadzu UV-2600",
        },
    )
    ch_id = c_resp.json()["id"]

    # Generate synthetic UV-Vis absorption spectrum (Eg ~ 2.10 eV -> ~590 nm edge)
    rows = ["wavelength,absorbance"]
    for wl in range(300, 800, 5):
        energy_ev = 1239.8419 / wl
        if energy_ev >= 2.10:
            # Absorption edge
            abs_val = 0.1 + 0.5 * np.sqrt(energy_ev - 2.10)
        else:
            abs_val = 0.05 + 0.0001 * (800 - wl)
        rows.append(f"{wl},{abs_val:.4f}")

    file_bytes = "\n".join(rows).encode("utf-8")
    files = {"file": ("cuo_uvvis_spectrum.csv", file_bytes, "text/csv")}

    up_resp = await client.post(f"{CHAR_API}/{ch_id}/files", files=files)
    assert up_resp.status_code == 201

    return ch_id, s_id


@pytest.mark.asyncio
async def test_uvvis_analysis_full_pipeline(client: AsyncClient) -> None:
    """Execute UV-Vis analysis, verify Tauc plot fit, Optical Band Gap Eg property, and Tauc curve data."""
    ch_id, sample_id = await setup_uvvis_characterization_with_file(client, "FULL1")

    # Run analysis
    an_resp = await client.post(
        f"{CHAR_API}/{ch_id}/uvvis/analyze",
        json={
            "preprocessing": {
                "smoothing": True,
                "savgol_window": 11,
            },
            "tauc": {
                "transition_type": "DIRECT_ALLOWED",
                "sample_thickness_cm": 0.05,
                "fit_energy_min_ev": 2.2,
                "fit_energy_max_ev": 3.8,
            },
            "notes": "CuO thin film direct optical band gap estimation",
        },
    )
    assert an_resp.status_code == 201
    run_data = an_resp.json()
    assert run_data["status"] == "COMPLETED"
    assert run_data["analysis_type"] == "UV_VIS"
    run_id = run_data["id"]

    # Verify calculated property (Optical Band Gap)
    props = run_data["calculated_properties"]
    assert len(props) == 1
    bg_prop = props[0]
    assert bg_prop["property_name"] == "Optical Band Gap"
    assert bg_prop["unit"] == "eV"
    assert abs(bg_prop["value"] - 2.10) < 0.2
    assert bg_prop["calculation_method"] == "Tauc Plot Linear Extrapolation"

    # Fetch Tauc curve data for Plotly
    tauc_resp = await client.get(f"{ANALYSIS_API}/analysis-runs/{run_id}/tauc-data")
    assert tauc_resp.status_code == 200
    tauc_data = tauc_resp.json()
    assert tauc_data["transition_type"] == "DIRECT_ALLOWED"
    assert tauc_data["using_alpha"] is True
    assert len(tauc_data["data_points"]) == 100
    assert len(tauc_data["fit_line"]) > 0


@pytest.mark.asyncio
async def test_uvvis_missing_thickness_warning(client: AsyncClient) -> None:
    """Missing thickness displays warning message in assumptions without failing calculation."""
    ch_id, _ = await setup_uvvis_characterization_with_file(client, "WARN1")

    an_resp = await client.post(
        f"{CHAR_API}/{ch_id}/uvvis/analyze",
        json={
            "tauc": {
                "transition_type": "DIRECT_ALLOWED",
                "sample_thickness_cm": None,  # Missing thickness
            },
        },
    )
    assert an_resp.status_code == 201
    run_data = an_resp.json()
    bg_prop = run_data["calculated_properties"][0]
    assert "sample thickness is missing" in bg_prop["assumptions"]["warning"]


@pytest.mark.asyncio
async def test_uvvis_multiple_analysis_runs_history(client: AsyncClient) -> None:
    """Executing UV-Vis analysis for Direct vs Indirect transition models stores coexisting reproducible runs."""
    ch_id, _ = await setup_uvvis_characterization_with_file(client, "HIST1")

    # Run 1: Direct Allowed
    await client.post(
        f"{CHAR_API}/{ch_id}/uvvis/analyze",
        json={
            "tauc": {"transition_type": "DIRECT_ALLOWED"},
            "notes": "Run 1: Direct transition model",
        },
    )

    # Run 2: Indirect Allowed
    await client.post(
        f"{CHAR_API}/{ch_id}/uvvis/analyze",
        json={
            "tauc": {"transition_type": "INDIRECT_ALLOWED"},
            "notes": "Run 2: Indirect transition model",
        },
    )

    # List history
    hist_resp = await client.get(f"{CHAR_API}/{ch_id}/analysis-runs")
    assert hist_resp.status_code == 200
    history = hist_resp.json()
    assert len(history) == 2
    notes_list = [h["notes"] for h in history]
    assert "Run 1: Direct transition model" in notes_list
    assert "Run 2: Indirect transition model" in notes_list
