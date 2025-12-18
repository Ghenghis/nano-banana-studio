/**
 * Nano Banana Studio Pro - API Client Tests
 * ==========================================
 * Comprehensive test coverage for API client functions
 */

import { describe, test, expect, vi, beforeEach } from 'vitest'
import api from './api'

// Mock fetch globally
global.fetch = vi.fn()

describe('API Client', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    global.fetch.mockReset()
  })

  describe('Timeline API', () => {
    test('quickCreate sends correct request', async () => {
      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ project_id: 'proj-123' })
      })

      const result = await api.quickCreate({
        prompt: 'Test video',
        duration: 30,
        style: 'Cinematic'
      })

      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/timeline/quick-create'),
        expect.objectContaining({ method: 'POST' })
      )
      expect(result.project_id).toBe('proj-123')
    })

    test('getPreviewGallery fetches project gallery', async () => {
      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ scenes: [] })
      })

      await api.getPreviewGallery('proj-123')

      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/proj-123/preview-gallery'),
        expect.anything()
      )
    })

    test('approveScene sends approval', async () => {
      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ approved: true })
      })

      await api.approveScene('proj-123', 0)

      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/scenes/0/approve'),
        expect.objectContaining({ method: 'POST' })
      )
    })

    test('rejectScene sends rejection with new prompt', async () => {
      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ regenerating: true })
      })

      await api.rejectScene('proj-123', 0, 'New prompt')

      expect(global.fetch).toHaveBeenCalled()
    })

    test('undo sends undo request', async () => {
      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ undone: true })
      })

      await api.undo('proj-123')

      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/undo'),
        expect.objectContaining({ method: 'POST' })
      )
    })

    test('redo sends redo request', async () => {
      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ redone: true })
      })

      await api.redo('proj-123')

      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/redo'),
        expect.objectContaining({ method: 'POST' })
      )
    })
  })

  describe('Prompt Enhancement API', () => {
    test('enhanceConcept sends enhancement request', async () => {
      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ enhanced_prompt: 'Enhanced text' })
      })

      const result = await api.enhanceConcept('Original prompt', 'Cinematic', 'YouTube')

      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/enhance/concept'),
        expect.objectContaining({ method: 'POST' })
      )
      expect(result.enhanced_prompt).toBe('Enhanced text')
    })

    test('enhanceFull runs full enhancement pipeline', async () => {
      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ enhanced_prompt: 'Fully enhanced' })
      })

      await api.enhanceFull('Prompt', 'Style', 'Platform')

      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/enhance/full'),
        expect.anything()
      )
    })
  })

  describe('Image Generation API', () => {
    test('generateImage sends generation request', async () => {
      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ job_id: 'job-123' })
      })

      const result = await api.generateImage({
        prompt: 'A beautiful sunset',
        style: 'Photorealistic'
      })

      expect(result.job_id).toBe('job-123')
    })
  })

  describe('Animation API', () => {
    test('animateImage sends animation request', async () => {
      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ job_id: 'anim-123' })
      })

      const result = await api.animateImage({
        image_path: '/image.jpg',
        motion_prompt: 'zoom in'
      })

      expect(result.job_id).toBe('anim-123')
    })
  })

  describe('Music Generation API', () => {
    test('generateMusic sends Suno request', async () => {
      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ job_id: 'music-123' })
      })

      const result = await api.generateMusic({
        prompt: 'upbeat electronic',
        style: 'electronic'
      })

      expect(result.job_id).toBe('music-123')
    })
  })

  describe('Job Management API', () => {
    test('getJob fetches job status', async () => {
      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ status: 'completed' })
      })

      const result = await api.getJob('job-123')

      expect(result.status).toBe('completed')
    })

    test('listJobs fetches all jobs', async () => {
      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve([{ id: 'job-1' }, { id: 'job-2' }])
      })

      const result = await api.listJobs()

      expect(result.length).toBe(2)
    })
  })

  describe('YouTube API', () => {
    test('getYouTubeAccounts fetches accounts', async () => {
      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ accounts: [] })
      })

      await api.getYouTubeAccounts()

      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/youtube/accounts'),
        expect.anything()
      )
    })

    test('uploadToYouTube sends upload request', async () => {
      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ video_id: 'yt-123' })
      })

      const result = await api.uploadToYouTube({
        video_path: '/video.mp4',
        title: 'Test'
      })

      expect(result.video_id).toBe('yt-123')
    })
  })

  describe('Error Handling', () => {
    test('throws error on non-ok response', async () => {
      global.fetch.mockResolvedValueOnce({
        ok: false,
        status: 500,
        json: () => Promise.resolve({ message: 'Server error' })
      })

      await expect(api.getJob('job-123')).rejects.toThrow()
    })

    test('handles network errors', async () => {
      global.fetch.mockRejectedValueOnce(new Error('Network error'))

      await expect(api.getJob('job-123')).rejects.toThrow('Network error')
    })
  })

  describe('Health API', () => {
    test('health check returns status', async () => {
      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ status: 'healthy' })
      })

      const result = await api.health()

      expect(result.status).toBe('healthy')
    })
  })
})
