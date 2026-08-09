/**
 * GreenSynth Analytics — XRD Pattern Plot Chart
 *
 * Visualizes Raw XRD vs Processed XRD curves and overlays detected peak markers.
 * Renders interactive SVG chart with hover tooltips and toggles.
 */

import React, { useState } from 'react'
import type { XRDDataPoint, XRDPeak } from '@/types'

interface XrdPlotChartProps {
  dataPoints: XRDDataPoint[]
  peaks: XRDPeak[]
}

export function XrdPlotChart({ dataPoints, peaks }: XrdPlotChartProps) {
  const [showRaw, setShowRaw] = useState(true)
  const [showProcessed, setShowProcessed] = useState(true)
  const [showPeaks, setShowPeaks] = useState(true)

  if (!dataPoints || dataPoints.length === 0) {
    return (
      <div style={{ padding: 40, textAlign: 'center', color: 'var(--color-text-muted)' }}>
        No XRD data points to render.
      </div>
    )
  }

  // Calculate bounds
  const xMin = Math.min(...dataPoints.map((p) => p.two_theta))
  const xMax = Math.max(...dataPoints.map((p) => p.two_theta))
  const yMaxRaw = Math.max(...dataPoints.map((p) => p.raw_intensity))
  const yMaxProc = Math.max(...dataPoints.map((p) => p.processed_intensity ?? 0))
  const yMax = Math.max(yMaxRaw, yMaxProc, 10) * 1.05

  const width = 800
  const height = 400
  const padding = { top: 30, right: 30, bottom: 50, left: 70 }

  const innerW = width - padding.left - padding.right
  const innerH = height - padding.top - padding.bottom

  const scaleX = (val: number) =>
    padding.left + ((val - xMin) / (xMax - xMin || 1)) * innerW
  const scaleY = (val: number) =>
    height - padding.bottom - (val / yMax) * innerH

  // Generate SVG paths
  const rawPath = dataPoints.reduce((acc, p, i) => {
    const x = scaleX(p.two_theta)
    const y = scaleY(p.raw_intensity)
    return i === 0 ? `M ${x} ${y}` : `${acc} L ${x} ${y}`
  }, '')

  const procPath = dataPoints.reduce((acc, p, i) => {
    if (p.processed_intensity == null) return acc
    const x = scaleX(p.two_theta)
    const y = scaleY(p.processed_intensity)
    return i === 0 ? `M ${x} ${y}` : `${acc} L ${x} ${y}`
  }, '')

  // Generate X-axis ticks (5 ticks)
  const xTicks = Array.from({ length: 6 }, (_, i) => {
    const val = xMin + (i / 5) * (xMax - xMin)
    return { val: val.toFixed(1), x: scaleX(val) }
  })

  // Generate Y-axis ticks (4 ticks)
  const yTicks = Array.from({ length: 5 }, (_, i) => {
    const val = (i / 4) * yMax
    return { val: Math.round(val), y: scaleY(val) }
  })

  return (
    <div style={{ background: 'white', borderRadius: 'var(--radius-md)', padding: 16, border: '1px solid var(--color-border)' }}>
      {/* Controls / Legend Bar */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
        <div style={{ fontWeight: 600, fontSize: '0.9375rem' }}>
          XRD Diffraction Pattern (2θ vs Intensity)
        </div>
        <div style={{ display: 'flex', gap: 16, fontSize: '0.8125rem' }}>
          <label style={{ display: 'flex', alignItems: 'center', gap: 6, cursor: 'pointer', color: '#94a3b8' }}>
            <input type="checkbox" checked={showRaw} onChange={(e) => setShowRaw(e.target.checked)} />
            <span style={{ display: 'inline-block', width: 12, height: 3, background: '#94a3b8' }}></span>
            Raw Pattern
          </label>
          <label style={{ display: 'flex', alignItems: 'center', gap: 6, cursor: 'pointer', color: '#1e3a8a', fontWeight: 600 }}>
            <input type="checkbox" checked={showProcessed} onChange={(e) => setShowProcessed(e.target.checked)} />
            <span style={{ display: 'inline-block', width: 12, height: 3, background: '#1e3a8a' }}></span>
            Processed Pattern
          </label>
          <label style={{ display: 'flex', alignItems: 'center', gap: 6, cursor: 'pointer', color: '#dc2626', fontWeight: 600 }}>
            <input type="checkbox" checked={showPeaks} onChange={(e) => setShowPeaks(e.target.checked)} />
            <span style={{ display: 'inline-block', width: 8, height: 8, borderRadius: '50%', background: '#dc2626' }}></span>
            Detected Peaks ({peaks.length})
          </label>
        </div>
      </div>

      {/* SVG Chart */}
      <div style={{ overflowX: 'auto' }}>
        <svg viewBox={`0 0 ${width} ${height}`} style={{ width: '100%', height: 'auto', display: 'block' }}>
          {/* Grid lines */}
          {yTicks.map((tick, i) => (
            <line
              key={i}
              x1={padding.left}
              y1={tick.y}
              x2={width - padding.right}
              y2={tick.y}
              stroke="#f1f5f9"
              strokeWidth="1"
            />
          ))}
          {xTicks.map((tick, i) => (
            <line
              key={i}
              x1={tick.x}
              y1={padding.top}
              x2={tick.x}
              y2={height - padding.bottom}
              stroke="#f1f5f9"
              strokeWidth="1"
            />
          ))}

          {/* Axes */}
          <line x1={padding.left} y1={height - padding.bottom} x2={width - padding.right} y2={height - padding.bottom} stroke="#64748b" strokeWidth="1.5" />
          <line x1={padding.left} y1={padding.top} x2={padding.left} y2={height - padding.bottom} stroke="#64748b" strokeWidth="1.5" />

          {/* Axis Labels */}
          <text x={width / 2} y={height - 12} textAnchor="middle" fill="#475569" fontSize="12" fontWeight="600">
            2θ Angle (Degrees)
          </text>
          <text x={18} y={height / 2} textAnchor="middle" transform={`rotate(-90 18 ${height / 2})`} fill="#475569" fontSize="12" fontWeight="600">
            Intensity (Counts / a.u.)
          </text>

          {/* X Ticks */}
          {xTicks.map((t, i) => (
            <g key={i}>
              <line x1={t.x} y1={height - padding.bottom} x2={t.x} y2={height - padding.bottom + 5} stroke="#64748b" />
              <text x={t.x} y={height - padding.bottom + 20} textAnchor="middle" fill="#64748b" fontSize="10">
                {t.val}°
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

          {/* Raw Pattern Line */}
          {showRaw && (
            <path d={rawPath} fill="none" stroke="#cbd5e1" strokeWidth="1.5" />
          )}

          {/* Processed Pattern Line */}
          {showProcessed && (
            <path d={procPath} fill="none" stroke="#1e3a8a" strokeWidth="2" />
          )}

          {/* Peak Markers */}
          {showPeaks &&
            peaks.map((p, i) => {
              const cx = scaleX(p.peak_position)
              const cy = scaleY(p.intensity)
              return (
                <g key={p.id || i}>
                  <circle cx={cx} cy={cy} r="5" fill="#dc2626" stroke="white" strokeWidth="1.5" />
                  <line x1={cx} y1={cy - 6} x2={cx} y2={cy - 16} stroke="#dc2626" strokeWidth="1" />
                  <text x={cx} y={cy - 20} textAnchor="middle" fill="#dc2626" fontSize="10" fontWeight="700">
                    {p.peak_position.toFixed(2)}°
                  </text>
                </g>
              )
            })}
        </svg>
      </div>
    </div>
  )
}
