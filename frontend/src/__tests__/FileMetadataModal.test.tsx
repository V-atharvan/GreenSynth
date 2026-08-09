import { render, screen, fireEvent } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import { FileMetadataModal } from '../components/FileMetadataModal'
import type { RawFile } from '../types'

const MOCK_RAW_FILE: RawFile = {
  id: 'file-123',
  characterization_id: 'char-456',
  sample_id: 'sample-789',
  original_filename: 'sample_xrd_spectrum.csv',
  stored_filename: 'uuid-123.csv',
  file_extension: 'csv',
  mime_type: 'text/csv',
  file_size: 2048,
  checksum: 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855',
  storage_path: 'P7/EXP-001/S-001/char-456/uuid-123.csv',
  uploaded_at: '2026-08-01T12:00:00Z',
  uploaded_by: 'Dr. Analyst',
  status: 'ACTIVE',
}

describe('FileMetadataModal', () => {
  it('renders raw file metadata including original filename and SHA-256 checksum', () => {
    const handleClose = vi.fn()
    render(<FileMetadataModal file={MOCK_RAW_FILE} onClose={handleClose} />)

    expect(screen.getByText('sample_xrd_spectrum.csv')).toBeDefined()
    expect(screen.getByText('.CSV (text/csv)')).toBeDefined()
    expect(screen.getByText('2.00 KB')).toBeDefined()
    expect(screen.getByText('e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855')).toBeDefined()
  })
})
