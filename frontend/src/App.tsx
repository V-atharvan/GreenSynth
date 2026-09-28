/**
 * GreenSynth Analytics — Main Application & Routing
 *
 * Configures Public and Protected routes with AuthProvider, ProjectProvider, and ProtectedRoute guards.
 */

import React from 'react'
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import { AuthProvider, useAuth } from '@/context/AuthContext'
import { ProjectProvider } from '@/context/ProjectContext'
import ProtectedRoute from '@/components/ProtectedRoute'
import AdminRoute from '@/components/AdminRoute'
import MainLayout from '@/layouts/MainLayout'
import LandingPage from '@/pages/landing/LandingPage'
import Login from '@/pages/Login'
import Register from '@/pages/Register'
import AcceptInvitation from '@/pages/AcceptInvitation'
import Unauthorized from '@/pages/Unauthorized'
import Dashboard from '@/pages/Dashboard'
import Projects from '@/pages/Projects'
import ProjectDetail from '@/pages/ProjectDetail'
import Experiments from '@/pages/Experiments'
import ExperimentDetail from '@/pages/ExperimentDetail'
import Samples from '@/pages/Samples'
import SampleDetail from '@/pages/SampleDetail'
import { SampleComparison } from '@/pages/SampleComparison'
import MLDashboard from '@/pages/MLDashboard'
import MLDatasetBuilder from '@/pages/MLDatasetBuilder'
import MLModelTraining from '@/pages/MLModelTraining'
import MLPrediction from '@/pages/MLPrediction'
import ModelValidationStudio from '@/pages/ModelValidationStudio'
import ValidationDashboard from '@/pages/ValidationDashboard'
import ExperimentalValidation from '@/pages/ExperimentalValidation'
import RecommendationStudio from '@/pages/RecommendationStudio'
import ClosedLoopDashboard from '@/pages/ClosedLoopDashboard'
import { DOEDashboard } from '@/pages/DOEDashboard'
import { StatisticalAnalysisStudio } from '@/pages/StatisticalAnalysisStudio'
import OptimizationStudio from '@/pages/OptimizationStudio'
import AdminDashboard from '@/pages/admin/AdminDashboard'
import Settings from '@/pages/Settings'
import Profile from '@/pages/Profile'

function RootRedirect() {
  const { isAdmin } = useAuth()
  return isAdmin ? <Navigate to="/admin" replace /> : <Navigate to="/dashboard" replace />
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <ProjectProvider>
          <Routes>
            {/* ── Public Landing Page ────────────────────────────────── */}
            <Route path="/" element={<LandingPage />} />

            {/* ── Public Authentication Routes ───────────────────────── */}
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<Register />} />
            <Route path="/accept-invitation" element={<AcceptInvitation />} />
            <Route path="/invite/accept/:token" element={<AcceptInvitation />} />
            <Route path="/invite/accept" element={<AcceptInvitation />} />
            <Route path="/unauthorized" element={<Unauthorized />} />

            {/* ── Protected Research Platform Routes ─────────────────── */}
            <Route element={<ProtectedRoute />}>
              <Route element={<MainLayout />}>
                <Route path="/dashboard" element={<Dashboard />} />
                <Route path="/student" element={<Dashboard />} />
                <Route
                  path="/admin"
                  element={
                    <AdminRoute>
                      <AdminDashboard />
                    </AdminRoute>
                  }
                />
                <Route
                  path="/admin/*"
                  element={
                    <AdminRoute>
                      <AdminDashboard />
                    </AdminRoute>
                  }
                />
                <Route path="/projects" element={<Projects />} />
                <Route path="/projects/:id" element={<ProjectDetail />} />
                <Route path="/experiments" element={<Experiments />} />
                <Route path="/experiments/:id" element={<ExperimentDetail />} />
                <Route path="/samples" element={<Samples />} />
                <Route path="/samples/:id" element={<SampleDetail />} />
                <Route path="/comparison" element={<SampleComparison />} />
                <Route path="/ml" element={<MLDashboard />} />
                <Route path="/ml/datasets/new" element={<MLDatasetBuilder />} />
                <Route path="/ml/training" element={<MLModelTraining />} />
                <Route path="/ml/predict" element={<MLPrediction />} />
                <Route path="/ml/validation" element={<ModelValidationStudio />} />
                <Route path="/validation" element={<ValidationDashboard />} />
                <Route path="/validation/experimental" element={<ExperimentalValidation />} />
                <Route path="/recommendations" element={<RecommendationStudio />} />
                <Route path="/closed-loop" element={<ClosedLoopDashboard />} />
                <Route path="/doe" element={<DOEDashboard />} />
                <Route path="/statistics" element={<StatisticalAnalysisStudio />} />
                <Route path="/optimization" element={<OptimizationStudio />} />
                <Route path="/settings" element={<Settings />} />
                <Route path="/profile" element={<Profile />} />

                {/* Legacy /app/* aliases for seamless backwards compatibility */}
                <Route path="/app" element={<RootRedirect />} />
                <Route path="/app/admin" element={<Navigate to="/admin" replace />} />
                <Route path="/app/admin/*" element={<Navigate to="/admin" replace />} />
                <Route path="/app/dashboard" element={<Navigate to="/dashboard" replace />} />
                <Route path="/app/student" element={<Navigate to="/dashboard" replace />} />
                <Route path="/app/projects" element={<Navigate to="/projects" replace />} />
                <Route path="/app/projects/:id" element={<Navigate to="/projects" replace />} />
                <Route path="/app/experiments" element={<Navigate to="/experiments" replace />} />
                <Route path="/app/samples" element={<Navigate to="/samples" replace />} />
                <Route path="/app/comparison" element={<Navigate to="/comparison" replace />} />
                <Route path="/app/ml" element={<Navigate to="/ml" replace />} />
                <Route path="/app/validation" element={<Navigate to="/validation" replace />} />
                <Route path="/app/recommendations" element={<Navigate to="/recommendations" replace />} />
                <Route path="/app/closed-loop" element={<Navigate to="/closed-loop" replace />} />
                <Route path="/app/doe" element={<Navigate to="/doe" replace />} />
                <Route path="/app/statistics" element={<Navigate to="/statistics" replace />} />
                <Route path="/app/optimization" element={<Navigate to="/optimization" replace />} />
                <Route path="/app/settings" element={<Navigate to="/settings" replace />} />
                <Route path="/app/profile" element={<Navigate to="/profile" replace />} />
              </Route>
            </Route>

            {/* ── Catch-All Fallback (Prevents blank white screens on unknown paths) ── */}
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </ProjectProvider>
      </AuthProvider>
    </BrowserRouter>
  )
}
