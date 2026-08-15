import { render, screen, fireEvent } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { UvVisPlotChart } from '../components/UvVisPlotChart'
import type { TaucDataPoint, TaucFitLinePoint } from '../types'

const MOCK_POINTS: TaucDataPoint[] = [
  { wavelength_nm: 400.0, absorbance: 0.8, photon_energy_ev: 3.10, tauc_y: 6.0 },
  { wavelength_nm: 500.0, absorbance: 0.5, photon_energy_ev: 2.48, tauc_y: 2.5 },
  { wavelength_nm: 620.0, absorbance: 0.1, photon_energy_ev: 2.00, tauc_y: 0.0 },
]

const MOCK_FIT: TaucFitLinePoint[] = [
  { photon_energy_ev: 2.10, fit_y: 0.0 },
  { photon_energy_ev: 3.10, fit_y: 6.0 },
]

describe('UvVisPlotChart', () => {
  it('renders Tauc plot with photon energy axis, Eg marker, and tab switcher', () => {
    render(
      <UvVisPlotChart
        dataPoints={MOCK_POINTS}
        fitLine={MOCK_FIT}
        bandGapEv={2.10}
        transitionType="DIRECT_ALLOWED"
        usingAlpha={false}
      />
    )

    expect(screen.getByText('Extrapolated Optical Eg = 2.10 eV')).toBeDefined()
    expect(screen.getByText('Photon Energy hν (eV)')).toBeDefined()
    expect(screen.getByText('(A · hν)² (a.u.)')).toBeDefined()

    // Switch to Absorbance Spectrum tab
    const specBtn = screen.getByText('Absorbance Spectrum (λ vs A)')
    fireEvent.click(specBtn)

    expect(screen.getByText('Wavelength λ (nm)')).toBeDefined()
    expect(screen.getByText('Absorbance A (a.u.)')).toBeDefined()
  })
})
