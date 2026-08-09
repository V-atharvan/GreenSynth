/**
 * GreenSynth Analytics — XRD Analysis Service Client
 */

import apiClient from './api'
import type {
  CalculatedProperty,
  XRDAnalysisInput,
  XRDAnalysisRun,
  XRDPeak,
  XRDProcessedDataResponse,
  UVVisAnalysisInput,
  TaucProcessedResponse,
  ElectricalAnalysisInput,
  ElectricalProcessedResponse,
  FTIRAnalysisInput,
  FTIRProcessedResponse,
  FTIRAnnotationCreate,
  FTIRAnnotationResponse,
  SEMMetadataUpdate,
  SEMMetadataResponse,
  SEMAnnotationCreate,
  SEMAnnotationResponse,
  SEMMeasurementCreate,
  SEMMeasurementResponse,
  DatasetCreateInput,
  DatasetResponse,
  ComparisonTableResponse,
  StatisticalAnalysisRunInput,
  StatisticalAnalysisResponse,
} from '@/types'

export const analysisService = {
  /**
   * Execute XRD scientific analysis run.
   */
  async runXrdAnalysis(
    characterizationId: string,
    inputData: XRDAnalysisInput,
    rawFileId?: string
  ): Promise<XRDAnalysisRun> {
    const url = `/characterizations/${characterizationId}/xrd/analyze` +
      (rawFileId ? `?raw_file_id=${rawFileId}` : '')
    const response = await apiClient.post<XRDAnalysisRun>(url, inputData)
    return response.data
  },

  /**
   * Get metadata & results of an analysis run.
   */
  async getAnalysisRun(runId: string): Promise<XRDAnalysisRun> {
    const response = await apiClient.get<XRDAnalysisRun>(`/analysis-runs/${runId}`)
    return response.data
  },

  /**
   * List detected peaks for an analysis run.
   */
  async getAnalysisPeaks(runId: string): Promise<XRDPeak[]> {
    const response = await apiClient.get<XRDPeak[]>(`/analysis-runs/${runId}/peaks`)
    return response.data
  },

  /**
   * List calculated properties (e.g. Scherrer crystallite size).
   */
  async getAnalysisProperties(runId: string): Promise<CalculatedProperty[]> {
    const response = await apiClient.get<CalculatedProperty[]>(
      `/analysis-runs/${runId}/properties`
    )
    return response.data
  },

  /**
   * Get 2θ, raw intensity, and processed intensity data points for Plotly rendering.
   */
  async getProcessedData(runId: string): Promise<XRDProcessedDataResponse> {
    const response = await apiClient.get<XRDProcessedDataResponse>(
      `/analysis-runs/${runId}/processed-data`
    )
    return response.data
  },

  /**
   * Execute UV-Vis scientific analysis run (Tauc optical band gap fit).
   */
  async runUvVisAnalysis(
    characterizationId: string,
    inputData: UVVisAnalysisInput,
    rawFileId?: string
  ): Promise<XRDAnalysisRun> {
    const url = `/characterizations/${characterizationId}/uvvis/analyze` +
      (rawFileId ? `?raw_file_id=${rawFileId}` : '')
    const response = await apiClient.post<XRDAnalysisRun>(url, inputData)
    return response.data
  },

  /**
   * Get Tauc plot curve data points and linear regression fit line.
   */
  async getTaucData(runId: string): Promise<TaucProcessedResponse> {
    const response = await apiClient.get<TaucProcessedResponse>(
      `/analysis-runs/${runId}/tauc-data`
    )
    return response.data
  },

  /**
   * Execute Electrical I-V scientific analysis run.
   */
  async runElectricalAnalysis(
    characterizationId: string,
    inputData: ElectricalAnalysisInput,
    rawFileId?: string
  ): Promise<XRDAnalysisRun> {
    const url = `/characterizations/${characterizationId}/electrical/analyze` +
      (rawFileId ? `?raw_file_id=${rawFileId}` : '')
    const response = await apiClient.post<XRDAnalysisRun>(url, inputData)
    return response.data
  },

  /**
   * Get raw I-V curve data points and linear fit line.
   */
  async getElectricalData(runId: string): Promise<ElectricalProcessedResponse> {
    const response = await apiClient.get<ElectricalProcessedResponse>(
      `/analysis-runs/${runId}/electrical-data`
    )
    return response.data
  },

  // ── FTIR Methods ───────────────────────────────────────────
  async runFtirAnalysis(
    characterizationId: string,
    inputData: FTIRAnalysisInput,
    rawFileId?: string
  ): Promise<XRDAnalysisRun> {
    const url = `/characterizations/${characterizationId}/ftir/analyze` +
      (rawFileId ? `?raw_file_id=${rawFileId}` : '')
    const response = await apiClient.post<XRDAnalysisRun>(url, inputData)
    return response.data
  },

  async getFtirData(runId: string): Promise<FTIRProcessedResponse> {
    const response = await apiClient.get<FTIRProcessedResponse>(
      `/analysis-runs/${runId}/ftir-data`
    )
    return response.data
  },

  async addFtirAnnotation(
    runId: string,
    payload: FTIRAnnotationCreate
  ): Promise<FTIRAnnotationResponse> {
    const response = await apiClient.post<FTIRAnnotationResponse>(
      `/analysis-runs/${runId}/ftir-annotations`,
      payload
    )
    return response.data
  },

  async listFtirAnnotations(runId: string): Promise<FTIRAnnotationResponse[]> {
    const response = await apiClient.get<FTIRAnnotationResponse[]>(
      `/analysis-runs/${runId}/ftir-annotations`
    )
    return response.data
  },

  // ── SEM Methods ────────────────────────────────────────────
  async updateSemMetadata(
    fileId: string,
    payload: SEMMetadataUpdate
  ): Promise<SEMMetadataResponse> {
    const response = await apiClient.post<SEMMetadataResponse>(
      `/files/${fileId}/sem-metadata`,
      payload
    )
    return response.data
  },

  async getSemMetadata(fileId: string): Promise<SEMMetadataResponse> {
    const response = await apiClient.get<SEMMetadataResponse>(
      `/files/${fileId}/sem-metadata`
    )
    return response.data
  },

  async addSemAnnotation(
    fileId: string,
    payload: SEMAnnotationCreate
  ): Promise<SEMAnnotationResponse> {
    const response = await apiClient.post<SEMAnnotationResponse>(
      `/files/${fileId}/sem-annotations`,
      payload
    )
    return response.data
  },

  async listSemAnnotations(fileId: string): Promise<SEMAnnotationResponse[]> {
    const response = await apiClient.get<SEMAnnotationResponse[]>(
      `/files/${fileId}/sem-annotations`
    )
    return response.data
  },

  async addSemMeasurement(
    fileId: string,
    payload: SEMMeasurementCreate
  ): Promise<SEMMeasurementResponse> {
    const response = await apiClient.post<SEMMeasurementResponse>(
      `/files/${fileId}/sem-measurements`,
      payload
    )
    return response.data
  },

  async listSemMeasurements(fileId: string): Promise<SEMMeasurementResponse[]> {
    const response = await apiClient.get<SEMMeasurementResponse[]>(
      `/files/${fileId}/sem-measurements`
    )
    return response.data
  },

  // ── Phase 8 Analytics Methods ──────────────────────────────
  async createDataset(payload: DatasetCreateInput): Promise<DatasetResponse> {
    const response = await apiClient.post<DatasetResponse>(
      '/analytics/datasets',
      payload
    )
    return response.data
  },

  async listDatasets(projectId: string): Promise<DatasetResponse[]> {
    const response = await apiClient.get<DatasetResponse[]>(
      `/analytics/datasets?project_id=${projectId}`
    )
    return response.data
  },

  async getDataset(datasetId: string): Promise<DatasetResponse> {
    const response = await apiClient.get<DatasetResponse>(
      `/analytics/datasets/${datasetId}`
    )
    return response.data
  },

  async getComparisonTable(datasetId: string): Promise<ComparisonTableResponse> {
    const response = await apiClient.get<ComparisonTableResponse>(
      `/analytics/datasets/${datasetId}/comparison-table`
    )
    return response.data
  },

  async runStatisticalAnalysis(
    datasetId: string,
    payload: StatisticalAnalysisRunInput
  ): Promise<StatisticalAnalysisResponse> {
    const response = await apiClient.post<StatisticalAnalysisResponse>(
      `/analytics/datasets/${datasetId}/statistics`,
      payload
    )
    return response.data
  },

  async getStatisticalAnalysis(analysisId: string): Promise<StatisticalAnalysisResponse> {
    const response = await apiClient.get<StatisticalAnalysisResponse>(
      `/analytics/statistical-analyses/${analysisId}`
    )
    return response.data
  },

  async exportDatasetCsv(datasetId: string): Promise<Blob> {
    const response = await apiClient.get(`/analytics/datasets/${datasetId}/export`, {
      responseType: 'blob',
    })
    return response.data
  },

  /**
   * List historical analysis runs for a characterization.
   */
  async listCharacterizationRuns(
    characterizationId: string
  ): Promise<XRDAnalysisRun[]> {
    const response = await apiClient.get<XRDAnalysisRun[]>(
      `/characterizations/${characterizationId}/analysis-runs`
    )
    return response.data
  },
}
