"""
GreenSynth Analytics — Integration Tests: FTIR Spectroscopy & Researcher Annotations
"""

from __future__ import annotations

import pytest
from httpx import AsyncClient

PROJECTS_API = "/api/v1/projects"
EXPERIMENTS_API = "/api/v1/experiments"
SAMPLES_API = "/api/v1/samples"
CHAR_API = "/api/v1/characterizations"
ANALYSIS_API = "/api/v1"


async def setup_ftir_characterization_with_file(client: AsyncClient, suffix: str) -> tuple[str, str]:
    """Helper: create Project → Exp → Sample → FTIR Characterization → Raw File."""
    p_resp = await client.post(
        f"{PROJECTS_API}/",
        json={
            "project_code": f"P-FT-{suffix}",
            "name": f"FTIR Test Project {suffix}",
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
            "experiment_code": f"EXP-FT-{suffix}",
            "title": f"FTIR Exp {suffix}",
        },
    )
    e_id = e_resp.json()["id"]

    s_resp = await client.post(
        f"{SAMPLES_API}/",
        json={
            "experiment_id": e_id,
            "sample_code": f"S-FT-{suffix}",
            "name": f"CuO Powder {suffix}",
            "material": "CuO",
        },
    )
    s_id = s_resp.json()["id"]

    c_resp = await client.post(
        CHAR_API,
        json={
            "sample_id": s_id,
            "technique": "FTIR",
            "operator": "Dr. FTIR Spectroscopist",
            "instrument_name": "PerkinElmer Spectrum Two",
        },
    )
    ch_id = c_resp.json()["id"]

    # Generate synthetic FTIR dataset with C=O dip at ~1700 cm^-1 and Cu-O dip at ~600 cm^-1
    rows = ["wavenumber,transmittance"]
    for wn in range(400, 4000, 10):
        t_val = 98.0 - 45.0 * ((wn - 1700) ** 2 / ( (wn - 1700)**2 + 1000 ))
        rows.append(f"{wn},{t_val:.2f}")

    file_bytes = "\n".join(rows).encode("utf-8")
    files = {"file": ("cuo_ftir_spectrum.csv", file_bytes, "text/csv")}

    up_resp = await client.post(f"{CHAR_API}/{ch_id}/files", files=files)
    assert up_resp.status_code == 201

    return ch_id, s_id


@pytest.mark.asyncio
async def test_ftir_analysis_and_annotations_pipeline(client: AsyncClient) -> None:
    """Execute FTIR analysis, verify peaks detected, add researcher annotation, and query annotations list."""
    ch_id, _ = await setup_ftir_characterization_with_file(client, "FULL1")

    # Run analysis
    an_resp = await client.post(
        f"{CHAR_API}/{ch_id}/ftir/analyze",
        json={
            "preprocessing": {
                "smoothing": True,
                "savgol_window": 11,
            },
            "peak_detection": {
                "prominence": 1.0,
                "min_distance": 10,
            },
            "notes": "CuO green synthesis phytochemical capping layer FTIR analysis",
        },
    )
    assert an_resp.status_code == 201
    run_data = an_resp.json()
    assert run_data["status"] == "COMPLETED"
    assert run_data["analysis_type"] == "FTIR"
    run_id = run_data["id"]

    # Fetch FTIR spectrum curve & detected peaks
    ft_resp = await client.get(f"{ANALYSIS_API}/analysis-runs/{run_id}/ftir-data")
    assert ft_resp.status_code == 200
    ft_data = ft_resp.json()
    assert len(ft_data["data_points"]) > 100

    # Add researcher annotation (C=O stretch)
    ann_resp = await client.post(
        f"{ANALYSIS_API}/analysis-runs/{run_id}/ftir-annotations",
        json={
            "wavenumber_cm1": 1700.0,
            "label": "C=O Stretch",
            "interpretation": "Phytochemical carbonyl capping group absorption",
            "confidence": "Medium",
            "notes": "Observed in plant extract capping agent",
        },
    )
    assert ann_resp.status_code == 201
    ann_data = ann_resp.json()
    assert ann_data["label"] == "C=O Stretch"

    # List annotations
    list_resp = await client.get(f"{ANALYSIS_API}/analysis-runs/{run_id}/ftir-annotations")
    assert list_resp.status_code == 200
    anns = list_resp.json()
    assert len(anns) == 1
    assert anns[0]["label"] == "C=O Stretch"
