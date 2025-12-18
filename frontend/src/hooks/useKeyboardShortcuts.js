/**
 * Nano Banana Studio Pro - Keyboard Shortcuts Hook
 * Global keyboard shortcuts for timeline editor
 */

import { useEffect, useCallback } from 'react'

const DEFAULT_SHORTCUTS = {
  'ctrl+z': 'undo',
  'ctrl+y': 'redo',
  'ctrl+shift+z': 'redo',
  'ctrl+s': 'save',
  'ctrl+n': 'newProject',
  'ctrl+e': 'export',
  'space': 'playPause',
  'delete': 'deleteScene',
  'backspace': 'deleteScene',
  'ctrl+d': 'duplicateScene',
  'ctrl+a': 'selectAll',
  'escape': 'deselect',
  'arrowleft': 'prevScene',
  'arrowright': 'nextScene',
  'ctrl+arrowleft': 'moveSceneLeft',
  'ctrl+arrowright': 'moveSceneRight',
  '+': 'zoomIn',
  '=': 'zoomIn',
  '-': 'zoomOut',
  '0': 'zoomReset',
  'r': 'regenerate',
  'g': 'generate',
}

export function useKeyboardShortcuts(handlers, enabled = true) {
  const handleKeyDown = useCallback((event) => {
    if (!enabled) return
    
    // Ignore if typing in input/textarea
    if (['INPUT', 'TEXTAREA', 'SELECT'].includes(event.target.tagName)) {
      return
    }

    const key = []
    if (event.ctrlKey || event.metaKey) key.push('ctrl')
    if (event.shiftKey) key.push('shift')
    if (event.altKey) key.push('alt')
    key.push(event.key.toLowerCase())
    
    const combo = key.join('+')
    const action = DEFAULT_SHORTCUTS[combo]
    
    if (action && handlers[action]) {
      event.preventDefault()
      handlers[action](event)
    }
  }, [handlers, enabled])

  useEffect(() => {
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [handleKeyDown])
}

export function useShortcutHelp() {
  const shortcuts = [
    { keys: 'Ctrl+Z', action: 'Undo' },
    { keys: 'Ctrl+Y', action: 'Redo' },
    { keys: 'Ctrl+S', action: 'Save project' },
    { keys: 'Ctrl+N', action: 'New project' },
    { keys: 'Ctrl+E', action: 'Export video' },
    { keys: 'Space', action: 'Play/Pause' },
    { keys: 'Delete', action: 'Delete scene' },
    { keys: 'Ctrl+D', action: 'Duplicate scene' },
    { keys: '←/→', action: 'Navigate scenes' },
    { keys: '+/-', action: 'Zoom in/out' },
    { keys: 'R', action: 'Regenerate scene' },
    { keys: 'Esc', action: 'Deselect' },
  ]
  
  return shortcuts
}

export default useKeyboardShortcuts
