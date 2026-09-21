/**
 * GreenSynth Analytics — Central Landing Page Data
 * All P1–P8 project definitions and groupings.
 * Used by ResearchPortfolioSection, HeroSection, CaseStudyDetailSection, etc.
 */

export type SynthesisMethod = 'Sol-gel' | 'Hydrothermal' | 'Spray Pyrolysis'
export type Solvent = 'Ethanol' | 'Acetone'
export type Material = 'CuO' | 'Silica/Silicon'

export interface Project {
  id: string
  title: string
  material: Material
  greenComponents: string[]
  solvent: Solvent
  method: SynthesisMethod
  description: string
  tags: string[]
  featured?: boolean
}

export const PROJECTS: Project[] = [
  {
    id: 'P1',
    title: 'CuO Synthesis Using Mulberry Extract in Ethanol by Sol-Gel',
    material: 'CuO',
    greenComponents: ['Mulberry extract'],
    solvent: 'Ethanol',
    method: 'Sol-gel',
    description: 'Sol-gel synthesis of copper oxide nanostructures using mulberry extract as a green component in ethanol solvent.',
    tags: ['CuO', 'Sol-gel', 'Ethanol'],
  },
  {
    id: 'P2',
    title: 'CuO Synthesis Using Mulberry Extract in Acetone by Sol-Gel',
    material: 'CuO',
    greenComponents: ['Mulberry extract'],
    solvent: 'Acetone',
    method: 'Sol-gel',
    description: 'Sol-gel synthesis of copper oxide using mulberry extract with acetone solvent for comparative analysis.',
    tags: ['CuO', 'Sol-gel', 'Acetone'],
  },
  {
    id: 'P3',
    title: 'CuO Synthesis Using Mulberry Extract in Ethanol by Hydrothermal Method',
    material: 'CuO',
    greenComponents: ['Mulberry extract'],
    solvent: 'Ethanol',
    method: 'Hydrothermal',
    description: 'Hydrothermal synthesis of copper oxide with mulberry extract in ethanol under controlled temperature and pressure.',
    tags: ['CuO', 'Hydrothermal', 'Ethanol'],
  },
  {
    id: 'P4',
    title: 'CuO Synthesis Using Mulberry Extract in Acetone by Hydrothermal Method',
    material: 'CuO',
    greenComponents: ['Mulberry extract'],
    solvent: 'Acetone',
    method: 'Hydrothermal',
    description: 'Hydrothermal synthesis of copper oxide with mulberry extract in acetone for solvent-effect comparison.',
    tags: ['CuO', 'Hydrothermal', 'Acetone'],
  },
  {
    id: 'P5',
    title: 'Silica/Silicon Synthesis Using Rice Husk and Mulberry Extract in Ethanol by Hydrothermal Method',
    material: 'Silica/Silicon',
    greenComponents: ['Rice husk', 'Mulberry extract'],
    solvent: 'Ethanol',
    method: 'Hydrothermal',
    description: 'Hydrothermal synthesis of silica/silicon using rice husk and mulberry extract as dual green resources in ethanol.',
    tags: ['Silica/Silicon', 'Hydrothermal', 'Ethanol', 'Rice Husk'],
  },
  {
    id: 'P6',
    title: 'Silica/Silicon Synthesis Using Rice Husk and Mulberry Extract in Acetone by Hydrothermal Method',
    material: 'Silica/Silicon',
    greenComponents: ['Rice husk', 'Mulberry extract'],
    solvent: 'Acetone',
    method: 'Hydrothermal',
    description: 'Hydrothermal synthesis of silica/silicon using rice husk and mulberry extract in acetone for solvent comparison.',
    tags: ['Silica/Silicon', 'Hydrothermal', 'Acetone', 'Rice Husk'],
  },
  {
    id: 'P7',
    title: 'Phytochemical Synthesis of Semiconducting CuO Using Mulberry Extract in Ethanol by Spray Pyrolysis',
    material: 'CuO',
    greenComponents: ['Mulberry extract'],
    solvent: 'Ethanol',
    method: 'Spray Pyrolysis',
    description: 'Spray pyrolysis deposition of semiconducting copper oxide using mulberry extract — the primary platform demonstration case.',
    tags: ['CuO', 'Spray Pyrolysis', 'Ethanol'],
    featured: true,
  },
  {
    id: 'P8',
    title: 'CuO Synthesis Using Mulberry Extract in Acetone by Spray Pyrolysis',
    material: 'CuO',
    greenComponents: ['Mulberry extract'],
    solvent: 'Acetone',
    method: 'Spray Pyrolysis',
    description: 'Spray pyrolysis synthesis of copper oxide with mulberry extract in acetone for solvent-effect investigation.',
    tags: ['CuO', 'Spray Pyrolysis', 'Acetone'],
  },
]

