<p align="center">
  <img src="https://img.shields.io/badge/🍌-NANO_BANANA_STUDIO_PRO-FFD700?style=for-the-badge&labelColor=000000" alt="Nano Banana Studio Pro"/>
</p>

<h1 align="center">🍌 NANO BANANA STUDIO PRO v2.0.0</h1>

<p align="center">
  <strong>Enterprise-Grade AI Video Production Pipeline</strong><br>
  <em>Transform ideas into stunning videos with AI-powered intelligence</em>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Version-2.0.0-blue?style=flat-square" alt="Version"/>
  <img src="https://img.shields.io/badge/License-MIT-green?style=flat-square" alt="License"/>
  <img src="https://img.shields.io/badge/Python-3.10+-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python"/>
  <img src="https://img.shields.io/badge/React-18.2-61DAFB?style=flat-square&logo=react&logoColor=black" alt="React"/>
  <img src="https://img.shields.io/badge/FastAPI-0.109-009688?style=flat-square&logo=fastapi&logoColor=white" alt="FastAPI"/>
  <img src="https://img.shields.io/badge/Docker-Ready-2496ED?style=flat-square&logo=docker&logoColor=white" alt="Docker"/>
</p>

<p align="center">
  <a href="#-features">Features</a> •
  <a href="#-quick-start">Quick Start</a> •
  <a href="#-api-reference">API</a> •
  <a href="#-architecture">Architecture</a> •
  <a href="#-timeline-editor">Timeline Editor</a> •
  <a href="#-documentation">Docs</a>
</p>

---

## 🎬 What is Nano Banana Studio Pro?

Nano Banana Studio Pro is a **complete, self-hosted AI video production system** that transforms simple text prompts into professional-quality videos with:

- 🎨 **AI Image Generation** - Gemini, FLUX, SDXL, and more
- 🎬 **Video Animation** - Runway, Kling, SVD, LTX-Video
- 🎵 **AI Music Generation** - Suno API integration
- 👤 **Character Consistency** - Face detection & embedding
- 🎙️ **Voice & Audio** - Whisper, TTS, beat detection
- 📺 **YouTube Publishing** - Direct upload with metadata

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                                                                                     │
│   📝 PROMPT          🎨 IMAGE           🎬 VIDEO          🎵 AUDIO         📤 OUTPUT│
│                                                                                     │
│   ┌─────────┐       ┌─────────┐       ┌─────────┐       ┌─────────┐     ┌─────────┐│
│   │ 7-Stage │  ──▶  │ Multi   │  ──▶  │ Animate │  ──▶  │ Beat    │ ──▶ │ YouTube ││
│   │ Enhance │       │ Model   │       │ + Ken   │       │ Sync    │     │ Publish ││
│   │ Pipeline│       │ Generate│       │ Burns   │       │ + Mix   │     │ + Export││
│   └─────────┘       └─────────┘       └─────────┘       └─────────┘     └─────────┘│
│                                                                                     │
│   ✅ LLM-powered     ✅ 30+ models     ✅ 4 providers    ✅ Suno AI      ✅ One-click│
│   ✅ Style DNA       ✅ Character      ✅ Transitions    ✅ Whisper      ✅ Metadata │
│   ✅ Consistency     ✅ Batch mode     ✅ Assembly       ✅ TTS          ✅ Analytics│
│                                                                                     │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

---

## ✨ Features at a Glance

<table>
<tr>
<td width="50%">

### 🎨 Image Generation
- **Text-to-Image** with Gemini, FLUX, SDXL
- **Multi-Reference Blending** (up to 14 images)
- **Character Consistency** with IPAdapter
- **Style Transfer** with 14 presets
- **ControlNet** (Pose, Depth, Canny)
- **Batch Processing** for efficiency

</td>
<td width="50%">

### 🎬 Video Production
- **Image-to-Video** animation
- **Ken Burns Effects** (pan, zoom, parallax)
- **25+ Transitions** (fade, wipe, zoom, etc.)
- **Multi-Scene Assembly**
- **Export Presets** (YouTube, TikTok, Instagram)
- **Real-time Preview**

</td>
</tr>
<tr>
<td width="50%">

