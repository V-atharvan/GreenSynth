"""
GreenSynth Analytics — Integration Tests: Parameter Schema & Experiment Creation
"""

from __future__ import annotations

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.ml.dataset.resolver import ParameterResolver

from app.database.seed import seed_demo_project

PROJECTS_API = "/api/v1/projects"
EXPERIMENTS_API = "/api/v1/experiments"


@pytest_asyncio.fixture(autouse=True)
async def seed_projects(db_session: AsyncSession) -> None:
    """Ensure P1-P8 projects and parameter definitions are seeded before tests."""
    await seed_demo_project(db_session)


def make_p8_payload(def_map: dict[str, str], overrides: dict[str, tuple[str, str | None]] | None = None) -> dict:
    defaults: dict[str, tuple[str, str | None]] = {
        "copper_precursor_salt": ("Copper acetate monohydrate", None),
        "precursor_concentration": ("0.1", "mol/L"),
        "precursor_solution_volume": ("100", "mL"),
        "mulberry_extract_concentration": ("10", "g/L"),
        "mulberry_extract_volume": ("20", "mL"),
        "ethanol_volume": ("80", "mL"),
        "substrate_type": ("FTO Glass", None),
        "substrate_temperature_c": ("350", "°C"),
        "spray_rate_ml_min": ("5", "mL/min"),
        "spray_duration_min": ("15", "min"),
        "nozzle_substrate_distance_cm": ("20", "cm"),
        "carrier_gas_pressure_kpa": ("150", "kPa"),
        "spray_cycles": ("10", "cycles"),
        "ambient_temperature_c": ("25", "°C"),
        "ambient_relative_humidity": ("45", "%"),
    }
    if overrides:
        defaults.update(overrides)
    params = []
    for code, (val, unit) in defaults.items():
        if code in def_map:
            item: dict[str, str] = {"parameter_definition_id": def_map[code], "value": val}
            if unit:
                item["unit"] = unit
            params.append(item)
    return {"parameters": params}


@pytest.mark.asyncio
async def test_p8_all_valid_parameters(client: AsyncClient) -> None:
    """1. Creating a P8 experiment with all 15 valid parameters."""
    p_resp = await client.get(f"{PROJECTS_API}/")
    assert p_resp.status_code == 200
    projects = p_resp.json()
    p8 = next((p for p in projects if p["project_code"] == "P8"), None)
    if not p8:
        pytest.skip("P8 project not seeded")

    p8_id = p8["id"]
    defs_resp = await client.get(f"{PROJECTS_API}/{p8_id}/parameters")
    assert defs_resp.status_code == 200
    defs = defs_resp.json()
    def_map = {d["parameter_code"]: d["id"] for d in defs}

    expected_codes = [
        "copper_precursor_salt",
        "precursor_concentration",
        "precursor_solution_volume",
        "mulberry_extract_concentration",
        "mulberry_extract_volume",
        "ethanol_volume",
        "substrate_type",
        "substrate_temperature_c",
        "spray_rate_ml_min",
        "spray_duration_min",
        "nozzle_substrate_distance_cm",
        "carrier_gas_pressure_kpa",
        "spray_cycles",
        "ambient_temperature_c",
        "ambient_relative_humidity",
    ]
    for code in expected_codes:
        assert code in def_map, f"Missing expected parameter definition code: {code}"

    exp_resp = await client.post(
        f"{EXPERIMENTS_API}/",
        json={
            "project_id": p8_id,
            "experiment_code": "EXP-P8-VALID-001",
            "title": "P8 Valid Spray Pyrolysis Test",
            "status": "COMPLETED",
        },
    )
    assert exp_resp.status_code == 201
    exp_id = exp_resp.json()["id"]

    valid_payload = make_p8_payload(def_map)
    save_resp = await client.post(f"{EXPERIMENTS_API}/{exp_id}/parameters", json=valid_payload)
    assert save_resp.status_code == 200
    saved = save_resp.json()
    assert len(saved) == 15