export interface ProjectGroup {
  id: string
  label: string
  projects: string[]
  description: string
  color: string
  bg: string
}

export const PROJECT_GROUPS: ProjectGroup[] = [
  {
    id: 'cuo',
    label: 'Copper Oxide Research',
    projects: ['P1', 'P2', 'P3', 'P4', 'P7', 'P8'],
    description:
      'Copper oxide research explores how plant-based extract conditions, solvent choice, precursor conditions, and synthesis methods influence the structural, optical, morphological, and electrical properties of CuO.',
    color: '#f59e0b',
    bg: 'rgba(245,158,11,0.1)',
  },
  {
    id: 'silica',
    label: 'Silica / Silicon Research',
    projects: ['P5', 'P6'],
    description:
      'Silica/silicon research investigates the use of rice husk and mulberry extract as green resources in hydrothermal synthesis using different solvent conditions.',
    color: '#3b9ede',
    bg: 'rgba(59,158,222,0.1)',
  },
  {
    id: 'methods',
    label: 'Synthesis Method Comparison',
    projects: ['P1', 'P2', 'P3', 'P4', 'P5', 'P6', 'P7', 'P8'],
    description:
      'The platform supports comparison between sol-gel, hydrothermal, and spray pyrolysis synthesis methods while preserving method-specific parameters and scientific requirements.',
    color: '#8b5cf6',
    bg: 'rgba(139,92,246,0.1)',
  },
  {
    id: 'solvents',
    label: 'Solvent Comparison',
    projects: ['P1', 'P2', 'P3', 'P4', 'P5', 'P6', 'P7', 'P8'],
    description:
      'The research portfolio allows researchers to study how solvent choice (ethanol vs. acetone) may influence synthesis behavior and resulting material properties.',
    color: '#34d399',
    bg: 'rgba(52,211,153,0.1)',
  },
]

export type FilterKey = 'all' | 'CuO' | 'Silica/Silicon' | 'Sol-gel' | 'Hydrothermal' | 'Spray Pyrolysis' | 'Ethanol' | 'Acetone'

export const FILTER_OPTIONS: { key: FilterKey; label: string }[] = [
  { key: 'all',            label: 'All Projects' },
  { key: 'CuO',           label: 'CuO' },
  { key: 'Silica/Silicon', label: 'Silica / Silicon' },
  { key: 'Sol-gel',        label: 'Sol-gel' },
  { key: 'Hydrothermal',   label: 'Hydrothermal' },
  { key: 'Spray Pyrolysis',label: 'Spray Pyrolysis' },
  { key: 'Ethanol',        label: 'Ethanol' },
  { key: 'Acetone',        label: 'Acetone' },
]

export function filterProjects(projects: Project[], key: FilterKey): Project[] {
  if (key === 'all') return projects
  return projects.filter((p) => {
    if (key === 'CuO' || key === 'Silica/Silicon') return p.material === key
    if (key === 'Sol-gel' || key === 'Hydrothermal' || key === 'Spray Pyrolysis') return p.method === key
    if (key === 'Ethanol' || key === 'Acetone') return p.solvent === key
    return true
  })
}
