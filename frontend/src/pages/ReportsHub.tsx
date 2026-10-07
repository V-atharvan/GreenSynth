/**
 * GreenSynth Analytics - Reports Hub Page
 *
 * Central location to browse all experiments and download their
 * scientific PDF reports. Uses existing experimentService + the
 * /api/v1/reports/experiments/{id}/pdf endpoint.
 */

import React, { useEffect, useState } from 'react'
import { FileText, Download, Search, AlertCircle, RefreshCw, FlaskConical, CheckCircle2 } from 'lucide-react'
import { experimentService } from '@/services/experimentService'
import type { ExperimentSummary } from '@/types'

export default function ReportsHub() {
  const [experiments, setExperiments] = useState<ExperimentSummary[]>([])
  const [filtered, setFiltered] = useState<ExperimentSummary[]>([])
  const [search, setSearch] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [downloading, setDownloading] = useState<string | null>(null)
  const [downloaded, setDownloaded] = useState<Set<string>>(new Set())

  const load = async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await experimentService.getAll()
      setExperiments(data)
      setFiltered(data)
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Failed to load experiments.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [])

  useEffect(() => {
    const q = search.toLowerCase()
    setFiltered(
      experiments.filter(
        (e) =>
          e.experiment_code.toLowerCase().includes(q) ||
          e.title.toLowerCase().includes(q) ||
          e.status.toLowerCase().includes(q)
      )
    )
  }, [search, experiments])

  const downloadPdf = async (exp: ExperimentSummary) => {
    setDownloading(exp.id)
    try {
      const blob = await experimentService.downloadPdfReport(exp.id)
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `GreenSynth_Report_${exp.experiment_code}.pdf`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(url)
      setDownloaded((prev) => new Set([...prev, exp.id]))
    } catch {
      alert(`Could not generate PDF for ${exp.experiment_code}. Ensure characterization data exists.`)
    } finally {
      setDownloading(null)
    }
  }

  const statusColor: Record<string, { bg: string; color: string }> = {
    COMPLETED:   { bg: '#dcfce7', color: '#16a34a' },
    IN_PROGRESS: { bg: '#dbeafe', color: '#1d4ed8' },
    PLANNED:     { bg: '#fef9c3', color: '#a16207' },
    FAILED:      { bg: '#fee2e2', color: '#dc2626' },
    ARCHIVED:    { bg: '#f1f5f9', color: '#64748b' },
  }

  return (
    <div style={{ minHeight: '100vh', backgroundColor: '#f8fafc', padding: '24px 32px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
        <div>
          <h1 style={{ fontSize: '22px', fontWeight: 700, color: '#0f172a', margin: 0, display: 'flex', alignItems: 'center', gap: '8px' }}>
            <FileText size={22} color="#0f766e" />
            Scientific Reports Hub
          </h1>
          <p style={{ fontSize: '13px', color: '#64748b', margin: '4px 0 0 0' }}>
            Generate and download formal scientific PDF reports for all experiments
          </p>
        </div>
        <button
          onClick={load}
          style={{ background: '#ffffff', border: '1px solid #cbd5e1', color: '#334155', padding: '8px 12px', borderRadius: '6px', fontSize: '13px', display: 'flex', alignItems: 'center', gap: '6px', cursor: 'pointer' }}
        >
          <RefreshCw size={14} />
          Refresh
        </button>
      </div>

      <div style={{ background: '#f0fdf4', border: '1px solid #bbf7d0', borderRadius: '8px', padding: '10px 14px', fontSize: '12px', color: '#166534', marginBottom: '20px', display: 'flex', alignItems: 'center', gap: '8px' }}>
        <CheckCircle2 size={14} />
        PDF reports include 14 scientific sections: XRD, UV-Vis, FTIR, SEM, Electrical, ML predictions, Validation, and more.
      </div>

      {error && (
        <div style={{ background: '#fef2f2', border: '1px solid #fecaca', borderRadius: '8px', padding: '12px 16px', color: '#991b1b', fontSize: '13px', display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '20px' }}>
          <AlertCircle size={16} /> {error}
        </div>
      )}

      <div style={{ position: 'relative', marginBottom: '20px', maxWidth: '400px' }}>
        <Search size={14} style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)', color: '#94a3b8' }} />
        <input
          type="text"
          placeholder="Search experiments..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          style={{ width: '100%', padding: '9px 12px 9px 36px', border: '1px solid #cbd5e1', borderRadius: '8px', fontSize: '13px', color: '#334155', outline: 'none', boxSizing: 'border-box' }}
        />
      </div>

      <div style={{ background: '#ffffff', border: '1px solid #e2e8f0', borderRadius: '12px', overflow: 'hidden' }}>
        {loading ? (
          <div style={{ textAlign: 'center', padding: '60px', color: '#64748b', fontSize: '14px' }}>Loading experiments...</div>
        ) : filtered.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '60px', color: '#94a3b8', fontSize: '14px' }}>
            <FlaskConical size={40} style={{ marginBottom: '12px', opacity: 0.4 }} />
            <div>No experiments found</div>
          </div>
        ) : (
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px' }}>
            <thead>
              <tr style={{ borderBottom: '2px solid #e2e8f0', backgroundColor: '#f8fafc' }}>
                <th style={{ padding: '12px 16px', textAlign: 'left', color: '#64748b', fontWeight: 600 }}>Experiment Code</th>
                <th style={{ padding: '12px 16px', textAlign: 'left', color: '#64748b', fontWeight: 600 }}>Title</th>
                <th style={{ padding: '12px 16px', textAlign: 'left', color: '#64748b', fontWeight: 600 }}>Status</th>
                <th style={{ padding: '12px 16px', textAlign: 'left', color: '#64748b', fontWeight: 600 }}>Date</th>
                <th style={{ padding: '12px 16px', textAlign: 'left', color: '#64748b', fontWeight: 600 }}>PDF Report</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((exp) => {
                const sc = statusColor[exp.status] || { bg: '#f1f5f9', color: '#64748b' }
                const isDownloading = downloading === exp.id
                const wasDownloaded = downloaded.has(exp.id)
                return (
                  <tr key={exp.id} style={{ borderBottom: '1px solid #f1f5f9' }}>
                    <td style={{ padding: '12px 16px', fontWeight: 700, color: '#0f766e' }}>{exp.experiment_code}</td>
                    <td style={{ padding: '12px 16px', color: '#0f172a' }}>{exp.title}</td>
                    <td style={{ padding: '12px 16px' }}>
                      <span style={{ background: sc.bg, color: sc.color, padding: '2px 10px', borderRadius: '12px', fontSize: '11px', fontWeight: 600 }}>{exp.status}</span>
                    </td>
                    <td style={{ padding: '12px 16px', color: '#64748b' }}>{new Date(exp.created_at).toLocaleDateString()}</td>
                    <td style={{ padding: '12px 16px' }}>
                      <button
                        onClick={() => downloadPdf(exp)}
                        disabled={isDownloading}
                        style={{
                          display: 'inline-flex', alignItems: 'center', gap: '6px',
                          padding: '6px 14px', borderRadius: '6px', fontSize: '12px', fontWeight: 600,
                          border: 'none', cursor: isDownloading ? 'not-allowed' : 'pointer',
                          background: wasDownloaded ? '#dcfce7' : isDownloading ? '#f1f5f9' : '#0f766e',
                          color: wasDownloaded ? '#16a34a' : isDownloading ? '#94a3b8' : '#ffffff',
                          transition: 'all 0.15s',
                        }}
                      >
                        {wasDownloaded ? <CheckCircle2 size={13} /> : <Download size={13} />}
                        {isDownloading ? 'Generating...' : wasDownloaded ? 'Downloaded' : 'Download PDF'}
                      </button>
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        )}
      </div>
      <div style={{ marginTop: '10px', fontSize: '12px', color: '#94a3b8' }}>
        Showing {filtered.length} of {experiments.length} experiments
      </div>
    </div>
  )
}
