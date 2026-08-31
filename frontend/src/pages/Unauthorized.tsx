/**
 * GreenSynth Analytics — 403 Unauthorized / Access Denied Page
 *
 * Rendered when an authenticated user attempts to access a resource or route
 * outside their authorized account scope (e.g. Student accessing /admin).
 */

import React from 'react'
import { Link } from 'react-router-dom'
import { Dna, ShieldAlert, ArrowLeft } from 'lucide-react'
import { useAuth } from '@/context/AuthContext'

export default function Unauthorized() {
  const { user, isAdmin } = useAuth()

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
          width: '100%',
          backgroundColor: '#ffffff',
          borderRadius: '12px',
          border: '1px solid #dee2e6',
          boxShadow: '0 8px 24px rgba(0, 0, 0, 0.06)',
          padding: '40px 32px',
          textAlign: 'center',
        }}
      >
        <div
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            justifyContent: 'center',
            width: '64px',
            height: '64px',
            backgroundColor: '#fee2e2',
            color: '#dc2626',
            borderRadius: '50%',
            marginBottom: '20px',
          }}
        >
          <ShieldAlert className="w-8 h-8" />
        </div>

        <h1
          style={{
            fontSize: '24px',
            fontWeight: 800,
            color: '#1e293b',
            margin: '0 0 8px 0',
          }}
        >
          403 — Access Denied
        </h1>

        <p
          style={{
            fontSize: '15px',
            color: '#64748b',
            lineHeight: 1.6,
            margin: '0 0 24px 0',
          }}
        >
          You do not have administrative permission to access this portal or resource.
          Your research access is restricted to your assigned group and project catalog.
        </p>

        {user && (
          <div
            style={{
              backgroundColor: '#f8fafc',
              border: '1px solid #e2e8f0',
              borderRadius: '8px',
              padding: '14px',
              fontSize: '13px',
              color: '#64748b',
              textAlign: 'left',
              marginBottom: '24px',
            }}
          >
            <div><strong>Authenticated User:</strong> {user.full_name} ({user.email})</div>
            <div><strong>Account Type:</strong> {user.account_type}</div>
            <div><strong>Department:</strong> {user.department || 'N/A'}</div>
          </div>
        )}

        <div style={{ display: 'flex', justifyContent: 'center', gap: '12px' }}>
          <Link
            to={isAdmin ? '/admin' : '/dashboard'}
            className="btn btn-primary"
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '8px',
              padding: '10px 20px',
              backgroundColor: '#0f766e',
              color: '#ffffff',
              borderRadius: '8px',
              fontWeight: 600,
              textDecoration: 'none',
            }}
          >
            <ArrowLeft className="w-4 h-4" />
            <span>Return to Dashboard</span>
          </Link>
        </div>
      </div>
    </div>
  )
}
