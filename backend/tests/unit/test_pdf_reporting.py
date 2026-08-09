"""
GreenSynth Analytics — Scientific PDF Report Generation Module Unit Tests
"""

import uuid
from datetime import datetime

import pytest
from app.reporting.charts import ReportChartGenerator
from app.reporting.renderer import PDFReportRenderer
from app.reporting.schemas import (
    ElectricalReportSectionSchema,
    ExperimentReportData,
    MLPredictionReportSectionSchema,
    OptimizationReportSectionSchema,
    ProvenanceItemSchema,
    StatisticalReportSectionSchema,
    UVVisReportSectionSchema,
    ValidationReportSectionSchema,
    XRDReportSectionSchema,
)


def test_experiment_report_dto_instantiation():
    exp_id = str(uuid.uuid4())
    data = ExperimentReportData(
        project_code="P7",
        project_name="CuO Phytochemical Spray Pyrolysis",
        material="CuO",
        extract="Mulberry",
        solvent="Ethanol",
        synthesis_method="Spray Pyrolysis",
        experiment_id=exp_id,
        experiment_code="EXP-P7-001",
        title="Mulberry CuO Deposition Test",
        researcher="Dr. Scientist",
        status="COMPLETED",
        created_at=datetime.utcnow(),
        synthesis_parameters=[
            {
                "parameter_code": "substrate_temp_c",
                "parameter_name": "Substrate Temperature",
                "value": "350",
                "unit": "°C",
                "source": "Experiment Record",
                "validation_status": "Valid",
            }
        ],
        samples=[
            {
                "sample_id": str(uuid.uuid4()),
                "sample_code": "SAMP-P7-001-A",
                "name": "CuO Thin Film",
                "material": "CuO",
                "status": "COMPLETED",
                "created_at": "2026-08-09",
            }
        ],
        characterization_summary=[
            {
                "sample_code": "SAMP-P7-001-A",
                "technique": "XRD",
                "raw_file": "P7_001_xrd.csv",
                "analysis_status": "Analyzed",
                "calculated_properties": "Crystallite Size: 22.4 nm",
            }
        ],
        xrd=XRDReportSectionSchema(
            available=True,
            raw_filename="P7_001_xrd.csv",
            analysis_version="v1.0",
            crystallite_size_nm=22.4,
            peaks=[
                {"peak_number": 1, "two_theta": 35.5, "intensity": 800.0, "fwhm": 0.38, "crystallite_size_nm": 22.4}
            ],
        ),
        uvvis=UVVisReportSectionSchema(
            available=True,
            raw_filename="P7_001_uvvis.csv",
            optical_band_gap_ev=1.45,
        ),
        electrical=ElectricalReportSectionSchema(
            available=True,
            raw_filename="P7_001_iv.csv",
            resistance_ohms=200.0,
            resistivity_ohm_cm=20.8,
            conductivity_s_cm=0.048,
        ),
        provenance_items=[
            ProvenanceItemSchema(
                sample_code="SAMP-P7-001-A",
                technique="XRD",
                raw_filename="P7_001_xrd.csv",
                raw_file_id=str(uuid.uuid4()),
                sha256_checksum="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
                analysis_run_id=str(uuid.uuid4()),
                analysis_method="XRD Peak Analysis",
            )
        ],
    )

    assert data.project_code == "P7"
    assert data.xrd.crystallite_size_nm == 22.4
    assert data.uvvis.optical_band_gap_ev == 1.45
    assert data.electrical.conductivity_s_cm == 0.048
    assert len(data.provenance_items) == 1


def test_chart_generator_matplotlib_bytes():
    xrd_bytes = ReportChartGenerator.generate_xrd_plot()
    assert isinstance(xrd_bytes, bytes)
    assert len(xrd_bytes) > 500
    assert xrd_bytes.startswith(b"\x89PNG")

    uvvis_bytes = ReportChartGenerator.generate_uvvis_tauc_plot(1.45)
    assert isinstance(uvvis_bytes, bytes)
    assert len(uvvis_bytes) > 500
    assert uvvis_bytes.startswith(b"\x89PNG")

    elec_bytes = ReportChartGenerator.generate_electrical_iv_plot(200.0)
    assert isinstance(elec_bytes, bytes)
    assert len(elec_bytes) > 500
    assert elec_bytes.startswith(b"\x89PNG")


def test_pdf_report_renderer_compilation():
    exp_id = str(uuid.uuid4())
    data = ExperimentReportData(
        project_code="P7",
        project_name="CuO Phytochemical Spray Pyrolysis",
        material="CuO",
        extract="Mulberry",
        solvent="Ethanol",
        synthesis_method="Spray Pyrolysis",
        experiment_id=exp_id,
        experiment_code="EXP-P7-001",
        title="Mulberry CuO Deposition Test",
        researcher="Dr. Scientist",
        status="COMPLETED",
        created_at=datetime.utcnow(),
        synthesis_parameters=[
            {
                "parameter_code": "substrate_temp_c",
                "parameter_name": "Substrate Temperature",
                "value": "350",
                "unit": "°C",
                "source": "Experiment Record",
                "validation_status": "Valid",
            }
        ],
        xrd=XRDReportSectionSchema(available=True, crystallite_size_nm=22.4),
        uvvis=UVVisReportSectionSchema(available=True, optical_band_gap_ev=1.45),
        electrical=ElectricalReportSectionSchema(available=True, conductivity_s_cm=0.048),
        provenance_items=[
            ProvenanceItemSchema(
                sample_code="SAMP-P7-001-A",
                technique="XRD",
                raw_filename="P7_001_xrd.csv",
                raw_file_id=str(uuid.uuid4()),
                sha256_checksum="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            )
        ],
    )

    pdf_bytes = PDFReportRenderer.render_experiment_report(data)
    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 1000
    assert pdf_bytes.startswith(b"%PDF-")
