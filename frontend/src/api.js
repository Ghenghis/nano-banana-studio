/**
 * Nano Banana Studio Pro - Complete API Client
 * Connects frontend to all backend services
 */

const API_BASE = '/api/v1'
const TIMELINE_URL = `${API_BASE}/timeline`

async function request(baseUrl, endpoint, options = {}) {
  const url = `${baseUrl}${endpoint}`
  const config = {
    headers: { 'Content-Type': 'application/json' },
    ...options
  }
  
  try {
    const response = await fetch(url, config)
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ message: `HTTP ${response.status}` }))
      throw new Error(errorData.error?.message || errorData.message || `HTTP ${response.status}`)
    }
    
    return response.json()
  } catch (error) {
    console.error(`API Error [${url}]:`, error)
    throw error
  }
}

async function formRequest(baseUrl, endpoint, data) {
  const url = `${baseUrl}${endpoint}`
  const formData = new FormData()
  
  Object.entries(data).forEach(([key, value]) => {
    if (value !== undefined && value !== null) {
      formData.append(key, value)
    }
  })
  
  try {
    const response = await fetch(url, {
      method: 'POST',
      body: formData
    })
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ message: `HTTP ${response.status}` }))
      throw new Error(errorData.error?.message || errorData.message || `HTTP ${response.status}`)
    }
    
    return response.json()
  } catch (error) {
    console.error(`API Error [${url}]:`, error)
    throw error
  }
}

// Timeline API helper
const timeline = (endpoint, options) => request(TIMELINE_URL, endpoint, options)
const timelineForm = (endpoint, data) => formRequest(TIMELINE_URL, endpoint, data)

// General API helper
const apiRequest = (endpoint, options) => request(API_BASE, endpoint, options)
const apiForm = (endpoint, data) => formRequest(API_BASE, endpoint, data)

