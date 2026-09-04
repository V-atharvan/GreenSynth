/**
 * GreenSynth Analytics — Research Project Context & Provider
 *
 * Exposes the authenticated user's assigned research group and project context (P1–P8).
 * - Students: Strictly bound to their assigned group and project.
 * - Admin: System-wide access to all 8 projects with project switcher capability.
 */

import React, { createContext, useContext, useEffect, useState, useCallback, useMemo } from 'react'
import { useAuth } from '@/context/AuthContext'
import { projectService } from '@/services/projectService'
import type { MembershipRead, ProjectSummary } from '@/types'

export interface ProjectContextValue {
  /** The full project summary for the active project */
  project: ProjectSummary | null
  /** The unique UUID of the active project */
  projectId: string | null
  /** The project code (e.g. "P1"–"P8") */
  projectCode: string | null
  /** The human-readable synthesis project name */
  projectName: string | null
  /** The user's active research group membership */
  group: MembershipRead | null
  /** The research group ID */
  groupId: string | null
  /** The research group name */
  groupName: string | null
  /** Whether the user is the leader of this group */
  isGroupLeader: boolean
  /** Whether the user has an active group & project membership */
  hasGroupMembership: boolean
  /** All available projects (populated for Admin) */
  allProjects: ProjectSummary[]
  /** Admin active project selector */
  selectAdminProject: (projectId: string) => void
  /** Loading state during project resolution */
  isLoading: boolean
  /** Error message if project resolution fails */
  error: string | null
  /** Manually refresh project metadata */
  refreshProject: () => Promise<void>
}

const ProjectContext = createContext<ProjectContextValue | undefined>(undefined)

export const ProjectProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { user, activeMembership, isAuthenticated, isAdmin, isLoading: authLoading } = useAuth()

  const [project, setProject] = useState<ProjectSummary | null>(null)
  const [allProjects, setAllProjects] = useState<ProjectSummary[]>([])
  const [adminSelectedProjectId, setAdminSelectedProjectId] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState<boolean>(true)
  const [error, setError] = useState<string | null>(null)

  const studentProjectId = activeMembership?.project_id ?? null
  const studentProjectCode = activeMembership?.project_code ?? null
  const groupName = activeMembership?.group_name ?? null
  const groupId = activeMembership?.group_id ?? null
  const isGroupLeader = activeMembership?.is_leader ?? false
  const hasGroupMembership = isAdmin || (!!activeMembership && !!studentProjectId)

  const effectiveProjectId = isAdmin ? (adminSelectedProjectId || project?.id || null) : studentProjectId

  const refreshProject = useCallback(async () => {
    if (!isAuthenticated) {
      setProject(null)
      setAllProjects([])
      setIsLoading(false)
      return
    }

    setIsLoading(true)
    setError(null)

    try {
      if (isAdmin) {
        const projects = await projectService.getAll()
        setAllProjects(projects)
        if (adminSelectedProjectId) {
          // Admin has explicitly selected a specific project
          const selected = projects.find((p: ProjectSummary) => p.id === adminSelectedProjectId) || null
          setProject(selected)
        } else {
          // Default: "All Projects" — no specific project selected
          setProject(null)
        }
      } else if (studentProjectId) {
        const proj = await projectService.getById(studentProjectId)
        setProject(proj)
      }
    } catch (err: any) {
      if (studentProjectCode && studentProjectId) {
        setProject({
          id: studentProjectId,
          project_code: studentProjectCode,
          name:
            (activeMembership as any)?.project_name ||
            (activeMembership as any)?.group?.project?.name ||
            (groupName ? `${studentProjectCode} — ${groupName}` : `Project ${studentProjectCode}`),
          material: '',
          synthesis_method: '',
          status: 'ACTIVE',
          created_at: activeMembership?.joined_at || new Date().toISOString(),
        })
      } else {
        setError(err?.message || 'Failed to resolve assigned project context.')
      }
    } finally {
      setIsLoading(false)
    }
  }, [isAuthenticated, isAdmin, studentProjectId, studentProjectCode, groupName, activeMembership, adminSelectedProjectId])

  useEffect(() => {
    if (authLoading) return
    refreshProject()
  }, [authLoading, refreshProject])

  const selectAdminProject = useCallback(
    (newProjectId: string) => {
      if (!isAdmin) return
      if (!newProjectId || newProjectId === 'all') {
        // "All Projects" — system-wide view
        setAdminSelectedProjectId(null)
        setProject(null)
      } else {
        setAdminSelectedProjectId(newProjectId)
        const found = allProjects.find((p: ProjectSummary) => p.id === newProjectId)
        if (found) {
          setProject(found)
        }
      }
    },
    [isAdmin, allProjects]
  )

  const value = useMemo<ProjectContextValue>(
    () => ({
      project,
      projectId: project?.id ?? effectiveProjectId,
      projectCode: project?.project_code ?? studentProjectCode,
      projectName:
        project?.name ??
        (activeMembership as any)?.project_name ??
        (activeMembership as any)?.group?.project?.name ??
        (studentProjectCode ? `Project ${studentProjectCode}` : null),
      group: activeMembership,
      groupId,
      groupName,
      isGroupLeader,
      hasGroupMembership,
      allProjects,
      selectAdminProject,
      isLoading: authLoading || isLoading,
      error,
      refreshProject,
    }),
    [
      project,
      effectiveProjectId,
      studentProjectCode,
      activeMembership,
      groupId,
      groupName,
      isGroupLeader,
      hasGroupMembership,
      allProjects,
      selectAdminProject,
      authLoading,
      isLoading,
      error,
      refreshProject,
    ]
  )

  return <ProjectContext.Provider value={value}>{children}</ProjectContext.Provider>
}

export function useProjectContext(): ProjectContextValue {
  const context = useContext(ProjectContext)
  if (!context) {
    throw new Error('useProjectContext must be used within a ProjectProvider')
  }
  return context
}

export default ProjectContext
