/**
 * GreenSynth Analytics — Electrical I-V Curve SVG Chart
 *
 * Visualizes:
 *  - Raw Measured I-V Curve (Voltage V vs Current A)
 *  - Linear Regression Ohm's Law Fit Line (V = I*R + c)
 */

import React from 'react'
import type { IVDataPoint, IVFitLinePoint } from '@/types'

interface ElectricalPlotChartProps {
  dataPoints: IVDataPoint[]
  fitLine: IVFitLinePoint[]
  resistanceOhms?: number | null
  voltageUnit?: string
  currentUnit?: string
}

export function ElectricalPlotChart({
  dataPoints,
  fitLine,
  resistanceOhms,
  voltageUnit = 'V',
  currentUnit = 'A',
}: ElectricalPlotChartProps) {
  if (!dataPoints || dataPoints.length === 0) {
    return (
      <div style={{ padding: 40, textAlign: 'center', color: 'var(--color-text-muted)' }}>
        No I-V data points available.
      </div>
    )
  }

  const width = 800
  const height = 380
  const padding = { top: 30, right: 30, bottom: 50, left: 70 }
  const innerW = width - padding.left - padding.right
  const innerH = height - padding.top - padding.bottom

  const xVals = dataPoints.map((p) => p.voltage_v)
  const yVals = dataPoints.map((p) => p.current_a)

  const xMin = Math.min(...xVals)
  const xMax = Math.max(...xVals)
  const yMin = Math.min(...yVals)
  const yMax = Math.max(...yVals)

  const padX = (xMax - xMin || 1) * 0.05
  const padY = (yMax - yMin || 1) * 0.05

  const minX = xMin - padX
  const maxX = xMax + padX
  const minY = yMin - padY
  const maxY = yMax + padY

  const scaleX = (val: number) =>
    padding.left + ((val - minX) / (maxX - minX || 1)) * innerW
  const scaleY = (val: number) =>
    height - padding.bottom - ((val - minY) / (maxY - minY || 1)) * innerH

  const dataPath = dataPoints.reduce((acc, p, i) => {
    const x = scaleX(p.voltage_v)
    const y = scaleY(p.current_a)
    return i === 0 ? `M ${x} ${y}` : `${acc} L ${x} ${y}`
  }, '')

  const fitPath = fitLine.length > 0
    ? fitLine.reduce((acc, f, i) => {
        const x = scaleX(f.fit_voltage_v)
        const y = scaleY(f.current_a)
        return i === 0 ? `M ${x} ${y}` : `${acc} L ${x} ${y}`
      }, '')
    : ''

  const xTicks = Array.from({ length: 6 }, (_, i) => {
    const val = minX + (i / 5) * (maxX - minX)
    return { val: val.toFixed(2), x: scaleX(val) }
  })

  const yTicks = Array.from({ length: 5 }, (_, i) => {
    const val = minY + (i / 4) * (maxY - minY)
    return { val: val.toExponential(1), y: scaleY(val) }
  })

  return (
    <div style={{ background: 'white', borderRadius: 'var(--radius-md)', padding: 16, border: '1px solid var(--color-border)' }}>
      {/* Legend Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
        <div style={{ fontWeight: 600, fontSize: '0.9375rem' }}>
          Measured I-V Characteristic Curve
        </div>
        {resistanceOhms && (
          <div style={{ fontSize: '0.875rem', fontWeight: 700, color: '#1d4ed8', background: '#eff6ff', padding: '4px 12px', borderRadius: 4, border: '1px solid #bfdbfe' }}>
            Linear Fit R = {resistanceOhms.toFixed(2)} Ω
          </div>
        )}
      </div>

      {/* SVG Plot */}
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
          <text x={width / 2} y={height - 12} textAnchor="middle" fill="#475569" fontSize="12" fontWeight="600">
            Voltage V ({voltageUnit})
          </text>
          <text x={18} y={height / 2} textAnchor="middle" transform={`rotate(-90 18 ${height / 2})`} fill="#475569" fontSize="12" fontWeight="600">
            Current I ({currentUnit})
          </text>

          {/* X Ticks */}
          {xTicks.map((t, i) => (
            <g key={i}>
              <line x1={t.x} y1={height - padding.bottom} x2={t.x} y2={height - padding.bottom + 5} stroke="#64748b" />
              <text x={t.x} y={height - padding.bottom + 20} textAnchor="middle" fill="#64748b" fontSize="10">
                {t.val} V
              </text>
            </g>
          ))}

          {/* Y Ticks */}
          {yTicks.map((t, i) => (
            <g key={i}>
              <line x1={padding.left - 5} y1={t.y} x2={padding.left} y2={t.y} stroke="#64748b" />
              <text x={padding.left - 10} y={t.y + 4} textAnchor="end" fill="#64748b" fontSize="10">
                {t.val} A
              </text>
            </g>
          ))}

          {/* Raw Measured I-V Data Points Path */}
          <path d={dataPath} fill="none" stroke="#2563eb" strokeWidth="2" />

          {/* Data Point Markers */}
          {dataPoints.map((p, i) => (
            <circle
              key={i}
              cx={scaleX(p.voltage_v)}
              cy={scaleY(p.current_a)}
              r="3.5"
              fill="#1d4ed8"
            />
          ))}

          {/* Linear Fit Line */}
          {fitPath && (
            <path d={fitPath} fill="none" stroke="#dc2626" strokeWidth="2" strokeDasharray="5 3" />
          )}
        </svg>
      </div>
    </div>
  )
}
