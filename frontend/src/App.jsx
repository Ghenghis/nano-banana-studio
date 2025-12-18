import React, { useState, useEffect } from 'react'
import {
  Play, Pause, SkipBack, SkipForward, Plus, Trash2, Copy,
  Wand2, Camera, Palette, Clock, Music, Type, Undo, Redo,
  Check, X, RefreshCw, Upload, Download, Youtube, Settings,
  ChevronDown, Layers, Film, Volume2, Sparkles
} from 'lucide-react'
import api from './api'
import { YouTubePublisher, CharacterManager, AudioMixer, DraggableTimeline } from './components'

// Header Component
function Header({ mode, setMode, onNewProject }) {
  return (
    <header className="bg-gray-800 border-b border-gray-700 px-6 py-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <h1 className="text-2xl font-bold text-banana-400">🍌 Nano Banana Studio Pro</h1>
          <span className="text-gray-400">Timeline Editor</span>
        </div>

        <div className="flex items-center gap-4">
          {/* Mode Toggle */}
          <div className="flex bg-gray-700 rounded-lg p-1">
            <button
              onClick={() => setMode('simple')}
              className={`px-4 py-2 rounded-md text-sm font-medium transition-colors
                ${mode === 'simple' ? 'bg-banana-500 text-black' : 'text-gray-300 hover:text-white'}`}
            >
              Simple
            </button>
            <button
              onClick={() => setMode('advanced')}
              className={`px-4 py-2 rounded-md text-sm font-medium transition-colors
                ${mode === 'advanced' ? 'bg-banana-500 text-black' : 'text-gray-300 hover:text-white'}`}
            >
              Advanced
            </button>
          </div>

          <button onClick={onNewProject} className="tool-button bg-banana-500 text-black hover:bg-banana-400">
            <Plus size={18} /> New Project
          </button>
        </div>
      </div>
    </header>
  )
}

// Quick Create Panel (Simple Mode)
function QuickCreatePanel({ onCreateProject, loading }) {
  const [prompt, setPrompt] = useState('')
  const [duration, setDuration] = useState(60)
  const [style, setStyle] = useState('Cinematic')
  const [musicPrompt, setMusicPrompt] = useState('')

  const handleCreate = () => {
    onCreateProject({ prompt, duration, style, music_prompt: musicPrompt || undefined })
  }

  return (
    <div className="bg-gray-800 rounded-xl p-6 max-w-2xl mx-auto">
      <div className="flex items-center gap-3 mb-6">
        <Sparkles className="text-banana-400" size={24} />
        <h2 className="text-xl font-bold">Quick Create - One Click Magic</h2>
      </div>

      <div className="space-y-4">
        <div>
          <label className="block text-sm text-gray-400 mb-2">What's your video about?</label>
          <textarea
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            placeholder="A magical cat exploring an enchanted forest with glowing butterflies..."
            className="w-full bg-gray-700 rounded-lg px-4 py-3 text-white placeholder-gray-500 
                     focus:ring-2 focus:ring-banana-500 focus:outline-none resize-none"
            rows={3}
          />
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm text-gray-400 mb-2">Duration (seconds)</label>
            <input
              type="number"
              value={duration}
              onChange={(e) => setDuration(Number(e.target.value))}
              className="w-full bg-gray-700 rounded-lg px-4 py-2 text-white focus:ring-2 focus:ring-banana-500 focus:outline-none"
            />
          </div>
          <div>
            <label className="block text-sm text-gray-400 mb-2">Style</label>
            <select
              value={style}
              onChange={(e) => setStyle(e.target.value)}
              className="w-full bg-gray-700 rounded-lg px-4 py-2 text-white focus:ring-2 focus:ring-banana-500 focus:outline-none"
            >
              <option>Cinematic</option>
              <option>Anime</option>
              <option>Photorealistic</option>
              <option>Fantasy</option>
              <option>Sci-Fi</option>
              <option>Vintage</option>
            </select>
          </div>
        </div>

        <div>
          <label className="block text-sm text-gray-400 mb-2">Music Style (optional)</label>
          <input
            type="text"
            value={musicPrompt}
            onChange={(e) => setMusicPrompt(e.target.value)}
            placeholder="whimsical orchestral, epic cinematic..."
            className="w-full bg-gray-700 rounded-lg px-4 py-2 text-white placeholder-gray-500 
                     focus:ring-2 focus:ring-banana-500 focus:outline-none"
          />
        </div>

        <button
          onClick={handleCreate}
          disabled={!prompt || loading}
          className="w-full py-3 bg-gradient-to-r from-banana-400 to-banana-600 text-black font-bold 
                   rounded-lg hover:from-banana-300 hover:to-banana-500 transition-all
                   disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
        >
          {loading ? (
            <><RefreshCw className="animate-spin" size={20} /> Creating...</>
          ) : (
            <><Wand2 size={20} /> Create Video</>
          )}
        </button>
      </div>
    </div>
  )
}

