# 🍌 Nano Banana Studio Pro - Supported Models

## Video Generation Models

| Model | VRAM | Quality | Speed | Local | Notes |
|-------|------|---------|-------|-------|-------|
| **LTX-Video 0.9.7-distilled** | 12GB | ★★★★☆ | Fast | ✅ | Recommended for most users |
| LTX-Video 0.9.8-13B | 24GB | ★★★★★ | Slow | ✅ | Best quality, high VRAM |
| WanVideo | 16GB | ★★★★★ | Medium | ✅ | Excellent motion |
| SVD-XT 1.1 | 16GB | ★★★★☆ | Medium | ✅ | Stable, reliable |
| Runway Gen-3 | N/A | ★★★★★ | Fast | ❌ | Cloud API required |
| Kling AI | N/A | ★★★★★ | Medium | ❌ | Cloud API required |

### Download Video Models

```powershell
# Using download script
.\scripts\download-all-models.ps1 -Category video

# Manual download (LTX-Video)
# https://huggingface.co/Lightricks/LTX-Video
```

## Image Generation Models

| Model | VRAM | Quality | Speed | Local | Notes |
|-------|------|---------|-------|-------|-------|
| **Gemini 2.0 Flash** | N/A | ★★★★★ | Fast | ❌ | Default, via OpenRouter |
| FLUX.1-dev | 16GB | ★★★★★ | Medium | ✅ | Excellent prompt following |
| FLUX.1-schnell | 12GB | ★★★★☆ | Fast | ✅ | Speed optimized |
| SDXL 1.0 | 8GB | ★★★★☆ | Medium | ✅ | Widely supported |
| SD 1.5 | 4GB | ★★★☆☆ | Fast | ✅ | Low VRAM option |

## Music Generation Models

| Model | VRAM | Quality | Local | Notes |
|-------|------|---------|-------|-------|
| **Suno AI** | N/A | ★★★★★ | ❌ | Best quality, cloud API |
| MusicGen-Large | 8GB | ★★★★★ | ✅ | Meta's open model |
| MusicGen-Melody | 6GB | ★★★★☆ | ✅ | With melody conditioning |
| MusicGen-Small | 4GB | ★★★☆☆ | ✅ | Fast, lower quality |

### Download Music Models

```python
# MusicGen downloads automatically on first use
from audiocraft.models import MusicGen
model = MusicGen.get_pretrained('facebook/musicgen-large')
```

## Text-to-Speech Models

| Model | VRAM | Quality | Local | Notes |
|-------|------|---------|-------|-------|
| **ElevenLabs** | N/A | ★★★★★ | ❌ | Best quality, cloud API |
| XTTS-v2 | 4GB | ★★★★★ | ✅ | Multilingual, voice cloning |
| Bark | 8GB | ★★★★☆ | ✅ | Expressive, with emotions |
| Edge TTS | N/A | ★★★☆☆ | ✅ | Free, Microsoft voices |

## Speech Recognition

| Model | VRAM | Quality | Local | Notes |
|-------|------|---------|-------|-------|
| **Whisper Large-v3** | 10GB | ★★★★★ | ✅ | Best accuracy |
| Whisper Medium | 5GB | ★★★★☆ | ✅ | Good balance |
| Whisper Small | 2GB | ★★★☆☆ | ✅ | Fast, lower accuracy |

## Face Detection/Embedding

| Model | VRAM | Purpose | Local |
|-------|------|---------|-------|
| **MediaPipe** | CPU | Face detection (468 landmarks) | ✅ |
| InsightFace | 2GB | Face embedding (512-dim) | ✅ |
| GFPGAN | 4GB | Face restoration | ✅ |

## LLM Models (Prompt Enhancement)

| Model | Context | Quality | Local | Notes |
|-------|---------|---------|-------|-------|
| **GPT-4o-mini** | 128K | ★★★★★ | ❌ | Default via OpenAI |
| Claude 3.5 Sonnet | 200K | ★★★★★ | ❌ | Via Anthropic |
| Qwen2.5-Coder 32B | 32K | ★★★★★ | ✅ | Via LM Studio/Ollama |
| Llama 3.1 70B | 128K | ★★★★☆ | ✅ | Via Ollama |

## Model Directory Structure

```
models/
├── video/
│   ├── ltx-video/
│   └── svd/
├── image/
│   ├── flux/
│   └── sdxl/
├── audio/
│   ├── musicgen/
│   └── bark/
├── tts/
│   └── xtts/
└── face/
    ├── insightface/
    └── gfpgan/
```

## VRAM Requirements Summary

| Configuration | Minimum VRAM | Recommended |
|---------------|--------------|-------------|
| Basic (Image only) | 8GB | 12GB |
| Standard (Image + Video) | 12GB | 16GB |
| Full (All features) | 16GB | 24GB |
| Maximum Quality | 24GB | 48GB |

## Downloading Models

```powershell
# Download all essential models
.\scripts\download-all-models.ps1 -Priority essential

# Download specific category
.\scripts\download-all-models.ps1 -Category video

# Download with specific model
.\scripts\download-all-models.ps1 -Model ltx-video-distilled
```
