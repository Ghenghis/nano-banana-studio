# 🍌 NANO BANANA STUDIO PRO - API SPECIFICATION

> **Version**: 2.0.0  
> **Base URL**: `http://localhost:8000`  
> **Documentation**: `http://localhost:8000/docs` (Swagger UI)

---

## 📋 OVERVIEW

The Nano Banana Studio Pro API provides comprehensive endpoints for:
- Prompt enhancement (7-stage pipeline)
- Image generation (multi-model)
- Video generation & assembly
- Audio analysis & music generation
- Face detection & character management
- Job queue management
- Real-time progress (WebSocket)

---

## 🔐 AUTHENTICATION

Currently, the API runs locally without authentication. For production deployment, implement:
- API Key authentication
- JWT tokens
- OAuth2 (for external services)

---

## 📍 ENDPOINTS

### 1. PROMPT ENHANCEMENT

#### POST `/api/v1/enhance/prompt`
Enhance a prompt using the full 7-stage pipeline.

**Request Body:**
```json
{
  "prompt": "woman singing in a studio",
  "style": "Cinematic",
  "platform": "YouTube (16:9)",
  "enhancement_level": "full",
  "include_negative": true
}
```

**Response:**
```json
{
  "job_id": "uuid-here",
  "original_prompt": "woman singing in a studio",
  "enhanced_prompt": "Passionate female vocalist performing in a professional recording studio, cinematic three-point lighting, shot on 35mm anamorphic lens, shallow depth of field, warm color grading...",
  "negative_prompt": "blurry, distorted, low quality, oversaturated...",
  "stages_completed": ["concept", "scene", "visual", "cinematic", "narrative", "technical", "consistency"],
  "style_dna": {
    "primary_colors": ["warm amber", "deep burgundy"],
    "lighting": "three-point cinematic",
    "mood": "passionate, professional",
    "camera": "35mm anamorphic"
  },
  "timestamp": "2025-12-17T12:00:00Z"
}
```

**Enhancement Levels:**
| Level | Stages | Time |
|-------|--------|------|
| `quick` | 1-3 | ~2s |
| `standard` | 1-5 | ~5s |
| `full` | 1-7 | ~10s |

---

#### POST `/api/v1/enhance/quick`
Quick 3-stage enhancement for fast results.

---

#### GET `/api/v1/enhance/styles`
List available style presets.

**Response:**
```json
{
  "styles": [
    {
      "name": "Cinematic",
      "description": "Hollywood film look with anamorphic lenses",
      "keywords": ["anamorphic", "shallow DOF", "warm tones"]
    },
    {
      "name": "Anime",
      "description": "Japanese animation style",
      "keywords": ["bold lines", "vibrant colors", "dynamic"]
    }
  ]
}
```

---

### 2. IMAGE GENERATION

#### POST `/api/v1/generate/image`
Generate a single image from prompt.

**Request Body:**
```json
{
  "prompt": "Enhanced prompt here...",
  "negative_prompt": "blurry, distorted...",
  "model": "google/gemini-2.0-flash-exp:free",
  "width": 1920,
  "height": 1080,
  "style_preset": "Cinematic",
  "reference_images": ["base64_or_url"],
  "character_id": "uuid-optional"
}
```

**Response:**
```json
{
  "job_id": "uuid",
  "status": "completed",
  "image_url": "/outputs/images/uuid.png",
  "image_base64": "...",
  "metadata": {
    "model": "gemini-2.0-flash-exp",
    "resolution": "1920x1080",
    "generation_time": 2.5,
    "seed": 12345
  }
}
```

**Supported Models:**
| Model | Provider | Features |
|-------|----------|----------|
| `google/gemini-2.0-flash-exp:free` | Google | Fast, free tier |
| `flux.1-schnell` | ComfyUI | 4-step generation |
| `sdxl-base-1.0` | ComfyUI | Industry standard |
| `sdxl-turbo` | ComfyUI | 1-4 step fast |

---

#### POST `/api/v1/generate/batch`
Generate multiple images in batch.

**Request Body:**
```json
{
  "prompts": ["prompt1", "prompt2", "prompt3"],
  "shared_settings": {
    "style_preset": "Cinematic",
    "character_id": "uuid"
  }
}
```

---

### 3. VIDEO GENERATION

#### POST `/api/v1/video/generate`
Generate video from text prompt.

**Request Body:**
```json
{
  "prompt": "A serene mountain lake at sunset",
  "negative_prompt": "blurry, jittery",
  "model": "ltx-video-0.9.7-distilled",
  "num_frames": 121,
  "height": 512,
  "width": 768,
  "fps": 24,
  "num_inference_steps": 8,
  "guidance_scale": 3.0,
  "seed": null
}
```

