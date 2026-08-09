import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { ElectricalPlotChart } from '../components/ElectricalPlotChart'
import type { IVDataPoint, IVFitLinePoint } from '../types'

const MOCK_POINTS: IVDataPoint[] = [
  { voltage_v: -1.0, current_a: -0.01 },
  { voltage_v: 0.0, current_a: 0.0 },
  { voltage_v: 1.0, current_a: 0.01 },
]

const MOCK_FIT: IVFitLinePoint[] = [
  { current_a: -0.01, fit_voltage_v: -1.0 },
  { current_a: 0.01, fit_voltage_v: 1.0 },
]

describe('ElectricalPlotChart', () => {
  it('renders I-V curve plot with resistance legend and axes labels', () => {
    render(
      <ElectricalPlotChart
        dataPoints={MOCK_POINTS}
        fitLine={MOCK_FIT}
        resistanceOhms={100.0}
        voltageUnit="V"
        currentUnit="A"
      />
    )

    expect(screen.getByText('Measured I-V Characteristic Curve')).toBeDefined()
    expect(screen.getByText('Linear Fit R = 100.00 Ω')).toBeDefined()
    expect(screen.getByText('Voltage V (V)')).toBeDefined()
    expect(screen.getByText('Current I (A)')).toBeDefined()
  })
})
