import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { XrdPlotChart } from '../components/XrdPlotChart'
import type { XRDDataPoint, XRDPeak } from '../types'

const MOCK_POINTS: XRDDataPoint[] = [
  { two_theta: 20.0, raw_intensity: 100, processed_intensity: 50 },
  { two_theta: 35.5, raw_intensity: 500, processed_intensity: 450 },
  { two_theta: 50.0, raw_intensity: 120, processed_intensity: 70 },
]

const MOCK_PEAKS: XRDPeak[] = [
  {
    id: 'peak-1',
    analysis_run_id: 'run-1',
    peak_position: 35.5,
    intensity: 450,
    fwhm: 0.4,
    prominence: 400,
    width: 0.4,
    created_at: '2026-08-01T12:00:00Z',
  },
]

describe('XrdPlotChart', () => {
  it('renders XRD pattern chart with 2θ angle axis and peak marker overlay', () => {
    render(<XrdPlotChart dataPoints={MOCK_POINTS} peaks={MOCK_PEAKS} />)

    expect(screen.getByText('XRD Diffraction Pattern (2θ vs Intensity)')).toBeDefined()
    expect(screen.getByText('2θ Angle (Degrees)')).toBeDefined()
    expect(screen.getByText('Intensity (Counts / a.u.)')).toBeDefined()
    expect(screen.getByText('35.50°')).toBeDefined()
  })
})