### 🎵 Audio Intelligence
- **AI Music Generation** via Suno
- **Beat Detection** with Librosa/Aubio
- **Beat-Synced Transitions**
- **Speech Recognition** with Whisper
- **Text-to-Speech** (Bark, XTTS, ElevenLabs)
- **Audio Mixing** with FFmpeg

</td>
<td width="50%">

### 👤 Character System
- **Face Detection** (468 landmarks)
- **Face Embedding** (512-dim vectors)
- **Character Registration** database
- **Similarity Verification** (≥0.85 threshold)
- **Multi-Reference Averaging**
- **Auto-Rejection** of inconsistent frames

</td>
</tr>
</table>

---

## 🏗️ Architecture

```
┌──────────────────────────────────────────────────────────────────────────────────────┐
│                           NANO BANANA STUDIO PRO v2.0                                │
├──────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐ │
│  │                              🖥️ FRONTEND (React 18)                             │ │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐        │ │
│  │  │  Timeline    │  │   Scene      │  │   Tool       │  │   Render     │        │ │
│  │  │  Editor      │  │   Gallery    │  │   Panel      │  │   Panel      │        │ │
│  │  │  (NLE)       │  │   Preview    │  │   Controls   │  │   Export     │        │ │
│  │  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘        │ │
│  └─────────────────────────────────────────────────────────────────────────────────┘ │
│                                         │                                            │
│                              ┌──────────▼──────────┐                                 │
│                              │   API Client (50+)  │                                 │
│                              │   axios + WebSocket │                                 │
│                              └──────────┬──────────┘                                 │
│                                         │                                            │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐ │
│  │                           🚀 BACKEND (FastAPI)                                  │ │
│  │                                                                                 │ │
│  │  ┌─────────────────────────────────────────────────────────────────────────┐   │ │
│  │  │                         52 API ENDPOINTS                                │   │ │
│  │  │  /api/v1/enhance/*     │  /api/v1/generate/*   │  /api/v1/animate/*    │   │ │
│  │  │  /api/v1/face/*        │  /api/v1/character/*  │  /api/v1/audio/*      │   │ │
│  │  │  /api/v1/suno/*        │  /api/v1/storyboard/* │  /api/v1/video/*      │   │ │
│  │  │  /api/v1/timeline/*    │  /api/v1/youtube/*    │  /api/v1/jobs/*       │   │ │
│  │  └─────────────────────────────────────────────────────────────────────────┘   │ │
│  │                                                                                 │ │
│  │  ┌──────────────────────────────────────────────────────────────────────────┐  │ │
│  │  │                         24 SERVICE MODULES                               │  │ │
│  │  │                                                                          │  │ │
│  │  │  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐            │  │ │
│  │  │  │ Face       │ │ LLM        │ │ Audio      │ │ Timeline   │            │  │ │
│  │  │  │ Service    │ │ Provider   │ │ Intel      │ │ Editor     │            │  │ │
│  │  │  └────────────┘ └────────────┘ └────────────┘ └────────────┘            │  │ │
│  │  │  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐            │  │ │
│  │  │  │ Suno       │ │ YouTube    │ │ Animation  │ │ Storyboard │            │  │ │
│  │  │  │ Music      │ │ Publishing │ │ Service    │ │ Generator  │            │  │ │
│  │  │  └────────────┘ └────────────┘ └────────────┘ └────────────┘            │  │ │
│  │  │  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐            │  │ │
│  │  │  │ Whisper    │ │ TTS        │ │ Thumbnail  │ │ Publishing │            │  │ │
│  │  │  │ Service    │ │ Service    │ │ Generator  │ │ Service    │            │  │ │
│  │  │  └────────────┘ └────────────┘ └────────────┘ └────────────┘            │  │ │
│  │  │  + 12 more services...                                                   │  │ │
│  │  └──────────────────────────────────────────────────────────────────────────┘  │ │
│  └─────────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                      │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐ │
│  │                           🔧 INFRASTRUCTURE                                     │ │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐          │ │
│  │  │ Redis    │  │ SQLite   │  │ FFmpeg   │  │ n8n      │  │ Docker   │          │ │
│  │  │ Cache    │  │ Database │  │ Media    │  │ Workflows│  │ Compose  │          │ │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘  └──────────┘          │ │
│  └─────────────────────────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 📝 7-Stage Prompt Enhancement Pipeline

Our LLM-powered prompt enhancement transforms simple ideas into cinematic masterpieces:

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                        7-STAGE PROMPT ENHANCEMENT PIPELINE                          │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                     │
│  INPUT: "A cat in a forest"                                                         │
│                                                                                     │
│  ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐                          │
│  │ STAGE 1 │───▶│ STAGE 2 │───▶│ STAGE 3 │───▶│ STAGE 4 │                          │
│  │ Concept │    │  Scene  │    │ Visual  │    │Cinematic│                          │
│  │Expansion│    │Definition│   │  Spec   │    │Language │                          │
│  └─────────┘    └─────────┘    └─────────┘    └─────────┘                          │
│       │              │              │              │                                │
│       ▼              ▼              ▼              ▼                                │
│  Theme analysis  Environment   Color palette  Camera angles                        │
│  Mood profile    Spatial comp  Lighting       Lens choice                          │
│  Visual metaphor Time context  Textures       Frame dynamics                       │
│                                                                                     │
│  ┌─────────┐    ┌─────────┐    ┌─────────┐                                         │
│  │ STAGE 5 │───▶│ STAGE 6 │───▶│ STAGE 7 │                                         │
│  │Narrative│    │Technical│    │ Polish  │                                         │
│  │ Context │    │  Params │    │  Final  │                                         │
│  └─────────┘    └─────────┘    └─────────┘                                         │
│       │              │              │                                               │
│       ▼              ▼              ▼                                               │
│  Story beat      Resolution     Style DNA                                          │
│  Emotional arc   Quality keys   Character inject                                   │
│  Engagement      Tech specs     Consistency                                        │
│                                                                                     │
│  OUTPUT: "Majestic Maine Coon cat with emerald eyes, sitting regally on a          │
│          moss-covered ancient oak root, enchanted forest backdrop with              │
│          volumetric god rays filtering through towering redwoods, mystical          │
│          atmosphere with floating pollen particles, shallow depth of field,         │
│          golden hour lighting, shot on Arri Alexa, 85mm f/1.4, cinematic           │
│          color grade with teal shadows and amber highlights, 8K resolution"        │
│                                                                                     │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 🖥️ Timeline Editor

Professional non-linear editing with **Simple** and **Advanced** modes:

### Simple Mode (One-Click Magic)
```
┌─────────────────────────────────────────────────────────────────────────┐
│  🍌 Nano Banana Studio Pro          [Simple] [Advanced]    [+ New]     │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌───────────────────────────────────────────────────────────────────┐ │
│  │  ✨ Quick Create - One Click Magic                                │ │
│  │                                                                   │ │
│  │  What's your video about?                                         │ │
│  │  ┌─────────────────────────────────────────────────────────────┐ │ │
│  │  │ A magical cat exploring an enchanted forest with glowing   │ │ │
│  │  │ butterflies...                                              │ │ │
│  │  └─────────────────────────────────────────────────────────────┘ │ │
│  │                                                                   │ │
│  │  Duration: [60 seconds ▼]    Style: [Cinematic ▼]                │ │
│  │                                                                   │ │
│  │  Music Prompt (optional):                                         │ │
│  │  ┌─────────────────────────────────────────────────────────────┐ │ │
│  │  │ Ethereal orchestral, magical wonder, gentle piano          │ │ │
│  │  └─────────────────────────────────────────────────────────────┘ │ │
│  │                                                                   │ │
│  │          [ ✨ Create Magic Video ]                                │ │
│  └───────────────────────────────────────────────────────────────────┘ │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### Advanced Mode (Full Control)
```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  🍌 Nano Banana Studio Pro              [Simple] [Advanced]         [+ New]        │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                     │
│  SCENE GALLERY                                                                      │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐                  │
│  │ Scene 1  │ │ Scene 2  │ │ Scene 3  │ │ Scene 4  │ │ Scene 5  │                  │
│  │ [img]    │ │ [img]    │ │ [img]    │ │ [img]    │ │ [img]    │                  │
│  │ ✅ 5.0s  │ │ ✅ 4.5s  │ │ ⏳ 5.0s  │ │ ⏳ 3.5s  │ │ ❌ 5.0s  │                  │
│  │ [✓] [✗]  │ │ [✓] [✗]  │ │ [✓] [✗]  │ │ [✓] [✗]  │ │ [✓] [✗]  │                  │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘                  │
│                                                                                     │
│  TIMELINE TRACK                                                     [Zoom: 100%]   │
│  ┌─────────────────────────────────────────────────────────────────────────────┐   │
│  │ 0:00    0:05    0:10    0:15    0:20    0:25    0:30    0:35    0:40       │   │
│  │ ├───────┼───────┼───────┼───────┼───────┼───────┼───────┼───────┼          │   │
│  │ │░░░░░░░│▓▓▓▓▓▓▓│░░░░░░░│▓▓▓▓▓▓▓│░░░░░░░│▓▓▓▓▓▓▓│░░░░░░░│▓▓▓▓▓▓▓│          │   │
│  │ │ Sc.1  │ Sc.2  │ Sc.3  │ Sc.4  │ Sc.5  │ Sc.6  │ Sc.7  │ Sc.8  │          │   │
│  │ └───────┴───────┴───────┴───────┴───────┴───────┴───────┴───────┴          │   │
│  │ 🎵 ════════════════════════════════════════════════════════════            │   │
│  └─────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                     │
│  TOOLS                              │  RENDER                                       │
│  ┌─────────────────────────────────┐│  ┌───────────────────────────────────────┐   │
│  │ 🎬 Camera   [Pan ▼] [50%]       ││  │ Preset: [YouTube 1080p ▼]             │   │
│  │ 🔀 Transition [Fade ▼] [0.5s]   ││  │ Total: 23 scenes | 01:45              │   │
│  │ 🎨 Color    [Cinematic ▼]       ││  │ Approved: 20/23                       │   │
│  │ ⚡ Speed    [1.0x]              ││  │                                       │   │
│  │                                  ││  │ [ 🎬 Render Video ]                   │   │
│  │ [↶ Undo] [↷ Redo]               ││  │ [ 📺 Upload to YouTube ]              │   │
│  └─────────────────────────────────┘│  └───────────────────────────────────────┘   │
│                                                                                     │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 📡 API Reference

### Complete Endpoint Coverage (52 Endpoints)

<details>
<summary><b>📝 Prompt Enhancement</b></summary>

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/enhance/concept` | Stage 1: Concept expansion |
| `POST` | `/api/v1/enhance/full` | Full 7-stage pipeline |

