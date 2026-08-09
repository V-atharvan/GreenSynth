import { render, screen, fireEvent } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { FtirPlotChart } from '../components/FtirPlotChart'
import type { FTIRAnnotationResponse, FTIRDataPoint, FTIRPeakItem } from '../types'

const MOCK_POINTS: FTIRDataPoint[] = [
  { wavenumber_cm1: 4000.0, signal_value: 98.0 },
  { wavenumber_cm1: 1700.0, signal_value: 45.0 },
  { wavenumber_cm1: 400.0, signal_value: 92.0 },
]

const MOCK_PEAKS: FTIRPeakItem[] = [
  { wavenumber_cm1: 1700.0, signal_value: 45.0, prominence: 50.0, width_cm1: 30.0 },
]

const MOCK_ANNS: FTIRAnnotationResponse[] = [
  {
    id: 'ann-1',
    analysis_run_id: 'run-1',
    wavenumber_cm1: 1700.0,
    label: 'C=O Stretch',
    interpretation: 'Carbonyl capping group',
    confidence: 'High',
    created_at: '2026-08-09T08:00:00Z',
  },
]

describe('FtirPlotChart', () => {
  it('renders FTIR spectrum chart with peak markers, annotations, and axis toggle', () => {
    render(
      <FtirPlotChart
        dataPoints={MOCK_POINTS}
        detectedPeaks={MOCK_PEAKS}
        annotations={MOCK_ANNS}
        signalType="TRANSMITTANCE"
      />
    )

    expect(screen.getByText('FTIR Spectrum (TRANSMITTANCE) · Detected Peaks (1)')).toBeDefined()
    expect(screen.getByText('Wavenumber ν (cm⁻¹)')).toBeDefined()
    expect(screen.getByText('C=O Stretch')).toBeDefined()

    // Toggle wavenumber axis direction
    const toggleBtn = screen.getByText(/Wavenumber Axis:/)
    fireEvent.click(toggleBtn)

    expect(screen.getByText(/Wavenumber Axis: Ascending/)).toBeDefined()
  })
})
