"""
GreenSynth Analytics — Integration Tests: Characterization & File Storage API
"""

from __future__ import annotations

import pytest
from httpx import AsyncClient

PROJECTS_API = "/api/v1/projects"
EXPERIMENTS_API = "/api/v1/experiments"
SAMPLES_API = "/api/v1/samples"
CHAR_API = "/api/v1/characterizations"
FILES_API = "/api/v1/files"


async def setup_sample(client: AsyncClient, suffix: str) -> tuple[str, str, str]:
    """Helper: create Project → Experiment → Sample hierarchy."""
    p_resp = await client.post(
        f"{PROJECTS_API}/",
        json={
            "project_code": f"P-CHAR-{suffix}",
            "name": f"Characterization Test Project {suffix}",
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
            "experiment_code": f"EXP-CHAR-{suffix}",
            "title": f"Char Experiment {suffix}",
            "status": "COMPLETED",
        },
    )
    e_id = e_resp.json()["id"]

    s_resp = await client.post(
        f"{SAMPLES_API}/",
        json={
            "experiment_id": e_id,
            "sample_code": f"S-CHAR-{suffix}",
            "name": f"Char Sample {suffix}",
            "material": "CuO",
            "status": "PREPARED",
        },
    )
    s_id = s_resp.json()["id"]
    return p_id, e_id, s_id


@pytest.mark.asyncio
async def test_create_and_get_characterization(client: AsyncClient) -> None:
    """Create a characterization record for a sample and retrieve it."""
    _, _, sample_id = await setup_sample(client, "C1")

    # Create characterization
    resp = await client.post(
        CHAR_API,
        json={
            "sample_id": sample_id,
            "technique": "XRD",
            "operator": "Dr. Researcher",
            "instrument_name": "Rigaku SmartLab",
            "instrument_model": "SmartLab SE",
            "notes": "Cu-Ka radiation, 2theta 20-80 deg",
        },
    )
    assert resp.status_code == 201
    ch = resp.json()
    assert ch["technique"] == "XRD"
    assert ch["status"] == "UPLOADED"
    assert ch["sample_id"] == sample_id
    ch_id = ch["id"]

    # List characterizations for sample
    list_resp = await client.get(f"{SAMPLES_API}/{sample_id}/characterizations")
    assert list_resp.status_code == 200
    chs = list_resp.json()
    assert len(chs) == 1
    assert chs[0]["id"] == ch_id


@pytest.mark.asyncio
async def test_upload_and_download_raw_file(client: AsyncClient) -> None:
    """Upload a raw XRD CSV file, verify checksum, and download the exact original file."""
    _, _, sample_id = await setup_sample(client, "U1")

    # Create characterization
    c_resp = await client.post(
        CHAR_API,
        json={
            "sample_id": sample_id,
            "technique": "XRD",
            "operator": "Alice",
            "instrument_name": "XRD Diffractometer",
        },
    )
    ch_id = c_resp.json()["id"]

    # Upload raw file
    file_content = b"2theta,intensity\n20.0,150\n20.1,155\n20.2,160\n"
    files = {"file": ("test_xrd_spectrum.csv", file_content, "text/csv")}

    up_resp = await client.post(f"{CHAR_API}/{ch_id}/files", files=files)
    assert up_resp.status_code == 201
    file_data = up_resp.json()
    assert file_data["original_filename"] == "test_xrd_spectrum.csv"
    assert file_data["file_extension"] == "csv"
    assert len(file_data["checksum"]) == 64  # SHA-256 length
    file_id = file_data["id"]

    # Verify characterization status updated to READY_FOR_ANALYSIS
    ch_resp = await client.get(f"{CHAR_API}/{ch_id}")
    assert ch_resp.json()["status"] == "READY_FOR_ANALYSIS"

    # Download file
    dl_resp = await client.get(f"{FILES_API}/{file_id}/download")
    assert dl_resp.status_code == 200
    assert dl_resp.content == file_content
    assert "test_xrd_spectrum.csv" in dl_resp.headers.get("Content-Disposition", "")


@pytest.mark.asyncio
async def test_invalid_file_extension_rejection(client: AsyncClient) -> None:
    """Uploading an image (.png) for XRD characterization returns 422 error."""
    _, _, sample_id = await setup_sample(client, "INVEXT")

    c_resp = await client.post(
        CHAR_API,
        json={"sample_id": sample_id, "technique": "XRD"},
    )
    ch_id = c_resp.json()["id"]

    # Try uploading PNG for XRD
    files = {"file": ("image.png", b"\x89PNG\r\n\x1a\nfake_image_data", "image/png")}
    up_resp = await client.post(f"{CHAR_API}/{ch_id}/files", files=files)
    assert up_resp.status_code == 422
    assert "is not supported for XRD characterization" in up_resp.json()["detail"]


@pytest.mark.asyncio
async def test_duplicate_file_detection(client: AsyncClient) -> None:
    """Uploading the exact same file content twice returns HTTP 409 Conflict."""
    _, _, sample_id = await setup_sample(client, "DUP")

    c_resp = await client.post(
        CHAR_API,
        json={"sample_id": sample_id, "technique": "UV_VIS"},
    )
    ch_id = c_resp.json()["id"]

    content = b"wavelength,absorbance\n300,0.12\n301,0.13\n302,0.14\n"
    files1 = {"file": ("uv_vis_data.csv", content, "text/csv")}

    # First upload - Success
    up_resp1 = await client.post(f"{CHAR_API}/{ch_id}/files", files=files1)
    assert up_resp1.status_code == 201

    # Second upload with same content - 409 Conflict
    files2 = {"file": ("uv_vis_copy.csv", content, "text/csv")}
    up_resp2 = await client.post(f"{CHAR_API}/{ch_id}/files", files=files2)
    assert up_resp2.status_code == 409
    assert "Duplicate file detected" in up_resp2.json()["detail"]


@pytest.mark.asyncio
async def test_path_traversal_protection(client: AsyncClient) -> None:
    """Uploading file with path traversal in filename remains safely inside storage directory."""
    _, _, sample_id = await setup_sample(client, "PATHTRAV")

    c_resp = await client.post(
        CHAR_API,
        json={"sample_id": sample_id, "technique": "FTIR"},
    )
    ch_id = c_resp.json()["id"]

    files = {"file": ("../../../etc/malicious.csv", b"wavenumber,transmittance\n1000,80\n", "text/csv")}
    up_resp = await client.post(f"{CHAR_API}/{ch_id}/files", files=files)
    assert up_resp.status_code == 201
    file_id = up_resp.json()["id"]

    # Verify file metadata stored safely
    meta_resp = await client.get(f"{FILES_API}/{file_id}")
    assert meta_resp.status_code == 200
    assert ".." not in meta_resp.json()["storage_path"]
