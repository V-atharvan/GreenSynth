/**
 * GreenSynth Analytics — Admin Route Guard
 *
 * Ensures only users with account_type === "ADMIN" can access platform-wide administration routes.
 * Non-admin students are redirected to /unauthorized, and unauthenticated sessions to /login.
 */

import React from 'react'
import { Navigate, Outlet } from 'react-router-dom'
import { useAuth } from '@/context/AuthContext'
import { Dna, Loader2 } from 'lucide-react'

export interface AdminRouteProps {
  children?: React.ReactNode
}

export const AdminRoute: React.FC<AdminRouteProps> = ({ children }) => {
  const { isAuthenticated, isLoading, isAdmin } = useAuth()

  if (isLoading) {
    return (
      <div
        style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          minHeight: '100vh',
          backgroundColor: 'var(--color-bg, #f4f6f9)',
          gap: '16px',
        }}
        role="status"
        aria-live="polite"
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '20px', fontWeight: 700, color: '#1e3a5f' }}>
          <Dna className="w-6 h-6 text-emerald-600" style={{ color: '#0f766e' }} />
          <span>GreenSynth Analytics</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#6c757d', fontSize: '14px' }}>
          <Loader2 className="w-4 h-4 animate-spin" style={{ animation: 'spin 1s linear infinite' }} />
          <span>Verifying administrator authorization...</span>
        </div>
      </div>
    )
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }

  if (!isAdmin) {
    return <Navigate to="/unauthorized" replace />
  }

  return children ? <>{children}</> : <Outlet />
}

export default AdminRoute
