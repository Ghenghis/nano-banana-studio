# 🍌 NANO BANANA STUDIO PRO v2.0

<div align="center">

![Nano Banana Studio](https://img.shields.io/badge/🍌-Nano_Banana_Studio-yellow?style=for-the-badge)
![Version](https://img.shields.io/badge/Version-2.0.0-blue?style=for-the-badge)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)
![Python](https://img.shields.io/badge/Python-3.10+-blue?style=for-the-badge&logo=python)
![Docker](https://img.shields.io/badge/Docker-Ready-blue?style=for-the-badge&logo=docker)

**Enterprise-Grade AI Video Production Pipeline**

*Transform images and music into stunning videos with AI-powered character consistency, beat-synced transitions, and professional-grade output.*

[Features](#-features) • [Quick Start](#-quick-start) • [Architecture](#-architecture) • [API](#-api-reference) • [Workflows](#-n8n-workflows) • [Contributing](#-contributing)

</div>

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Features](#-features)
- [System Requirements](#-system-requirements)
- [Quick Start](#-quick-start)
- [Architecture](#-architecture)
- [Configuration](#-configuration)
- [API Reference](#-api-reference)
- [n8n Workflows](#-n8n-workflows)
- [Model Support](#-model-support)
- [Troubleshooting](#-troubleshooting)
- [Roadmap](#-roadmap)

---

## 🎬 Overview

Nano Banana Studio Pro is a comprehensive, self-hosted AI video production system that combines:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     NANO BANANA STUDIO PRO                                   │
│                                                                              │
│   📝 Prompt        🎨 Image         🎵 Audio         🎬 Video               │
│   Enhancement  →   Generation   →   Intelligence →   Assembly               │
│                                                                              │
│   7-Stage          Multi-Model      Beat Detection   Professional           │
│   Pipeline         Support          AI Music         Output                  │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Why Nano Banana?

| Feature | Commercial Tools | Nano Banana |
|---------|-----------------|-------------|
| **Cost** | $20-200/month | Free (self-hosted) |
| **Privacy** | Cloud-dependent | 100% local option |
| **Customization** | Limited | Fully extensible |
| **Models** | Proprietary | 30+ open models |
| **API Access** | Restricted | Full REST + WebSocket |
| **Character Consistency** | Basic | Advanced (512-dim embeddings) |

---

## ✨ Features

### 🎨 Image Generation
| Feature | Status | Technology | Description |
|---------|--------|------------|-------------|
| Text-to-Image | ✅ | Gemini, FLUX, SDXL | Generate images from text prompts |
| Multi-Reference Blending | ✅ | Custom algorithm | Blend up to 14 reference images |
| Character Consistency | ✅ | IPAdapter, InstantID | Preserve identity across generations |
| ControlNet Guidance | ✅ | Pose, Depth, Canny | Structural control for compositions |
| Style Transfer | ✅ | 14 built-in presets | Apply consistent visual styles |
| Batch Generation | ✅ | Parallel processing | Generate multiple images simultaneously |

### 🎬 Video Generation
| Feature | Status | Technology | Description |
|---------|--------|------------|-------------|
| Image-to-Video | ✅ | LTX-Video, WanVideo, SVD | Animate still images |
| Keyframe Control | ✅ | LTX-Video 0.9.7+ | Control specific frames |
| Motion Strength | ✅ | All video models | Adjust animation intensity |
| Ken Burns Effects | ✅ | FFmpeg-based | Pan, zoom, and parallax |
| Video Extension | ✅ | Frame interpolation | Extend video duration |
| Multi-Scene Assembly | ✅ | FFmpeg + xfade | Combine scenes with transitions |

### 🎵 Audio Intelligence
| Feature | Status | Technology | Description |
|---------|--------|------------|-------------|
| AI Music Generation | ✅ | MusicGen, Suno | Create original music |
| Beat Detection | ✅ | Librosa, Aubio | Analyze rhythm and tempo |
| Beat-Synced Transitions | ✅ | Custom algorithm | Sync transitions to beats |
| Lyrics Extraction | ✅ | Whisper | Transcribe vocals |
| Text-to-Speech | ✅ | Bark, XTTS, ElevenLabs | Generate voiceovers |
| Audio Mixing | ✅ | FFmpeg | Layer and mix tracks |
| Emotion Detection | 🔄 | Speech emotion models | Analyze vocal sentiment |

### 👤 Character System
| Feature | Status | Technology | Description |
|---------|--------|------------|-------------|
| Face Detection | ✅ | MediaPipe (468 landmarks) | Detect faces in images |
| Face Embedding | ✅ | InsightFace (512-dim) | Create identity vectors |
| Character Registration | ✅ | SQLite database | Store character profiles |
| Similarity Verification | ✅ | Cosine similarity ≥0.85 | Verify identity matches |
| Multi-Reference Averaging | ✅ | Up to 14 references | Robust identity capture |
| Auto-Rejection | ✅ | Threshold filtering | Reject inconsistent frames |

### 📝 Prompt Enhancement (7-Stage Pipeline)
| Stage | Name | Description |
|-------|------|-------------|
| 1 | **Concept Expansion** | Theme analysis, mood profile, visual metaphors |
| 2 | **Scene Definition** | Environment, spatial composition, time context |
| 3 | **Visual Specification** | Color palette, lighting design, texture profile |
| 4 | **Cinematic Language** | Camera angles, lens characteristics, frame dynamics |
| 5 | **Narrative Context** | Story beat, emotional arc, audience engagement |
| 6 | **Technical Parameters** | Quality keywords, resolution, technical specs |
| 7 | **Consistency Polish** | Style DNA extraction, character injection, final polish |

### 🔧 Production Tools
| Feature | Status | Description |
|---------|--------|-------------|
| 25+ Video Transitions | ✅ | FFmpeg xfade library |
| 14 Style Presets | ✅ | Pre-configured visual styles |
| Content-Addressed Cache | ✅ | SHA256 fingerprinting |
| Job Queue System | ✅ | Redis-backed with priorities |
| WebSocket Updates | ✅ | Real-time progress tracking |
| Export Formats | ✅ | MP4, MOV, GIF, WebM |

---

## 💻 System Requirements

### Minimum Requirements
| Component | Requirement |
|-----------|-------------|
| OS | Windows 10/11, Linux, macOS |
| CPU | 8+ cores |
| RAM | 16GB |
| GPU | NVIDIA GTX 1080 (8GB VRAM) |
| Storage | 50GB free space |
| Docker | 24.0+ with GPU support |

### Recommended (Your Setup)
| Component | Specification |
|-----------|---------------|
| CPU | AMD Ryzen 7 5800X3D |
| RAM | 128GB DDR4 |
| GPU (Primary) | RTX 3090 Ti (24GB VRAM) |
| GPU (Secondary) | RTX 3060 Ti (12GB VRAM) |
| Storage | 4TB NVMe |
| OS | Windows 11 + WSL2 |

---

## 🚀 Quick Start

### Option 1: Docker (Recommended)

```powershell
# Clone repository
git clone https://github.com/your-repo/nano-banana-studio.git
cd nano-banana-studio

# Copy environment template
copy env\.env.example .env

# Edit configuration
notepad .env

# Start all services
docker compose up -d

# Access services:
# - API: http://localhost:8000
# - n8n: http://localhost:5678
# - Docs: http://localhost:8000/docs
```

### Option 2: Local Development

```powershell
# Setup environment
.\scripts\setup.ps1

# Activate virtual environment
.\.venv\Scripts\activate

# Start development server
.\scripts\run-dev.ps1
```

### Option 3: Windows Native

```powershell
# Install dependencies
pip install -r requirements.txt

# Start FastAPI server
uvicorn backend.api.main:app --reload --host 0.0.0.0 --port 8000

# In another terminal, start n8n
npx n8n start
```

---

## 🏗 Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                            NANO BANANA STUDIO PRO                                │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                         USER INTERFACES                                  │   │
│  │  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐               │   │
│  │  │  n8n Forms    │  │  REST API     │  │  WebSocket    │               │   │
│  │  │  :5678        │  │  :8000        │  │  :8000/ws     │               │   │
│  │  └───────────────┘  └───────────────┘  └───────────────┘               │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
│                                       │                                         │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                      ORCHESTRATION (n8n)                                 │   │
│  │  • 14 Specialized Workflows    • Conditional Branching                  │   │
│  │  • Parallel Execution          • Error Handling & Retry                 │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
│                                       │                                         │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                      PROCESSING SERVICES                                 │   │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐      │   │
│  │  │ Prompt   │ │  Image   │ │  Face    │ │  Audio   │ │  Video   │      │   │
│  │  │ Enhancer │ │Generator │ │ Service  │ │ Analyzer │ │ Assembler│      │   │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘      │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
│                                       │                                         │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                      AI MODEL LAYER                                      │   │
│  │  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐                     │   │
│  │  │  LLM Pool    │ │  Vision      │ │  Audio       │                     │   │
│  │  │  (Local/API) │ │  (Diffusers) │ │  (MusicGen)  │                     │   │
│  │  └──────────────┘ └──────────────┘ └──────────────┘                     │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
│                                       │                                         │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                      INFRASTRUCTURE                                      │   │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐                    │   │
│  │  │  Redis   │ │  SQLite  │ │  Cache   │ │  Storage │                    │   │
│  │  │  :6379   │ │  (Local) │ │  (SHA256)│ │  /data/* │                    │   │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘                    │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### Directory Structure

```
nano-banana-studio/
├── 📁 backend/                  # Python backend services
│   ├── 📁 api/                  # FastAPI application
│   │   └── main.py              # Main API server (1,397 lines)
│   ├── 📁 prompt_enhancers/     # 7-stage prompt system
│   │   └── seven_stage_pipeline.py
│   ├── 📁 services/             # Core services
│   │   ├── captcha_solver.py    # 2Captcha integration
│   │   ├── comfyui_service.py   # ComfyUI integration
│   │   ├── face_service.py      # Face detection (780 lines)
│   │   ├── ltx_video_service.py # LTX-Video generation
│   │   ├── musicgen_service.py  # MusicGen local
│   │   ├── suno_pip_client.py   # Suno pip wrapper
│   │   ├── suno_service.py      # Suno REST client
│   │   └── whisper_service.py   # Speech recognition
│   └── 📁 workers/              # Background workers
│       ├── audio_worker.py      # Audio processing
│       └── video_worker.py      # Video assembly
├── 📁 config/                   # Configuration files
│   ├── models.yaml              # Model definitions
│   ├── model_registry_complete.yaml
│   ├── styles.yaml              # 14 style presets (344 lines)
│   ├── transitions.yaml         # 25+ transitions (337 lines)
│   └── 📁 prompts/              # System prompts
│       ├── cinematic_system.txt
│       ├── concept_system.txt
│       ├── consistency_system.txt
│       ├── narrative_system.txt
│       ├── scene_system.txt
│       ├── technical_system.txt
│       └── visual_system.txt
├── 📁 n8n/                      # n8n workflows
│   └── 📁 workflows/            # 14 JSON workflows
│       ├── 01_prompt_enhancer_master.json
│       ├── 02_image_generation.json
│       ├── 03_multi_asset_processor.json
│       ├── 04_video_assembly_pro.json
│       ├── 05_video_extender.json
│       ├── 06_master_pipeline.json
│       ├── 07_face_character_system.json
│       ├── 08_suno_music_generator.json
│       ├── 09_audio_beat_analyzer.json
│       ├── 10_image_to_video_animation.json
│       ├── 11_pdf_markdown_parser.json
│       ├── 12_comfyui_integration.json
│       ├── 13_suno_music_pipeline_v2.json
│       └── 99_full_music_video_pipeline.json
├── 📁 docker/                   # Docker configurations
│   └── docker-compose.suno.yml
├── 📁 scripts/                  # Automation scripts
│   ├── download-all-models.ps1  # Model downloader
│   ├── run-dev.ps1              # Development server
│   ├── setup.ps1                # Initial setup
│   ├── setup-suno.ps1           # Suno setup
│   └── test-suno.ps1            # Suno testing
├── 📁 docs/                     # Documentation
│   ├── ARCHITECTURE.md
│   ├── API_REFERENCE.md
│   ├── FEATURES.md
│   ├── GAP_ANALYSIS_ACTION_PLAN.md
│   ├── MASTER_MILESTONE_PLAN_v2.md
│   ├── SUNO_INTEGRATION_GUIDE.md
│   └── SUNO_QUICKSTART.md
├── 📁 data/                     # Runtime data
│   ├── 📁 uploads/              # User uploads
│   ├── 📁 outputs/              # Generated content
│   └── 📁 cache/                # Cached results
├── docker-compose.yml           # Main compose file
├── Dockerfile                   # API container
├── Dockerfile.ffmpeg            # FFmpeg container
├── Dockerfile.gpu               # GPU-enabled container
├── requirements.txt             # Python dependencies
└── README.md                    # This file
```

---

## 📚 Documentation Index

| Document | Description |
|----------|-------------|
| [README.md](README.md) | Project overview and quick start |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | System architecture and components |
| [docs/API_REFERENCE.md](docs/API_REFERENCE.md) | Complete API documentation |
| [docs/FEATURES.md](docs/FEATURES.md) | Detailed feature descriptions |
| [docs/WORKFLOWS.md](docs/WORKFLOWS.md) | n8n workflow documentation |
| [docs/CONFIGURATION.md](docs/CONFIGURATION.md) | Configuration guide |
| [docs/MODELS.md](docs/MODELS.md) | Supported AI models |
| [docs/SUNO_INTEGRATION_GUIDE.md](docs/SUNO_INTEGRATION_GUIDE.md) | Suno music setup |
| [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) | Common issues and solutions |

---

## 🔑 Configuration

### Environment Variables

```env
# =============================================================================
# API KEYS (Cloud Services)
# =============================================================================
GOOGLE_API_KEY=your_google_api_key          # Gemini image generation
OPENROUTER_API_KEY=your_openrouter_key      # Multi-model access
OPENAI_API_KEY=your_openai_key              # GPT fallback
ELEVENLABS_API_KEY=your_elevenlabs_key      # Premium TTS
RUNWAY_API_KEY=your_runway_key              # Video generation fallback

# =============================================================================
# MUSIC GENERATION
# =============================================================================
SUNO_COOKIE=your_suno_cookie                # Suno AI music (required)
TWOCAPTCHA_API_KEY=your_2captcha_key        # Optional: auto-CAPTCHA solving

# =============================================================================
# LOCAL SERVICES
# =============================================================================
LM_STUDIO_URL=http://localhost:1234/v1      # Local LLM
OLLAMA_URL=http://localhost:11434           # Ollama server
REDIS_URL=redis://localhost:6379            # Job queue

# =============================================================================
# PATHS
# =============================================================================
UPLOAD_DIR=/app/data/uploads
OUTPUT_DIR=/app/data/outputs
CACHE_DIR=/app/data/cache
MODEL_DIR=G:/models                         # AI model storage
```

---

## 📡 API Reference

### Base URL
```
http://localhost:8000/api/v1
```

### Endpoints Summary

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/enhance/full` | Full 7-stage prompt enhancement |
| `POST` | `/enhance/concept` | Stage 1: Concept expansion |
| `POST` | `/face/extract` | Extract face from image |
| `POST` | `/character/register` | Register character identity |
| `POST` | `/character/verify` | Verify character consistency |
| `POST` | `/generate/image` | Generate image from prompt |
| `POST` | `/generate/batch` | Batch image generation |
| `POST` | `/animate/image` | Animate still image to video |
| `POST` | `/audio/analyze` | Analyze audio for beats/lyrics |
| `POST` | `/audio/mix` | Mix multiple audio tracks |
| `POST` | `/suno/generate` | Generate AI music |
| `POST` | `/video/assemble` | Assemble final video |
| `GET`  | `/jobs/{job_id}` | Get job status |
| `WS`   | `/ws/{job_id}` | WebSocket job updates |

See [docs/API_REFERENCE.md](docs/API_REFERENCE.md) for complete documentation.

---

## 🔄 n8n Workflows

### Available Workflows (14 Total)

| # | Workflow | Trigger | Description |
|---|----------|---------|-------------|
| 01 | Prompt Enhancer Master | Webhook | 7-stage prompt enhancement |
| 02 | Image Generation | Webhook | Multi-model image creation |
| 03 | Multi-Asset Processor | Webhook | Batch file processing |
| 04 | Video Assembly Pro | Webhook | Professional video rendering |
| 05 | Video Extender | Webhook | Extend video duration |
| 06 | Master Pipeline | Webhook | Full automation orchestration |
| 07 | Face Character System | Webhook | Character consistency |
| 08 | Suno Music Generator | Webhook | AI music creation |
| 09 | Audio Beat Analyzer | Webhook | Beat detection & analysis |
| 10 | Image-to-Video Animation | Webhook | Animate images |
| 11 | PDF/Markdown Parser | Webhook | Document parsing |
| 12 | ComfyUI Integration | Webhook | ComfyUI workflows |
| 13 | Suno Pipeline v2 | Webhook | Enhanced Suno integration |
| 99 | Full Music Video Pipeline | Webhook | Complete automation |

---

## 🤖 Model Support

### Video Generation Models
| Model | VRAM | Quality | Speed | Local |
|-------|------|---------|-------|-------|
| LTX-Video 0.9.7-distilled | 12GB | ★★★★☆ | Fast | ✅ |
| LTX-Video 0.9.8-13B | 24GB | ★★★★★ | Slow | ✅ |
| WanVideo | 16GB | ★★★★★ | Medium | ✅ |
| SVD-XT 1.1 | 16GB | ★★★★☆ | Medium | ✅ |

### Music Generation Models
| Model | VRAM | Quality | Local |
|-------|------|---------|-------|
| MusicGen-Large | 8GB | ★★★★★ | ✅ |
| MusicGen-Melody | 6GB | ★★★★☆ | ✅ |
| Suno (API) | N/A | ★★★★★ | ❌ |

### TTS Models
| Model | VRAM | Quality | Local |
|-------|------|---------|-------|
| Bark | 8GB | ★★★★☆ | ✅ |
| XTTS-v2 | 4GB | ★★★★★ | ✅ |
| ElevenLabs | N/A | ★★★★★ | ❌ |

---

## 🔧 Troubleshooting

### Common Issues

<details>
<summary><b>Docker containers won't start</b></summary>

```powershell
# Check Docker status
docker info

# Ensure GPU support
docker run --gpus all nvidia/cuda:12.1-base nvidia-smi

# Rebuild containers
docker compose down
docker compose build --no-cache
docker compose up -d
```
</details>

<details>
<summary><b>Suno API returns errors</b></summary>

1. Check cookie is valid (refresh from suno.com)
2. Test connectivity: `.\scripts\test-suno.ps1`
3. Check for CAPTCHA: Consider 2Captcha integration
</details>

<details>
<summary><b>Out of GPU memory</b></summary>

```powershell
# Use quantized models
.\scripts\download-all-models.ps1 -Category video

# Enable CPU offload in config
# Edit .env: ENABLE_CPU_OFFLOAD=true
```
</details>

<details>
<summary><b>n8n workflows not working</b></summary>

1. Ensure n8n is running: `docker logs nano-banana-n8n`
2. Import workflows manually via n8n UI
3. Check webhook URLs match your setup
</details>

---

## 📈 Roadmap

### Current Status: v2.0 (48% Complete)

| Phase | Status | Progress |
|-------|--------|----------|
| Phase 1: Foundation | 🔄 In Progress | 70% |
| Phase 2: Audio Intelligence | 🔄 In Progress | 60% |
| Phase 3: Video Generation | 🔄 In Progress | 50% |
| Phase 4: User Experience | 📋 Planned | 10% |
| Phase 5: Production | 📋 Planned | 10% |

### Upcoming Features
- [x] ~~Web UI Dashboard~~ **DONE** - Timeline Editor Frontend (React + TailwindCSS)
- [ ] Lip Sync Service
- [ ] ComfyUI Node Pack
- [x] ~~YouTube Publisher~~ **DONE** - End-to-end Timeline → YouTube workflow
- [ ] A/B Testing Interface

### NEW: Timeline Editor (10-Star Professional NLE)
See [docs/TIMELINE_EDITOR.md](docs/TIMELINE_EDITOR.md) for complete guide.

| Feature | Status |
|---------|--------|
| Simple Mode (One-Click) | ✅ |
| Advanced Mode (53 Tools) | ✅ |
| 8K Prompt Enhancer | ✅ |
| Frontend UI | ✅ |
| YouTube Integration | ✅ |

**Quick Start:**
```bash
# Backend
uvicorn backend.api.main:app --reload

# Frontend
cd frontend && npm install && npm run dev
```

---

## 🤝 Contributing

Contributions are welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

---

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

---

<div align="center">

**Made with 🍌 by the Nano Banana Team**

[Report Bug](https://github.com/your-repo/issues) • [Request Feature](https://github.com/your-repo/issues) • [Discussions](https://github.com/your-repo/discussions)

</div>
