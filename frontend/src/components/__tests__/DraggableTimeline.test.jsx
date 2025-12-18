/**
 * Nano Banana Studio Pro - DraggableTimeline Component Tests
 */

import React from 'react'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import DraggableTimeline from '../DraggableTimeline'

describe('DraggableTimeline Component', () => {
  const mockScenes = [
    { id: 1, visual_prompt: 'Scene 1', duration: 5, status: 'ready' },
    { id: 2, visual_prompt: 'Scene 2', duration: 3, status: 'ready' },
    { id: 3, visual_prompt: 'Scene 3', duration: 4, status: 'generating' }
  ]

  const mockHandlers = {
    onReorder: jest.fn(),
    onSceneSelect: jest.fn(),
    onSceneDelete: jest.fn(),
    onSceneDuplicate: jest.fn()
  }

  beforeEach(() => jest.clearAllMocks())

  describe('Rendering', () => {
    test('renders timeline component', () => {
      render(<DraggableTimeline scenes={mockScenes} {...mockHandlers} />)
      expect(screen.getByText(/Timeline/i)).toBeInTheDocument()
    })

    test('renders all scenes', () => {
      render(<DraggableTimeline scenes={mockScenes} {...mockHandlers} />)
      expect(screen.getByText(/1/)).toBeInTheDocument()
      expect(screen.getByText(/2/)).toBeInTheDocument()
      expect(screen.getByText(/3/)).toBeInTheDocument()
    })

    test('displays total duration', () => {
      render(<DraggableTimeline scenes={mockScenes} {...mockHandlers} />)
      expect(screen.getByText(/0:12/)).toBeInTheDocument()
    })

    test('displays scene count', () => {
      render(<DraggableTimeline scenes={mockScenes} {...mockHandlers} />)
      expect(screen.getByText(/3 scenes/i)).toBeInTheDocument()
    })

    test('shows empty state when no scenes', () => {
      render(<DraggableTimeline scenes={[]} {...mockHandlers} />)
      expect(screen.getByText(/No scenes/i)).toBeInTheDocument()
    })

    test('shows generating indicator for processing scenes', () => {
      render(<DraggableTimeline scenes={mockScenes} {...mockHandlers} />)
      const spinners = document.querySelectorAll('.animate-spin')
      expect(spinners.length).toBeGreaterThan(0)
    })
  })

  describe('Scene Selection', () => {
    test('calls onSceneSelect when scene clicked', () => {
      render(<DraggableTimeline scenes={mockScenes} {...mockHandlers} />)

      const sceneCards = document.querySelectorAll('[draggable="true"]')
      fireEvent.click(sceneCards[0])

      expect(mockHandlers.onSceneSelect).toHaveBeenCalledWith(mockScenes[0], 0)
    })

    test('highlights selected scene', () => {
      render(<DraggableTimeline scenes={mockScenes} {...mockHandlers} />)

      const sceneCards = document.querySelectorAll('[draggable="true"]')
      fireEvent.click(sceneCards[1])

      expect(sceneCards[1].className).toContain('ring')
    })
  })

  describe('Drag and Drop', () => {
    test('scene is draggable', () => {
      render(<DraggableTimeline scenes={mockScenes} {...mockHandlers} />)

      const sceneCards = document.querySelectorAll('[draggable="true"]')
      expect(sceneCards[0]).toHaveAttribute('draggable', 'true')
    })

    test('calls onReorder after drop', () => {
      render(<DraggableTimeline scenes={mockScenes} {...mockHandlers} />)

      const sceneCards = document.querySelectorAll('[draggable="true"]')

      const dataTransfer = { setData: jest.fn(), getData: jest.fn(() => '0'), effectAllowed: '' }

      fireEvent.dragStart(sceneCards[0], { dataTransfer })
      fireEvent.dragOver(sceneCards[2], { dataTransfer, preventDefault: () => { } })
      fireEvent.drop(sceneCards[2], { dataTransfer, preventDefault: () => { } })

      expect(mockHandlers.onReorder).toHaveBeenCalled()
    })

    test('shows drop indicator on drag over', () => {
      render(<DraggableTimeline scenes={mockScenes} {...mockHandlers} />)

      const sceneCards = document.querySelectorAll('[draggable="true"]')
      const dataTransfer = { setData: jest.fn(), getData: jest.fn(() => '0'), effectAllowed: '' }

      fireEvent.dragStart(sceneCards[0], { dataTransfer })
      fireEvent.dragOver(sceneCards[1], { dataTransfer, preventDefault: () => { } })

      expect(sceneCards[1].className).toContain('border-banana')
    })

    test('reduces opacity during drag', () => {
      render(<DraggableTimeline scenes={mockScenes} {...mockHandlers} />)

      const sceneCards = document.querySelectorAll('[draggable="true"]')
      const dataTransfer = { setData: jest.fn(), effectAllowed: '' }

      fireEvent.dragStart(sceneCards[0], { dataTransfer })

      expect(sceneCards[0].style.opacity).toBe('0.5')
    })

    test('restores opacity after drag end', () => {
      render(<DraggableTimeline scenes={mockScenes} {...mockHandlers} />)

      const sceneCards = document.querySelectorAll('[draggable="true"]')
      const dataTransfer = { setData: jest.fn(), effectAllowed: '' }

      fireEvent.dragStart(sceneCards[0], { dataTransfer })
      fireEvent.dragEnd(sceneCards[0])

      expect(sceneCards[0].style.opacity).toBe('1')
    })
  })

  describe('Scene Actions', () => {
    test('calls onSceneDuplicate when duplicate clicked', () => {
      render(<DraggableTimeline scenes={mockScenes} {...mockHandlers} />)

      const duplicateButtons = screen.getAllByTitle(/Duplicate/i)
      fireEvent.click(duplicateButtons[0])

      expect(mockHandlers.onSceneDuplicate).toHaveBeenCalledWith(0)
    })

    test('calls onSceneDelete when delete clicked', () => {
      render(<DraggableTimeline scenes={mockScenes} {...mockHandlers} />)

      const deleteButtons = screen.getAllByTitle(/Delete/i)
      fireEvent.click(deleteButtons[0])

      expect(mockHandlers.onSceneDelete).toHaveBeenCalledWith(0)
    })

    test('stops event propagation on action buttons', () => {
      render(<DraggableTimeline scenes={mockScenes} {...mockHandlers} />)

      const deleteButtons = screen.getAllByTitle(/Delete/i)
      fireEvent.click(deleteButtons[0])

      expect(mockHandlers.onSceneSelect).not.toHaveBeenCalled()
    })
  })

  describe('Playback Controls', () => {
    test('renders play button', () => {
      render(<DraggableTimeline scenes={mockScenes} {...mockHandlers} />)
      expect(document.querySelector('button svg')).toBeInTheDocument()
    })

    test('renders progress bar', () => {
      render(<DraggableTimeline scenes={mockScenes} {...mockHandlers} />)
      const progressBars = document.querySelectorAll('.bg-banana-500')
      expect(progressBars.length).toBeGreaterThan(0)
    })
  })

  describe('Time Display', () => {
    test('formats duration correctly', () => {
      const longScenes = [{ id: 1, visual_prompt: 'Long', duration: 125 }]
      render(<DraggableTimeline scenes={longScenes} {...mockHandlers} />)
      expect(screen.getByText(/2:05/)).toBeInTheDocument()
    })

    test('displays scene duration', () => {
      render(<DraggableTimeline scenes={mockScenes} {...mockHandlers} />)
      expect(screen.getByText(/0:05/)).toBeInTheDocument()
    })
  })

  describe('Preview Images', () => {
    test('displays preview image when available', () => {
      const scenesWithPreview = [{
        id: 1,
        visual_prompt: 'Scene 1',
        duration: 5,
        preview_image: '/preview/scene1.jpg'
      }]

      render(<DraggableTimeline scenes={scenesWithPreview} {...mockHandlers} />)

      const img = screen.getByRole('img')
      expect(img).toHaveAttribute('src', '/preview/scene1.jpg')
    })

    test('shows placeholder when no preview', () => {
      render(<DraggableTimeline scenes={mockScenes} {...mockHandlers} />)
      const icons = document.querySelectorAll('svg')
      expect(icons.length).toBeGreaterThan(0)
    })
  })
})
