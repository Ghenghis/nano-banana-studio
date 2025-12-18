import React from 'react'
import { Loader2, CheckCircle, XCircle, Clock } from 'lucide-react'

export function ProgressBar({ progress, status, showPercentage = true, size = 'md' }) {
  const heights = { sm: 'h-1', md: 'h-2', lg: 'h-3' }
  const height = heights[size] || heights.md

  const statusColors = {
    pending: 'bg-gray-500',
    processing: 'bg-banana-500',
    completed: 'bg-green-500',
    failed: 'bg-red-500'
  }

  return (
    <div className="w-full">
      <div className={`w-full bg-gray-700 rounded-full ${height} overflow-hidden`}>
        <div
          className={`${height} rounded-full transition-all duration-300 ${statusColors[status] || statusColors.processing}`}
          style={{ width: `${Math.min(100, Math.max(0, progress * 100))}%` }}
        />
      </div>
      {showPercentage && (
        <div className="flex justify-between items-center mt-1 text-xs text-gray-400">
          <span className="capitalize">{status}</span>
          <span>{Math.round(progress * 100)}%</span>
        </div>
      )}
    </div>
  )
}

export function StatusBadge({ status }) {
  const config = {
    pending: { icon: Clock, color: 'text-gray-400 bg-gray-700', label: 'Pending' },
    processing: { icon: Loader2, color: 'text-banana-400 bg-banana-900/30', label: 'Processing', spin: true },
    completed: { icon: CheckCircle, color: 'text-green-400 bg-green-900/30', label: 'Complete' },
    failed: { icon: XCircle, color: 'text-red-400 bg-red-900/30', label: 'Failed' }
  }

  const { icon: Icon, color, label, spin } = config[status] || config.pending

  return (
    <span className={`inline-flex items-center gap-1.5 px-2 py-1 rounded-full text-xs font-medium ${color}`}>
      <Icon size={12} className={spin ? 'animate-spin' : ''} />
      {label}
    </span>
  )
}

export function JobProgress({ jobId, progress, status, stage, onCancel }) {
  return (
    <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          <StatusBadge status={status} />
          {stage && <span className="text-xs text-gray-500">• {stage}</span>}
        </div>
        {status === 'processing' && onCancel && (
          <button
            onClick={onCancel}
            className="text-xs text-gray-400 hover:text-red-400 transition-colors"
          >
            Cancel
          </button>
        )}
      </div>
      <ProgressBar progress={progress} status={status} />
      <p className="text-xs text-gray-500 mt-2 truncate">Job: {jobId}</p>
    </div>
  )
}

export function LoadingSpinner({ size = 'md', text }) {
  const sizes = { sm: 16, md: 24, lg: 32, xl: 48 }
  const iconSize = sizes[size] || sizes.md

  return (
    <div className="flex flex-col items-center justify-center gap-2">
      <Loader2 size={iconSize} className="animate-spin text-banana-400" />
      {text && <span className="text-sm text-gray-400">{text}</span>}
    </div>
  )
}

export function LoadingOverlay({ visible, text = 'Processing...' }) {
  if (!visible) return null

  return (
    <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50">
      <div className="bg-gray-800 rounded-xl p-8 flex flex-col items-center gap-4 shadow-xl">
        <LoadingSpinner size="xl" />
        <p className="text-lg text-white">{text}</p>
      </div>
    </div>
  )
}

export default ProgressBar
