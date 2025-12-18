import React, { useState, useEffect } from 'react'
import { User, Upload, Check, X, Trash2, RefreshCw } from 'lucide-react'
import api from '../api'

export default function CharacterManager({ onCharacterSelect }) {
  const [characters, setCharacters] = useState([])
  const [newCharacter, setNewCharacter] = useState({ name: '', images: [] })
  const [loading, setLoading] = useState(false)
  const [extracting, setExtracting] = useState(false)
  const [selectedFile, setSelectedFile] = useState(null)
  const [facePreview, setFacePreview] = useState(null)

  const handleFileSelect = async (e) => {
    const file = e.target.files[0]
    if (!file) return

    setSelectedFile(file)
    setExtracting(true)

    try {
      // Convert to base64
      const reader = new FileReader()
      reader.onload = async (event) => {
        const base64 = event.target.result.split(',')[1]

        // Extract face
        const result = await api.extractFace({ image_base64: base64 })

        if (result.face_detected) {
          setFacePreview({
            image: event.target.result,
            embedding: result.face_embedding,
            bbox: result.primary_face?.bounding_box
          })
        } else {
          alert('No face detected in image. Please try another image.')
        }
        setExtracting(false)
      }
      reader.readAsDataURL(file)
    } catch (err) {
      console.error('Face extraction failed:', err)
      alert('Failed to extract face: ' + err.message)
      setExtracting(false)
    }
  }

  const handleRegister = async () => {
    if (!newCharacter.name || !facePreview?.embedding) {
      alert('Please provide a name and upload an image with a detectable face')
      return
    }

    setLoading(true)
    try {
      const result = await api.registerCharacter(
        newCharacter.name,
        facePreview.embedding,
        [selectedFile?.name || 'reference.jpg'],
        []
      )

      setCharacters(prev => [...prev, {
        id: result.character_id,
        name: newCharacter.name,
        preview: facePreview.image
      }])

      // Reset form
      setNewCharacter({ name: '', images: [] })
      setFacePreview(null)
      setSelectedFile(null)

    } catch (err) {
      console.error('Registration failed:', err)
      alert('Failed to register character: ' + err.message)
    } finally {
      setLoading(false)
    }
  }

  const handleVerify = async (characterId, imageBase64) => {
    try {
      const result = await api.verifyCharacter(characterId, imageBase64)
      return result
    } catch (err) {
      console.error('Verification failed:', err)
      return { is_consistent: false, error: err.message }
    }
  }

  return (
    <div className="bg-gray-800 rounded-xl p-6">
      <div className="flex items-center gap-3 mb-6">
        <User className="text-banana-400" size={24} />
        <h2 className="text-xl font-bold">Character Manager</h2>
      </div>

      {/* Register New Character */}
      <div className="mb-6 p-4 bg-gray-700 rounded-lg">
        <h3 className="text-sm font-semibold text-gray-300 mb-4">Register New Character</h3>

        <div className="space-y-4">
          <div>
            <label className="block text-sm text-gray-400 mb-2">Character Name</label>
            <input
              type="text"
              value={newCharacter.name}
              onChange={(e) => setNewCharacter(prev => ({ ...prev, name: e.target.value }))}
              placeholder="e.g., Hero, Narrator, Alex"
              className="w-full bg-gray-600 rounded-lg px-4 py-2 text-white placeholder-gray-400 focus:ring-2 focus:ring-banana-500 focus:outline-none"
            />
          </div>

          <div>
            <label className="block text-sm text-gray-400 mb-2">Reference Image</label>
            <div className="flex items-center gap-4">
              <label className="flex-1 flex items-center justify-center gap-2 px-4 py-3 bg-gray-600 rounded-lg cursor-pointer hover:bg-gray-500 transition-colors">
                <Upload size={18} />
                <span>{selectedFile ? selectedFile.name : 'Upload Face Image'}</span>
                <input
                  type="file"
                  accept="image/*"
                  onChange={handleFileSelect}
                  className="hidden"
                />
              </label>
              {extracting && <RefreshCw className="animate-spin text-banana-400" size={20} />}
            </div>
          </div>

          {facePreview && (
            <div className="flex items-center gap-4 p-3 bg-gray-600 rounded-lg">
              <img
                src={facePreview.image}
                alt="Face preview"
                className="w-16 h-16 object-cover rounded-lg"
              />
              <div className="flex-1">
                <p className="text-sm text-green-400 flex items-center gap-2">
                  <Check size={16} /> Face detected
                </p>
                <p className="text-xs text-gray-400">
                  Embedding: {facePreview.embedding?.length || 0} dimensions
                </p>
              </div>
            </div>
          )}

          <button
            onClick={handleRegister}
            disabled={loading || !newCharacter.name || !facePreview}
            className="w-full py-3 bg-banana-500 text-black font-semibold rounded-lg hover:bg-banana-400 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {loading ? 'Registering...' : 'Register Character'}
          </button>
        </div>
      </div>

      {/* Registered Characters */}
      <div>
        <h3 className="text-sm font-semibold text-gray-300 mb-4">Registered Characters</h3>

        {characters.length === 0 ? (
          <p className="text-gray-500 text-center py-4">No characters registered yet</p>
        ) : (
          <div className="space-y-2">
            {characters.map(char => (
              <div
                key={char.id}
                className="flex items-center gap-3 p-3 bg-gray-700 rounded-lg hover:bg-gray-600 cursor-pointer transition-colors"
                onClick={() => onCharacterSelect?.(char)}
              >
                {char.preview ? (
                  <img src={char.preview} alt={char.name} className="w-10 h-10 rounded-full object-cover" />
                ) : (
                  <div className="w-10 h-10 rounded-full bg-gray-600 flex items-center justify-center">
                    <User size={20} className="text-gray-400" />
                  </div>
                )}
                <div className="flex-1">
                  <p className="font-medium">{char.name}</p>
                  <p className="text-xs text-gray-400">ID: {char.id}</p>
                </div>
                <button
                  className="p-2 text-gray-400 hover:text-red-400 transition-colors"
                  onClick={(e) => {
                    e.stopPropagation()
                    setCharacters(prev => prev.filter(c => c.id !== char.id))
                  }}
                >
                  <Trash2 size={16} />
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
