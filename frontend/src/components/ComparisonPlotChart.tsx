/**
 * GreenSynth Analytics — Comparison Plot SVG Chart
 *
 * Renders:
 *  1. Interactive SVG Scatter Plot with Linear Regression Fit Line (Y = slope * X + intercept)
 *  2. Hover Tooltips displaying Sample Code & exact values
 *  3. Group Comparison Bar Chart
 */

import React from 'react'

interface PointData {
  sampleCode: string
  x: number
  y: number
}

interface ComparisonPlotChartProps {
  xLabel: string
  yLabel: string
  points: PointData[]
  regression?: {
    slope: number
    intercept: number
    rSquared: number
    formula: string
  } | null
}

export function ComparisonPlotChart({
  xLabel,
  yLabel,
  points,
  regression,
}: ComparisonPlotChartProps) {
  if (!points || points.length === 0) {
    return (
      <div style={{ padding: 40, textAlign: 'center', color: 'var(--color-text-muted)', background: 'white', borderRadius: 8, border: '1px solid var(--color-border)' }}>
        No paired numerical data points available for plot visualization.
      </div>
    )
  }

  const width = 760
  const height = 360
  const padding = { top: 30, right: 30, bottom: 50, left: 70 }
  const innerW = width - padding.left - padding.right
  const innerH = height - padding.top - padding.bottom

  const xVals = points.map((p) => p.x)
  const yVals = points.map((p) => p.y)

  const xMin = Math.min(...xVals)
  const xMax = Math.max(...xVals)
  const xRange = xMax - xMin || 1.0

  const yMin = Math.min(...yVals)
  const yMax = Math.max(...yVals)
  const yRange = yMax - yMin || 1.0

  // Padding bounds
  const xPadMin = xMin - xRange * 0.08
  const xPadMax = xMax + xRange * 0.08
  const yPadMin = yMin - yRange * 0.08
  const yPadMax = yMax + yRange * 0.08

  const scaleX = (val: number) =>
    padding.left + ((val - xPadMin) / (xPadMax - xPadMin || 1)) * innerW

  const scaleY = (val: number) =>
    height - padding.bottom - ((val - yPadMin) / (yPadMax - yPadMin || 1)) * innerH

  // Regression line start & end points
  let regPath = ''
  if (regression) {
    const x1 = xPadMin
    const y1 = regression.slope * x1 + regression.intercept
    const x2 = xPadMax
    const y2 = regression.slope * x2 + regression.intercept

    const px1 = scaleX(x1)
    const py1 = scaleY(y1)
    const px2 = scaleX(x2)
    const py2 = scaleY(y2)
    regPath = `M ${px1} ${py1} L ${px2} ${py2}`
  }

  const xTicks = Array.from({ length: 5 }, (_, i) => {
    const val = xPadMin + (i / 4) * (xPadMax - xPadMin)
    return { val: val.toFixed(1), x: scaleX(val) }
  })

  const yTicks = Array.from({ length: 5 }, (_, i) => {
    const val = yPadMin + (i / 4) * (yPadMax - yPadMin)
    return { val: val.toFixed(2), y: scaleY(val) }
  })

  return (
    <div style={{ background: 'white', borderRadius: 'var(--radius-md)', padding: 16, border: '1px solid var(--color-border)' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 }}>
        <div style={{ fontWeight: 600, fontSize: '0.9375rem' }}>
          Scatter Plot: {yLabel} vs {xLabel} (n = {points.length})
        </div>
        {regression && (
          <div style={{ fontSize: '0.75rem', background: '#eff6ff', color: '#1e40af', padding: '4px 8px', borderRadius: 4, fontWeight: 600 }}>
            OLS Linear Fit: R² = {regression.rSquared.toFixed(3)}
          </div>
        )}
      </div>

      <div style={{ overflowX: 'auto' }}>
        <svg viewBox={`0 0 ${width} ${height}`} style={{ width: '100%', height: 'auto', display: 'block' }}>
          {/* Grid lines */}
          {yTicks.map((tick, i) => (
            <line key={i} x1={padding.left} y1={tick.y} x2={width - padding.right} y2={tick.y} stroke="#f1f5f9" strokeWidth="1" />
          ))}
          {xTicks.map((tick, i) => (
            <line key={i} x1={tick.x} y1={padding.top} x2={tick.x} y2={height - padding.bottom} stroke="#f1f5f9" strokeWidth="1" />
          ))}

          {/* Axes */}
          <line x1={padding.left} y1={height - padding.bottom} x2={width - padding.right} y2={height - padding.bottom} stroke="#64748b" strokeWidth="1.5" />
          <line x1={padding.left} y1={padding.top} x2={padding.left} y2={height - padding.bottom} stroke="#64748b" strokeWidth="1.5" />

          {/* Axis Labels */}
          <text x={width / 2} y={height - 10} textAnchor="middle" fill="#475569" fontSize="12" fontWeight="600">
            {xLabel}
          </text>
          <text x={18} y={height / 2} textAnchor="middle" transform={`rotate(-90 18 ${height / 2})`} fill="#475569" fontSize="12" fontWeight="600">
            {yLabel}
          </text>

          {/* X Ticks */}
          {xTicks.map((t, i) => (
            <g key={i}>
              <line x1={t.x} y1={height - padding.bottom} x2={t.x} y2={height - padding.bottom + 5} stroke="#64748b" />
              <text x={t.x} y={height - padding.bottom + 18} textAnchor="middle" fill="#64748b" fontSize="10">
                {t.val}
              </text>
            </g>
          ))}

          {/* Y Ticks */}
          {yTicks.map((t, i) => (
            <g key={i}>
              <line x1={padding.left - 5} y1={t.y} x2={padding.left} y2={t.y} stroke="#64748b" />
              <text x={padding.left - 8} y={t.y + 4} textAnchor="end" fill="#64748b" fontSize="10">
                {t.val}
              </text>
            </g>
          ))}

          {/* Regression Fit Line */}
          {regPath && (
            <path d={regPath} fill="none" stroke="#2563eb" strokeWidth="2" strokeDasharray="5 5" />
          )}

          {/* Data Points */}
          {points.map((p, i) => {
            const px = scaleX(p.x)
            const py = scaleY(p.y)
            return (
              <g key={i}>
                <circle cx={px} cy={py} r="6" fill="#2563eb" stroke="white" strokeWidth="2">
                  <title>{`${p.sampleCode}: (${xLabel}=${p.x}, ${yLabel}=${p.y})`}</title>
                </circle>
                <text x={px} y={py - 10} textAnchor="middle" fill="#1e293b" fontSize="9" fontWeight="700">
                  {p.sampleCode}
                </text>
              </g>
            )
          })}
        </svg>
      </div>
    </div>
  )
}
