/**
 * GreenSynth Analytics — Main Application & Routing
 */

import React from 'react'
import { BrowserRouter, Route, Routes } from 'react-router-dom'
import MainLayout from '@/layouts/MainLayout'
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

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<MainLayout />}>
          <Route index element={<Dashboard />} />
          <Route path="projects" element={<Projects />} />
          <Route path="projects/:id" element={<ProjectDetail />} />
          <Route path="experiments" element={<Experiments />} />
          <Route path="experiments/:id" element={<ExperimentDetail />} />
          <Route path="samples" element={<Samples />} />
          <Route path="samples/:id" element={<SampleDetail />} />
          <Route path="comparison" element={<SampleComparison />} />
          <Route path="ml" element={<MLDashboard />} />
          <Route path="ml/datasets/new" element={<MLDatasetBuilder />} />
          <Route path="ml/training" element={<MLModelTraining />} />
          <Route path="ml/predict" element={<MLPrediction />} />
          <Route path="ml/validation" element={<ModelValidationStudio />} />
          <Route path="validation" element={<ValidationDashboard />} />
          <Route path="validation/experimental" element={<ExperimentalValidation />} />
          <Route path="recommendations" element={<RecommendationStudio />} />
          <Route path="closed-loop" element={<ClosedLoopDashboard />} />
          <Route path="doe" element={<DOEDashboard />} />
          <Route path="statistics" element={<StatisticalAnalysisStudio />} />
          <Route path="optimization" element={<OptimizationStudio />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}
