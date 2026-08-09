"""
GreenSynth Analytics — Analysis & XRD API Router

REST API endpoints for running scientific XRD analysis, fetching detected peaks,
retrieving calculated properties, and obtaining processed XY curves for Plotly visualization.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.scientific.electrical.parser import ElectricalParseError
from app.scientific.electrical.schemas import ElectricalAnalysisInput, ElectricalProcessedResponse
from app.scientific.electrical.service import ElectricalAnalysisService
from app.scientific.ftir.parser import FTIRParseError
from app.scientific.ftir.schemas import (
    FTIRAnalysisInput,
    FTIRAnnotationCreate,
    FTIRAnnotationResponse,
    FTIRProcessedResponse,
)
from app.scientific.ftir.service import FTIRAnalysisService
from app.scientific.sem.schemas import (
    SEMAnnotationCreate,
    SEMAnnotationResponse,
    SEMMeasurementCreate,
    SEMMeasurementResponse,
    SEMMetadataResponse,
    SEMMetadataUpdate,
)
from app.scientific.sem.service import SEMAnalysisService
from app.scientific.uvvis.parser import UVVisParseError
from app.scientific.uvvis.schemas import TaucProcessedResponse, UVVisAnalysisInput
from app.scientific.uvvis.service import UVVisAnalysisService
from app.scientific.xrd.parser import XRDParseError
from app.scientific.xrd.schemas import (
    CalculatedPropertyResponse,
    XRDAnalysisInput,
    XRDAnalysisRunResponse,
    XRDPeakResponse,
    XRDProcessedDataResponse,
)
from app.scientific.xrd.service import XRDAnalysisService
from app.services.characterization_service import (
    CharacterizationNotFoundError,
    RawFileNotFoundError,
)

router = APIRouter(tags=["analysis"])


# ─────────────────────────────────────────────────────────────
# FTIR ENDPOINTS
# ─────────────────────────────────────────────────────────────

@router.post(
    "/characterizations/{characterization_id}/ftir/analyze",
    response_model=XRDAnalysisRunResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Execute FTIR scientific spectrum analysis run",
)
async def run_ftir_analysis(
    characterization_id: uuid.UUID,
    input_data: FTIRAnalysisInput,
    raw_file_id: uuid.UUID | None = None,
    db: AsyncSession = Depends(get_db),
) -> XRDAnalysisRunResponse:
    """Execute FTIR spectrum parsing, Savitzky-Golay noise smoothing, and peak detection."""
    service = FTIRAnalysisService(db)
    try:
        run = await service.run_analysis(
            characterization_id=characterization_id,
            input_data=input_data,
            raw_file_id=raw_file_id,
        )
    except CharacterizationNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except RawFileNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except FTIRParseError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    return XRDAnalysisRunResponse.model_validate(run)


@router.get(
    "/analysis-runs/{analysis_run_id}/ftir-data",
    response_model=FTIRProcessedResponse,
    summary="Get preprocessed FTIR spectrum data points and detected peaks",
)
async def get_analysis_ftir_data(
    analysis_run_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> FTIRProcessedResponse:
    """Return Wavenumber cm^-1, Signal, and detected peak list."""
    service = FTIRAnalysisService(db)
    try:
        return await service.get_ftir_data(analysis_run_id)
    except (ValueError, FileNotFoundError) as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.post(
    "/analysis-runs/{analysis_run_id}/ftir-annotations",
    response_model=FTIRAnnotationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add researcher peak annotation for FTIR spectrum",
)
async def add_ftir_annotation(
    analysis_run_id: uuid.UUID,
    payload: FTIRAnnotationCreate,
    db: AsyncSession = Depends(get_db),
) -> FTIRAnnotationResponse:
    """Add researcher peak annotation (e.g. C=O functional group stretch)."""
    service = FTIRAnalysisService(db)
    try:
        ann = await service.add_annotation(analysis_run_id, payload)
        return FTIRAnnotationResponse.model_validate(ann)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.get(
    "/analysis-runs/{analysis_run_id}/ftir-annotations",
    response_model=list[FTIRAnnotationResponse],
    summary="List researcher peak annotations for FTIR spectrum",
)
async def list_ftir_annotations(
    analysis_run_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> list[FTIRAnnotationResponse]:
    """List researcher peak annotations for an FTIR analysis run."""
    service = FTIRAnalysisService(db)
    try:
        anns = await service.list_annotations(analysis_run_id)
        return [FTIRAnnotationResponse.model_validate(a) for a in anns]
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


# ─────────────────────────────────────────────────────────────
# SEM ENDPOINTS
# ─────────────────────────────────────────────────────────────

@router.post(
    "/files/{file_id}/sem-metadata",
    response_model=SEMMetadataResponse,
    summary="Create or update SEM image metadata and scale calibration",
)
async def update_sem_metadata(
    file_id: uuid.UUID,
    payload: SEMMetadataUpdate,
    db: AsyncSession = Depends(get_db),
) -> SEMMetadataResponse:
    """Update SEM image magnification, kV, working distance, detector, and scale bar calibration."""
    service = SEMAnalysisService(db)
    try:
        meta = await service.update_metadata(file_id, payload)
        return SEMMetadataResponse.model_validate(meta)
    except RawFileNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.get(
    "/files/{file_id}/sem-metadata",
    response_model=SEMMetadataResponse,
    summary="Get SEM image metadata and scale calibration",
)
async def get_sem_metadata(
    file_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> SEMMetadataResponse:
    """Get SEM image metadata."""
    service = SEMAnalysisService(db)
    try:
        meta = await service.get_or_create_metadata(file_id)
        return SEMMetadataResponse.model_validate(meta)
    except RawFileNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.post(
    "/files/{file_id}/sem-annotations",
    response_model=SEMAnnotationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add visual annotation to SEM image",
)
async def add_sem_annotation(
    file_id: uuid.UUID,
    payload: SEMAnnotationCreate,
    db: AsyncSession = Depends(get_db),
) -> SEMAnnotationResponse:
    """Add visual annotation (point, line, rectangle) to SEM image."""
    service = SEMAnalysisService(db)
    try:
        ann = await service.add_annotation(file_id, payload)
        return SEMAnnotationResponse.model_validate(ann)
    except RawFileNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.get(
    "/files/{file_id}/sem-annotations",
    response_model=list[SEMAnnotationResponse],
    summary="List visual annotations for SEM image",
)
async def list_sem_annotations(
    file_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> list[SEMAnnotationResponse]:
    """List visual annotations for an SEM image."""
    service = SEMAnalysisService(db)
    try:
        anns = await service.list_annotations(file_id)
        return [SEMAnnotationResponse.model_validate(a) for a in anns]
    except RawFileNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.post(
    "/files/{file_id}/sem-measurements",
    response_model=SEMMeasurementResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add manual physical length measurement on SEM image",
)
async def add_sem_measurement(
    file_id: uuid.UUID,
    payload: SEMMeasurementCreate,
    db: AsyncSession = Depends(get_db),
) -> SEMMeasurementResponse:
    """Record manual length measurement using scale calibration."""
    service = SEMAnalysisService(db)
    try:
        meas = await service.add_manual_measurement(file_id, payload)
        return SEMMeasurementResponse.model_validate(meas)
    except RawFileNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.get(
    "/files/{file_id}/sem-measurements",
    response_model=list[SEMMeasurementResponse],
    summary="List manual physical measurements on SEM image",
)
async def list_sem_measurements(
    file_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> list[SEMMeasurementResponse]:
    """List manual physical length measurements for an SEM image."""
    service = SEMAnalysisService(db)
    try:
        meass = await service.list_measurements(file_id)
        return [SEMMeasurementResponse.model_validate(m) for m in meass]
    except RawFileNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.post(
    "/characterizations/{characterization_id}/electrical/analyze",
    response_model=XRDAnalysisRunResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Execute Electrical scientific analysis run",
)
async def run_electrical_analysis(
    characterization_id: uuid.UUID,
    input_data: ElectricalAnalysisInput,
    raw_file_id: uuid.UUID | None = None,
    db: AsyncSession = Depends(get_db),
) -> XRDAnalysisRunResponse:
    """
    Execute Electrical I-V scientific analysis (unit conversions, Ohm's law linear fit for resistance,
    sample geometry cross-sectional area, resistivity, and conductivity calculations).
    """
    service = ElectricalAnalysisService(db)
    try:
        run = await service.run_analysis(
            characterization_id=characterization_id,
            input_data=input_data,
            raw_file_id=raw_file_id,
        )
    except CharacterizationNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except RawFileNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except ElectricalParseError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    return XRDAnalysisRunResponse.model_validate(run)


@router.get(
    "/analysis-runs/{analysis_run_id}/electrical-data",
    response_model=ElectricalProcessedResponse,
    summary="Get raw I-V curve data points and linear fit line",
)
async def get_analysis_electrical_data(
    analysis_run_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> ElectricalProcessedResponse:
    """Return Voltage V, Current A, linear fit line, resistance, resistivity, and conductivity for Plotly."""
    service = ElectricalAnalysisService(db)
    try:
        return await service.get_electrical_data(analysis_run_id)
    except (ValueError, FileNotFoundError) as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.post(
    "/characterizations/{characterization_id}/uvvis/analyze",
    response_model=XRDAnalysisRunResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Execute UV-Vis Tauc scientific analysis run",
)
async def run_uvvis_analysis(
    characterization_id: uuid.UUID,
    input_data: UVVisAnalysisInput,
    raw_file_id: uuid.UUID | None = None,
    db: AsyncSession = Depends(get_db),
) -> XRDAnalysisRunResponse:
    """
    Execute UV-Vis Tauc optical band gap scientific analysis (wavelength to photon energy conversion,
    Tauc plot transformation, linear regression fitting, and optical band gap Eg calculation).
    """
    service = UVVisAnalysisService(db)
    try:
        run = await service.run_analysis(
            characterization_id=characterization_id,
            input_data=input_data,
            raw_file_id=raw_file_id,
        )
    except CharacterizationNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except RawFileNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except UVVisParseError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    return XRDAnalysisRunResponse.model_validate(run)


@router.get(
    "/analysis-runs/{analysis_run_id}/tauc-data",
    response_model=TaucProcessedResponse,
    summary="Get Tauc curve data points and linear regression fit line",
)
async def get_analysis_tauc_data(
    analysis_run_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> TaucProcessedResponse:
    """Return Wavelength, Absorbance, Photon Energy E (eV), Tauc Y, and linear regression fit line for Plotly."""
    service = UVVisAnalysisService(db)
    try:
        return await service.get_tauc_data(analysis_run_id)
    except (ValueError, FileNotFoundError) as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.post(
    "/characterizations/{characterization_id}/xrd/analyze",
    response_model=XRDAnalysisRunResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Execute XRD scientific analysis run",
)
async def run_xrd_analysis(
    characterization_id: uuid.UUID,
    input_data: XRDAnalysisInput,
    raw_file_id: uuid.UUID | None = None,
    db: AsyncSession = Depends(get_db),
) -> XRDAnalysisRunResponse:
    """
    Execute XRD scientific analysis (data parsing, baseline subtraction,
    Savitzky-Golay noise smoothing, peak detection, and Scherrer crystallite size calculation).
    """
    service = XRDAnalysisService(db)
    try:
        run = await service.run_analysis(
            characterization_id=characterization_id,
            input_data=input_data,
            raw_file_id=raw_file_id,
        )
    except CharacterizationNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except RawFileNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except XRDParseError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    return XRDAnalysisRunResponse.model_validate(run)


@router.get(
    "/analysis-runs/{analysis_run_id}",
    response_model=XRDAnalysisRunResponse,
    summary="Get analysis run details & status",
)
async def get_analysis_run(
    analysis_run_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> XRDAnalysisRunResponse:
    """Get metadata, parameters, assumptions, peaks, and calculated properties for an analysis run."""
    service = XRDAnalysisService(db)
    try:
        run = await service.get_analysis_run(analysis_run_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    return XRDAnalysisRunResponse.model_validate(run)


@router.get(
    "/analysis-runs/{analysis_run_id}/peaks",
    response_model=list[XRDPeakResponse],
    summary="Get detected peaks for an analysis run",
)
async def get_analysis_peaks(
    analysis_run_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> list[XRDPeakResponse]:
    """Get detected diffraction peaks with 2θ positions, intensities, and FWHMs."""
    service = XRDAnalysisService(db)
    try:
        run = await service.get_analysis_run(analysis_run_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    return [XRDPeakResponse.model_validate(p) for p in run.peaks]


@router.get(
    "/analysis-runs/{analysis_run_id}/properties",
    response_model=list[CalculatedPropertyResponse],
    summary="Get calculated properties for an analysis run",
)
async def get_analysis_properties(
    analysis_run_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> list[CalculatedPropertyResponse]:
    """Get derived material properties (e.g. Scherrer Crystallite Size in nm) with formula and assumptions."""
    service = XRDAnalysisService(db)
    try:
        run = await service.get_analysis_run(analysis_run_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    return [CalculatedPropertyResponse.model_validate(p) for p in run.calculated_properties]


@router.get(
    "/analysis-runs/{analysis_run_id}/processed-data",
    response_model=XRDProcessedDataResponse,
    summary="Get raw vs processed curve data points for Plotly rendering",
)
async def get_analysis_processed_data(
    analysis_run_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> XRDProcessedDataResponse:
    """Return 2θ, raw intensity, and processed intensity data points for Plotly visualization."""
    service = XRDAnalysisService(db)
    try:
        return await service.get_processed_data_points(analysis_run_id)
    except (ValueError, FileNotFoundError) as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.get(
    "/characterizations/{characterization_id}/analysis-runs",
    response_model=list[XRDAnalysisRunResponse],
    summary="List analysis history runs for a characterization",
)
async def list_characterization_analysis_runs(
    characterization_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> list[XRDAnalysisRunResponse]:
    """Return all historical analysis runs executed for a characterization."""
    service = XRDAnalysisService(db)
    runs = await service.get_characterization_runs(characterization_id)
    return [XRDAnalysisRunResponse.model_validate(r) for r in runs]