</details>

<details>
<summary><b>👤 Face & Character</b></summary>

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/face/extract` | Extract face from image |
| `POST` | `/api/v1/character/register` | Register new character |
| `GET` | `/api/v1/character/{id}` | Get character details |
| `POST` | `/api/v1/character/verify` | Verify character consistency |

</details>

<details>
<summary><b>🎨 Image Generation</b></summary>

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/generate/image` | Generate single image |
| `POST` | `/api/v1/generate/batch` | Batch image generation |

</details>

<details>
<summary><b>🎬 Animation</b></summary>

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/animate/image` | Animate still image to video |

</details>

<details>
<summary><b>🎵 Audio</b></summary>

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/audio/analyze` | Analyze audio (beats, sections) |
| `POST` | `/api/v1/audio/mix` | Mix multiple audio tracks |
| `POST` | `/api/v1/suno/generate` | Generate AI music |

</details>

<details>
<summary><b>🎬 Video & Storyboard</b></summary>

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/storyboard/generate` | Generate AI storyboard |
| `POST` | `/api/v1/video/assemble` | Assemble final video |

</details>

<details>
<summary><b>📺 YouTube</b></summary>

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/youtube/accounts` | List connected accounts |
| `POST` | `/api/v1/youtube/accounts/add` | Add YouTube account |
| `DELETE` | `/api/v1/youtube/accounts/{id}` | Remove account |
| `POST` | `/api/v1/youtube/upload` | Upload video to YouTube |
| `POST` | `/api/v1/youtube/quick-upload` | One-click upload |
| `GET` | `/api/v1/youtube/playlists/{id}` | Get playlists |
| `POST` | `/api/v1/youtube/playlists/{id}` | Create playlist |
| `POST` | `/api/v1/youtube/generate-metadata` | Generate video metadata |
| `GET` | `/api/v1/youtube/analytics/{acc}/{vid}` | Get video analytics |

