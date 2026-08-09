"""
GreenSynth Analytics — Integration Tests: XRD Analysis Workflow
"""

from __future__ import annotations

import pytest
from httpx import AsyncClient

PROJECTS_API = "/api/v1/projects"
EXPERIMENTS_API = "/api/v1/experiments"
SAMPLES_API = "/api/v1/samples"
CHAR_API = "/api/v1/characterizations"
ANALYSIS_API = "/api/v1"


async def setup_xrd_characterization_with_file(client: AsyncClient, suffix: str) -> tuple[str, str]:
    """Helper: create Project → Exp → Sample → XRD Characterization → Raw File."""
    p_resp = await client.post(
        f"{PROJECTS_API}/",
        json={
            "project_code": f"P-XRD-{suffix}",
            "name": f"XRD Test Project {suffix}",
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
            "experiment_code": f"EXP-XRD-{suffix}",
            "title": f"XRD Exp {suffix}",
        },
    )
    e_id = e_resp.json()["id"]

    s_resp = await client.post(
        f"{SAMPLES_API}/",
        json={
            "experiment_id": e_id,
            "sample_code": f"S-XRD-{suffix}",
            "name": f"CuO Specimen {suffix}",
            "material": "CuO",
        },
    )
    s_id = s_resp.json()["id"]

    c_resp = await client.post(
        CHAR_API,
        json={
            "sample_id": s_id,
            "technique": "XRD",
            "operator": "Dr. XRD Analyst",
            "instrument_name": "Rigaku SmartLab",
        },
    )
    ch_id = c_resp.json()["id"]

    # Generate synthetic XRD data with 2 prominent CuO peaks (35.5 deg and 38.7 deg)
    rows = ["2theta,intensity"]
    for theta_10 in range(200, 600):
        t = theta_10 / 10.0
        # Peak 1 at 35.5
        i1 = 400.0 * np_exp(-((t - 35.5) ** 2) / (2 * 0.2 ** 2))
        # Peak 2 at 38.7
        i2 = 300.0 * np_exp(-((t - 38.7) ** 2) / (2 * 0.2 ** 2))
        bg = 50.0 + 0.1 * t
        intensity = bg + i1 + i2
        rows.append(f"{t:.1f},{intensity:.2f}")

    file_bytes = "\n".join(rows).encode("utf-8")
    files = {"file": ("cuo_xrd_spectrum.csv", file_bytes, "text/csv")}

    up_resp = await client.post(f"{CHAR_API}/{ch_id}/files", files=files)
    assert up_resp.status_code == 201

    return ch_id, s_id


def np_exp(val: float) -> float:
    import math
    return math.exp(val)


@pytest.mark.asyncio
async def test_xrd_analysis_full_pipeline(client: AsyncClient) -> None:
    """Execute XRD analysis, verify detected peaks, Scherrer size property, and processed curve points."""
    ch_id, sample_id = await setup_xrd_characterization_with_file(client, "FULL1")

    # Run analysis
    an_resp = await client.post(
        f"{CHAR_API}/{ch_id}/xrd/analyze",
        json={
            "preprocessing": {
                "baseline_subtraction": True,
                "smoothing": True,
                "savgol_window": 11,
                "savgol_polyorder": 3,
            },
            "peak_detection": {
                "prominence": 30.0,
                "min_distance": 5,
            },
            "scherrer": {
                "calculate_crystallite_size": True,
                "wavelength_nm": 0.15406,
                "shape_factor_k": 0.9,
            },
            "notes": "Standard CuO diffraction pattern analysis",
        },
    )
    assert an_resp.status_code == 201
    run_data = an_resp.json()
    assert run_data["status"] == "COMPLETED"
    assert run_data["analysis_type"] == "XRD"
    run_id = run_data["id"]

    # Verify peaks were detected
    peaks = run_data["peaks"]
    assert len(peaks) >= 2
    # Verify main peak position around 35.5 deg
    main_peak = max(peaks, key=lambda p: p["intensity"])
    assert abs(main_peak["peak_position"] - 35.5) < 0.3

    # Verify calculated property (Scherrer Crystallite Size)
    props = run_data["calculated_properties"]
    assert len(props) == 1
    sch_prop = props[0]
    assert sch_prop["property_name"] == "Crystallite Size"
    assert sch_prop["unit"] == "nm"
    assert sch_prop["value"] > 0.0
    assert sch_prop["calculation_method"] == "Scherrer Equation"

    # Fetch processed curve data points for Plotly
    proc_resp = await client.get(f"{ANALYSIS_API}/analysis-runs/{run_id}/processed-data")
    assert proc_resp.status_code == 200
    pts = proc_resp.json()["data_points"]
    assert len(pts) == 400
    assert "raw_intensity" in pts[0]
    assert "processed_intensity" in pts[0]


@pytest.mark.asyncio
async def test_multiple_analysis_runs_history(client: AsyncClient) -> None:
    """Running XRD analysis twice with different parameters stores separate reproducible AnalysisRun records."""
    ch_id, _ = await setup_xrd_characterization_with_file(client, "HIST1")

    # Run 1: High prominence threshold
    r1_resp = await client.post(
        f"{CHAR_API}/{ch_id}/xrd/analyze",
        json={
            "peak_detection": {"prominence": 100.0},
            "notes": "Run 1: High prominence filter",
        },
    )
    assert r1_resp.status_code == 201

    # Run 2: Low prominence threshold
    r2_resp = await client.post(
        f"{CHAR_API}/{ch_id}/xrd/analyze",
        json={
            "peak_detection": {"prominence": 10.0},
            "notes": "Run 2: Sensitive peak filter",
        },
    )
    assert r2_resp.status_code == 201

    # List history
    hist_resp = await client.get(f"{CHAR_API}/{ch_id}/analysis-runs")
    assert hist_resp.status_code == 200
    history = hist_resp.json()
    assert len(history) == 2
    notes_list = [h["notes"] for h in history]
    assert "Run 1: High prominence filter" in notes_list
    assert "Run 2: Sensitive peak filter" in notes_list