// Scene Card Component
function SceneCard({ scene, selected, onSelect, onApprove, onReject, onRegenerate }) {
  const statusColors = {
    pending: 'status-pending',
    generating: 'status-generating',
    ready: 'status-ready',
    approved: 'status-approved',
    error: 'status-error'
  }

  return (
    <div
      className={`scene-card ${scene.status === 'approved' ? 'approved' : ''} ${selected ? 'ring-2 ring-banana-400' : ''}`}
      onClick={() => onSelect(scene.index)}
    >
      {/* Preview Image */}
      <div className="aspect-video bg-gray-700 relative">
        {scene.preview ? (
          <img src={scene.preview} alt={`Scene ${scene.index}`} className="w-full h-full object-cover" />
        ) : (
          <div className="w-full h-full flex items-center justify-center text-gray-500">
            <Film size={32} />
          </div>
        )}

        {/* Status Badge */}
        <span className={`status-badge absolute top-2 right-2 ${statusColors[scene.status]}`}>
          {scene.status}
        </span>

        {/* Scene Number */}
        <span className="absolute top-2 left-2 bg-black/50 px-2 py-1 rounded text-xs">
          Scene {scene.index}
        </span>

        {/* Duration */}
        <span className="absolute bottom-2 right-2 bg-black/50 px-2 py-1 rounded text-xs flex items-center gap-1">
          <Clock size={12} /> {scene.duration}s
        </span>
      </div>

      {/* Info */}
      <div className="p-3">
        <p className="text-sm text-gray-300 line-clamp-2">{scene.prompt}</p>

        {/* Quick Actions */}
        {scene.status === 'ready' && (
          <div className="flex gap-2 mt-3">
            <button
              onClick={(e) => { e.stopPropagation(); onApprove(scene.index); }}
              className="flex-1 py-1.5 bg-green-600 hover:bg-green-500 rounded text-sm flex items-center justify-center gap-1"
            >
              <Check size={14} /> Approve
            </button>
            <button
              onClick={(e) => { e.stopPropagation(); onReject(scene.index); }}
              className="flex-1 py-1.5 bg-red-600 hover:bg-red-500 rounded text-sm flex items-center justify-center gap-1"
            >
              <X size={14} /> Reject
            </button>
          </div>
        )}

        {scene.status === 'approved' && (
          <div className="mt-3 text-green-400 text-sm flex items-center gap-1">
            <Check size={14} /> Approved
          </div>
        )}
      </div>
    </div>
  )
}

