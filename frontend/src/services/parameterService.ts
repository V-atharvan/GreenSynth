/**
 * GreenSynth Analytics — Parameter Service
 */

import apiClient from './api'
import type {
  ExperimentParameter,
  ExperimentParameterCreate,
  ParameterDefinition,
  ParameterDefinitionCreate,
  ParameterDefinitionUpdate,
} from '@/types'

export const parameterService = {
  /**
   * Fetch synthesis parameter definitions configured for a project.
   */
  async getProjectParameters(
    projectId: string,
    includeInactive = false
  ): Promise<ParameterDefinition[]> {
    const response = await apiClient.get<ParameterDefinition[]>(
      `/projects/${projectId}/parameters`,
      { params: { include_inactive: includeInactive } }
    )
    return response.data
  },

  /**
   * Add a new parameter definition to a project.
   */
  async createProjectParameter(
    projectId: string,
    data: ParameterDefinitionCreate
  ): Promise<ParameterDefinition> {
    const response = await apiClient.post<ParameterDefinition>(
      `/projects/${projectId}/parameters`,
      data
    )
    return response.data
  },

  /**
   * Update an existing parameter definition.
   */
  async updateProjectParameter(
    projectId: string,
    parameterId: string,
    data: ParameterDefinitionUpdate
  ): Promise<ParameterDefinition> {
    const response = await apiClient.put<ParameterDefinition>(
      `/projects/${projectId}/parameters/${parameterId}`,
      data
    )
    return response.data
  },

  /**
   * Deactivate a parameter definition (soft delete).
   */
  async deactivateProjectParameter(
    projectId: string,
    parameterId: string
  ): Promise<ParameterDefinition> {
    const response = await apiClient.delete<ParameterDefinition>(
      `/projects/${projectId}/parameters/${parameterId}`
    )
    return response.data
  },

  /**
   * Fetch recorded parameter values for an experiment.
   */
  async getExperimentParameters(
    experimentId: string
  ): Promise<ExperimentParameter[]> {
    const response = await apiClient.get<ExperimentParameter[]>(
      `/experiments/${experimentId}/parameters`
    )
    return response.data
  },

  /**
   * Save or update recorded parameter values for an experiment.
   */
  async saveExperimentParameters(
    experimentId: string,
    parameters: ExperimentParameterCreate[]
  ): Promise<ExperimentParameter[]> {
    const response = await apiClient.post<ExperimentParameter[]>(
      `/experiments/${experimentId}/parameters`,
      { parameters }
    )
    return response.data
  },
}