</details>

<details>
<summary><b>🎞️ Timeline Editor (25+ endpoints)</b></summary>

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/timeline/quick-create` | One-click project creation |
| `GET` | `/api/v1/timeline/{id}/preview-gallery` | Get scene previews |
| `POST` | `/api/v1/timeline/{id}/scenes/{idx}/approve` | Approve scene |
| `POST` | `/api/v1/timeline/{id}/scenes/{idx}/reject` | Reject & regenerate |
| `POST` | `/api/v1/timeline/{id}/approve-all` | Approve all scenes |
| `POST` | `/api/v1/timeline/{id}/render` | Render final video |
| `POST` | `/api/v1/timeline/projects` | Create project |
| `GET` | `/api/v1/timeline/projects` | List projects |
| `GET` | `/api/v1/timeline/{id}` | Get project details |
| `GET` | `/api/v1/timeline/{id}/timeline` | Get timeline view |
| `POST` | `/api/v1/timeline/{id}/scenes` | Add new scene |
| `POST` | `/api/v1/timeline/{id}/scenes/{idx}/regenerate` | Regenerate scene |
| `POST` | `/api/v1/timeline/{id}/scenes/{idx}/style-transfer` | Apply style |
| `POST` | `/api/v1/timeline/{id}/scenes/{idx}/camera` | Set camera movement |
| `POST` | `/api/v1/timeline/{id}/scenes/{idx}/transition` | Set transition |
| `POST` | `/api/v1/timeline/{id}/scenes/{idx}/color-grade` | Apply color grade |
| `POST` | `/api/v1/timeline/{id}/scenes/{idx}/split` | Split scene |
| `POST` | `/api/v1/timeline/{id}/scenes/{idx}/duplicate` | Duplicate scene |
| `DELETE` | `/api/v1/timeline/{id}/scenes/{idx}` | Delete scene |
| `POST` | `/api/v1/timeline/{id}/scenes/{idx}/speed` | Set playback speed |
| `POST` | `/api/v1/timeline/{id}/undo` | Undo last action |
| `POST` | `/api/v1/timeline/{id}/redo` | Redo action |
| `POST` | `/api/v1/timeline/{id}/publish-youtube` | Publish to YouTube |

</details>

<details>
<summary><b>📁 Files & Jobs</b></summary>

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/upload/image` | Upload image file |
| `POST` | `/api/v1/upload/audio` | Upload audio file |
| `GET` | `/api/v1/download/{filename}` | Download file |
| `POST` | `/api/v1/parse/markdown` | Parse markdown |
| `GET` | `/api/v1/jobs/{id}` | Get job status |
| `GET` | `/api/v1/jobs` | List all jobs |
| `GET` | `/api/v1/workflow/status/{id}` | Get workflow status |
| `WS` | `/ws/{job_id}` | Real-time job updates |

