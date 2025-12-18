# 🍌 Nano Banana Studio Pro - Troubleshooting Guide

## Common Issues

### Docker Issues

#### Containers won't start
```powershell
# Check Docker status
docker info

# View container logs
docker compose logs -f

# Rebuild containers
docker compose down
docker compose build --no-cache
docker compose up -d
```

#### GPU not detected
```powershell
# Verify NVIDIA driver
nvidia-smi

# Test Docker GPU access
docker run --gpus all nvidia/cuda:12.1-base nvidia-smi

# Ensure nvidia-container-toolkit is installed
# On Windows, update Docker Desktop and enable WSL2 GPU support
```

#### Redis connection errors
```powershell
# Check Redis is running
docker compose ps redis

# Test Redis connectivity
docker compose exec redis redis-cli ping
```

### API Issues

#### 503 "All LLM providers unavailable"
1. Check at least one LLM provider is configured in `.env`
2. Verify API keys are valid
3. Test local LLM if using:
   ```bash
   curl http://localhost:1234/v1/models  # LM Studio
   curl http://localhost:11434/api/tags  # Ollama
   ```

#### 500 Internal Server Error
```powershell
# Check API logs
docker compose logs -f api

# Or if running locally
uvicorn backend.api.main:app --reload --log-level debug
```

### Suno Music Generation

#### Cookie expired
1. Log into [suno.com](https://suno.com) in browser
2. Open Developer Tools (F12) → Network tab
3. Find any API request and copy the `Cookie` header
4. Update `SUNO_COOKIE` in `.env`

#### CAPTCHA blocking requests
1. Consider adding 2Captcha API key
2. Or manually solve CAPTCHA on suno.com and retry

### FFmpeg Issues

#### "FFmpeg not found"
```powershell
# Windows - Install via Chocolatey
choco install ffmpeg

# Or download from https://ffmpeg.org/download.html
# Add to PATH
```

#### Video encoding fails
- Check input files exist and are valid
- Verify sufficient disk space
- Check FFmpeg logs for specific codec errors

### Memory Issues

#### Out of GPU memory
```env
# Enable CPU offload in .env
ENABLE_CPU_OFFLOAD=true

# Or use quantized models
DEFAULT_MODEL_QUANTIZATION=8bit
```

#### Python memory errors
- Reduce batch sizes
- Process files sequentially instead of parallel
- Increase system swap space

### n8n Workflow Issues

#### Workflows not loading
1. Check n8n is running: `docker compose ps n8n`
2. Access n8n UI: http://localhost:5678
3. Manually import from `n8n/workflows/`

#### Webhook URLs incorrect
- Update webhook URLs to match your setup
- Default: `http://localhost:8000/api/v1/...`

### Face Detection

#### No face detected
- Ensure image has clear, front-facing face
- Minimum recommended resolution: 256x256
- Check lighting - avoid dark/overexposed images

#### Low similarity scores
- Use higher quality reference images
- Provide multiple reference images (up to 14)
- Ensure consistent lighting across references

## Debug Mode

Enable verbose logging:
```env
LOG_LEVEL=DEBUG
VITE_LOG_LEVEL=debug
```

## Health Checks

```bash
# API health
curl http://localhost:8000/health

# n8n health
curl http://localhost:5678/healthz

# Redis health
docker compose exec redis redis-cli ping
```

## Getting Help

1. Check logs: `docker compose logs -f [service]`
2. Search existing issues on GitHub
3. Open new issue with:
   - Error message
   - Steps to reproduce
   - Environment details
   - Relevant logs
