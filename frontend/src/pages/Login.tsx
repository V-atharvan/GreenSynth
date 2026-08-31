/**
 * GreenSynth Analytics — Research Portal Login Page
 *
 * Secure institutional sign-in for Group Leaders and Research Members.
 */

import React, { useState, useEffect } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '@/context/AuthContext'
import {
  AlertCircle,
  ArrowRight,
  CheckCircle2,
  Dna,
  Eye,
  EyeOff,
  FlaskConical,
  Lock,
  Mail,
  ShieldCheck,
  Users,
} from 'lucide-react'

export default function Login() {
  const navigate = useNavigate()
  const location = useLocation()
  const { login, isAuthenticated, isAdmin, isLoading: authLoading } = useAuth()

  const [email, setEmail] = useState<string>('')
  const [password, setPassword] = useState<string>('')
  const [showPassword, setShowPassword] = useState<boolean>(false)
  const [loading, setLoading] = useState<boolean>(false)
  const [error, setError] = useState<string | null>(null)

  // Determine redirect target after login
  const fromLocation = (location.state as { from?: { pathname?: string } })?.from?.pathname || '/'

  // Redirect if already authenticated
  useEffect(() => {
    if (!authLoading && isAuthenticated) {
      if (isAdmin) {
        navigate('/admin', { replace: true })
      } else {
        const dest = fromLocation && fromLocation !== '/login' && fromLocation !== '/' ? fromLocation : '/dashboard'
        navigate(dest, { replace: true })
      }
    }
  }, [isAuthenticated, isAdmin, authLoading, navigate, fromLocation])

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    setError(null)

    const trimmedEmail = email.trim()
    if (!trimmedEmail) {
      setError('Please enter your institutional email address.')
      return
    }

    if (!password) {
      setError('Please enter your password.')
      return
    }

    setLoading(true)
    try {
      const loggedUser = await login({ email: trimmedEmail, password })
      if (loggedUser.account_type === 'ADMIN' || (loggedUser as any).role === 'ADMIN') {
        navigate('/admin', { replace: true })
      } else {
        const dest = fromLocation && fromLocation !== '/login' && fromLocation !== '/' ? fromLocation : '/dashboard'
        navigate(dest, { replace: true })
      }
    } catch (err: any) {
      setError(err?.message || 'Invalid email or password. Please verify your credentials.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div
      style={{
        minHeight: '100vh',
        backgroundColor: 'var(--color-bg, #f4f6f9)',
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'center',
        alignItems: 'center',
        padding: '32px 16px',
      }}
    >
      {/* Brand Header */}
      <div style={{ textAlign: 'center', marginBottom: '28px' }}>
        <div
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            justifyContent: 'center',
            width: '54px',
            height: '54px',
            backgroundColor: '#1e3a5f',
            borderRadius: '14px',
            marginBottom: '12px',
            boxShadow: '0 4px 12px rgba(30, 58, 95, 0.25)',
          }}
        >
          <Dna className="w-8 h-8 text-emerald-400" style={{ color: '#34d399' }} />
        </div>
        <h1
          style={{
            fontSize: '24px',
            fontWeight: 800,
            color: '#1e3a5f',
            margin: '0 0 4px 0',
            letterSpacing: '-0.02em',
          }}
        >
          GreenSynth Analytics
        </h1>
        <p style={{ fontSize: '14px', color: '#6c757d', margin: 0 }}>
          Semiconductor Phytochemical Synthesis & ML Platform
        </p>
      </div>

      {/* Login Card */}
      <div
        style={{
          width: '100%',
          maxWidth: '440px',
          backgroundColor: '#ffffff',
          borderRadius: '12px',
          border: '1px solid #dee2e6',
          boxShadow: '0 8px 24px rgba(0, 0, 0, 0.06)',
          padding: '32px',
        }}
      >
        <div style={{ marginBottom: '24px' }}>
          <h2
            style={{
              fontSize: '18px',
              fontWeight: 700,
              color: '#212529',
              margin: '0 0 4px 0',
            }}
          >
            Researcher Sign In
          </h2>
          <p style={{ fontSize: '13px', color: '#6c757d', margin: 0 }}>
            Enter your credentials to access your research group data.
          </p>
        </div>

        {/* Error Alert Banner */}
        {error && (
          <div
            role="alert"
            style={{
              display: 'flex',
              alignItems: 'flex-start',
              gap: '10px',
              backgroundColor: '#fde8e6',
              border: '1px solid #f5c2c7',
              borderRadius: '8px',
              padding: '12px 14px',
              marginBottom: '20px',
              color: '#842029',
              fontSize: '13px',
              lineHeight: 1.4,
            }}
          >
            <AlertCircle className="w-4 h-4" style={{ flexShrink: 0, marginTop: '2px' }} />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} noValidate>
          {/* Email Input */}
          <div style={{ marginBottom: '18px' }}>
            <label
              htmlFor="login-email"
              style={{
                display: 'block',
                fontSize: '13px',
                fontWeight: 600,
                color: '#343a40',
                marginBottom: '6px',
              }}
            >
              Institutional Email
            </label>
            <div style={{ position: 'relative' }}>
              <span
                style={{
                  position: 'absolute',
                  left: '12px',
                  top: '50%',
                  transform: 'translateY(-50%)',
                  color: '#adb5bd',
                  display: 'flex',
                  alignItems: 'center',
                }}
              >
                <Mail className="w-4 h-4" />
              </span>
              <input
                id="login-email"
                type="email"
                name="email"
                autoComplete="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="researcher@greensynth.edu"
                required
                style={{
                  width: '100%',
                  padding: '10px 12px 10px 38px',
                  fontSize: '14px',
                  borderRadius: '6px',
                  border: '1px solid #ced4da',
                  outline: 'none',
                  backgroundColor: '#ffffff',
                  color: '#212529',
                  boxSizing: 'border-box',
                }}
              />
            </div>
          </div>

          {/* Password Input */}
          <div style={{ marginBottom: '24px' }}>
            <label
              htmlFor="login-password"
              style={{
                display: 'block',
                fontSize: '13px',
                fontWeight: 600,
                color: '#343a40',
                marginBottom: '6px',
              }}
            >
              Password
            </label>
            <div style={{ position: 'relative' }}>
              <span
                style={{
                  position: 'absolute',
                  left: '12px',
                  top: '50%',
                  transform: 'translateY(-50%)',
                  color: '#adb5bd',
                  display: 'flex',
                  alignItems: 'center',
                }}
              >
                <Lock className="w-4 h-4" />
              </span>
              <input
                id="login-password"
                type={showPassword ? 'text' : 'password'}
                name="password"
                autoComplete="current-password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Enter account password"
                required
                style={{
                  width: '100%',
                  padding: '10px 38px 10px 38px',
                  fontSize: '14px',
                  borderRadius: '6px',
                  border: '1px solid #ced4da',
                  outline: 'none',
                  backgroundColor: '#ffffff',
                  color: '#212529',
                  boxSizing: 'border-box',
                }}
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                style={{
                  position: 'absolute',
                  right: '10px',
                  top: '50%',
                  transform: 'translateY(-50%)',
                  background: 'none',
                  border: 'none',
                  cursor: 'pointer',
                  color: '#6c757d',
                  padding: '4px',
                  display: 'flex',
                  alignItems: 'center',
                }}
                aria-label={showPassword ? 'Hide password' : 'Show password'}
              >
                {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              </button>
            </div>
          </div>

          {/* Submit Button */}
          <button
            type="submit"
            disabled={loading}
            style={{
              width: '100%',
              padding: '11px 16px',
              fontSize: '14px',
              fontWeight: 600,
              borderRadius: '6px',
              backgroundColor: '#1e3a5f',
              color: '#ffffff',
              border: 'none',
              cursor: loading ? 'not-allowed' : 'pointer',
              opacity: loading ? 0.75 : 1,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '8px',
              transition: 'background-color 150ms ease',
            }}
          >
            {loading ? (
              <span>Signing in...</span>
            ) : (
              <>
                <span>Sign In to Research Portal</span>
                <ArrowRight className="w-4 h-4" />
              </>
            )}
          </button>
        </form>

        {/* Divider */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            margin: '24px 0',
            color: '#adb5bd',
            fontSize: '12px',
          }}
        >
          <div style={{ flex: 1, height: '1px', backgroundColor: '#e9ecef' }} />
          <span style={{ padding: '0 10px', textTransform: 'uppercase', fontWeight: 600 }}>or</span>
          <div style={{ flex: 1, height: '1px', backgroundColor: '#e9ecef' }} />
        </div>

        {/* Action Links */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
          <Link
            to="/register"
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '8px',
              padding: '9px 14px',
              borderRadius: '6px',
              border: '1px solid #1e3a5f',
              color: '#1e3a5f',
              textDecoration: 'none',
              fontSize: '13px',
              fontWeight: 600,
              backgroundColor: '#ffffff',
              transition: 'all 150ms ease',
            }}
          >
            <ShieldCheck className="w-4 h-4 text-emerald-600" style={{ color: '#0f766e' }} />
            <span>Register Research Group as Leader</span>
          </Link>

          <Link
            to="/accept-invitation"
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '8px',
              padding: '9px 14px',
              borderRadius: '6px',
              border: '1px solid #dee2e6',
              color: '#495057',
              textDecoration: 'none',
              fontSize: '13px',
              fontWeight: 500,
              backgroundColor: '#f8f9fa',
            }}
          >
            <Users className="w-4 h-4 text-slate-500" />
            <span>Accept Member Invitation / Join Group</span>
          </Link>
        </div>
      </div>

      {/* Footer Info */}
      <div style={{ marginTop: '28px', textAlign: 'center', color: '#868e96', fontSize: '12px' }}>
        <p style={{ margin: '0 0 4px 0' }}>
          GreenSynth Analytics &bull; Multi-Tenant Research Isolation Active
        </p>
        <p style={{ margin: 0 }}>
          P1–P8 Phytochemical Synthesis &bull; XRD / FTIR / UV-Vis / Electrical Analysis
        </p>
      </div>
    </div>
  )
}
