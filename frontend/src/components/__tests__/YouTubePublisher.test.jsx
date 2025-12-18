/**
 * Nano Banana Studio Pro - YouTubePublisher Component Tests
 */

import React from 'react'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import YouTubePublisher from '../YouTubePublisher'

jest.mock('../../api', () => ({
  getYouTubeAccounts: jest.fn(),
  uploadToYouTube: jest.fn(),
  generateYouTubeMetadata: jest.fn()
}))

describe('YouTubePublisher Component', () => {
  const mockProps = {
    videoPath: '/output/video.mp4',
    projectTitle: 'Test Video',
    onPublished: jest.fn()
  }

  beforeEach(() => {
    jest.clearAllMocks()
  })

  describe('Rendering', () => {
    test('renders component', () => {
      render(<YouTubePublisher {...mockProps} />)
      expect(screen.getByText(/YouTube/i)).toBeInTheDocument()
    })

    test('renders title input', () => {
      render(<YouTubePublisher {...mockProps} />)
      expect(screen.getByPlaceholderText(/title/i)).toBeInTheDocument()
    })

    test('renders description textarea', () => {
      render(<YouTubePublisher {...mockProps} />)
      expect(screen.getByPlaceholderText(/description/i)).toBeInTheDocument()
    })

    test('renders privacy selector', () => {
      render(<YouTubePublisher {...mockProps} />)
      expect(screen.getByText(/Privacy/i)).toBeInTheDocument()
    })

    test('renders publish button', () => {
      render(<YouTubePublisher {...mockProps} />)
      expect(screen.getByRole('button', { name: /publish|upload/i })).toBeInTheDocument()
    })
  })

  describe('Form Inputs', () => {
    test('updates title on input', async () => {
      render(<YouTubePublisher {...mockProps} />)

      const titleInput = screen.getByPlaceholderText(/title/i)
      await userEvent.clear(titleInput)
      await userEvent.type(titleInput, 'New Title')

      expect(titleInput.value).toBe('New Title')
    })

    test('updates description on input', async () => {
      render(<YouTubePublisher {...mockProps} />)

      const descInput = screen.getByPlaceholderText(/description/i)
      await userEvent.type(descInput, 'Test description')

      expect(descInput.value).toContain('Test description')
    })

    test('shows character count for title', () => {
      render(<YouTubePublisher {...mockProps} />)
      expect(screen.getByText(/\/100/)).toBeInTheDocument()
    })

    test('updates tags on input', async () => {
      render(<YouTubePublisher {...mockProps} />)

      const tagsInput = screen.getByPlaceholderText(/tags/i)
      await userEvent.type(tagsInput, 'tag1, tag2, tag3')

      expect(tagsInput.value).toContain('tag1')
    })
  })

  describe('Privacy Settings', () => {
    test('allows selecting public privacy', async () => {
      render(<YouTubePublisher {...mockProps} />)

      const publicOption = screen.getByLabelText(/public/i) || screen.getByText(/Public/i)
      if (publicOption) {
        fireEvent.click(publicOption)
      }
    })

    test('allows selecting unlisted privacy', async () => {
      render(<YouTubePublisher {...mockProps} />)

      const unlistedOption = screen.getByLabelText(/unlisted/i) || screen.getByText(/Unlisted/i)
      if (unlistedOption) {
        fireEvent.click(unlistedOption)
      }
    })

    test('allows selecting private privacy', async () => {
      render(<YouTubePublisher {...mockProps} />)

      const privateOption = screen.getByLabelText(/private/i) || screen.getByText(/Private/i)
      if (privateOption) {
        fireEvent.click(privateOption)
      }
    })
  })

  describe('AI Metadata Generation', () => {
    test('has generate metadata button', () => {
      render(<YouTubePublisher {...mockProps} />)
      const genButton = screen.getByRole('button', { name: /generate|ai|magic/i })
      expect(genButton).toBeInTheDocument()
    })

    test('generates metadata on button click', async () => {
      const api = require('../../api')
      api.generateYouTubeMetadata.mockResolvedValue({
        title: 'AI Title',
        description: 'AI Description',
        tags: ['ai', 'generated']
      })

      render(<YouTubePublisher {...mockProps} />)

      const genButton = screen.getByRole('button', { name: /generate|ai|magic/i })
      fireEvent.click(genButton)

      await waitFor(() => {
        expect(api.generateYouTubeMetadata).toHaveBeenCalled()
      })
    })
  })

  describe('Publishing', () => {
    test('calls onPublished on successful upload', async () => {
      const api = require('../../api')
      api.getYouTubeAccounts.mockResolvedValue({ accounts: [{ id: '1', name: 'Test' }] })
      api.uploadToYouTube.mockResolvedValue({ video_url: 'https://youtube.com/watch?v=123' })

      render(<YouTubePublisher {...mockProps} />)

      const publishButton = screen.getByRole('button', { name: /publish|upload/i })
      fireEvent.click(publishButton)

      await waitFor(() => {
        expect(mockProps.onPublished).toHaveBeenCalled()
      })
    })

    test('shows progress during upload', async () => {
      const api = require('../../api')
      api.uploadToYouTube.mockImplementation(() => new Promise(resolve => setTimeout(resolve, 1000)))

      render(<YouTubePublisher {...mockProps} />)

      const publishButton = screen.getByRole('button', { name: /publish|upload/i })
      fireEvent.click(publishButton)

      expect(screen.queryByText(/uploading|progress/i)).toBeInTheDocument()
    })

    test('disables button during upload', async () => {
      render(<YouTubePublisher {...mockProps} />)

      const publishButton = screen.getByRole('button', { name: /publish|upload/i })
      fireEvent.click(publishButton)

      expect(publishButton).toBeDisabled()
    })
  })

  describe('Error Handling', () => {
    test('shows error on upload failure', async () => {
      const api = require('../../api')
      api.uploadToYouTube.mockRejectedValue(new Error('Upload failed'))

      render(<YouTubePublisher {...mockProps} />)

      const publishButton = screen.getByRole('button', { name: /publish|upload/i })
      fireEvent.click(publishButton)

      await waitFor(() => {
        expect(screen.getByText(/error|failed/i)).toBeInTheDocument()
      })
    })

    test('validates required fields', async () => {
      render(<YouTubePublisher {...mockProps} />)

      const titleInput = screen.getByPlaceholderText(/title/i)
      await userEvent.clear(titleInput)

      const publishButton = screen.getByRole('button', { name: /publish|upload/i })
      fireEvent.click(publishButton)

      expect(screen.getByText(/required|title/i)).toBeInTheDocument()
    })
  })

  describe('Account Selection', () => {
    test('loads accounts on mount', async () => {
      const api = require('../../api')
      api.getYouTubeAccounts.mockResolvedValue({
        accounts: [
          { id: '1', name: 'Channel 1' },
          { id: '2', name: 'Channel 2' }
        ]
      })

      render(<YouTubePublisher {...mockProps} />)

      await waitFor(() => {
        expect(api.getYouTubeAccounts).toHaveBeenCalled()
      })
    })
  })
})