@pytest.mark.asyncio
async def test_reject_invalid_substrate_temperature(client: AsyncClient) -> None:
    """2. Rejecting invalid substrate temperature (> 600 °C)."""
    p_resp = await client.get(f"{PROJECTS_API}/")
    p8 = next((p for p in p_resp.json() if p["project_code"] == "P8"), None)
    if not p8:
        pytest.skip("P8 project not seeded")

    defs_resp = await client.get(f"{PROJECTS_API}/{p8['id']}/parameters")
    def_map = {d["parameter_code"]: d["id"] for d in defs_resp.json()}

    exp_resp = await client.post(
        f"{EXPERIMENTS_API}/",
        json={"project_id": p8["id"], "experiment_code": "EXP-INV-TEMP", "title": "Invalid Temp"},
    )
    exp_id = exp_resp.json()["id"]

    payload = make_p8_payload(def_map, {"substrate_temperature_c": ("700", "°C")})
    resp = await client.post(f"{EXPERIMENTS_API}/{exp_id}/parameters", json=payload)
    assert resp.status_code == 422
    assert "maximum allowed limit of 600.0" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_reject_invalid_spray_rate(client: AsyncClient) -> None:
    """3. Rejecting invalid spray rate (> 20 mL/min)."""
    p_resp = await client.get(f"{PROJECTS_API}/")
    p8 = next((p for p in p_resp.json() if p["project_code"] == "P8"), None)
    if not p8:
        pytest.skip("P8 project not seeded")

    defs_resp = await client.get(f"{PROJECTS_API}/{p8['id']}/parameters")
    def_map = {d["parameter_code"]: d["id"] for d in defs_resp.json()}

    exp_resp = await client.post(
        f"{EXPERIMENTS_API}/",
        json={"project_id": p8["id"], "experiment_code": "EXP-INV-RATE", "title": "Invalid Spray Rate"},
    )
    exp_id = exp_resp.json()["id"]

    payload = make_p8_payload(def_map, {"spray_rate_ml_min": ("50", "mL/min")})
    resp = await client.post(f"{EXPERIMENTS_API}/{exp_id}/parameters", json=payload)
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_reject_invalid_spray_duration(client: AsyncClient) -> None:
    """4. Rejecting invalid spray duration (< 0.5 min)."""
    p_resp = await client.get(f"{PROJECTS_API}/")
    p8 = next((p for p in p_resp.json() if p["project_code"] == "P8"), None)
    if not p8:
        pytest.skip("P8 project not seeded")

    defs_resp = await client.get(f"{PROJECTS_API}/{p8['id']}/parameters")
    def_map = {d["parameter_code"]: d["id"] for d in defs_resp.json()}

    exp_resp = await client.post(
        f"{EXPERIMENTS_API}/",
        json={"project_id": p8["id"], "experiment_code": "EXP-INV-DUR", "title": "Invalid Spray Duration"},
    )
    exp_id = exp_resp.json()["id"]

    payload = make_p8_payload(def_map, {"spray_duration_min": ("0.1", "min")})
    resp = await client.post(f"{EXPERIMENTS_API}/{exp_id}/parameters", json=payload)
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_reject_invalid_nozzle_distance(client: AsyncClient) -> None:
    """5. Rejecting invalid nozzle distance (< 5 cm)."""
    p_resp = await client.get(f"{PROJECTS_API}/")
    p8 = next((p for p in p_resp.json() if p["project_code"] == "P8"), None)
    if not p8:
        pytest.skip("P8 project not seeded")

    defs_resp = await client.get(f"{PROJECTS_API}/{p8['id']}/parameters")
    def_map = {d["parameter_code"]: d["id"] for d in defs_resp.json()}

    exp_resp = await client.post(
        f"{EXPERIMENTS_API}/",
        json={"project_id": p8["id"], "experiment_code": "EXP-INV-DIST", "title": "Invalid Nozzle Distance"},
    )
    exp_id = exp_resp.json()["id"]

    payload = make_p8_payload(def_map, {"nozzle_substrate_distance_cm": ("2.0", "cm")})
    resp = await client.post(f"{EXPERIMENTS_API}/{exp_id}/parameters", json=payload)
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_reject_invalid_carrier_pressure(client: AsyncClient) -> None:
    """6. Rejecting invalid carrier pressure (> 500 kPa)."""
    p_resp = await client.get(f"{PROJECTS_API}/")
    p8 = next((p for p in p_resp.json() if p["project_code"] == "P8"), None)
    if not p8:
        pytest.skip("P8 project not seeded")

    defs_resp = await client.get(f"{PROJECTS_API}/{p8['id']}/parameters")
    def_map = {d["parameter_code"]: d["id"] for d in defs_resp.json()}

    exp_resp = await client.post(
        f"{EXPERIMENTS_API}/",
        json={"project_id": p8["id"], "experiment_code": "EXP-INV-PRESS", "title": "Invalid Carrier Pressure"},
    )
    exp_id = exp_resp.json()["id"]

    payload = make_p8_payload(def_map, {"carrier_gas_pressure_kpa": ("600", "kPa")})
    resp = await client.post(f"{EXPERIMENTS_API}/{exp_id}/parameters", json=payload)
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_reject_invalid_spray_cycle_count(client: AsyncClient) -> None:
    """7. Rejecting invalid spray cycle count (< 1 cycle)."""
    p_resp = await client.get(f"{PROJECTS_API}/")
    p8 = next((p for p in p_resp.json() if p["project_code"] == "P8"), None)
    if not p8:
        pytest.skip("P8 project not seeded")

    defs_resp = await client.get(f"{PROJECTS_API}/{p8['id']}/parameters")
    def_map = {d["parameter_code"]: d["id"] for d in defs_resp.json()}

    exp_resp = await client.post(
        f"{EXPERIMENTS_API}/",
        json={"project_id": p8["id"], "experiment_code": "EXP-INV-CYC", "title": "Invalid Spray Cycles"},
    )
    exp_id = exp_resp.json()["id"]

    payload = make_p8_payload(def_map, {"spray_cycles": ("0", "cycles")})
    resp = await client.post(f"{EXPERIMENTS_API}/{exp_id}/parameters", json=payload)
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_reject_invalid_humidity(client: AsyncClient) -> None:
    """8. Rejecting invalid humidity (> 95%)."""
    p_resp = await client.get(f"{PROJECTS_API}/")
    p8 = next((p for p in p_resp.json() if p["project_code"] == "P8"), None)
    if not p8:
        pytest.skip("P8 project not seeded")

    defs_resp = await client.get(f"{PROJECTS_API}/{p8['id']}/parameters")
    def_map = {d["parameter_code"]: d["id"] for d in defs_resp.json()}

    exp_resp = await client.post(
        f"{EXPERIMENTS_API}/",
        json={"project_id": p8["id"], "experiment_code": "EXP-INV-HUM", "title": "Invalid Humidity"},
    )
    exp_id = exp_resp.json()["id"]

    payload = make_p8_payload(def_map, {"ambient_relative_humidity": ("100", "%")})
    resp = await client.post(f"{EXPERIMENTS_API}/{exp_id}/parameters", json=payload)
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_persistence_and_retrieval(client: AsyncClient) -> None:
    """9 & 10. Correct persistence of parameter codes and retrieval of experiment."""
    p_resp = await client.get(f"{PROJECTS_API}/")
    p8 = next((p for p in p_resp.json() if p["project_code"] == "P8"), None)
    if not p8:
        pytest.skip("P8 project not seeded")

    defs_resp = await client.get(f"{PROJECTS_API}/{p8['id']}/parameters")
    def_map = {d["parameter_code"]: d["id"] for d in defs_resp.json()}

    exp_resp = await client.post(
        f"{EXPERIMENTS_API}/",
        json={"project_id": p8["id"], "experiment_code": "EXP-PERSIST-01", "title": "Persistence Check"},
    )
    exp_id = exp_resp.json()["id"]

    payload = make_p8_payload(
        def_map,
        {
            "ambient_temperature_c": ("24.5", "°C"),
            "ambient_relative_humidity": ("50.0", "%"),
        },
    )
    await client.post(f"{EXPERIMENTS_API}/{exp_id}/parameters", json=payload)

    # Retrieve experiment parameters
    get_params = await client.get(f"{EXPERIMENTS_API}/{exp_id}/parameters")
    assert get_params.status_code == 200
    params = get_params.json()
    assert len(params) == 15
    codes = [p["parameter_definition"]["parameter_code"] for p in params]
    assert "ambient_temperature_c" in codes
    assert "ambient_relative_humidity" in codes


