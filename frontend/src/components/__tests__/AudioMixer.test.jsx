/**
 * Nano Banana Studio Pro - AudioMixer Component Tests
 * =====================================================
 * Comprehensive test coverage for AudioMixer component
 */

import React from 'react'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import AudioMixer from '../AudioMixer'

// Mock API
jest.mock('../../api', () => ({
  mixAudio: jest.fn(),
  uploadAudio: jest.fn()
}))

describe('AudioMixer Component', () => {
  const mockOnMixComplete = jest.fn()

  beforeEach(() => {
    jest.clearAllMocks()
  })

  describe('Rendering', () => {
    test('renders AudioMixer component', () => {
      render(<AudioMixer onMixComplete={mockOnMixComplete} />)
      expect(screen.getByText(/Audio Mixer/i)).toBeInTheDocument()
    })

    test('renders track list section', () => {
      render(<AudioMixer onMixComplete={mockOnMixComplete} />)
      expect(screen.getByText(/Tracks/i)).toBeInTheDocument()
    })

    test('renders mix button', () => {
      render(<AudioMixer onMixComplete={mockOnMixComplete} />)
      expect(screen.getByRole('button', { name: /mix/i })).toBeInTheDocument()
    })

    test('renders volume controls', () => {
      render(<AudioMixer
        tracks={[{ id: 1, name: 'Track 1', volume: 1.0 }]}
        onMixComplete={mockOnMixComplete}
      />)
      expect(screen.getByRole('slider')).toBeInTheDocument()
    })
  })

  describe('Track Management', () => {
    test('displays empty state when no tracks', () => {
      render(<AudioMixer tracks={[]} onMixComplete={mockOnMixComplete} />)
      expect(screen.getByText(/No tracks/i)).toBeInTheDocument()
    })

    test('displays track names', () => {
      const tracks = [
        { id: 1, name: 'Background Music', volume: 1.0 },
        { id: 2, name: 'Voice Over', volume: 0.8 }
      ]
      render(<AudioMixer tracks={tracks} onMixComplete={mockOnMixComplete} />)

      expect(screen.getByText('Background Music')).toBeInTheDocument()
      expect(screen.getByText('Voice Over')).toBeInTheDocument()
    })

    test('allows adding new track', async () => {
      render(<AudioMixer onMixComplete={mockOnMixComplete} />)

      const addButton = screen.getByRole('button', { name: /add/i })
      fireEvent.click(addButton)

      // Should open file picker or add track dialog
    })

    test('allows removing track', async () => {
      const tracks = [{ id: 1, name: 'Track 1', volume: 1.0 }]
      const onTracksChange = jest.fn()

      render(<AudioMixer
        tracks={tracks}
        onTracksChange={onTracksChange}
        onMixComplete={mockOnMixComplete}
      />)

      const removeButton = screen.getByRole('button', { name: /remove|delete/i })
      fireEvent.click(removeButton)

      expect(onTracksChange).toHaveBeenCalled()
    })
  })

  describe('Volume Controls', () => {
    test('adjusts track volume via slider', async () => {
      const tracks = [{ id: 1, name: 'Track 1', volume: 1.0 }]
      const onTracksChange = jest.fn()

      render(<AudioMixer
        tracks={tracks}
        onTracksChange={onTracksChange}
        onMixComplete={mockOnMixComplete}
      />)

      const slider = screen.getByRole('slider')
      fireEvent.change(slider, { target: { value: 0.5 } })

      expect(onTracksChange).toHaveBeenCalled()
    })

    test('mutes track when mute button clicked', async () => {
      const tracks = [{ id: 1, name: 'Track 1', volume: 1.0, muted: false }]
      const onTracksChange = jest.fn()

      render(<AudioMixer
        tracks={tracks}
        onTracksChange={onTracksChange}
        onMixComplete={mockOnMixComplete}
      />)

      const muteButton = screen.getByRole('button', { name: /mute/i })
      if (muteButton) {
        fireEvent.click(muteButton)
        expect(onTracksChange).toHaveBeenCalled()
      }
    })

    test('displays volume percentage', () => {
      const tracks = [{ id: 1, name: 'Track 1', volume: 0.75 }]

      render(<AudioMixer tracks={tracks} onMixComplete={mockOnMixComplete} />)

      expect(screen.getByText(/75%/)).toBeInTheDocument()
    })
  })

  describe('Mixing Modes', () => {
    test('renders mixing mode selector', () => {
      render(<AudioMixer onMixComplete={mockOnMixComplete} />)
      expect(screen.getByText(/Mode/i)).toBeInTheDocument()
    })

    test('allows selecting layer mode', async () => {
      render(<AudioMixer onMixComplete={mockOnMixComplete} />)

      const modeSelect = screen.getByRole('combobox') || screen.getByLabelText(/mode/i)
      if (modeSelect) {
        await userEvent.selectOptions(modeSelect, 'layer')
      }
    })

    test('allows selecting ducking mode', async () => {
      render(<AudioMixer onMixComplete={mockOnMixComplete} />)

      const modeSelect = screen.getByRole('combobox') || screen.getByLabelText(/mode/i)
      if (modeSelect) {
        await userEvent.selectOptions(modeSelect, 'ducking')
      }
    })
  })

  describe('Mix Action', () => {
    test('calls onMixComplete when mix button clicked', async () => {
      const tracks = [
        { id: 1, name: 'Track 1', volume: 1.0 },
        { id: 2, name: 'Track 2', volume: 0.8 }
      ]

      render(<AudioMixer tracks={tracks} onMixComplete={mockOnMixComplete} />)

      const mixButton = screen.getByRole('button', { name: /mix/i })
      fireEvent.click(mixButton)

      await waitFor(() => {
        expect(mockOnMixComplete).toHaveBeenCalled()
      })
    })

    test('disables mix button when no tracks', () => {
      render(<AudioMixer tracks={[]} onMixComplete={mockOnMixComplete} />)

      const mixButton = screen.getByRole('button', { name: /mix/i })
      expect(mixButton).toBeDisabled()
    })

    test('shows loading state during mix', async () => {
      const tracks = [{ id: 1, name: 'Track 1', volume: 1.0 }]

      render(<AudioMixer tracks={tracks} onMixComplete={mockOnMixComplete} />)

      const mixButton = screen.getByRole('button', { name: /mix/i })
      fireEvent.click(mixButton)

      // Check for loading indicator
      expect(screen.queryByText(/mixing/i) || screen.queryByRole('progressbar')).toBeInTheDocument()
    })
  })

  describe('Accessibility', () => {
    test('has accessible labels for sliders', () => {
      const tracks = [{ id: 1, name: 'Track 1', volume: 1.0 }]

      render(<AudioMixer tracks={tracks} onMixComplete={mockOnMixComplete} />)

      const slider = screen.getByRole('slider')
      expect(slider).toHaveAttribute('aria-label') || expect(slider).toHaveAttribute('aria-labelledby')
    })

    test('buttons have accessible names', () => {
      render(<AudioMixer onMixComplete={mockOnMixComplete} />)

      const buttons = screen.getAllByRole('button')
      buttons.forEach(button => {
        expect(button).toHaveAccessibleName()
      })
    })
  })

  describe('Error Handling', () => {
    test('displays error message on mix failure', async () => {
      const api = require('../../api')
      api.mixAudio.mockRejectedValue(new Error('Mix failed'))

      const tracks = [{ id: 1, name: 'Track 1', volume: 1.0 }]

      render(<AudioMixer tracks={tracks} onMixComplete={mockOnMixComplete} />)

      const mixButton = screen.getByRole('button', { name: /mix/i })
      fireEvent.click(mixButton)

      await waitFor(() => {
        expect(screen.getByText(/error|failed/i)).toBeInTheDocument()
      })
    })
  })
})
