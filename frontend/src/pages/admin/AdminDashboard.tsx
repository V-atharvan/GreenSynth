/**
 * GreenSynth Analytics — Centralized Administrator Dashboard
 *
 * Provides system-wide oversight, cross-project visibility (P1–P8), research group monitoring,
 * student management, and deep integration into existing characterization and analytics studios.
 *
 * Restricted strictly to users with account_type === 'ADMIN'.
 */

import React, { useEffect, useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import {
  Activity,
  AlertCircle,
  BarChart2,
  BarChart3,
  Building2,
  CheckCircle2,
  Cpu,
  Database,
  Dna,
  FileSpreadsheet,
  FileText,
  Filter,
  FlaskConical,
  FolderKanban,
  Lightbulb,
  Lock,
  LogOut,
  RefreshCw,
  RotateCw,
  Ruler,
  Search,
  ShieldCheck,
  TestTube2,
  UserCheck,
  Users,
  Zap,
} from 'lucide-react'
import { useAuth } from '@/context/AuthContext'
import { adminService, type AdminOverviewStats } from '@/services/adminService'
import type { Experiment, GroupDetail, Project, Sample, User } from '@/types'

type AdminTab = 'overview' | 'projects' | 'groups' | 'students' | 'experiments' | 'samples' | 'studios'

export default function AdminDashboard() {
  const navigate = useNavigate()
  const location = useLocation()
  const { user, logout } = useAuth()

  const [activeTab, setActiveTab] = useState<AdminTab>('overview')
  const [stats, setStats] = useState<AdminOverviewStats | null>(null)
  const [projects, setProjects] = useState<Project[]>([])
  const [groups, setGroups] = useState<GroupDetail[]>([])
  const [usersList, setUsersList] = useState<User[]>([])
  const [experiments, setExperiments] = useState<Experiment[]>([])
  const [samples, setSamples] = useState<Sample[]>([])

  const [selectedProjectId, setSelectedProjectId] = useState<string>('')
  const [searchQuery, setSearchQuery] = useState<string>('')
  const [loading, setLoading] = useState<boolean>(true)

  // Sync tab with URL route
  useEffect(() => {
    const subpath = location.pathname.replace(/^\/admin\/?/, '').split('/')[0]
    if (subpath && ['overview', 'projects', 'groups', 'students', 'experiments', 'samples', 'studios'].includes(subpath)) {
      setActiveTab(subpath as AdminTab)
    }
  }, [location.pathname])
  const [error, setError] = useState<string | null>(null)

  const isAdmin = user?.account_type === 'ADMIN' || (user as any)?.role === 'ADMIN'

  const loadDashboardData = async () => {
    setLoading(true)
    setError(null)
    try {
      const [overviewData, projectsData, groupsData, usersData, experimentsData, samplesData] =
        await Promise.all([
          adminService.getOverview(),
          adminService.getProjects(),
          adminService.getGroups(),
          adminService.getUsers(),
          adminService.getExperiments(selectedProjectId || undefined),
          adminService.getSamples(),
        ])

      setStats(overviewData)
      setProjects(projectsData)
      setGroups(groupsData)
      setUsersList(usersData.filter((u) => u.account_type !== 'ADMIN' && (u as any).role !== 'ADMIN'))
      setExperiments(experimentsData)
      setSamples(samplesData)
    } catch (err: any) {
      setError(err?.message || 'Failed to load system-wide administrator metrics.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (isAdmin) {
      loadDashboardData()
    }
  }, [isAdmin, selectedProjectId])

  const handleLogout = async () => {
    await logout()
    navigate('/login')
  }

  // Access Control Guard
  if (!isAdmin) {
    return (
      <div style={{ maxWidth: '600px', margin: '80px auto', padding: '0 16px', textAlign: 'center' }}>
        <div style={{ background: '#ffffff', border: '1px solid #fee2e2', borderRadius: '12px', padding: '32px', boxShadow: '0 4px 16px rgba(0,0,0,0.04)' }}>
          <div style={{ width: '48px', height: '48px', borderRadius: '50%', background: '#fee2e2', color: '#dc2626', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 16px auto' }}>
            <AlertCircle size={28} />
          </div>
          <h2 style={{ fontSize: '20px', fontWeight: 700, color: '#0f172a', margin: '0 0 8px 0' }}>
            Administrator Access Required
          </h2>
          <p style={{ color: '#64748b', fontSize: '14px', marginBottom: '24px' }}>
            You do not have permission to access the Platform Administrator Dashboard. This area is restricted to system administrators.
          </p>
          <Link
            to="/dashboard"
            style={{ display: 'inline-block', background: '#0f766e', color: '#ffffff', padding: '10px 20px', borderRadius: '6px', fontSize: '14px', fontWeight: 600, textDecoration: 'none' }}
          >
            Return to Researcher Dashboard
          </Link>
        </div>
      </div>
    )
  }

  return (
    <div style={{ minHeight: '100vh', backgroundColor: '#f8fafc', padding: '24px 32px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
        <div>
          <h1 style={{ fontSize: '24px', fontWeight: 700, color: '#0f172a', margin: 0, display: 'flex', alignItems: 'center', gap: '8px' }}>
            Admin Portal
          </h1>
          <p style={{ fontSize: '13px', color: '#64748b', margin: '4px 0 0 0' }}>
            System-Wide Institutional Research Oversight &amp; Multi-Project Management
          </p>
        </div>
        <button
          onClick={loadDashboardData}
          title="Refresh Metrics"
          style={{ background: '#ffffff', border: '1px solid #cbd5e1', color: '#334155', padding: '8px 12px', borderRadius: '6px', fontSize: '13px', display: 'flex', alignItems: 'center', gap: '6px', cursor: 'pointer', boxShadow: '0 1px 2px rgba(0,0,0,0.05)' }}
        >
          <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
          <span>Refresh</span>
        </button>
      </div>

      {/* ── Navigation Tabs ─────────────────────────────────────── */}
      <nav
        style={{
          display: 'flex',
          gap: '8px',
          borderBottom: '1px solid #e2e8f0',
          paddingBottom: '12px',
          marginBottom: '24px',
          overflowX: 'auto',
        }}
      >
        {[
          { id: 'overview', label: 'System Overview', icon: Activity },
          { id: 'projects', label: 'Projects (P1–P8)', icon: FolderKanban },
          { id: 'groups', label: 'Research Groups', icon: Users },
          { id: 'students', label: 'Student Accounts', icon: UserCheck },
          { id: 'experiments', label: 'Experiments', icon: FlaskConical },
          { id: 'samples', label: 'Synthesized Samples', icon: TestTube2 },
          { id: 'studios', label: 'Scientific Studios', icon: Cpu },
        ].map((tab) => {
          const Icon = tab.icon
          const isActive = activeTab === tab.id
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as AdminTab)}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                padding: '8px 16px',
                borderRadius: '8px',
                fontSize: '13px',
                fontWeight: isActive ? 700 : 500,
                border: 'none',
                background: isActive ? '#0f766e' : '#ffffff',
                color: isActive ? '#ffffff' : '#475569',
                cursor: 'pointer',
                boxShadow: isActive ? '0 2px 6px rgba(15, 118, 110, 0.3)' : '0 1px 2px rgba(0,0,0,0.05)',
                transition: 'all 0.15s ease',
              }}
            >
              <Icon size={16} />
              {tab.label}
            </button>
          )
        })}
      </nav>

      {/* ── Error Banner ────────────────────────────────────────── */}
      {error && (
        <div style={{ background: '#fef2f2', border: '1px solid #fecaca', borderRadius: '8px', padding: '12px 16px', color: '#991b1b', fontSize: '13px', display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '20px' }}>
          <AlertCircle size={16} />
          <span>{error}</span>
        </div>
      )}

      {/* ── TAB CONTENT: System Overview ────────────────────────── */}
      {activeTab === 'overview' && (
        <div>
          {/* Key Stat Cards */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '16px', marginBottom: '28px' }}>
            {[
              { label: 'Active Projects', value: stats?.total_projects ?? 0, icon: FolderKanban, color: '#0f766e', bg: '#ccfbf1' },
              { label: 'Research Groups', value: stats?.total_groups ?? 0, icon: Users, color: '#2563eb', bg: '#dbeafe' },
              { label: 'Enrolled Students', value: stats?.total_students ?? 0, icon: UserCheck, color: '#7c3aed', bg: '#ede9fe' },
              { label: 'Total Experiments', value: stats?.total_experiments ?? 0, icon: FlaskConical, color: '#ea580c', bg: '#ffedd5' },
              { label: 'Prepared Samples', value: stats?.total_samples ?? 0, icon: TestTube2, color: '#059669', bg: '#d1fae5' },
              { label: 'Characterization Sets', value: stats?.total_characterizations ?? 0, icon: BarChart3, color: '#0284c7', bg: '#e0f2fe' },
              { label: 'Trained ML Models', value: stats?.total_ml_models ?? 0, icon: Cpu, color: '#d97706', bg: '#fef3c7' },
              { label: 'Recommendations', value: stats?.total_recommendations ?? 0, icon: Lightbulb, color: '#4f46e5', bg: '#e0e7ff' },
              { label: 'Optimization Runs', value: stats?.total_optimization_runs ?? 0, icon: Ruler, color: '#be185d', bg: '#fce7f3' },
            ].map((stat, idx) => {
              const Icon = stat.icon
              return (
                <div
                  key={idx}
                  style={{
                    background: '#ffffff',
                    border: '1px solid #e2e8f0',
                    borderRadius: '10px',
                    padding: '18px 20px',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    boxShadow: '0 1px 3px rgba(0,0,0,0.03)',
                  }}
                >
                  <div>
                    <div style={{ fontSize: '12px', color: '#64748b', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.03em' }}>
                      {stat.label}
                    </div>
                    <div style={{ fontSize: '24px', fontWeight: 800, color: '#0f172a', marginTop: '4px' }}>
                      {loading ? '…' : stat.value}
                    </div>
                  </div>
                  <div style={{ width: '44px', height: '44px', borderRadius: '10px', background: stat.bg, color: stat.color, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                    <Icon size={22} />
                  </div>
                </div>
              )
            })}
          </div>

          {/* Quick Launch Studios Grid */}
          <div style={{ background: '#ffffff', border: '1px solid #e2e8f0', borderRadius: '12px', padding: '24px', marginBottom: '24px' }}>
            <h2 style={{ fontSize: '16px', fontWeight: 700, color: '#0f172a', margin: '0 0 16px 0' }}>
              Scientific Modules &amp; Analytical Studios
            </h2>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '14px' }}>
              {[
                { title: 'Sample Comparison', desc: 'Cross-sample characterization overlay', path: '/comparison', icon: BarChart3 },
                { title: 'Machine Learning Studio', desc: 'Predict bandgaps & electrical properties', path: '/ml', icon: Cpu },
                { title: 'Validation & Drift Studio', desc: 'Model integrity & drift detector', path: '/validation', icon: ShieldCheck },
                { title: 'Recommendation Engine', desc: 'Multi-objective synthesis optimization', path: '/recommendations', icon: Lightbulb },
                { title: 'Design of Experiments (DOE)', desc: 'Full factorial & Taguchi matrix design', path: '/doe', icon: Ruler },
                { title: 'Statistical Evidence Studio', desc: 'Hypothesis testing & p-value analysis', path: '/statistics', icon: BarChart2 },
                { title: 'Experimental Optimization', desc: 'Pareto frontier & Nelder-Mead simplex', path: '/optimization', icon: Ruler },
                { title: 'Autonomous Research Loop', desc: 'Closed-loop suggestion and feedback', path: '/closed-loop', icon: RotateCw },
              ].map((studio, idx) => {
                const Icon = studio.icon
                return (
                  <Link
                    key={idx}
                    to={studio.path}
                    style={{
                      display: 'flex',
                      alignItems: 'flex-start',
                      gap: '12px',
                      padding: '14px 16px',
                      border: '1px solid #e2e8f0',
                      borderRadius: '8px',
                      textDecoration: 'none',
                      color: 'inherit',
                      background: '#f8fafc',
                      transition: 'all 0.15s ease',
                    }}
                  >
                    <div style={{ width: '36px', height: '36px', borderRadius: '8px', background: '#e2e8f0', color: '#0f766e', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                      <Icon size={18} />
                    </div>
                    <div>
                      <div style={{ fontSize: '13px', fontWeight: 700, color: '#0f172a' }}>{studio.title}</div>
                      <div style={{ fontSize: '11px', color: '#64748b', marginTop: '2px' }}>{studio.desc}</div>
                    </div>
                  </Link>
                )
              })}
            </div>
          </div>
        </div>
      )}

      {/* ── TAB CONTENT: Projects (P1–P8) ────────────────────────── */}
      {activeTab === 'projects' && (
        <div style={{ background: '#ffffff', border: '1px solid #e2e8f0', borderRadius: '12px', padding: '24px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
            <h2 style={{ fontSize: '16px', fontWeight: 700, color: '#0f172a', margin: 0 }}>
              Synthesis Project Catalog (P1–P8)
            </h2>
            <div style={{ fontSize: '12px', color: '#64748b' }}>
              Showing {projects.length} configured research programs
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '16px' }}>
            {projects.map((p) => (
              <div
                key={p.id}
                style={{
                  border: '1px solid #e2e8f0',
                  borderRadius: '10px',
                  padding: '18px',
                  background: '#f8fafc',
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                  <span style={{ fontSize: '12px', fontWeight: 800, background: '#0f766e', color: '#ffffff', padding: '2px 8px', borderRadius: '6px' }}>
                    {p.project_code}
                  </span>
                  <span style={{ fontSize: '11px', fontWeight: 600, color: '#16a34a', background: '#dcfce7', padding: '2px 6px', borderRadius: '4px' }}>
                    {p.status}
                  </span>
                </div>
                <div style={{ fontSize: '14px', fontWeight: 700, color: '#0f172a', marginTop: '10px' }}>
                  {p.name}
                </div>
                <div style={{ fontSize: '12px', color: '#64748b', marginTop: '4px', lineHeight: 1.4 }}>
                  {p.description || 'Green synthesis nanoparticles research project.'}
                </div>
                <div style={{ marginTop: '12px', paddingTop: '10px', borderTop: '1px solid #e2e8f0', display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '6px', fontSize: '11px', color: '#475569' }}>
                  <div>Material: <strong>{p.material}</strong></div>
                  <div>Extract: <strong>{p.extract}</strong></div>
                  <div>Solvent: <strong>{p.solvent}</strong></div>
                  <div>Method: <strong>{p.synthesis_method}</strong></div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ── TAB CONTENT: Research Groups ────────────────────────── */}
      {activeTab === 'groups' && (
        <div style={{ background: '#ffffff', border: '1px solid #e2e8f0', borderRadius: '12px', padding: '24px' }}>
          <h2 style={{ fontSize: '16px', fontWeight: 700, color: '#0f172a', margin: '0 0 16px 0' }}>
            Registered Research Groups ({groups.length})
          </h2>
          {groups.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '40px', color: '#64748b', fontSize: '14px' }}>
              No research groups registered in the system yet.
            </div>
          ) : (
            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px', textAlign: 'left' }}>
                <thead>
                  <tr style={{ borderBottom: '2px solid #e2e8f0', color: '#64748b' }}>
                    <th style={{ padding: '10px 14px' }}>Group Name</th>
                    <th style={{ padding: '10px 14px' }}>Assigned Project</th>
                    <th style={{ padding: '10px 14px' }}>Group Leader</th>
                    <th style={{ padding: '10px 14px' }}>Leader Email</th>
                    <th style={{ padding: '10px 14px' }}>Active Members</th>
                    <th style={{ padding: '10px 14px' }}>Created Date</th>
                  </tr>
                </thead>
                <tbody>
                  {groups.map((g) => (
                    <tr key={g.group_id} style={{ borderBottom: '1px solid #f1f5f9' }}>
                      <td style={{ padding: '12px 14px', fontWeight: 600, color: '#0f172a' }}>{g.group_name}</td>
                      <td style={{ padding: '12px 14px' }}>
                        <span style={{ background: '#e0f2fe', color: '#0369a1', padding: '2px 6px', borderRadius: '4px', fontWeight: 700, fontSize: '11px' }}>
                          {g.project_code}
                        </span>
                      </td>
                      <td style={{ padding: '12px 14px' }}>{g.leader_name}</td>
                      <td style={{ padding: '12px 14px', color: '#64748b' }}>{g.leader_email}</td>
                      <td style={{ padding: '12px 14px' }}>{g.member_count} / {g.max_members}</td>
                      <td style={{ padding: '12px 14px', color: '#64748b' }}>
                        {new Date(g.created_at).toLocaleDateString()}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* ── TAB CONTENT: Students ───────────────────────────────── */}
      {activeTab === 'students' && (
        <div style={{ background: '#ffffff', border: '1px solid #e2e8f0', borderRadius: '12px', padding: '24px' }}>
          <h2 style={{ fontSize: '16px', fontWeight: 700, color: '#0f172a', margin: '0 0 16px 0' }}>
            Registered Student Accounts ({usersList.length})
          </h2>
          {usersList.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '40px', color: '#64748b', fontSize: '14px' }}>
              No student accounts found.
            </div>
          ) : (
            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px', textAlign: 'left' }}>
                <thead>
                  <tr style={{ borderBottom: '2px solid #e2e8f0', color: '#64748b' }}>
                    <th style={{ padding: '10px 14px' }}>Full Name</th>
                    <th style={{ padding: '10px 14px' }}>Email Address</th>
                    <th style={{ padding: '10px 14px' }}>Department</th>
                    <th style={{ padding: '10px 14px' }}>Roll Number</th>
                    <th style={{ padding: '10px 14px' }}>Account Status</th>
                    <th style={{ padding: '10px 14px' }}>Registered Date</th>
                  </tr>
                </thead>
                <tbody>
                  {usersList.map((u) => (
                    <tr key={u.id} style={{ borderBottom: '1px solid #f1f5f9' }}>
                      <td style={{ padding: '12px 14px', fontWeight: 600, color: '#0f172a' }}>{u.full_name}</td>
                      <td style={{ padding: '12px 14px', color: '#0f766e' }}>{u.email}</td>
                      <td style={{ padding: '12px 14px' }}>{u.department}</td>
                      <td style={{ padding: '12px 14px', color: '#64748b' }}>{u.roll_number}</td>
                      <td style={{ padding: '12px 14px' }}>
                        <span style={{ background: u.is_active ? '#dcfce7' : '#fee2e2', color: u.is_active ? '#16a34a' : '#dc2626', padding: '2px 8px', borderRadius: '12px', fontSize: '11px', fontWeight: 600 }}>
                          {u.is_active ? 'Active' : 'Inactive'}
                        </span>
                      </td>
                      <td style={{ padding: '12px 14px', color: '#64748b' }}>
                        {new Date(u.created_at).toLocaleDateString()}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* ── TAB CONTENT: Experiments ────────────────────────────── */}
      {activeTab === 'experiments' && (
        <div style={{ background: '#ffffff', border: '1px solid #e2e8f0', borderRadius: '12px', padding: '24px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
            <h2 style={{ fontSize: '16px', fontWeight: 700, color: '#0f172a', margin: 0 }}>
              System-Wide Experiments ({experiments.length})
            </h2>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Filter size={14} style={{ color: '#64748b' }} />
              <select
                value={selectedProjectId}
                onChange={(e) => setSelectedProjectId(e.target.value)}
                style={{ padding: '6px 12px', borderRadius: '6px', border: '1px solid #cbd5e1', fontSize: '13px', color: '#334155' }}
              >
                <option value="">All Projects (P1–P8)</option>
                {projects.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.project_code} — {p.name}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {experiments.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '40px', color: '#64748b', fontSize: '14px' }}>
              No experiments found for the selected filter.
            </div>
          ) : (
            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px', textAlign: 'left' }}>
                <thead>
                  <tr style={{ borderBottom: '2px solid #e2e8f0', color: '#64748b' }}>
                    <th style={{ padding: '10px 14px' }}>Code</th>
                    <th style={{ padding: '10px 14px' }}>Title</th>
                    <th style={{ padding: '10px 14px' }}>Status</th>
                    <th style={{ padding: '10px 14px' }}>Created Date</th>
                  </tr>
                </thead>
                <tbody>
                  {experiments.map((e) => (
                    <tr key={e.id} style={{ borderBottom: '1px solid #f1f5f9' }}>
                      <td style={{ padding: '12px 14px', fontWeight: 700, color: '#0f766e' }}>{e.experiment_code}</td>
                      <td style={{ padding: '12px 14px', color: '#0f172a' }}>{e.title}</td>
                      <td style={{ padding: '12px 14px' }}>
                        <span style={{ background: '#f1f5f9', color: '#475569', padding: '2px 8px', borderRadius: '6px', fontSize: '11px', fontWeight: 600 }}>
                          {e.status}
                        </span>
                      </td>
                      <td style={{ padding: '12px 14px', color: '#64748b' }}>
                        {new Date(e.created_at).toLocaleDateString()}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* ── TAB CONTENT: Samples ────────────────────────────────── */}
      {activeTab === 'samples' && (
        <div style={{ background: '#ffffff', border: '1px solid #e2e8f0', borderRadius: '12px', padding: '24px' }}>
          <h2 style={{ fontSize: '16px', fontWeight: 700, color: '#0f172a', margin: '0 0 16px 0' }}>
            Synthesized Samples Across Projects ({samples.length})
          </h2>
          {samples.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '40px', color: '#64748b', fontSize: '14px' }}>
              No samples recorded in the database yet.
            </div>
          ) : (
            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px', textAlign: 'left' }}>
                <thead>
                  <tr style={{ borderBottom: '2px solid #e2e8f0', color: '#64748b' }}>
                    <th style={{ padding: '10px 14px' }}>Sample Code</th>
                    <th style={{ padding: '10px 14px' }}>Sample Name</th>
                    <th style={{ padding: '10px 14px' }}>Material</th>
                    <th style={{ padding: '10px 14px' }}>Status</th>
                    <th style={{ padding: '10px 14px' }}>Created Date</th>
                  </tr>
                </thead>
                <tbody>
                  {samples.map((s) => (
                    <tr key={s.id} style={{ borderBottom: '1px solid #f1f5f9' }}>
                      <td style={{ padding: '12px 14px', fontWeight: 700, color: '#0f766e' }}>{s.sample_code}</td>
                      <td style={{ padding: '12px 14px', color: '#0f172a' }}>{s.name}</td>
                      <td style={{ padding: '12px 14px' }}>{s.material}</td>
                      <td style={{ padding: '12px 14px' }}>
                        <span style={{ background: '#dcfce7', color: '#16a34a', padding: '2px 8px', borderRadius: '6px', fontSize: '11px', fontWeight: 600 }}>
                          {s.status}
                        </span>
                      </td>
                      <td style={{ padding: '12px 14px', color: '#64748b' }}>
                        {new Date(s.created_at).toLocaleDateString()}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* ── TAB CONTENT: Studios ────────────────────────────────── */}
      {activeTab === 'studios' && (
        <div style={{ background: '#ffffff', border: '1px solid #e2e8f0', borderRadius: '12px', padding: '24px' }}>
          <h2 style={{ fontSize: '16px', fontWeight: 700, color: '#0f172a', margin: '0 0 16px 0' }}>
            Institutional Characterization &amp; Analytics Studios
          </h2>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '16px' }}>
            {[
              { title: 'X-Ray Diffraction (XRD)', desc: 'Peak detection, Scherrer crystallite sizing', path: '/comparison', icon: BarChart3 },
              { title: 'UV-Vis Spectroscopy', desc: 'Direct & indirect Tauc bandgap derivation', path: '/comparison', icon: Zap },
              { title: 'FTIR Spectroscopy', desc: 'Functional group identification & baseline', path: '/comparison', icon: Activity },
              { title: 'SEM Micrographs', desc: 'Nanoparticle morphology & size distribution', path: '/samples', icon: Database },
              { title: 'Electrical Analysis', desc: 'Four-point probe I-V & conductivity', path: '/comparison', icon: Zap },
              { title: 'Design of Experiments (DOE)', desc: 'Taguchi orthogonal arrays & ANOVA', path: '/doe', icon: Ruler },
              { title: 'Pareto Optimization', desc: 'Simultaneous bandgap & yield optimization', path: '/optimization', icon: Ruler },
              { title: 'Machine Learning Studio', desc: 'XGBoost & Random Forest regression', path: '/ml', icon: Cpu },
            ].map((studio, idx) => {
              const Icon = studio.icon
              return (
                <div key={idx} style={{ border: '1px solid #e2e8f0', borderRadius: '8px', padding: '16px', background: '#f8fafc' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '8px' }}>
                    <div style={{ width: '32px', height: '32px', borderRadius: '6px', background: '#ccfbf1', color: '#0f766e', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                      <Icon size={16} />
                    </div>
                    <div style={{ fontSize: '14px', fontWeight: 700, color: '#0f172a' }}>{studio.title}</div>
                  </div>
                  <div style={{ fontSize: '12px', color: '#64748b', marginBottom: '12px' }}>{studio.desc}</div>
                  <Link
                    to={studio.path}
                    style={{ fontSize: '12px', fontWeight: 600, color: '#0f766e', textDecoration: 'none', display: 'inline-flex', alignItems: 'center', gap: '4px' }}
                  >
                    Launch Studio &rarr;
                  </Link>
                </div>
              )
            })}
          </div>
        </div>
      )}
    </div>
  )
}
