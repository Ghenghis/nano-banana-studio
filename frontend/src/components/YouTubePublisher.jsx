import React, { useState, useEffect } from 'react'
import { Youtube, Upload, Check, AlertCircle, Settings, Eye, EyeOff } from 'lucide-react'
import api from '../api'

export default function YouTubePublisher({ videoPath, projectTitle, onPublished }) {
  const [accounts, setAccounts] = useState([])
  const [selectedAccount, setSelectedAccount] = useState(null)
  const [metadata, setMetadata] = useState({
    title: projectTitle || '',
    description: '',
    tags: [],
    category: '22', // People & Blogs
    privacy: 'private'
  })
  const [loading, setLoading] = useState(false)
  const [generating, setGenerating] = useState(false)
  const [uploadProgress, setUploadProgress] = useState(0)
  const [error, setError] = useState(null)

  useEffect(() => {
    loadAccounts()
  }, [])

  const loadAccounts = async () => {
    try {
      const result = await api.getYouTubeAccounts()
      setAccounts(result.accounts || [])
      if (result.accounts?.length > 0) {
        setSelectedAccount(result.accounts[0].id)
      }
    } catch (err) {
      console.error('Failed to load accounts:', err)
    }
  }

  const generateMetadata = async () => {
    setGenerating(true)
    try {
      const result = await api.generateYouTubeMetadata(
        metadata.title,
        metadata.description,
        metadata.category
      )

      setMetadata(prev => ({
        ...prev,
        title: result.title || prev.title,
        description: result.description || prev.description,
        tags: result.tags || prev.tags
      }))
    } catch (err) {
      console.error('Failed to generate metadata:', err)
    } finally {
      setGenerating(false)
    }
  }

  const handlePublish = async () => {
    if (!selectedAccount) {
      setError('Please select a YouTube account')
      return
    }
    if (!metadata.title) {
      setError('Please enter a video title')
      return
    }

    setLoading(true)
    setError(null)
    setUploadProgress(0)

    try {
      const result = await api.uploadToYouTube({
        video_path: videoPath,
        account_id: selectedAccount,
        title: metadata.title,
        description: metadata.description,
        tags: metadata.tags,
        category: metadata.category,
        privacy: metadata.privacy
      })

      // Poll for upload progress
      const pollProgress = async () => {
        try {
          const status = await api.getJob(result.job_id)
          if (status.status === 'completed') {
            setUploadProgress(100)
            onPublished?.(status.result)
          } else if (status.status === 'failed') {
            setError(status.error || 'Upload failed')
          } else {
            setUploadProgress(status.progress * 100 || 0)
            setTimeout(pollProgress, 2000)
          }
        } catch (err) {
          setError(err.message)
        }
      }

      pollProgress()
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const categories = [
    { id: '1', name: 'Film & Animation' },
    { id: '2', name: 'Autos & Vehicles' },
    { id: '10', name: 'Music' },
    { id: '15', name: 'Pets & Animals' },
    { id: '17', name: 'Sports' },
    { id: '20', name: 'Gaming' },
    { id: '22', name: 'People & Blogs' },
    { id: '23', name: 'Comedy' },
    { id: '24', name: 'Entertainment' },
    { id: '25', name: 'News & Politics' },
    { id: '26', name: 'Howto & Style' },
    { id: '27', name: 'Education' },
    { id: '28', name: 'Science & Technology' }
  ]

  return (
    <div className="bg-gray-800 rounded-xl p-6">
      <div className="flex items-center gap-3 mb-6">
        <Youtube className="text-red-500" size={24} />
        <h2 className="text-xl font-bold">Publish to YouTube</h2>
      </div>

      {error && (
        <div className="mb-4 p-3 bg-red-900/50 border border-red-500 rounded-lg flex items-center gap-2 text-red-300">
          <AlertCircle size={18} />
          <span>{error}</span>
        </div>
      )}

      <div className="space-y-4">
        {/* Account Selection */}
        <div>
          <label className="block text-sm text-gray-400 mb-2">YouTube Account</label>
          {accounts.length === 0 ? (
            <div className="p-3 bg-gray-700 rounded-lg text-center">
              <p className="text-gray-400 mb-2">No accounts connected</p>
              <button className="text-banana-400 hover:underline text-sm">
                Connect YouTube Account
              </button>
            </div>
          ) : (
            <select
              value={selectedAccount || ''}
              onChange={(e) => setSelectedAccount(e.target.value)}
              className="w-full bg-gray-700 rounded-lg px-4 py-2 text-white focus:ring-2 focus:ring-banana-500 focus:outline-none"
            >
              {accounts.map(acc => (
                <option key={acc.id} value={acc.id}>{acc.name || acc.email}</option>
              ))}
            </select>
          )}
        </div>

        {/* Title */}
        <div>
          <label className="block text-sm text-gray-400 mb-2">Video Title</label>
          <input
            type="text"
            value={metadata.title}
            onChange={(e) => setMetadata(prev => ({ ...prev, title: e.target.value }))}
            maxLength={100}
            className="w-full bg-gray-700 rounded-lg px-4 py-2 text-white focus:ring-2 focus:ring-banana-500 focus:outline-none"
            placeholder="Enter video title..."
          />
          <p className="text-xs text-gray-500 mt-1">{metadata.title.length}/100 characters</p>
        </div>

        {/* Description */}
        <div>
          <div className="flex items-center justify-between mb-2">
            <label className="text-sm text-gray-400">Description</label>
            <button
              onClick={generateMetadata}
              disabled={generating}
              className="text-xs text-banana-400 hover:underline flex items-center gap-1"
            >
              <Settings size={12} className={generating ? 'animate-spin' : ''} />
              AI Generate
            </button>
          </div>
          <textarea
            value={metadata.description}
            onChange={(e) => setMetadata(prev => ({ ...prev, description: e.target.value }))}
            rows={4}
            className="w-full bg-gray-700 rounded-lg px-4 py-2 text-white focus:ring-2 focus:ring-banana-500 focus:outline-none resize-none"
            placeholder="Enter video description..."
          />
        </div>

        {/* Tags */}
        <div>
          <label className="block text-sm text-gray-400 mb-2">Tags (comma separated)</label>
          <input
            type="text"
            value={metadata.tags.join(', ')}
            onChange={(e) => setMetadata(prev => ({
              ...prev,
              tags: e.target.value.split(',').map(t => t.trim()).filter(Boolean)
            }))}
            className="w-full bg-gray-700 rounded-lg px-4 py-2 text-white focus:ring-2 focus:ring-banana-500 focus:outline-none"
            placeholder="ai, video, nano banana..."
          />
        </div>

        {/* Category & Privacy */}
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm text-gray-400 mb-2">Category</label>
            <select
              value={metadata.category}
              onChange={(e) => setMetadata(prev => ({ ...prev, category: e.target.value }))}
              className="w-full bg-gray-700 rounded-lg px-4 py-2 text-white focus:ring-2 focus:ring-banana-500 focus:outline-none"
            >
              {categories.map(cat => (
                <option key={cat.id} value={cat.id}>{cat.name}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm text-gray-400 mb-2">Privacy</label>
            <select
              value={metadata.privacy}
              onChange={(e) => setMetadata(prev => ({ ...prev, privacy: e.target.value }))}
              className="w-full bg-gray-700 rounded-lg px-4 py-2 text-white focus:ring-2 focus:ring-banana-500 focus:outline-none"
            >
              <option value="private">🔒 Private</option>
              <option value="unlisted">🔗 Unlisted</option>
              <option value="public">🌍 Public</option>
            </select>
          </div>
        </div>

        {/* Progress Bar */}
        {uploadProgress > 0 && uploadProgress < 100 && (
          <div className="mt-4">
            <div className="flex justify-between text-sm text-gray-400 mb-1">
              <span>Uploading...</span>
              <span>{Math.round(uploadProgress)}%</span>
            </div>
            <div className="w-full bg-gray-700 rounded-full h-2">
              <div
                className="bg-red-500 h-2 rounded-full transition-all duration-300"
                style={{ width: `${uploadProgress}%` }}
              />
            </div>
          </div>
        )}

        {/* Publish Button */}
        <button
          onClick={handlePublish}
          disabled={loading || !selectedAccount || !metadata.title}
          className="w-full py-3 bg-red-600 text-white font-semibold rounded-lg hover:bg-red-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center justify-center gap-2"
        >
          {loading ? (
            <>Uploading...</>
          ) : uploadProgress === 100 ? (
            <><Check size={18} /> Published!</>
          ) : (
            <><Upload size={18} /> Publish to YouTube</>
          )}
        </button>
      </div>
    </div>
  )
}