const api = {
  // ===========================================
  // TIMELINE - Simple Mode
  // ===========================================
  quickCreate: (params) => timeline('/quick-create', {
    method: 'POST',
    body: JSON.stringify(params)
  }),
  
  getPreviewGallery: (projectId) => timeline(`/${projectId}/preview-gallery`),
  approveScene: (projectId, sceneIndex) => timeline(`/${projectId}/scenes/${sceneIndex}/approve`, { method: 'POST' }),
  rejectScene: (projectId, sceneIndex, newPrompt) => timelineForm(`/${projectId}/scenes/${sceneIndex}/reject`, { new_prompt: newPrompt }),
  approveAll: (projectId) => timeline(`/${projectId}/approve-all`, { method: 'POST' }),
  render: (projectId, preset = 'youtube_1080p') => timelineForm(`/${projectId}/render`, { preset }),
  
  // TIMELINE - Advanced Mode
  createProject: (title, mode = 'advanced') => timelineForm('/projects', { title, mode }),
  listProjects: () => timeline('/projects'),
  getProject: (projectId) => timeline(`/${projectId}`),
  getTimeline: (projectId) => timeline(`/${projectId}/timeline`),
  getScene: (projectId, sceneIndex) => timeline(`/${projectId}/scenes/${sceneIndex}`),
  addScene: (projectId, prompt, duration = 5, style = 'Cinematic') => timelineForm(`/${projectId}/scenes`, { prompt, duration, style }),
  regenerateScene: (projectId, sceneIndex) => timeline(`/${projectId}/scenes/${sceneIndex}/regenerate`, { method: 'POST' }),
  styleTransfer: (projectId, sceneIndex, style) => timelineForm(`/${projectId}/scenes/${sceneIndex}/style-transfer`, { style }),
  setCamera: (projectId, sceneIndex, movement, intensity = 50) => timelineForm(`/${projectId}/scenes/${sceneIndex}/camera`, { movement, intensity }),
  setTransition: (projectId, sceneIndex, transitionType, duration = 0.5) => timelineForm(`/${projectId}/scenes/${sceneIndex}/transition`, { transition_type: transitionType, duration }),
  setColorGrade: (projectId, sceneIndex, preset) => timelineForm(`/${projectId}/scenes/${sceneIndex}/color-grade`, { preset }),
  splitScene: (projectId, sceneIndex, atTime) => timelineForm(`/${projectId}/scenes/${sceneIndex}/split`, { at_time: atTime }),
  duplicateScene: (projectId, sceneIndex) => timeline(`/${projectId}/scenes/${sceneIndex}/duplicate`, { method: 'POST' }),
  deleteScene: (projectId, sceneIndex) => timeline(`/${projectId}/scenes/${sceneIndex}`, { method: 'DELETE' }),
  setSpeed: (projectId, sceneIndex, speed) => timelineForm(`/${projectId}/scenes/${sceneIndex}/speed`, { speed }),
  undo: (projectId) => timeline(`/${projectId}/undo`, { method: 'POST' }),
  redo: (projectId) => timeline(`/${projectId}/redo`, { method: 'POST' }),
  publishToYouTube: (projectId, params) => timeline(`/${projectId}/publish-youtube`, { method: 'POST', body: JSON.stringify(params) }),

  // ===========================================
  // PROMPT ENHANCEMENT
  // ===========================================
  enhanceConcept: (prompt, style, platform) => apiRequest('/enhance/concept', {
    method: 'POST',
    body: JSON.stringify({ prompt, style, platform })
  }),
  enhanceFull: (prompt, style, platform) => apiRequest('/enhance/full', {
    method: 'POST',
    body: JSON.stringify({ prompt, style, platform })
  }),

  // ===========================================
  // FACE DETECTION & CHARACTER
  // ===========================================
  extractFace: (imageData) => apiForm('/face/extract', imageData),
  registerCharacter: (name, faceEmbedding, referenceImages = [], styleKeywords = []) => apiRequest('/character/register', {
    method: 'POST',
    body: JSON.stringify({ name, face_embedding: faceEmbedding, reference_images: referenceImages, style_keywords: styleKeywords })
  }),
  getCharacter: (charId) => apiRequest(`/character/${charId}`),
  verifyCharacter: (characterId, imageBase64) => apiForm('/character/verify', { character_id: characterId, image_base64: imageBase64 }),

  // ===========================================
  // IMAGE GENERATION
  // ===========================================
  generateImage: (params) => apiRequest('/generate/image', {
    method: 'POST',
    body: JSON.stringify(params)
  }),
  generateBatch: (prompts, style, aspectRatio) => apiForm('/generate/batch', { prompts: JSON.stringify(prompts), style, aspect_ratio: aspectRatio }),

  // ===========================================
  // ANIMATION
  // ===========================================
  animateImage: (params) => apiRequest('/animate/image', {
    method: 'POST',
    body: JSON.stringify(params)
  }),

  // ===========================================
  // AUDIO
  // ===========================================
  analyzeAudio: (audioData) => apiForm('/audio/analyze', audioData),
  mixAudio: (tracks, volumes, mode = 'layer') => apiForm('/audio/mix', { tracks, volumes: JSON.stringify(volumes), mode }),

  // ===========================================
  // SUNO MUSIC GENERATION
  // ===========================================
  generateMusic: (params) => apiRequest('/suno/generate', {
    method: 'POST',
    body: JSON.stringify(params)
  }),

  // ===========================================
  // STORYBOARD
  // ===========================================
  generateStoryboard: (params) => apiRequest('/storyboard/generate', {
    method: 'POST',
    body: JSON.stringify(params)
  }),

  // ===========================================
  // VIDEO ASSEMBLY
  // ===========================================
  assembleVideo: (manifest, platform, quality, transitionStyle, kenBurns) => apiRequest('/video/assemble', {
    method: 'POST',
    body: JSON.stringify({ manifest, platform, quality, transition_style: transitionStyle, ken_burns: kenBurns })
  }),

  // ===========================================
  // JOBS
  // ===========================================
  getJob: (jobId) => apiRequest(`/jobs/${jobId}`),
  listJobs: (status, limit = 50) => apiRequest(`/jobs?status=${status || ''}&limit=${limit}`),
  getWorkflowStatus: (jobId) => apiRequest(`/workflow/status/${jobId}`),

  // ===========================================
  // UPLOADS
  // ===========================================
  uploadImage: (file) => {
    const formData = new FormData()
    formData.append('file', file)
    return fetch(`${API_BASE}/upload/image`, { method: 'POST', body: formData }).then(r => r.json())
  },
  uploadAudio: (file) => {
    const formData = new FormData()
    formData.append('file', file)
    return fetch(`${API_BASE}/upload/audio`, { method: 'POST', body: formData }).then(r => r.json())
  },
  downloadFile: (filename) => `${API_BASE}/download/${filename}`,

  // ===========================================
  // YOUTUBE
  // ===========================================
  getYouTubeAccounts: () => apiRequest('/youtube/accounts'),
  addYouTubeAccount: (authCode) => apiForm('/youtube/accounts/add', { auth_code: authCode }),
  removeYouTubeAccount: (accountId) => apiRequest(`/youtube/accounts/${accountId}`, { method: 'DELETE' }),
  uploadToYouTube: (params) => apiRequest('/youtube/upload', { method: 'POST', body: JSON.stringify(params) }),
  quickUploadYouTube: (videoPath, title, accountId, description, privacy) => apiForm('/youtube/quick-upload', { video_path: videoPath, title, account_id: accountId, description, privacy }),
  getYouTubePlaylists: (accountId) => apiRequest(`/youtube/playlists/${accountId}`),
  createYouTubePlaylist: (accountId, title, description, privacy) => apiForm(`/youtube/playlists/${accountId}`, { title, description, privacy }),
  generateYouTubeMetadata: (title, description, category) => apiForm('/youtube/generate-metadata', { title, description, category }),
  getYouTubeAnalytics: (accountId, videoId) => apiRequest(`/youtube/analytics/${accountId}/${videoId}`),

  // ===========================================
  // DOCUMENT PARSING
  // ===========================================
  parseMarkdown: (file) => {
    const formData = new FormData()
    formData.append('file', file)
    return fetch(`${API_BASE}/parse/markdown`, { method: 'POST', body: formData }).then(r => r.json())
  },

  // ===========================================
  // HEALTH
  // ===========================================
  health: () => fetch('/health').then(r => r.json()),
  info: () => fetch('/').then(r => r.json())
}

export default api