</details>

---

## 🚀 Quick Start

### Option 1: Docker (Recommended)

```bash
# Clone repository
git clone https://github.com/Ghenghis/nano-banana-studio.git
cd nano-banana-studio

# Copy environment template
cp .env.example .env

# Edit configuration (add your API keys)
nano .env

# Start all services
docker compose up -d

# Access services:
# - API: http://localhost:8000
# - Frontend: http://localhost:3000
# - API Docs: http://localhost:8000/docs
```

### Option 2: Local Development

```bash
# Backend
pip install -r requirements.txt
uvicorn backend.api.main:app --reload --port 8000

# Frontend (new terminal)
cd frontend
npm install
npm run dev
```

### Option 3: Windows PowerShell

```powershell
# Setup
.\scripts\setup.ps1

# Run development server
.\scripts\run-dev.ps1
```

---

## 🔧 Configuration

### Environment Variables

```env
# AI Model API Keys (at least one required)
OPENAI_API_KEY=sk-your-key
ANTHROPIC_API_KEY=sk-ant-your-key
GOOGLE_GENERATIVE_AI_API_KEY=your-key

# Local LLM (optional)
OLLAMA_API_BASE_URL=http://localhost:11434
LMSTUDIO_API_BASE_URL=http://localhost:1234

# Music Generation
SUNO_COOKIE=your-suno-cookie

# Animation Providers (optional)
RUNWAY_API_KEY=your-key
KLING_API_KEY=your-key

# TTS (optional)
ELEVENLABS_API_KEY=your-key

# Cache & Database
REDIS_URL=redis://localhost:6379
```

