import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { ComparisonPlotChart } from '../components/ComparisonPlotChart'

const MOCK_POINTS = [
  { sampleCode: 'S001', x: 300, y: 4.2 },
  { sampleCode: 'S002', x: 350, y: 5.1 },
  { sampleCode: 'S003', x: 400, y: 6.0 },
]

const MOCK_REGRESSION = {
  slope: 0.018,
  intercept: -1.2,
  rSquared: 0.995,
  formula: 'y = 0.018 * x - 1.2',
}

describe('ComparisonPlotChart', () => {
  it('renders scatter plot with linear regression line and axis labels', () => {
    render(
      <ComparisonPlotChart
        xLabel="Substrate Temperature (°C)"
        yLabel="Electrical Conductivity (S/cm)"
        points={MOCK_POINTS}
        regression={MOCK_REGRESSION}
      />
    )

    expect(screen.getByText('Scatter Plot: Electrical Conductivity (S/cm) vs Substrate Temperature (°C) (n = 3)')).toBeDefined()
    expect(screen.getByText('Substrate Temperature (°C)')).toBeDefined()
    expect(screen.getByText('Electrical Conductivity (S/cm)')).toBeDefined()
    expect(screen.getByText(/OLS Linear Fit: R² = 0.995/)).toBeDefined()
  })
})
