/**
 * Nano Banana Studio Pro - useWebSocket Hook Tests
 */

import { renderHook, act, waitFor } from '@testing-library/react'
import { useJobProgress, useWebSocketConnection } from '../useWebSocket'

// Mock WebSocket
class MockWebSocket {
  constructor(url) {
    this.url = url
    this.readyState = WebSocket.CONNECTING
    this.onopen = null
    this.onmessage = null
    this.onerror = null
    this.onclose = null
    
    setTimeout(() => {
      this.readyState = WebSocket.OPEN
      if (this.onopen) this.onopen()
    }, 10)
  }
  
  close() {
    this.readyState = WebSocket.CLOSED
    if (this.onclose) this.onclose()
  }
  
  send(data) {}
  
  simulateMessage(data) {
    if (this.onmessage) {
      this.onmessage({ data: JSON.stringify(data) })
    }
  }
  
  simulateError(error) {
    if (this.onerror) this.onerror(error)
  }
}

global.WebSocket = MockWebSocket

describe('useJobProgress Hook', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  describe('Initialization', () => {
    test('returns initial state', () => {
      const { result } = renderHook(() => useJobProgress(null))
      
      expect(result.current.progress).toBe(0)
      expect(result.current.status).toBe('pending')
      expect(result.current.result).toBe(null)
      expect(result.current.error).toBe(null)
    })

    test('does not connect without jobId', () => {
      const { result } = renderHook(() => useJobProgress(null))
      expect(result.current.status).toBe('pending')
    })

    test('connects when jobId provided', async () => {
      const { result } = renderHook(() => useJobProgress('job-123'))
      
      await waitFor(() => {
        expect(result.current.status).toBeDefined()
      })
    })
  })

  describe('Progress Updates', () => {
    test('updates progress on message', async () => {
      let ws
      global.WebSocket = class extends MockWebSocket {
        constructor(url) {
          super(url)
          ws = this
        }
      }
      
      const { result } = renderHook(() => useJobProgress('job-123'))
      
      await waitFor(() => {
        expect(ws).toBeDefined()
      })
      
      act(() => {
        ws.simulateMessage({ progress: 0.5 })
      })
      
      expect(result.current.progress).toBe(0.5)
    })

    test('updates status on message', async () => {
      let ws
      global.WebSocket = class extends MockWebSocket {
        constructor(url) {
          super(url)
          ws = this
        }
      }
      
      const { result } = renderHook(() => useJobProgress('job-123'))
      
      await waitFor(() => {
        expect(ws).toBeDefined()
      })
      
      act(() => {
        ws.simulateMessage({ status: 'processing' })
      })
      
      expect(result.current.status).toBe('processing')
    })

    test('updates result on completion', async () => {
      let ws
      global.WebSocket = class extends MockWebSocket {
        constructor(url) {
          super(url)
          ws = this
        }
      }
      
      const { result } = renderHook(() => useJobProgress('job-123'))
      
      await waitFor(() => {
        expect(ws).toBeDefined()
      })
      
      act(() => {
        ws.simulateMessage({ 
          status: 'completed',
          result: { video_path: '/output/video.mp4' }
        })
      })
      
      expect(result.current.status).toBe('completed')
      expect(result.current.result).toEqual({ video_path: '/output/video.mp4' })
    })
  })

  describe('Error Handling', () => {
    test('sets error on WebSocket error', async () => {
      let ws
      global.WebSocket = class extends MockWebSocket {
        constructor(url) {
          super(url)
          ws = this
        }
      }
      
      const { result } = renderHook(() => useJobProgress('job-123'))
      
      await waitFor(() => {
        expect(ws).toBeDefined()
      })
      
      act(() => {
        ws.simulateError(new Error('Connection failed'))
      })
      
      expect(result.current.error).toBeDefined()
    })

    test('handles malformed JSON gracefully', async () => {
      let ws
      global.WebSocket = class extends MockWebSocket {
        constructor(url) {
          super(url)
          ws = this
        }
      }
      
      const { result } = renderHook(() => useJobProgress('job-123'))
      
      await waitFor(() => {
        expect(ws).toBeDefined()
      })
      
      act(() => {
        if (ws.onmessage) {
          ws.onmessage({ data: 'not valid json' })
        }
      })
      
      // Should not crash
      expect(result.current.progress).toBe(0)
    })
  })

  describe('Cleanup', () => {
    test('closes connection on unmount', async () => {
      let ws
      global.WebSocket = class extends MockWebSocket {
        constructor(url) {
          super(url)
          ws = this
        }
      }
      
      const { unmount } = renderHook(() => useJobProgress('job-123'))
      
      await waitFor(() => {
        expect(ws).toBeDefined()
      })
      
      unmount()
      
      expect(ws.readyState).toBe(WebSocket.CLOSED)
    })

    test('disconnect function works', async () => {
      let ws
      global.WebSocket = class extends MockWebSocket {
        constructor(url) {
          super(url)
          ws = this
        }
      }
      
      const { result } = renderHook(() => useJobProgress('job-123'))
      
      await waitFor(() => {
        expect(ws).toBeDefined()
        expect(ws.readyState).toBe(WebSocket.OPEN)
      })
      
      act(() => {
        result.current.disconnect()
      })
      
      expect(ws.readyState).toBe(WebSocket.CLOSED)
    })
  })

  describe('Job ID Changes', () => {
    test('reconnects on jobId change', async () => {
      const connections = []
      global.WebSocket = class extends MockWebSocket {
        constructor(url) {
          super(url)
          connections.push(this)
        }
      }
      
      const { rerender } = renderHook(
        ({ jobId }) => useJobProgress(jobId),
        { initialProps: { jobId: 'job-1' } }
      )
      
      await waitFor(() => {
        expect(connections.length).toBe(1)
      })
      
      rerender({ jobId: 'job-2' })
      
      await waitFor(() => {
        expect(connections.length).toBe(2)
      })
    })
  })
})

describe('useWebSocketConnection Hook', () => {
  describe('Initialization', () => {
    test('returns initial state', () => {
      const { result } = renderHook(() => useWebSocketConnection())
      
      expect(result.current.connected).toBe(false)
      expect(result.current.jobs).toEqual({})
    })
  })

  describe('Subscribe', () => {
    test('subscribes to job', async () => {
      const { result } = renderHook(() => useWebSocketConnection())
      
      act(() => {
        result.current.subscribe('job-123')
      })
      
      await waitFor(() => {
        expect(result.current.connected).toBe(true)
      })
    })

    test('tracks multiple jobs', async () => {
      const { result } = renderHook(() => useWebSocketConnection())
      
      act(() => {
        result.current.subscribe('job-1')
        result.current.subscribe('job-2')
      })
      
      await waitFor(() => {
        expect(Object.keys(result.current.jobs).length).toBeGreaterThanOrEqual(1)
      })
    })
  })

  describe('Unsubscribe', () => {
    test('removes job from tracking', async () => {
      const { result } = renderHook(() => useWebSocketConnection())
      
      act(() => {
        result.current.subscribe('job-123')
      })
      
      await waitFor(() => {
        expect(result.current.connected).toBe(true)
      })
      
      act(() => {
        result.current.unsubscribe('job-123')
      })
      
      expect(result.current.jobs['job-123']).toBeUndefined()
    })
  })
})