---

## 📊 Service Modules (24 Total)

| Category | Services |
|----------|----------|
| **Core AI** | FaceService, LLMProviderService, PromptEnhancer8K |
| **Media** | AnimationService, AudioIntelligenceService, SceneAssemblyService |
| **Generation** | ComfyUIService, LTXVideoService, MusicGenService |
| **Audio** | WhisperService, TTSService, SunoService |
| **Publishing** | YouTubeService, PublishingService, ThumbnailService |
| **Editor** | TimelineEditorService, StoryboardService |
| **Content** | ScreenplayService, PodcastService |

---

## 🎨 Supported Models

### Image Generation
| Model | Provider | Notes |
|-------|----------|-------|
| Gemini Pro | Google | Fast, high quality |
| FLUX.1 | Black Forest | Excellent composition |
| SDXL | Stability AI | Highly customizable |
| Midjourney | Midjourney | Via API |

### Video Animation
| Model | Provider | Features |
|-------|----------|----------|
| LTX-Video | Lightricks | Keyframe control |
| WanVideo | Wan | High quality |
| SVD | Stability AI | Consistent motion |
| Runway Gen-3 | Runway | Professional grade |

### LLM Providers
| Provider | Models | Priority |
|----------|--------|----------|
| LM Studio | Llama 3.1, Mistral, Qwen | Local (1st) |
| Ollama | Llama, Codellama | Local (2nd) |
| OpenRouter | Gemini, GPT-4, Claude | Cloud (fallback) |

---

## 📁 Project Structure

```
nano-banana-studio/
├── backend/
│   ├── api/
│   │   ├── main.py              # FastAPI app (52 endpoints)
│   │   └── middleware.py        # Error handling
│   ├── services/                # 24 service modules
│   │   ├── face_service.py      # Face detection & embedding
│   │   ├── llm_provider_service.py  # Multi-LLM with fallback
│   │   ├── audio_intelligence_service.py
│   │   ├── timeline/            # Timeline editor
│   │   └── ...
│   └── workers/                 # Background workers
├── frontend/
│   ├── src/
│   │   ├── App.jsx              # Main React app
│   │   └── api.js               # API client (50+ methods)
│   └── package.json
├── config/
│   ├── llm_providers.yaml       # LLM configuration
│   ├── models.yaml              # Model registry
│   ├── styles.yaml              # Style presets
│   └── prompts/                 # 7-stage prompt templates
├── n8n/workflows/               # 14 automation workflows
├── docs/                        # 17 documentation files
├── scripts/code-quality/        # Linting & auto-repair
├── tests/                       # Test suite
├── docker-compose.yml
└── requirements.txt
```

---

## 🧪 Testing

```bash
# Run all tests
pytest tests/ -v

# Run specific test
pytest tests/test_timeline_editor.py -v

# Code quality checks
.\scripts\code-quality\run-all-checks.ps1
```

---

## 📚 Documentation

| Document | Description |
|----------|-------------|
| [API Reference](docs/API_REFERENCE.md) | Complete API documentation |
| [Architecture](docs/ARCHITECTURE.md) | System design |
| [Timeline Editor](docs/TIMELINE_EDITOR.md) | Editor guide |
| [YouTube Publishing](docs/YOUTUBE_PUBLISHING.md) | YouTube integration |
| [Suno Integration](docs/SUNO_INTEGRATION_GUIDE.md) | Music generation |
| [Troubleshooting](docs/TROUBLESHOOTING.md) | Common issues |
| [Code Quality](docs/CODE_QUALITY_STANDARDS.md) | Coding standards |

---

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

<p align="center">
  <b>Made with 🍌 by the Nano Banana Team</b><br>
  <em>Transform your ideas into stunning videos with AI</em>
</p>

<p align="center">
  <a href="https://github.com/Ghenghis/nano-banana-studio/issues">Report Bug</a> •
  <a href="https://github.com/Ghenghis/nano-banana-studio/issues">Request Feature</a>
</p>
