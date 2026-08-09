import { render, screen, fireEvent } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import { DynamicParameterForm } from '../components/DynamicParameterForm'
import type { ParameterDefinition } from '../types'

const MOCK_DEFS: ParameterDefinition[] = [
  {
    id: 'def-1',
    project_id: 'p1',
    parameter_code: 'temp',
    parameter_name: 'Substrate Temperature',
    description: 'Deposition temperature',
    data_type: 'NUMBER',
    unit: '°C',
    required: true,
    minimum_value: 100,
    maximum_value: 600,
    allowed_values: null,
    status: 'ACTIVE',
    created_at: '2026-08-01T00:00:00Z',
    updated_at: '2026-08-01T00:00:00Z',
  },
  {
    id: 'def-2',
    project_id: 'p1',
    parameter_code: 'substrate',
    parameter_name: 'Substrate Type',
    description: 'Substrate material',
    data_type: 'ENUM',
    unit: null,
    required: false,
    minimum_value: null,
    maximum_value: null,
    allowed_values: ['Glass', 'FTO Glass', 'Quartz'],
    status: 'ACTIVE',
    created_at: '2026-08-01T00:00:00Z',
    updated_at: '2026-08-01T00:00:00Z',
  },
]

describe('DynamicParameterForm', () => {
  it('renders dynamic fields based on ParameterDefinitions', () => {
    const handleChange = vi.fn()
    render(
      <DynamicParameterForm
        definitions={MOCK_DEFS}
        values={{ 'def-1': { value: '350' }, 'def-2': { value: '' } }}
        onChange={handleChange}
      />
    )

    expect(screen.getByText('Substrate Temperature')).toBeDefined()
    expect(screen.getByText('Unit: °C')).toBeDefined()
    expect(screen.getByText('Range: 100 to 600 °C')).toBeDefined()
    expect(screen.getByText('Substrate Type')).toBeDefined()

    // Test input change
    const tempInput = screen.getByPlaceholderText('Enter numeric value in °C')
    fireEvent.change(tempInput, { target: { value: '400' } })
    expect(handleChange).toHaveBeenCalledWith('def-1', '400', undefined)
  })
})
