/**
 * GreenSynth Analytics — FTIR Spectrum SVG Chart
 *
 * Visualizes:
 *  - FTIR Spectrum (Wavenumber cm^-1 vs Transmittance % / Absorbance)
 *  - Descending Wavenumber X-axis toggle (4000 -> 400 cm^-1)
 *  - Detected Peak Markers and Researcher Functional Group Annotation Badges
 */

import React, { useState } from 'react'
import type { FTIRAnnotationResponse, FTIRDataPoint, FTIRPeakItem } from '@/types'

interface FtirPlotChartProps {
  dataPoints: FTIRDataPoint[]
  detectedPeaks: FTIRPeakItem[]
  annotations?: FTIRAnnotationResponse[]
  signalType?: string
}

export function FtirPlotChart({
  dataPoints,
  detectedPeaks,
  annotations = [],
  signalType = 'TRANSMITTANCE',
}: FtirPlotChartProps) {
  const [reverseX, setReverseX] = useState(true) // Conventional FTIR descending wavenumber display

  if (!dataPoints || dataPoints.length === 0) {
    return (
      <div style={{ padding: 40, textAlign: 'center', color: 'var(--color-text-muted)' }}>
        No FTIR spectrum data points available.
      </div>
    )
  }

  const width = 800
  const height = 380
  const padding = { top: 30, right: 30, bottom: 50, left: 70 }
  const innerW = width - padding.left - padding.right
  const innerH = height - padding.top - padding.bottom

  const rawXMin = Math.min(...dataPoints.map((p) => p.wavenumber_cm1))
  const rawXMax = Math.max(...dataPoints.map((p) => p.wavenumber_cm1))
  const yMin = 0
  const yMax = Math.max(...dataPoints.map((p) => p.signal_value), 100) * 1.05

  const scaleX = (val: number) => {
    if (reverseX) {
      // Descending (4000 -> 400 cm^-1)
      return padding.left + ((rawXMax - val) / (rawXMax - rawXMin || 1)) * innerW
    }
    // Ascending (400 -> 4000 cm^-1)
    return padding.left + ((val - rawXMin) / (rawXMax - rawXMin || 1)) * innerW
  }

  const scaleY = (val: number) =>
    height - padding.bottom - ((val - yMin) / (yMax - yMin || 1)) * innerH

  const dataPath = dataPoints.reduce((acc, p, i) => {
    const x = scaleX(p.wavenumber_cm1)
    const y = scaleY(p.signal_value)
    return i === 0 ? `M ${x} ${y}` : `${acc} L ${x} ${y}`
  }, '')

  const xTicks = Array.from({ length: 6 }, (_, i) => {
    const val = reverseX
      ? rawXMax - (i / 5) * (rawXMax - rawXMin)
      : rawXMin + (i / 5) * (rawXMax - rawXMin)
    return { val: Math.round(val), x: scaleX(val) }
  })

  const yTicks = Array.from({ length: 5 }, (_, i) => {
    const val = yMin + (i / 4) * (yMax - yMin)
    return { val: val.toFixed(1), y: scaleY(val) }
  })

  return (
    <div style={{ background: 'white', borderRadius: 'var(--radius-md)', padding: 16, border: '1px solid var(--color-border)' }}>
      {/* Legend & X-Axis Orientation Toggle */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
        <div style={{ fontWeight: 600, fontSize: '0.9375rem' }}>
          FTIR Spectrum ({signalType}) · Detected Peaks ({detectedPeaks.length})
        </div>
        <button
          className="btn btn-secondary btn-sm"
          onClick={() => setReverseX(!reverseX)}
        >
          ↔ Wavenumber Axis: {reverseX ? 'Descending (4000 → 400 cm⁻¹)' : 'Ascending (400 → 4000 cm⁻¹)'}
        </button>
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
            Wavenumber ν (cm⁻¹)
          </text>
          <text x={18} y={height / 2} textAnchor="middle" transform={`rotate(-90 18 ${height / 2})`} fill="#475569" fontSize="12" fontWeight="600">
            {signalType === 'TRANSMITTANCE' ? 'Transmittance T (%)' : 'Absorbance / Intensity'}
          </text>

          {/* X Ticks */}
          {xTicks.map((t, i) => (
            <g key={i}>
              <line x1={t.x} y1={height - padding.bottom} x2={t.x} y2={height - padding.bottom + 5} stroke="#64748b" />
              <text x={t.x} y={height - padding.bottom + 20} textAnchor="middle" fill="#64748b" fontSize="10">
                {t.val} cm⁻¹
              </text>
            </g>
          ))}

          {/* Y Ticks */}
          {yTicks.map((t, i) => (
            <g key={i}>
              <line x1={padding.left - 5} y1={t.y} x2={padding.left} y2={t.y} stroke="#64748b" />
              <text x={padding.left - 10} y={t.y + 4} textAnchor="end" fill="#64748b" fontSize="10">
                {t.val}
              </text>
            </g>
          ))}

          {/* Spectrum Path */}
          <path d={dataPath} fill="none" stroke="#7c3aed" strokeWidth="2" />

          {/* Detected Peak Markers */}
          {detectedPeaks.map((p, i) => {
            const px = scaleX(p.wavenumber_cm1)
            const py = scaleY(p.signal_value)
            return (
              <g key={i}>
                <circle cx={px} cy={py} r="4" fill="#6d28d9" stroke="white" strokeWidth="1.5" />
                <text x={px} y={py - 8} textAnchor="middle" fill="#5b21b6" fontSize="9" fontWeight="700">
                  {p.wavenumber_cm1.toFixed(0)}
                </text>
              </g>
            )
          })}

          {/* Researcher Annotations */}
          {annotations.map((a) => {
            const ax = scaleX(a.wavenumber_cm1)
            return (
              <g key={a.id}>
                <line x1={ax} y1={padding.top} x2={ax} y2={height - padding.bottom} stroke="#dc2626" strokeWidth="1" strokeDasharray="3 3" />
                <rect x={ax - 35} y={padding.top + 5} width="70" height="18" fill="#fef2f2" stroke="#fca5a5" rx="3" />
                <text x={ax} y={padding.top + 17} textAnchor="middle" fill="#b91c1c" fontSize="9" fontWeight="700">
                  {a.label}
                </text>
              </g>
            )
          })}
        </svg>
      </div>
    </div>
  )
}
