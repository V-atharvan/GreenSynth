/**
 * GreenSynth Analytics — Status Badge Component
 *
 * Renders a colour-coded badge for project, experiment, and sample statuses.
 */

import React from 'react'
import type { ExperimentStatus, ProjectStatus, SampleStatus } from '@/types'

type StatusValue = ProjectStatus | ExperimentStatus | SampleStatus

interface StatusBadgeProps {
  status: StatusValue
}

const LABELS: Record<string, string> = {
  ACTIVE: 'Active',
  ARCHIVED: 'Archived',
  PLANNED: 'Planned',
  IN_PROGRESS: 'In Progress',
  COMPLETED: 'Completed',
  FAILED: 'Failed',
  PREPARED: 'Prepared',
  READY_FOR_CHARACTERIZATION: 'Ready for Characterization',
  UNDER_ANALYSIS: 'Under Analysis',
  COMPLETE: 'Complete',
}

const CSS_CLASS: Record<string, string> = {
  ACTIVE: 'badge-active',
  ARCHIVED: 'badge-archived',
  PLANNED: 'badge-planned',
  IN_PROGRESS: 'badge-in_progress',
  COMPLETED: 'badge-completed',
  FAILED: 'badge-failed',
  PREPARED: 'badge-prepared',
  READY_FOR_CHARACTERIZATION: 'badge-planned',
  UNDER_ANALYSIS: 'badge-characterising',
  COMPLETE: 'badge-complete',
}

export function StatusBadge({ status }: StatusBadgeProps) {
  const label = LABELS[status] ?? status
  const cls = CSS_CLASS[status] ?? ''
  return (
    <span className={`badge ${cls}`} aria-label={`Status: ${label}`}>
      {label}
    </span>
  )
}
