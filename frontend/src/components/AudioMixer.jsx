import React, { useState } from 'react'
import { Volume2, Music, Upload, Play, Pause, Trash2, Plus } from 'lucide-react'
import api from '../api'

export default function AudioMixer({ onMixComplete }) {
  const [tracks, setTracks] = useState([])
  const [mixing, setMixing] = useState(false)
  const [mixMode, setMixMode] = useState('layer')

  const addTrack = (file) => {
    const reader = new FileReader()
    reader.onload = (e) => {
      setTracks(prev => [...prev, {
        id: Date.now(),
        name: file.name,
        file: file,
        volume: 1.0,
        preview: e.target.result
      }])
    }
    reader.readAsDataURL(file)
  }

  const removeTrack = (id) => {
    setTracks(prev => prev.filter(t => t.id !== id))
  }

  const updateVolume = (id, volume) => {
    setTracks(prev => prev.map(t =>
      t.id === id ? { ...t, volume: parseFloat(volume) } : t
    ))
  }

  const handleMix = async () => {
    if (tracks.length < 2) {
      alert('Add at least 2 tracks to mix')
      return
    }

    setMixing(true)
    try {
      const volumes = tracks.map(t => t.volume)
      const result = await api.mixAudio(
        tracks.map(t => t.file),
        volumes,
        mixMode
      )
      onMixComplete?.(result)
    } catch (err) {
      console.error('Mix failed:', err)
      alert('Failed to mix audio: ' + err.message)
    } finally {
      setMixing(false)
    }
  }

  return (
    <div className="bg-gray-800 rounded-xl p-6">
      <div className="flex items-center gap-3 mb-6">
        <Volume2 className="text-banana-400" size={24} />
        <h2 className="text-xl font-bold">Audio Mixer</h2>
      </div>

      {/* Mix Mode */}
      <div className="mb-4">
        <label className="block text-sm text-gray-400 mb-2">Mix Mode</label>
        <div className="flex gap-2">
          {['layer', 'sequence', 'ducking'].map(mode => (
            <button
              key={mode}
              onClick={() => setMixMode(mode)}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${mixMode === mode
                  ? 'bg-banana-500 text-black'
                  : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                }`}
            >
              {mode.charAt(0).toUpperCase() + mode.slice(1)}
            </button>
          ))}
        </div>
        <p className="text-xs text-gray-500 mt-1">
          {mixMode === 'layer' && 'Mix all tracks simultaneously'}
          {mixMode === 'sequence' && 'Play tracks one after another'}
          {mixMode === 'ducking' && 'Lower background when voice is present'}
        </p>
      </div>

      {/* Track List */}
      <div className="space-y-3 mb-4">
        {tracks.map((track, idx) => (
          <div key={track.id} className="flex items-center gap-3 p-3 bg-gray-700 rounded-lg">
            <div className="w-8 h-8 bg-gray-600 rounded flex items-center justify-center text-sm font-bold">
              {idx + 1}
            </div>
            <Music size={18} className="text-gray-400" />
            <div className="flex-1 min-w-0">
              <p className="text-sm truncate">{track.name}</p>
            </div>
            <div className="flex items-center gap-2 w-32">
              <Volume2 size={14} className="text-gray-400" />
              <input
                type="range"
                min="0"
                max="2"
                step="0.1"
                value={track.volume}
                onChange={(e) => updateVolume(track.id, e.target.value)}
                className="flex-1 accent-banana-500"
              />
              <span className="text-xs text-gray-400 w-8">{Math.round(track.volume * 100)}%</span>
            </div>
            <button
              onClick={() => removeTrack(track.id)}
              className="p-2 text-gray-400 hover:text-red-400 transition-colors"
            >
              <Trash2 size={16} />
            </button>
          </div>
        ))}

        {tracks.length === 0 && (
          <div className="text-center py-8 text-gray-500">
            <Music size={32} className="mx-auto mb-2 opacity-50" />
            <p>No tracks added yet</p>
          </div>
        )}
      </div>

      {/* Add Track */}
      <label className="flex items-center justify-center gap-2 p-4 border-2 border-dashed border-gray-600 rounded-lg cursor-pointer hover:border-banana-500 transition-colors mb-4">
        <Plus size={18} />
        <span>Add Audio Track</span>
        <input
          type="file"
          accept="audio/*"
          onChange={(e) => e.target.files[0] && addTrack(e.target.files[0])}
          className="hidden"
        />
      </label>

      {/* Mix Button */}
      <button
        onClick={handleMix}
        disabled={mixing || tracks.length < 2}
        className="w-full py-3 bg-banana-500 text-black font-semibold rounded-lg hover:bg-banana-400 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
      >
        {mixing ? 'Mixing...' : `Mix ${tracks.length} Tracks`}
      </button>
    </div>
  )
}