**Response:**
```json
{
  "job_id": "uuid",
  "status": "completed",
  "video_url": "/outputs/videos/uuid.mp4",
  "metadata": {
    "model": "ltx-video-0.9.7-distilled",
    "duration": 5.04,
    "frame_count": 121,
    "resolution": "768x512",
    "fps": 24
  }
}
```

---

#### POST `/api/v1/video/animate`
Animate a static image into video.

**Request Body:**
```json
{
  "image": "base64_or_path",
  "prompt": "the person waves and smiles",
  "num_frames": 121,
  "motion_strength": 0.8
}
```

---

#### POST `/api/v1/video/assemble`
Assemble multiple clips into final video.

**Request Body:**
```json
{
  "clips": [
    {
      "path": "/path/to/clip1.mp4",
      "duration": 5.0,
      "transition_in": "crossfade",
      "transition_out": "dip_to_black"
    }
  ],
  "audio": {
    "path": "/path/to/music.mp3",
    "volume": 0.8,
    "fade_in": 1.0,
    "fade_out": 2.0
  },
  "output_settings": {
    "resolution": "1920x1080",
    "fps": 30,
    "codec": "h264",
    "bitrate": "10M"
  },
  "beat_sync": {
    "enabled": true,
    "beat_markers": [0.5, 1.2, 2.4, 3.6]
  }
}
```

---

### 4. AUDIO PROCESSING

#### POST `/api/v1/audio/analyze`
Analyze audio file for beats, BPM, and structure.

**Request Body:**
```json
{
  "audio_path": "/path/to/audio.mp3",
  "analysis_type": "full"
}
```

**Response:**
```json
{
  "job_id": "uuid",
  "bpm": 128,
  "beats": [0.0, 0.468, 0.937, 1.406],
  "downbeats": [0.0, 1.875, 3.75],
  "segments": [
    {"start": 0, "end": 15, "type": "intro"},
    {"start": 15, "end": 45, "type": "verse"},
    {"start": 45, "end": 60, "type": "chorus"}
  ],
  "key": "C major",
  "duration": 180.5
}
```

---

#### POST `/api/v1/audio/detect-beats`
Quick beat detection only.

---

#### POST `/api/v1/audio/transcribe`
Transcribe audio to text using Whisper.

**Request Body:**
```json
{
  "audio_path": "/path/to/audio.mp3",
  "model": "whisper-large-v3",
  "language": "en",
  "word_timestamps": true
}
```

**Response:**
```json
{
  "text": "Full transcription here...",
  "segments": [
    {
      "start": 0.0,
      "end": 2.5,
      "text": "First line",
      "words": [
        {"word": "First", "start": 0.0, "end": 0.5},
        {"word": "line", "start": 0.6, "end": 1.0}
      ]
    }
  ],
  "language": "en",
  "duration": 180.5
}
```

---

### 5. MUSIC GENERATION

#### POST `/api/v1/suno/generate`
Generate music using Suno API.

**Request Body:**
```json
{
  "mode": "simple",
  "prompt": "upbeat pop song about coding",
  "style": "pop",
  "instrumental": false,
  "wait_audio": true,
  "model": "chirp-v3-5"
}
```

**Response:**
```json
{
  "success": true,
  "songs": [
    {
      "id": "song-uuid",
      "title": "Generated Title",
      "status": "complete",
      "audio_url": "https://...",
      "duration": 180,
      "lyrics": "Verse 1...",
      "style": "pop"
    }
  ],
  "saved_file": {
    "path": "/outputs/music/song.mp3",
    "size": 5242880
  },
  "credits_used": 10
}
```

---

#### POST `/api/v1/suno/lyrics`
Generate lyrics only (FREE).

**Request Body:**
```json
{
  "prompt": "a song about summer adventures"
}
```

---

#### GET `/api/v1/suno/credits`
Check Suno credit balance.

**Response:**
```json
{
  "credits_left": 450,
  "monthly_limit": 500,
  "monthly_usage": 50
}
```

---

#### POST `/api/v1/musicgen/generate`
Generate music locally using MusicGen.

**Request Body:**
```json
{
  "prompt": "calm ambient music for studying",
  "model": "musicgen-medium",
  "duration": 30,
  "temperature": 1.0,
  "top_k": 250
}
```

---

### 6. FACE & CHARACTER

#### POST `/api/v1/face/detect`
Detect faces in an image.

**Request Body:**
```json
{
  "image_base64": "...",
  "return_landmarks": true
}
```

**Response:**
```json
{
  "face_detected": true,
  "face_count": 1,
  "faces": [
    {
      "bbox": [100, 50, 200, 200],
      "confidence": 0.99,
      "landmarks": {
        "left_eye": [130, 100],
        "right_eye": [170, 100],
        "nose": [150, 130],
        "mouth_left": [125, 160],
        "mouth_right": [175, 160]
      }
    }
  ]
}
```

---

#### POST `/api/v1/face/embed`
Extract face embedding vector.

