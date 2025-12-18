/**
 * Nano Banana Studio Pro - WebSocket Hook
 * Real-time job progress updates via WebSocket connection
 */

import { useState, useEffect, useCallback, useRef } from 'react'

const WS_BASE = `ws://${window.location.hostname}:8000/ws`

export function useJobProgress(jobId) {
  const [progress, setProgress] = useState(0)
  const [status, setStatus] = useState('pending')
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)
  const wsRef = useRef(null)

  useEffect(() => {
    if (!jobId) return

    const ws = new WebSocket(`${WS_BASE}/${jobId}`)
    wsRef.current = ws

    ws.onopen = () => {
      console.log(`[WS] Connected to job ${jobId}`)
    }

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        
        if (data.progress !== undefined) {
          setProgress(data.progress)
        }
        if (data.status) {
          setStatus(data.status)
        }
        if (data.result) {
          setResult(data.result)
        }
        if (data.error) {
          setError(data.error)
        }
        if (data.current_stage) {
          setStatus(data.current_stage)
        }
      } catch (err) {
        console.error('[WS] Parse error:', err)
      }
    }

    ws.onerror = (err) => {
      console.error('[WS] Error:', err)
      setError('WebSocket connection error')
    }

    ws.onclose = () => {
      console.log(`[WS] Disconnected from job ${jobId}`)
    }

    return () => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.close()
      }
    }
  }, [jobId])

  const disconnect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.close()
    }
  }, [])

  return { progress, status, result, error, disconnect }
}

export function useWebSocketConnection() {
  const [connected, setConnected] = useState(false)
  const [jobs, setJobs] = useState({})
  const wsRef = useRef(null)

  const subscribe = useCallback((jobId) => {
    if (!jobId) return

    const ws = new WebSocket(`${WS_BASE}/${jobId}`)
    
    ws.onopen = () => {
      setConnected(true)
      setJobs(prev => ({ ...prev, [jobId]: { status: 'connected', progress: 0 } }))
    }

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        setJobs(prev => ({
          ...prev,
          [jobId]: { ...prev[jobId], ...data }
        }))
      } catch (err) {
        console.error('[WS] Parse error:', err)
      }
    }

    ws.onclose = () => {
      setJobs(prev => {
        const updated = { ...prev }
        delete updated[jobId]
        return updated
      })
      if (Object.keys(jobs).length <= 1) {
        setConnected(false)
      }
    }

    wsRef.current = ws
    return () => ws.close()
  }, [jobs])

  const unsubscribe = useCallback((jobId) => {
    setJobs(prev => {
      const updated = { ...prev }
      delete updated[jobId]
      return updated
    })
  }, [])

  return { connected, jobs, subscribe, unsubscribe }
}

export default useJobProgress
