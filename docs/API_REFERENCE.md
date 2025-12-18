# 🍌 NANO BANANA STUDIO PRO - API REFERENCE

> **Version:** 2.0.0  
> **Base URL:** `http://localhost:8000`  
> **OpenAPI Docs:** `http://localhost:8000/docs`

---

## 📋 Table of Contents

1. [Authentication](#authentication)
2. [Prompt Enhancement](#prompt-enhancement)
3. [Face & Character](#face--character)
4. [Image Generation](#image-generation)
5. [Video Generation](#video-generation)
6. [Audio Processing](#audio-processing)
7. [Suno Music](#suno-music)
8. [Job Management](#job-management)
9. [WebSocket](#websocket)
10. [Error Handling](#error-handling)

---

## Authentication

Currently, the API operates without authentication for local development. For production, configure API keys in environment variables.

---

## Prompt Enhancement

### POST `/api/v1/enhance/concept`
Stage 1: Expand concept with creative depth.

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
  "job_id": "enhance_concept_20251217_120000_abc123",
  "stage": "concept",
  "enhanced_concept": "A passionate female vocalist performing in a professional recording studio, dynamic and musical energy",
  "core_theme": "Musical performance and artistic expression",
  "mood_profile": ["passionate", "dynamic", "professional"],
  "emotional_keywords": ["powerful", "soulful", "expressive", "artistic", "vibrant"],
  "visual_metaphors": ["voice as color", "sound waves as light"]
}
```

---

### POST `/api/v1/enhance/full`
Run complete 7-stage enhancement pipeline.

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
  "job_id": "enhance_full_20251217_120000_abc123",
  "status": "processing",
  "message": "Full enhancement started"
}
```

**Final Result (via WebSocket or polling):**
```json
{
  "job_id": "enhance_full_20251217_120000_abc123",
  "original_prompt": "woman singing in a studio",
  "enhanced_prompt": "A passionate female vocalist performing in a professional recording studio, centered composition, cinematic color grading, dramatic three-point lighting, shot on 35mm anamorphic lens, shallow depth of field, emotional storytelling moment, 8K resolution, photorealistic, masterpiece quality",
  "negative_prompt": "blurry, low quality, distorted, amateur, flat lighting, overexposed, underexposed",
  "stages": {
    "concept": "...",
    "scene": "...",
    "visual": "...",
    "cinematic": "...",
    "narrative": "...",
    "technical": "...",
    "consistency": "..."
  },
  "style_dna": {
    "style": "Cinematic",
    "platform": "YouTube (16:9)",
    "anchor_keywords": ["vocalist", "studio", "cinematic", "dramatic", "professional"]
  }
}
```

---

## Face & Character

### POST `/api/v1/face/extract`
Extract face from image for character consistency.

**Request (Multipart Form):**
```
image: <file>
OR
image_base64: <base64_string>
OR
image_url: <url>
```

**Response:**
```json
{
  "job_id": "face_extract_20251217_120000_abc123",
  "face_detected": true,
  "face_count": 1,
  "primary_face": {
    "confidence": 0.98,
    "bounding_box": {"x": 100, "y": 50, "width": 200, "height": 250}
  },
  "face_embedding": [0.123, -0.456, ...],
  "landmarks": [{"x": 150.5, "y": 100.2}, ...],
  "image_path": "/app/data/uploads/face_extract_20251217_120000_abc123_input.jpg"
}
```

---

### POST `/api/v1/character/register`
Register a character for consistency across generations.

**Request Body:**
```json
{
  "name": "Sarah",
  "face_embedding": [0.123, -0.456, ...],
  "reference_images": ["base64_img1", "base64_img2"],
  "style_keywords": ["professional", "confident", "warm smile"]
}
```

**Response:**
```json
{
  "character_id": "char_a1b2c3d4",
  "name": "Sarah",
  "status": "registered"
}
```

---

### GET `/api/v1/character/{char_id}`
Get registered character details.

**Response:**
```json
{
  "id": "char_a1b2c3d4",
  "name": "Sarah",
  "face_embedding": [0.123, -0.456, ...],
  "reference_images": ["path1.jpg", "path2.jpg"],
  "style_keywords": ["professional", "confident"],
  "created_at": "2025-12-17T12:00:00Z"
}
```

---

### POST `/api/v1/character/verify`
Verify if image matches registered character.

**Request (Form):**
```
character_id: char_a1b2c3d4
image_base64: <base64_string>
```

**Response:**
```json
{
  "character_id": "char_a1b2c3d4",
  "match_score": 0.92,
  "is_consistent": true,
  "threshold": 0.85
}
```

---

## Image Generation

### POST `/api/v1/generate/image`
Generate image from text prompt.

**Request Body:**
```json
{
  "prompt": "A professional woman in a recording studio",
  "negative_prompt": "blurry, distorted",
  "style": "Cinematic",
  "aspect_ratio": "16:9",
  "quality": "high",
  "num_images": 1,
  "character_id": "char_a1b2c3d4",
  "reference_image": "<base64_optional>",
  "seed": 42,
  "use_enhancement": true
}
```

**Response:**
```json
{
  "job_id": "generate_image_20251217_120000_abc123",
  "status": "processing",
  "fingerprint": "sha256_hash"
}
```

**Final Result:**
```json
{
  "job_id": "generate_image_20251217_120000_abc123",
  "status": "completed",
  "result": {
    "image_data": "<base64>",
    "image_path": "/app/data/outputs/generate_image_20251217_120000_abc123.png",
    "prompt_used": "Enhanced prompt...",
    "fingerprint": "sha256_hash"
  }
}
```

---

### POST `/api/v1/generate/batch`
Generate multiple images in parallel.

**Request (Form):**
```
prompts: ["prompt1", "prompt2", "prompt3"]
style: Cinematic
aspect_ratio: 16:9
```

**Response:**
```json
{
  "job_id": "generate_batch_20251217_120000_abc123",
  "batch_jobs": [
    "generate_batch_20251217_120000_abc123_0",
    "generate_batch_20251217_120000_abc123_1",
    "generate_batch_20251217_120000_abc123_2"
  ],
  "total": 3
}
```

---

## Video Generation

### POST `/api/v1/animate/image`
Animate a still image into video.

**Request Body:**
```json
{
  "image_base64": "<base64>",
  "image_url": null,
  "motion_type": "subtle",
  "duration": 4.0,
  "provider": "auto"
}
```

**Motion Types:** `subtle`, `talking`, `dancing`, `walking`, `zoom_in`, `zoom_out`, `pan_left`, `pan_right`

**Providers:** `auto`, `runway`, `kling`, `svd`, `ltx`

**Response:**
```json
{
  "job_id": "animate_image_20251217_120000_abc123",
  "status": "processing",
  "motion_type": "subtle"
}
```

**Final Result:**
```json
{
  "job_id": "animate_image_20251217_120000_abc123",
  "status": "completed",
  "result": {
    "video_path": "/app/data/outputs/animate_image_20251217_120000_abc123_animated.mp4",
    "duration": 4.0,
    "motion_type": "subtle",
    "provider": "ffmpeg_kenburns"
  }
}
```

---

### POST `/api/v1/video/assemble`
Assemble final video from scenes.

**Request Body:**
```json
{
  "manifest": {
    "scenes": [
      {
        "id": "scene_1",
        "image_path": "/path/to/image1.png",
        "video_path": "/path/to/video1.mp4",
        "duration": 5.0,
        "transition": "dissolve",
        "transition_duration": 1.0
      }
    ],
    "audio": {
      "music_path": "/path/to/music.mp3",
      "voiceover_path": "/path/to/voiceover.mp3",
      "music_volume": 0.7,
      "voiceover_volume": 1.0
    },
    "output": {
      "filename": "final_video.mp4",
      "resolution": "1920x1080",
      "fps": 30
    }
  },
  "platform": "YouTube (16:9)",
  "quality": "high",
  "transition_style": "dissolve",
  "ken_burns": true,
  "color_grading": "cinematic"
}
```

**Response:**
```json
{
  "job_id": "video_assemble_20251217_120000_abc123",
  "status": "processing"
}
```

---

## Audio Processing

### POST `/api/v1/audio/analyze`
Analyze audio for beats, tempo, and lyrics.

**Request (Multipart Form):**
```
audio: <file>
OR
audio_base64: <base64_string>
extract_lyrics: true
detect_beats: true
```

**Response:**
```json
{
  "job_id": "audio_analyze_20251217_120000_abc123",
  "duration": 180.5,
  "bpm": 120,
  "beats": [0.5, 1.0, 1.5, 2.0, ...],
  "energy_curve": [0.3, 0.5, 0.8, 0.9, ...],
  "sections": [
    {"name": "intro", "start": 0, "end": 8, "energy": "low"},
    {"name": "verse1", "start": 8, "end": 32, "energy": "medium"},
    {"name": "chorus1", "start": 32, "end": 48, "energy": "high"}
  ],
  "lyrics": "Verse 1:\nLyrics here...\n\nChorus:\nMore lyrics...",
  "audio_path": "/app/data/uploads/audio_analyze_20251217_120000_abc123_audio.mp3"
}
```

---

### POST `/api/v1/audio/mix`
Mix multiple audio tracks.

**Request (Multipart Form):**
```
tracks: [<file1>, <file2>, <file3>]
volumes: "[1.0, 0.7, 0.5]"
mode: "layer"
```

**Modes:** `layer` (simultaneous), `sequence` (concatenate), `ducking` (auto-duck)

**Response:**
```json
{
  "job_id": "audio_mix_20251217_120000_abc123",
  "output_path": "/app/data/outputs/audio_mix_20251217_120000_abc123_mixed.mp3",
  "tracks_mixed": 3,
  "mode": "layer"
}
```

---

## Suno Music

### POST `/api/v1/suno/generate`
Generate AI music.

**Request Body:**
```json
{
  "prompt": "upbeat pop song about summer adventures",
  "genre": "pop",
  "duration": 120,
  "instrumental": false
}
```

**Response:**
```json
{
  "job_id": "suno_generate_20251217_120000_abc123",
  "status": "processing",
  "genre": "pop"
}
```

**Final Result:**
```json
{
  "job_id": "suno_generate_20251217_120000_abc123",
  "status": "completed",
  "result": {
    "audio_path": "/app/data/outputs/suno_20251217_120000_abc123.mp3",
    "audio_url": "https://cdn.suno.ai/...",
    "lyrics": "Verse 1:\nSunshine on my face...",
    "prompt": "upbeat pop song about summer adventures",
    "genre": "pop",
    "duration": 120
  }
}
```

---

### POST `/api/v1/suno/lyrics` (via n8n)
Generate lyrics only (FREE - no credits).

**Request Body:**
```json
{
  "prompt": "a song about coding and AI"
}
```

**Response:**
```json
{
  "success": true,
  "lyrics": "[Verse 1]\nLines of code flowing through the night...",
  "timestamp": "2025-12-17T12:00:00Z"
}
```

---

### GET `/api/v1/suno/credits` (via n8n)
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

## Job Management

### GET `/api/v1/jobs/{job_id}`
Get job status.

**Response:**
```json
{
  "job_id": "generate_image_20251217_120000_abc123",
  "status": "processing",
  "progress": 0.65,
  "current_stage": "generating",
  "result": null,
  "error": null,
  "created_at": "2025-12-17T12:00:00Z",
  "updated_at": "2025-12-17T12:00:30Z"
}
```

**Status Values:** `queued`, `processing`, `completed`, `failed`, `cancelled`

---

### POST `/api/v1/jobs/{job_id}/cancel`
Cancel a running job.

**Response:**
```json
{
  "job_id": "generate_image_20251217_120000_abc123",
  "status": "cancelled",
  "message": "Job cancelled successfully"
}
```

---

## WebSocket

### WS `/ws/{job_id}`
Real-time job progress updates.

**Connection:**
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/generate_image_20251217_120000_abc123');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Progress:', data.progress);
  console.log('Stage:', data.current_stage);
};
```

**Messages Received:**
```json
{
  "job_id": "generate_image_20251217_120000_abc123",
  "status": "processing",
  "progress": 0.5,
  "current_stage": "generating"
}
```

```json
{
  "job_id": "generate_image_20251217_120000_abc123",
  "status": "completed",
  "progress": 1.0,
  "result": {...}
}
```

---

## Error Handling

### Error Response Format
```json
{
  "detail": "Error message here",
  "status_code": 400,
  "error_type": "validation_error"
}
```

### HTTP Status Codes
| Code | Meaning |
|------|---------|
| 200 | Success |
| 201 | Created |
| 400 | Bad Request |
| 404 | Not Found |
| 422 | Validation Error |
| 500 | Server Error |
| 503 | Service Unavailable |

### Common Errors
| Error | Cause | Solution |
|-------|-------|----------|
| `No image provided` | Missing image data | Include image_base64 or file |
| `Character not found` | Invalid char_id | Register character first |
| `All LLM providers unavailable` | No LLM service | Start LM Studio or configure API key |
| `Suno API not configured` | Missing cookie | Set SUNO_COOKIE env var |

---

## Rate Limits

| Endpoint | Limit |
|----------|-------|
| Image Generation | 10/minute |
| Video Generation | 5/minute |
| Audio Analysis | 20/minute |
| Suno Generation | Based on credits |

---

## SDK Examples

### Python
```python
import httpx

async def generate_image(prompt: str):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/api/v1/generate/image",
            json={
                "prompt": prompt,
                "style": "Cinematic",
                "use_enhancement": True
            }
        )
        return response.json()
```

### JavaScript
```javascript
const response = await fetch('http://localhost:8000/api/v1/generate/image', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    prompt: 'A beautiful sunset over the ocean',
    style: 'Cinematic'
  })
});
const data = await response.json();
```

### cURL
```bash
curl -X POST http://localhost:8000/api/v1/generate/image \
  -H "Content-Type: application/json" \
  -d '{"prompt": "A mountain landscape", "style": "Photorealistic"}'
```

---

## Related Documentation

- [README.md](../README.md) - Project overview
- [FEATURES.md](FEATURES.md) - Feature reference
- [WORKFLOWS.md](WORKFLOWS.md) - n8n workflows
