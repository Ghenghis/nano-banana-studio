# 🍌 Nano Banana Studio Pro - Configuration Guide

## Environment Variables

All configuration is done through environment variables. Copy `.env.example` to `.env` and configure:

```bash
cp .env.example .env
```

## Required API Keys

At minimum, you need **one** LLM provider configured:

### Option 1: Cloud LLM (Recommended for quick start)
```env
OPENAI_API_KEY=sk-your-key-here
# OR
ANTHROPIC_API_KEY=sk-ant-your-key-here
# OR
GOOGLE_GENERATIVE_AI_API_KEY=your-key-here
```

### Option 2: Local LLM (Privacy-focused)
```env
LMSTUDIO_API_BASE_URL=http://localhost:1234
# OR
OLLAMA_API_BASE_URL=http://localhost:11434
```

## Service Configuration

### Core Services

| Variable | Default | Description |
|----------|---------|-------------|
| `REDIS_URL` | `redis://localhost:6379` | Redis connection for job queue |
| `UPLOAD_DIR` | `/app/data/uploads` | File upload directory |
| `OUTPUT_DIR` | `/app/data/outputs` | Generated output directory |
| `CACHE_DIR` | `/app/data/cache` | Cache directory |

### Image Generation

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENROUTER_API_KEY` | - | OpenRouter for Gemini/multi-model |
| `REPLICATE_API_KEY` | - | Replicate API for SDXL |
| `COMFYUI_URL` | `http://localhost:8188` | ComfyUI server URL |

### Video Animation

| Variable | Default | Description |
|----------|---------|-------------|
| `RUNWAY_API_KEY` | - | Runway ML for Gen-2/Gen-3 |
| `KLING_API_KEY` | - | Kling AI animation |
| `SVD_SERVICE_URL` | `http://localhost:8001` | Local SVD service |
| `LTX_SERVICE_URL` | `http://localhost:8002` | Local LTX-Video service |

### Audio/Music

| Variable | Default | Description |
|----------|---------|-------------|
| `SUNO_COOKIE` | - | Suno AI cookie for music generation |
| `TWOCAPTCHA_API_KEY` | - | 2Captcha for automatic CAPTCHA solving |
| `ELEVENLABS_API_KEY` | - | ElevenLabs premium TTS |

## Docker Configuration

### Basic Usage
```bash
docker compose up -d
```

### With GPU Support
```bash
docker compose --profile gpu up -d
```

### With ComfyUI
```bash
docker compose --profile comfyui up -d
```

### Full Stack
```bash
docker compose --profile gpu --profile comfyui --profile storage up -d
```

## Port Configuration

| Service | Default Port | Environment Variable |
|---------|--------------|---------------------|
| API | 8000 | `PORT` |
| n8n | 5678 | N/A (Docker config) |
| Redis | 6379 | N/A (Docker config) |
| ComfyUI | 8188 | N/A (Docker config) |

## Model Configuration

Edit `config/models.yaml` to configure model preferences:

```yaml
video:
  default: ltx-video-distilled
  models:
    - name: ltx-video-distilled
      vram: 12GB
      quality: high
      speed: fast
```

## Style Presets

Edit `config/styles.yaml` for custom visual styles:

```yaml
styles:
  custom_style:
    name: "My Custom Style"
    positive_keywords:
      - "vibrant colors"
      - "cinematic lighting"
    negative_keywords:
      - "blurry"
      - "low quality"
```

## Logging

| Variable | Default | Description |
|----------|---------|-------------|
| `LOG_LEVEL` | `INFO` | Logging level (DEBUG, INFO, WARNING, ERROR) |
| `VITE_LOG_LEVEL` | `info` | Frontend logging level |

## Security Notes

⚠️ **IMPORTANT**: Never commit `.env` files with real API keys to version control!

1. Always use `.env.example` as template
2. Add `.env` to `.gitignore`
3. Rotate any accidentally exposed keys immediately
4. Use secrets management in production