@pytest.mark.asyncio
async def test_ml_dataset_builder_mapping() -> None:
    """12. Correct mapping into ML Dataset Builder using ParameterResolver."""
    params_map = {
        "ethanol_volume": 80.0,
        "substrate_temperature_c": 350.0,
        "spray_rate_ml_min": 5.0,
    }
    param_units_map = {
        "ethanol_volume": "mL",
        "substrate_temperature_c": "°C",
        "spray_rate_ml_min": "mL/min",
    }

    # Resolve via canonical code
    res1 = ParameterResolver.resolve_parameter(
        params_map, param_units_map, {"feature_name": "ethanol_volume", "unit": "mL"}
    )
    assert res1.is_found is True
    assert res1.value == 80.0

    # Resolve via legacy alias 'solvent_volume'
    res_legacy = ParameterResolver.resolve_parameter(
        params_map, param_units_map, {"feature_name": "solvent_volume", "unit": "mL"}
    )
    assert res_legacy.is_found is True
    assert res_legacy.value == 80.0


@pytest.mark.asyncio
async def test_project_specific_parameter_isolation(client: AsyncClient) -> None:
    """14. P1/P2/P3/P4/P5/P6 do not incorrectly receive P8-only parameters."""
    p_resp = await client.get(f"{PROJECTS_API}/")
    projects = p_resp.json()

    p1 = next((p for p in projects if p["project_code"] == "P1"), None)
    if p1:
        p1_defs = await client.get(f"{PROJECTS_API}/{p1['id']}/parameters")
        p1_codes = [d["parameter_code"] for d in p1_defs.json()]
        # P1 (Sol-Gel) should have sol_gel_aging_temperature_c, but NOT spray_cycles
        assert "sol_gel_aging_temperature_c" in p1_codes
        assert "spray_cycles" not in p1_codes
