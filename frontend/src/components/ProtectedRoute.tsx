/**
 * GreenSynth Analytics — Protected Route Guard
 *
 * Enforces:
 *   1. User Authentication (redirects unauthenticated sessions to /login)
 *   2. Session Restoration & Project Context Loading
 *   3. Research Group Membership Verification
 *   4. Zero Flash of Protected Research Content
 */

import React from 'react'
import { Link, Navigate, Outlet, useLocation } from 'react-router-dom'
import { useAuth } from '@/context/AuthContext'
import { useProjectContext } from '@/context/ProjectContext'
import { AlertTriangle, Dna, Loader2, LogOut, ShieldAlert, Users } from 'lucide-react'

export interface ProtectedRouteProps {
  children?: React.ReactNode
}

export const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ children }) => {
  const { isAuthenticated, isLoading: authLoading, logout, isAdmin } = useAuth()
  const { hasGroupMembership, isLoading: projectLoading } = useProjectContext()
  const location = useLocation()

  // State 1: Authentication & Project Context Restoration
  if (authLoading || (isAuthenticated && projectLoading && !isAdmin)) {
    return (
      <div
        className="auth-loading-screen"
        style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          minHeight: '100vh',
          backgroundColor: 'var(--color-bg, #f4f6f9)',
          color: 'var(--color-primary, #1e3a5f)',
          gap: '16px',
        }}
        role="status"
        aria-live="polite"
      >
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            fontSize: '20px',
            fontWeight: 700,
            color: 'var(--color-primary, #1e3a5f)',
          }}
        >
          <Dna className="w-6 h-6 text-emerald-600" style={{ color: '#0f766e' }} />
          <span>GreenSynth Analytics</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#6c757d', fontSize: '14px' }}>
          <Loader2 className="w-4 h-4 animate-spin" style={{ animation: 'spin 1s linear infinite' }} />
          <span>Restoring research session and project context...</span>
        </div>
      </div>
    )
  }

  // State 2: Unauthenticated Session -> Redirect to Login
  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />
  }

  // State 5: Authenticated Student without Group Membership
  if (!isAdmin && !hasGroupMembership) {
    return (
      <div
        style={{
          minHeight: '100vh',
          backgroundColor: 'var(--color-bg, #f4f6f9)',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          padding: '32px 16px',
        }}
      >
        <div
          style={{
            maxWidth: '520px',
            backgroundColor: '#ffffff',
            borderRadius: '12px',
            border: '1px solid #dee2e6',
            padding: '32px',
            boxShadow: '0 8px 24px rgba(0, 0, 0, 0.05)',
            textAlign: 'center',
          }}
        >
          <div
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              justifyContent: 'center',
              width: '56px',
              height: '56px',
              backgroundColor: '#fef3c7',
              color: '#d97706',
              borderRadius: '50%',
              marginBottom: '16px',
            }}
          >
            <ShieldAlert className="w-7 h-7" />
          </div>

          <h2 style={{ fontSize: '20px', fontWeight: 700, color: '#1e3a5f', margin: '0 0 8px 0' }}>
            No Active Research Group
          </h2>
          <p style={{ fontSize: '14px', color: '#64748b', lineHeight: 1.5, marginBottom: '24px' }}>
            Your account is authenticated, but you are not currently assigned to an active research group or synthesis project.
          </p>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', marginBottom: '24px' }}>
            <Link
              to="/register"
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '8px',
                padding: '10px 16px',
                backgroundColor: '#0f766e',
                color: '#ffffff',
                textDecoration: 'none',
                borderRadius: '6px',
                fontSize: '13px',
                fontWeight: 600,
              }}
            >
              <Users className="w-4 h-4" />
              <span>Register a New Research Group</span>
            </Link>

            <Link
              to="/accept-invitation"
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '8px',
                padding: '10px 16px',
                backgroundColor: '#f8f9fa',
                color: '#495057',
                border: '1px solid #dee2e6',
                textDecoration: 'none',
                borderRadius: '6px',
                fontSize: '13px',
                fontWeight: 500,
              }}
            >
              <span>Accept Existing Invitation</span>
            </Link>
          </div>

          <button
            onClick={() => logout()}
            style={{
              background: 'none',
              border: 'none',
              color: '#ef4444',
              cursor: 'pointer',
              fontSize: '13px',
              fontWeight: 600,
              display: 'inline-flex',
              alignItems: 'center',
              gap: '6px',
            }}
          >
            <LogOut className="w-4 h-4" />
            <span>Sign Out</span>
          </button>
        </div>
      </div>
    )
  }

  // State 4: Authenticated with Valid Group & Project
  return children ? <>{children}</> : <Outlet />
}

export default ProtectedRoute
