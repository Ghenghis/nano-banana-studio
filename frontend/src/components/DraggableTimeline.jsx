import React, { useState, useCallback } from 'react'
import { GripVertical, Play, Pause, Clock, Film, Trash2, Copy, Settings } from 'lucide-react'

export default function DraggableTimeline({ scenes, onReorder, onSceneSelect, onSceneDelete, onSceneDuplicate }) {
  const [draggedIndex, setDraggedIndex] = useState(null)
  const [dragOverIndex, setDragOverIndex] = useState(null)
  const [selectedScene, setSelectedScene] = useState(null)

  const handleDragStart = useCallback((e, index) => {
    setDraggedIndex(index)
    e.dataTransfer.effectAllowed = 'move'
    e.dataTransfer.setData('text/plain', index.toString())
    e.target.style.opacity = '0.5'
  }, [])

  const handleDragEnd = useCallback((e) => {
    e.target.style.opacity = '1'
    setDraggedIndex(null)
    setDragOverIndex(null)
  }, [])

  const handleDragOver = useCallback((e, index) => {
    e.preventDefault()
    e.dataTransfer.dropEffect = 'move'
    if (index !== draggedIndex) {
      setDragOverIndex(index)
    }
  }, [draggedIndex])

  const handleDragLeave = useCallback(() => {
    setDragOverIndex(null)
  }, [])

  const handleDrop = useCallback((e, dropIndex) => {
    e.preventDefault()
    const dragIndex = parseInt(e.dataTransfer.getData('text/plain'), 10)

    if (dragIndex !== dropIndex && onReorder) {
      const newScenes = [...scenes]
      const [draggedScene] = newScenes.splice(dragIndex, 1)
      newScenes.splice(dropIndex, 0, draggedScene)
      onReorder(newScenes)
    }

    setDraggedIndex(null)
    setDragOverIndex(null)
  }, [scenes, onReorder])

  const handleSceneClick = (scene, index) => {
    setSelectedScene(index)
    onSceneSelect?.(scene, index)
  }

  const formatDuration = (seconds) => {
    const mins = Math.floor(seconds / 60)
    const secs = Math.floor(seconds % 60)
    return `${mins}:${secs.toString().padStart(2, '0')}`
  }

  const totalDuration = scenes.reduce((sum, s) => sum + (s.duration || 0), 0)

  return (
    <div className="bg-gray-800 rounded-xl p-4">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold flex items-center gap-2">
          <Film size={20} className="text-banana-400" />
          Timeline
        </h3>
        <div className="flex items-center gap-2 text-sm text-gray-400">
          <Clock size={14} />
          <span>{formatDuration(totalDuration)}</span>
          <span className="text-gray-600">|</span>
          <span>{scenes.length} scenes</span>
        </div>
      </div>

      {/* Timeline Track */}
      <div className="relative">
        {/* Time ruler */}
        <div className="flex items-center h-6 bg-gray-700 rounded-t-lg px-2 text-xs text-gray-400">
          {[0, 15, 30, 45, 60].map(sec => (
            <div key={sec} className="flex-1 text-center border-l border-gray-600 first:border-l-0">
              {formatDuration(sec)}
            </div>
          ))}
        </div>

        {/* Scene cards */}
        <div className="flex gap-1 p-2 bg-gray-700 rounded-b-lg overflow-x-auto min-h-[120px]">
          {scenes.length === 0 ? (
            <div className="flex-1 flex items-center justify-center text-gray-500">
              <p>No scenes yet. Create your first scene to get started.</p>
            </div>
          ) : (
            scenes.map((scene, index) => (
              <div
                key={scene.id || index}
                draggable
                onDragStart={(e) => handleDragStart(e, index)}
                onDragEnd={handleDragEnd}
                onDragOver={(e) => handleDragOver(e, index)}
                onDragLeave={handleDragLeave}
                onDrop={(e) => handleDrop(e, index)}
                onClick={() => handleSceneClick(scene, index)}
                className={`
                  relative flex-shrink-0 w-32 rounded-lg overflow-hidden cursor-grab active:cursor-grabbing
                  transition-all duration-200 border-2
                  ${dragOverIndex === index ? 'border-banana-400 scale-105' : 'border-transparent'}
                  ${selectedScene === index ? 'ring-2 ring-banana-500' : ''}
                  ${draggedIndex === index ? 'opacity-50' : 'opacity-100'}
                  hover:border-gray-500
                `}
                style={{
                  minWidth: `${Math.max(80, (scene.duration || 3) * 20)}px`,
                  maxWidth: '200px'
                }}
              >
                {/* Drag handle */}
                <div className="absolute top-1 left-1 z-10 p-1 bg-black/50 rounded cursor-grab">
                  <GripVertical size={12} className="text-white" />
                </div>

                {/* Scene number */}
                <div className="absolute top-1 right-1 z-10 px-1.5 py-0.5 bg-black/70 rounded text-xs font-bold">
                  {index + 1}
                </div>

                {/* Preview image */}
                <div className="h-16 bg-gray-600 relative">
                  {scene.preview_image ? (
                    <img
                      src={scene.preview_image}
                      alt={`Scene ${index + 1}`}
                      className="w-full h-full object-cover"
                    />
                  ) : (
                    <div className="w-full h-full flex items-center justify-center text-gray-400">
                      <Film size={24} />
                    </div>
                  )}

                  {/* Status indicator */}
                  {scene.status === 'generating' && (
                    <div className="absolute inset-0 bg-black/50 flex items-center justify-center">
                      <div className="w-6 h-6 border-2 border-banana-400 border-t-transparent rounded-full animate-spin" />
                    </div>
                  )}
                </div>

                {/* Scene info */}
                <div className="p-2 bg-gray-800">
                  <p className="text-xs truncate text-gray-300">
                    {scene.visual_prompt?.slice(0, 30) || `Scene ${index + 1}`}
                  </p>
                  <div className="flex items-center justify-between mt-1">
                    <span className="text-xs text-gray-500">
                      {formatDuration(scene.duration || 3)}
                    </span>
                    <div className="flex gap-1">
                      <button
                        onClick={(e) => { e.stopPropagation(); onSceneDuplicate?.(index) }}
                        className="p-1 text-gray-400 hover:text-banana-400 transition-colors"
                        title="Duplicate"
                      >
                        <Copy size={10} />
                      </button>
                      <button
                        onClick={(e) => { e.stopPropagation(); onSceneDelete?.(index) }}
                        className="p-1 text-gray-400 hover:text-red-400 transition-colors"
                        title="Delete"
                      >
                        <Trash2 size={10} />
                      </button>
                    </div>
                  </div>
                </div>

                {/* Drop indicator */}
                {dragOverIndex === index && draggedIndex !== index && (
                  <div className="absolute inset-y-0 left-0 w-1 bg-banana-400" />
                )}
              </div>
            ))
          )}

          {/* Drop zone at end */}
          {scenes.length > 0 && draggedIndex !== null && (
            <div
              onDragOver={(e) => { e.preventDefault(); setDragOverIndex(scenes.length) }}
              onDrop={(e) => handleDrop(e, scenes.length)}
              className={`
                w-16 h-24 border-2 border-dashed rounded-lg flex items-center justify-center
                transition-colors
                ${dragOverIndex === scenes.length ? 'border-banana-400 bg-banana-400/10' : 'border-gray-600'}
              `}
            >
              <span className="text-xs text-gray-500">Drop</span>
            </div>
          )}
        </div>
      </div>

      {/* Playback controls */}
      <div className="flex items-center justify-center gap-4 mt-4">
        <button className="p-2 bg-gray-700 rounded-full hover:bg-gray-600 transition-colors">
          <Play size={20} className="text-white" />
        </button>
        <div className="flex-1 h-1 bg-gray-700 rounded-full max-w-md">
          <div className="h-full w-0 bg-banana-500 rounded-full" />
        </div>
        <span className="text-sm text-gray-400">0:00 / {formatDuration(totalDuration)}</span>
      </div>
    </div>
  )
}