**Response:**
```json
{
  "embedding": [0.123, -0.456, ...],
  "embedding_dim": 512,
  "model": "insightface"
}
```

---

#### POST `/api/v1/character/register`
Register a new character with reference images.

**Request Body:**
```json
{
  "name": "Main Character",
  "reference_images": ["base64_1", "base64_2"],
  "description": "Young woman with brown hair"
}
```

**Response:**
```json
{
  "character_id": "uuid",
  "name": "Main Character",
  "embedding_count": 2,
  "average_embedding": [0.111, -0.222, ...]
}
```

---

#### POST `/api/v1/character/verify`
Verify if an image contains a registered character.

**Request Body:**
```json
{
  "character_id": "uuid",
  "test_image": "base64"
}
```

**Response:**
```json
{
  "match": true,
  "similarity": 0.92,
  "threshold": 0.85,
  "confidence": "high"
}
```

---

### 7. JOB MANAGEMENT

#### GET `/api/v1/jobs/list`
List all jobs.

**Query Parameters:**
- `status`: pending, running, completed, failed
- `limit`: Number of results (default: 50)
- `offset`: Pagination offset

---

#### GET `/api/v1/jobs/{job_id}`
Get job status and details.

**Response:**
```json
{
  "job_id": "uuid",
  "type": "video_generation",
  "status": "running",
  "progress": 65,
  "created_at": "2025-12-17T12:00:00Z",
  "updated_at": "2025-12-17T12:01:30Z",
  "result": null,
  "error": null
}
```

---

#### POST `/api/v1/jobs/{job_id}/cancel`
Cancel a running job.

---

### 8. WEBSOCKET

#### WS `/ws/{job_id}`
Real-time job progress updates.

**Messages (Server → Client):**
```json
{
  "type": "progress",
  "job_id": "uuid",
  "progress": 65,
  "message": "Generating frame 78/121",
  "timestamp": "2025-12-17T12:01:30Z"
}
```

```json
{
  "type": "completed",
  "job_id": "uuid",
  "result": {
    "video_url": "/outputs/videos/uuid.mp4"
  }
}
```

```json
{
  "type": "error",
  "job_id": "uuid",
  "error": "GPU out of memory",
  "details": "..."
}
```

---

## 🔧 ERROR HANDLING

All errors follow this format:

```json
{
  "error": true,
  "code": "VALIDATION_ERROR",
  "message": "Prompt is required",
  "details": {
    "field": "prompt",
    "constraint": "required"
  },
  "timestamp": "2025-12-17T12:00:00Z"
}
```

**Error Codes:**
| Code | HTTP Status | Description |
|------|-------------|-------------|
| `VALIDATION_ERROR` | 400 | Invalid input |
| `NOT_FOUND` | 404 | Resource not found |
| `RATE_LIMITED` | 429 | Too many requests |
| `GPU_ERROR` | 500 | GPU processing error |
| `MODEL_ERROR` | 500 | Model loading error |
| `EXTERNAL_API_ERROR` | 502 | External service error |

---

## 📊 RATE LIMITS

| Endpoint | Limit | Window |
|----------|-------|--------|
| `/enhance/*` | 60 | 1 min |
| `/generate/image` | 30 | 1 min |
| `/video/*` | 10 | 1 min |
| `/suno/*` | 10 | 1 min |

---

## 📁 FILE PATHS

| Type | Path |
|------|------|
| Uploads | `/app/data/uploads/` |
| Outputs | `/app/data/outputs/` |
| Cache | `/app/data/cache/` |
| Models | `/app/models/` |

---

## 🏷️ STATUS CODES

| Status | Description |
|--------|-------------|
| `pending` | Job queued |
| `running` | Currently processing |
| `completed` | Successfully finished |
| `failed` | Error occurred |
| `cancelled` | User cancelled |

---

## 📚 SDK EXAMPLES

### Python
```python
import httpx

client = httpx.Client(base_url="http://localhost:8000")

# Enhance prompt
response = client.post("/api/v1/enhance/prompt", json={
    "prompt": "woman singing",
    "enhancement_level": "full"
})
enhanced = response.json()["enhanced_prompt"]

# Generate image
response = client.post("/api/v1/generate/image", json={
    "prompt": enhanced,
    "style_preset": "Cinematic"
})
image_url = response.json()["image_url"]
```

### cURL
```bash
# Enhance prompt
curl -X POST http://localhost:8000/api/v1/enhance/prompt \
  -H "Content-Type: application/json" \
  -d '{"prompt": "woman singing", "enhancement_level": "full"}'

# Check Suno credits
curl http://localhost:8000/api/v1/suno/credits
```

### JavaScript
```javascript
const response = await fetch('http://localhost:8000/api/v1/enhance/prompt', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    prompt: 'woman singing',
    enhancement_level: 'full'
  })
});
const { enhanced_prompt } = await response.json();
```
