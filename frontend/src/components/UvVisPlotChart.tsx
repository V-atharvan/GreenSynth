/**
 * GreenSynth Analytics — UV-Vis Spectrum & Tauc Plot SVG Chart
 *
 * Visualizes:
 *  1. Absorbance Spectrum (Wavelength nm vs Absorbance A)
 *  2. Tauc Plot (Photon Energy eV vs (alpha*h*nu)^n) with linear fit line and Eg extrapolation
 */

import React, { useState } from 'react'
import type { TaucDataPoint, TaucFitLinePoint } from '@/types'

interface UvVisPlotChartProps {
  dataPoints: TaucDataPoint[]
  fitLine: TaucFitLinePoint[]
  bandGapEv?: number | null
  transitionType?: string
  usingAlpha?: boolean
}

export function UvVisPlotChart({
  dataPoints,
  fitLine,
  bandGapEv,
  transitionType = 'DIRECT_ALLOWED',
  usingAlpha = false,
}: UvVisPlotChartProps) {
  const [activeTab, setActiveTab] = useState<'tauc' | 'spectrum'>('tauc')

  if (!dataPoints || dataPoints.length === 0) {
    return (
      <div style={{ padding: 40, textAlign: 'center', color: 'var(--color-text-muted)' }}>
        No UV-Vis data points available.
      </div>
    )
  }

  const width = 800
  const height = 380
  const padding = { top: 30, right: 30, bottom: 50, left: 70 }
  const innerW = width - padding.left - padding.right
  const innerH = height - padding.top - padding.bottom

  const isTauc = activeTab === 'tauc'

  // X and Y bounds depending on active tab
  const xVals = dataPoints.map((p) => (isTauc ? p.photon_energy_ev : p.wavelength_nm))
  const yVals = dataPoints.map((p) => (isTauc ? p.tauc_y : p.absorbance))

  const xMin = Math.min(...xVals)
  const xMax = Math.max(...xVals)
  const yMin = 0
  const yMax = Math.max(...yVals, ...(isTauc ? fitLine.map((f) => f.fit_y) : []), 1) * 1.05

  const scaleX = (val: number) =>
    padding.left + ((val - xMin) / (xMax - xMin || 1)) * innerW
  const scaleY = (val: number) =>
    height - padding.bottom - ((val - yMin) / (yMax - yMin || 1)) * innerH

  const dataPath = dataPoints.reduce((acc, p, i) => {
    const xv = isTauc ? p.photon_energy_ev : p.wavelength_nm
    const yv = isTauc ? p.tauc_y : p.absorbance
    const x = scaleX(xv)
    const y = scaleY(yv)
    return i === 0 ? `M ${x} ${y}` : `${acc} L ${x} ${y}`
  }, '')

  const fitPath = isTauc && fitLine.length > 0
    ? fitLine.reduce((acc, f, i) => {
        const x = scaleX(f.photon_energy_ev)
        const y = scaleY(f.fit_y)
        return i === 0 ? `M ${x} ${y}` : `${acc} L ${x} ${y}`
      }, '')
    : ''

  const xTicks = Array.from({ length: 6 }, (_, i) => {
    const val = xMin + (i / 5) * (xMax - xMin)
    return { val: val.toFixed(2), x: scaleX(val) }
  })

  const yTicks = Array.from({ length: 5 }, (_, i) => {
    const val = yMin + (i / 4) * (yMax - yMin)
    return { val: val.toFixed(1), y: scaleY(val) }
  })

  const yLabel = isTauc
    ? transitionType === 'DIRECT_ALLOWED'
      ? usingAlpha ? '(α · hν)² (eV²·cm⁻²)' : '(A · hν)² (a.u.)'
      : usingAlpha ? '(α · hν)⁰·⁵ (eV⁰·⁵·cm⁻⁰·⁵)' : '(A · hν)⁰·⁵ (a.u.)'
    : 'Absorbance A (a.u.)'

  return (
    <div style={{ background: 'white', borderRadius: 'var(--radius-md)', padding: 16, border: '1px solid var(--color-border)' }}>
      {/* Tab Controls */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
        <div style={{ display: 'flex', gap: 8 }}>
          <button
            className={`btn btn-sm ${activeTab === 'tauc' ? 'btn-primary' : 'btn-secondary'}`}
            onClick={() => setActiveTab('tauc')}
          >
            📐 Tauc Plot ({transitionType === 'DIRECT_ALLOWED' ? 'Direct n=2' : 'Indirect n=0.5'})
          </button>
          <button
            className={`btn btn-sm ${activeTab === 'spectrum' ? 'btn-primary' : 'btn-secondary'}`}
            onClick={() => setActiveTab('spectrum')}
          >
            📊 Absorbance Spectrum (λ vs A)
          </button>
        </div>

        {isTauc && bandGapEv && (
          <div style={{ fontSize: '0.875rem', fontWeight: 700, color: '#15803d', background: '#f0fdf4', padding: '4px 12px', borderRadius: 4, border: '1px solid #bbf7d0' }}>
            Extrapolated Optical Eg = {bandGapEv.toFixed(2)} eV
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
            {isTauc ? 'Photon Energy hν (eV)' : 'Wavelength λ (nm)'}
          </text>
          <text x={18} y={height / 2} textAnchor="middle" transform={`rotate(-90 18 ${height / 2})`} fill="#475569" fontSize="12" fontWeight="600">
            {yLabel}
          </text>

          {/* X Ticks */}
          {xTicks.map((t, i) => (
            <g key={i}>
              <line x1={t.x} y1={height - padding.bottom} x2={t.x} y2={height - padding.bottom + 5} stroke="#64748b" />
              <text x={t.x} y={height - padding.bottom + 20} textAnchor="middle" fill="#64748b" fontSize="10">
                {t.val}{isTauc ? ' eV' : ' nm'}
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

          {/* Main Curve */}
          <path d={dataPath} fill="none" stroke={isTauc ? '#0284c7' : '#0d9488'} strokeWidth="2" />

          {/* Tauc Linear Regression Line */}
          {isTauc && fitPath && (
            <path d={fitPath} fill="none" stroke="#dc2626" strokeWidth="2.5" strokeDasharray="6 3" />
          )}

          {/* Extrapolated Eg Marker */}
          {isTauc && bandGapEv && bandGapEv >= xMin && bandGapEv <= xMax && (
            <g>
              <circle cx={scaleX(bandGapEv)} cy={scaleY(0)} r="6" fill="#dc2626" stroke="white" strokeWidth="2" />
              <line x1={scaleX(bandGapEv)} y1={padding.top} x2={scaleX(bandGapEv)} y2={height - padding.bottom} stroke="#dc2626" strokeWidth="1" strokeDasharray="3 3" />
              <text x={scaleX(bandGapEv)} y={padding.top - 8} textAnchor="middle" fill="#dc2626" fontSize="11" fontWeight="700">
                Eg = {bandGapEv.toFixed(2)} eV
              </text>
            </g>
          )}
        </svg>
      </div>
    </div>
  )
}