// Scene Gallery Component
function SceneGallery({ project, onApprove, onReject, onApproveAll, selectedScene, setSelectedScene }) {
  if (!project || !project.scenes) return null

  const readyCount = project.scenes.filter(s => s.status === 'ready').length
  const approvedCount = project.scenes.filter(s => s.status === 'approved').length

  return (
    <div className="p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-xl font-bold">{project.title}</h2>
          <p className="text-gray-400 text-sm">
            {project.scenes.length} scenes • {project.total_duration}s total
          </p>
        </div>

        <div className="flex items-center gap-3">
          <span className="text-sm text-gray-400">
            {approvedCount}/{project.scenes.length} approved
          </span>
          {readyCount > 0 && (
            <button onClick={onApproveAll} className="tool-button bg-green-600 hover:bg-green-500">
              <Check size={16} /> Approve All ({readyCount})
            </button>
          )}
        </div>
      </div>

      {/* Grid */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4">
        {project.scenes.map(scene => (
          <SceneCard
            key={scene.index}
            scene={scene}
            selected={selectedScene === scene.index}
            onSelect={setSelectedScene}
            onApprove={onApprove}
            onReject={onReject}
          />
        ))}
      </div>
    </div>
  )
}

// Timeline Track Component
function TimelineTrack({ project, selectedScene, setSelectedScene, zoom }) {
  if (!project || !project.scenes) return null

  const totalDuration = project.total_duration || 60
  const pixelsPerSecond = zoom * 10

  return (
    <div className="bg-gray-800 rounded-xl p-4">
      {/* Timeline Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <Layers size={20} className="text-banana-400" />
          <span className="font-medium">Timeline</span>
        </div>
        <span className="text-sm text-gray-400">{project.duration_formatted || '00:00'}</span>
      </div>

      {/* Timeline Ruler */}
      <div className="h-6 border-b border-gray-700 mb-2 relative">
        {Array.from({ length: Math.ceil(totalDuration / 5) + 1 }).map((_, i) => (
          <div
            key={i}
            className="absolute text-xs text-gray-500"
            style={{ left: `${i * 5 * pixelsPerSecond}px` }}
          >
            {i * 5}s
          </div>
        ))}
      </div>

      {/* Video Track */}
      <div className="timeline-track" style={{ width: `${totalDuration * pixelsPerSecond}px`, minWidth: '100%' }}>
        {project.scenes.map(scene => (
          <div
            key={scene.index}
            className={`timeline-scene ${selectedScene === scene.index ? 'selected' : ''}`}
            style={{
              left: `${(scene.start || 0) * pixelsPerSecond}px`,
              width: `${scene.duration * pixelsPerSecond}px`
            }}
            onClick={() => setSelectedScene(scene.index)}
          >
            <div className="p-2 text-xs truncate">{scene.index}</div>
          </div>
        ))}
      </div>

      {/* Audio Track */}
      <div className="mt-2 h-12 bg-gray-700/50 rounded-lg flex items-center px-3 text-sm text-gray-400">
        <Volume2 size={16} className="mr-2" /> Audio Track
      </div>
    </div>
  )
}

// Tool Panel Component
function ToolPanel({ project, selectedScene, onToolAction }) {
  const tools = [
    {
      category: 'Generation', items: [
        { id: 'regenerate', icon: RefreshCw, label: 'Regenerate' },
        { id: 'style-transfer', icon: Palette, label: 'Style Transfer' },
        { id: 'upscale', icon: Sparkles, label: 'Upscale 4K' },
      ]
    },
    {
      category: 'Editing', items: [
        { id: 'duplicate', icon: Copy, label: 'Duplicate' },
        { id: 'split', icon: Layers, label: 'Split' },
        { id: 'delete', icon: Trash2, label: 'Delete' },
      ]
    },
    {
      category: 'Motion', items: [
        { id: 'camera', icon: Camera, label: 'Camera Move' },
        { id: 'speed', icon: Clock, label: 'Speed' },
      ]
    },
    {
      category: 'Visual', items: [
        { id: 'color-grade', icon: Palette, label: 'Color Grade' },
      ]
    },
  ]

  return (
    <div className="bg-gray-800 rounded-xl p-4 w-64">
      <h3 className="font-medium mb-4 flex items-center gap-2">
        <Settings size={18} /> Scene Tools
      </h3>

      {!selectedScene ? (
        <p className="text-gray-500 text-sm">Select a scene to edit</p>
      ) : (
        <div className="space-y-4">
          {tools.map(group => (
            <div key={group.category}>
              <h4 className="text-xs text-gray-500 uppercase mb-2">{group.category}</h4>
              <div className="space-y-1">
                {group.items.map(tool => (
                  <button
                    key={tool.id}
                    onClick={() => onToolAction(tool.id, selectedScene)}
                    className="tool-button w-full justify-start"
                  >
                    <tool.icon size={16} /> {tool.label}
                  </button>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

// Render Panel Component
function RenderPanel({ project, onRender, onUploadYouTube }) {
  const canRender = project?.scenes?.every(s => s.status === 'approved')

  return (
    <div className="bg-gray-800 rounded-xl p-4">
      <h3 className="font-medium mb-4 flex items-center gap-2">
        <Film size={18} /> Export
      </h3>

      <div className="space-y-3">
        <button
          onClick={onRender}
          disabled={!canRender}
          className="w-full py-3 bg-gradient-to-r from-green-500 to-emerald-600 text-white font-medium 
                   rounded-lg hover:from-green-400 hover:to-emerald-500 transition-all
                   disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
        >
          <Download size={18} /> Render Video
        </button>

        <button
          onClick={onUploadYouTube}
          disabled={!canRender}
          className="w-full py-3 bg-red-600 hover:bg-red-500 text-white font-medium 
                   rounded-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed 
                   flex items-center justify-center gap-2"
        >
          <Youtube size={18} /> Upload to YouTube
        </button>

        {!canRender && (
          <p className="text-xs text-gray-500 text-center">
            Approve all scenes to enable export
          </p>
        )}
      </div>
    </div>
  )
}

// Main App Component
export default function App() {
  const [mode, setMode] = useState('simple')
  const [project, setProject] = useState(null)
  const [projects, setProjects] = useState([])
  const [selectedScene, setSelectedScene] = useState(null)
  const [loading, setLoading] = useState(false)
  const [zoom, setZoom] = useState(1)
  const [showYouTubePublisher, setShowYouTubePublisher] = useState(false)

  // Load projects on mount
  useEffect(() => {
    loadProjects()
  }, [])

  const loadProjects = async () => {
    try {
      const data = await api.listProjects()
      setProjects(data.projects || [])
    } catch (err) {
      console.error('Failed to load projects:', err)
    }
  }

  const handleCreateProject = async (params) => {
    setLoading(true)
    try {
      const data = await api.quickCreate(params)
      const gallery = await api.getPreviewGallery(data.project_id)
      setProject({ ...data, ...gallery })
      setMode('simple')
    } catch (err) {
      console.error('Failed to create project:', err)
      alert('Failed to create project: ' + err.message)
    } finally {
      setLoading(false)
    }
  }

  const handleApprove = async (sceneIndex) => {
    try {
      await api.approveScene(project.project_id, sceneIndex)
      refreshProject()
    } catch (err) {
      console.error('Failed to approve scene:', err)
    }
  }

  const handleReject = async (sceneIndex) => {
    try {
      await api.rejectScene(project.project_id, sceneIndex)
      refreshProject()
    } catch (err) {
      console.error('Failed to reject scene:', err)
    }
  }

  const handleApproveAll = async () => {
    try {
      await api.approveAll(project.project_id)
      refreshProject()
    } catch (err) {
      console.error('Failed to approve all:', err)
    }
  }

  const handleRender = async () => {
    try {
      const result = await api.render(project.project_id)
      alert(`Rendering started! Job ID: ${result.job_id}`)
    } catch (err) {
      console.error('Failed to start render:', err)
      alert('Failed to start render: ' + err.message)
    }
  }

  const handleToolAction = async (toolId, sceneIndex) => {
    try {
      switch (toolId) {
        case 'regenerate':
          await api.regenerateScene(project.project_id, sceneIndex)
          break
        case 'duplicate':
          await api.duplicateScene(project.project_id, sceneIndex)
          break
        case 'delete':
          if (confirm('Delete this scene?')) {
            await api.deleteScene(project.project_id, sceneIndex)
          }
          break
        default:
          console.log('Tool not implemented:', toolId)
      }
      refreshProject()
    } catch (err) {
      console.error(`Tool ${toolId} failed:`, err)
    }
  }

  const refreshProject = async () => {
    if (!project?.project_id) return
    try {
      const gallery = await api.getPreviewGallery(project.project_id)
      setProject(prev => ({ ...prev, ...gallery }))
    } catch (err) {
      console.error('Failed to refresh project:', err)
    }
  }

  return (
    <div className="min-h-screen bg-gray-900 flex flex-col">
      <Header mode={mode} setMode={setMode} onNewProject={() => setProject(null)} />

      <main className="flex-1 flex flex-col">
        {!project ? (
          <div className="flex-1 flex items-center justify-center p-6">
            <QuickCreatePanel onCreateProject={handleCreateProject} loading={loading} />
          </div>
        ) : mode === 'simple' ? (
          <SceneGallery
            project={project}
            selectedScene={selectedScene}
            setSelectedScene={setSelectedScene}
            onApprove={handleApprove}
            onReject={handleReject}
            onApproveAll={handleApproveAll}
          />
        ) : (
          <div className="flex-1 flex">
            {/* Main Timeline Area */}
            <div className="flex-1 p-4 space-y-4">
              <SceneGallery
                project={project}
                selectedScene={selectedScene}
                setSelectedScene={setSelectedScene}
                onApprove={handleApprove}
                onReject={handleReject}
                onApproveAll={handleApproveAll}
              />
              <TimelineTrack
                project={project}
                selectedScene={selectedScene}
                setSelectedScene={setSelectedScene}
                zoom={zoom}
              />
            </div>

            {/* Right Panel */}
            <div className="w-72 p-4 space-y-4 border-l border-gray-800">
              <ToolPanel
                project={project}
                selectedScene={selectedScene}
                onToolAction={handleToolAction}
              />
              <RenderPanel
                project={project}
                onRender={handleRender}
                onUploadYouTube={() => setShowYouTubePublisher(true)}
              />
            </div>
          </div>
        )}
      </main>

      {/* Bottom Bar */}
      {project && (
        <footer className="bg-gray-800 border-t border-gray-700 px-6 py-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <button className="p-2 hover:bg-gray-700 rounded"><SkipBack size={20} /></button>
              <button className="p-2 hover:bg-gray-700 rounded bg-banana-500 text-black"><Play size={20} /></button>
              <button className="p-2 hover:bg-gray-700 rounded"><SkipForward size={20} /></button>
            </div>

            <div className="flex items-center gap-4">
              <button onClick={() => api.undo(project.project_id)} className="tool-button">
                <Undo size={16} /> Undo
              </button>
              <button onClick={() => api.redo(project.project_id)} className="tool-button">
                <Redo size={16} /> Redo
              </button>
            </div>

            <div className="flex items-center gap-2">
              <span className="text-sm text-gray-400">Zoom:</span>
              <input
                type="range"
                min="0.5"
                max="3"
                step="0.1"
                value={zoom}
                onChange={(e) => setZoom(Number(e.target.value))}
                className="w-24"
              />
            </div>
          </div>
        </footer>
      )}

      {/* YouTube Publisher Modal */}
      {showYouTubePublisher && (
        <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50">
          <div className="relative max-w-lg w-full mx-4">
            <button
              onClick={() => setShowYouTubePublisher(false)}
              className="absolute -top-10 right-0 text-white hover:text-gray-300"
            >
              Close ✕
            </button>
            <YouTubePublisher
              videoPath={project?.output_path}
              projectTitle={project?.name || 'Untitled Project'}
              onPublished={(result) => {
                setShowYouTubePublisher(false)
                alert(`Video published! URL: ${result.video_url || 'Check YouTube Studio'}`)
              }}
            />
          </div>
        </div>
      )}
    </div>
  )
}
