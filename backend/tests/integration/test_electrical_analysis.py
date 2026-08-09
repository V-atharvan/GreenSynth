"""
GreenSynth Analytics — Integration Tests: Electrical I-V Analysis Workflow
"""

from __future__ import annotations

import pytest
from httpx import AsyncClient

PROJECTS_API = "/api/v1/projects"
EXPERIMENTS_API = "/api/v1/experiments"
SAMPLES_API = "/api/v1/samples"
CHAR_API = "/api/v1/characterizations"
ANALYSIS_API = "/api/v1"


async def setup_electrical_characterization_with_file(client: AsyncClient, suffix: str) -> tuple[str, str]:
    """Helper: create Project → Exp → Sample → Electrical Characterization → Raw File."""
    p_resp = await client.post(
        f"{PROJECTS_API}/",
        json={
            "project_code": f"P-E-{suffix}",
            "name": f"Electrical Test Project {suffix}",
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
            "experiment_code": f"EXP-E-{suffix}",
            "title": f"Electrical Exp {suffix}",
        },
    )
    e_id = e_resp.json()["id"]

    s_resp = await client.post(
        f"{SAMPLES_API}/",
        json={
            "experiment_id": e_id,
            "sample_code": f"S-E-{suffix}",
            "name": f"CuO Film {suffix}",
            "material": "CuO",
        },
    )
    s_id = s_resp.json()["id"]

    c_resp = await client.post(
        CHAR_API,
        json={
            "sample_id": s_id,
            "technique": "ELECTRICAL",
            "operator": "Dr. Electrical Engineer",
            "instrument_name": "Keithley 2400 SourceMeter",
        },
    )
    ch_id = c_resp.json()["id"]

    # Generate synthetic I-V curve (R = 150 Ohms -> V = 150 * I)
    rows = ["voltage,current"]
    for v in range(-5, 6):
        i = v / 150.0  # Current in Amperes
        rows.append(f"{v:.2f},{i:.6f}")

    file_bytes = "\n".join(rows).encode("utf-8")
    files = {"file": ("cuo_iv_curve.csv", file_bytes, "text/csv")}

    up_resp = await client.post(f"{CHAR_API}/{ch_id}/files", files=files)
    assert up_resp.status_code == 201

    return ch_id, s_id


@pytest.mark.asyncio
async def test_electrical_analysis_full_pipeline(client: AsyncClient) -> None:
    """Execute Electrical analysis, verify Resistance R, Resistivity rho, Conductivity sigma properties, and I-V data."""
    ch_id, sample_id = await setup_electrical_characterization_with_file(client, "FULL1")

    # Run analysis
    an_resp = await client.post(
        f"{CHAR_API}/{ch_id}/electrical/analyze",
        json={
            "units": {
                "voltage_unit": "V",
                "current_unit": "A",
                "length_unit": "cm",
            },
            "geometry": {
                "geometry_type": "RECTANGULAR_BAR",
                "length": 1.0,
                "width": 0.5,
                "thickness": 0.05,
            },
            "notes": "CuO thin film 2-probe electrical conductivity measurement",
        },
    )
    assert an_resp.status_code == 201
    run_data = an_resp.json()
    assert run_data["status"] == "COMPLETED"
    assert run_data["analysis_type"] == "ELECTRICAL"
    run_id = run_data["id"]

    # Verify calculated properties
    props = run_data["calculated_properties"]
    assert len(props) == 3

    prop_names = {p["property_name"]: p for p in props}
    assert "Electrical Resistance" in prop_names
    assert "Electrical Resistivity" in prop_names
    assert "Electrical Conductivity" in prop_names

    r_prop = prop_names["Electrical Resistance"]
    assert abs(r_prop["value"] - 150.0) < 0.1
    assert r_prop["unit"] == "Ohm"

    rho_prop = prop_names["Electrical Resistivity"]
    # rho = R * A / L = 150 * (0.5 * 0.05) / 1.0 = 3.75 Ohm*cm
    assert abs(rho_prop["value"] - 3.75) < 0.01

    sigma_prop = prop_names["Electrical Conductivity"]
    # sigma = 1 / 3.75 = 0.266667 S/cm
    assert abs(sigma_prop["value"] - 0.266667) < 0.01

    # Fetch I-V data points for Plotly
    iv_resp = await client.get(f"{ANALYSIS_API}/analysis-runs/{run_id}/electrical-data")
    assert iv_resp.status_code == 200
    iv_data = iv_resp.json()
    assert len(iv_data["data_points"]) == 11
    assert len(iv_data["fit_line"]) > 0


@pytest.mark.asyncio
async def test_electrical_missing_dimensions_warning(client: AsyncClient) -> None:
    """Missing sample thickness calculates Resistance but omits Resistivity/Conductivity with warning."""
    ch_id, _ = await setup_electrical_characterization_with_file(client, "WARN1")

    an_resp = await client.post(
        f"{CHAR_API}/{ch_id}/electrical/analyze",
        json={
            "geometry": {
                "length": 1.0,
                "width": 0.5,
                "thickness": None,  # Missing thickness
            },
        },
    )
    assert an_resp.status_code == 201
    run_data = an_resp.json()

    props = run_data["calculated_properties"]
    assert len(props) == 1
    assert props[0]["property_name"] == "Electrical Resistance"
    assert "sample thickness (T) is missing" in run_data["assumptions"]["warning"]


@pytest.mark.asyncio
async def test_electrical_multiple_analysis_runs_history(client: AsyncClient) -> None:
    """Executing electrical analysis twice with different fit regions stores coexisting reproducible runs."""
    ch_id, _ = await setup_electrical_characterization_with_file(client, "HIST1")

    # Run 1: Full voltage range
    await client.post(
        f"{CHAR_API}/{ch_id}/electrical/analyze",
        json={"notes": "Run 1: Full voltage range fit"},
    )

    # Run 2: Positive voltage range
    await client.post(
        f"{CHAR_API}/{ch_id}/electrical/analyze",
        json={
            "fit_voltage_min": 0.0,
            "notes": "Run 2: Positive bias linear fit",
        },
    )

    # List history
    hist_resp = await client.get(f"{CHAR_API}/{ch_id}/analysis-runs")
    assert hist_resp.status_code == 200
    history = hist_resp.json()
    assert len(history) == 2
    notes_list = [h["notes"] for h in history]
    assert "Run 1: Full voltage range fit" in notes_list
    assert "Run 2: Positive bias linear fit" in notes_list
