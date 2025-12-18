# 🚀 QUICK START GUIDE - Nano Banana Studio Pro

Get up and running in 5 minutes!

---

## 📋 Prerequisites

| Requirement | Minimum | Recommended |
|-------------|---------|-------------|
| **RAM** | 16GB | 32GB+ |
| **GPU** | 8GB VRAM | 12GB+ VRAM |
| **Storage** | 100GB | 500GB+ |
| **OS** | Windows 10/11, WSL2 | Windows 11 + WSL2 |
| **Docker** | Docker Desktop 4.0+ | Latest |
| **Python** | 3.10+ | 3.11 |

---

## ⚡ 5-Minute Setup

### Step 1: Clone & Navigate
```powershell
git clone https://github.com/your-repo/nano-banana-studio.git
cd nano-banana-studio
```

### Step 2: Run Setup Script
```powershell
.\scripts\setup.ps1
```
This will:
- Create virtual environment
- Install Python dependencies
- Build Docker images
- Create directory structure

### Step 3: Configure API Keys
```powershell
# Copy template
copy env\.env.example env\.env

# Edit with your keys
notepad env\.env
```

**Required Keys:**
```env
# Minimum required
GOOGLE_API_KEY=your-google-api-key

# Optional but recommended
SUNO_COOKIE=your-suno-cookie
OPENROUTER_API_KEY=your-openrouter-key
```

### Step 4: Start Services
```powershell
docker compose up -d
```

### Step 5: Access Interfaces
| Service | URL | Purpose |
|---------|-----|---------|
| n8n | http://localhost:5678 | Visual workflows |
| API Docs | http://localhost:8000/docs | REST API |
| ComfyUI | http://localhost:8188 | Visual AI |

---

## 🎬 First Video in 2 Minutes

### Option A: n8n Form (Easiest)
1. Open http://localhost:5678
2. Find workflow `99_full_music_video_pipeline`
3. Click "Execute" → Fill form
4. Wait for video!

### Option B: API Call
```bash
# Enhance prompt
curl -X POST http://localhost:8000/api/v1/enhance/prompt \
  -H "Content-Type: application/json" \
  -d '{"prompt": "beautiful sunset over mountains", "enhancement_level": "full"}'

# Generate image
curl -X POST http://localhost:8000/api/v1/generate/image \
  -H "Content-Type: application/json" \
  -d '{"prompt": "YOUR_ENHANCED_PROMPT", "style_preset": "Cinematic"}'
```

### Option C: Python SDK
```python
import httpx

client = httpx.Client(base_url="http://localhost:8000")

# Enhance prompt
resp = client.post("/api/v1/enhance/prompt", json={
    "prompt": "sunset over mountains",
    "enhancement_level": "full"
})
prompt = resp.json()["enhanced_prompt"]

# Generate image
resp = client.post("/api/v1/generate/image", json={
    "prompt": prompt,
    "style_preset": "Cinematic"
})
print(resp.json()["image_url"])
```

---

## 🎵 Generate Music

### Suno (Cloud - Best Quality)
```powershell
# First, get your Suno cookie
# 1. Go to suno.com/create
# 2. F12 → Network → Cookie header
# 3. Copy entire value to SUNO_COOKIE in .env

# Test Suno
.\scripts\test-suno.ps1 -Lyrics
```

### MusicGen (Local - Free)
```python
# Requires model download first
.\scripts\download-all-models.ps1 -Category music

# Generate
curl -X POST http://localhost:8000/api/v1/musicgen/generate \
  -H "Content-Type: application/json" \
  -d '{"prompt": "calm ambient music", "duration": 30}'
```

---

## 📥 Download AI Models

```powershell
# List all available models
.\scripts\download-all-models.ps1 -List

# Download essential models only (~20GB)
.\scripts\download-all-models.ps1 -Essential

# Download specific category
.\scripts\download-all-models.ps1 -Category video

# Download everything (~627GB)
.\scripts\download-all-models.ps1
```

### Model Categories
| Category | Essential | Total |
|----------|-----------|-------|
| Video | 18GB | 44GB |
| Music | 9GB | 12GB |
| TTS | 7GB | 9GB |
| Speech | 6GB | 6GB |
| Image | 31GB | 38GB |
| Face | 1GB | 2GB |

---

## 🛠️ Common Commands

```powershell
# Start all services
docker compose up -d

# Stop all services
docker compose down

# View logs
docker compose logs -f

# Restart specific service
docker compose restart backend

# Check GPU usage
nvidia-smi

# Test Suno
.\scripts\test-suno.ps1

# Development mode
.\scripts\run-dev.ps1
```

---

## 📁 Key Directories

```
nano-banana-studio/
├── data/
│   ├── uploads/     # Your uploaded files
│   ├── outputs/     # Generated content
│   └── cache/       # Temporary files
├── logs/            # Application logs
├── models/          # AI models (symlink to G:\models)
└── env/.env         # Configuration
```

---

## 🔧 Troubleshooting

### Docker won't start
```powershell
# Restart Docker Desktop
# Then:
docker compose down
docker compose up -d --build
```

### GPU not detected
```powershell
# Check NVIDIA drivers
nvidia-smi

# Ensure Docker GPU support
docker run --gpus all nvidia/cuda:12.4-base nvidia-smi
```

### Out of memory
```yaml
# In docker-compose.yml, add:
services:
  backend:
    deploy:
      resources:
        reservations:
          devices:
            - capabilities: [gpu]
              device_ids: ['0']
```

### n8n workflows not importing
1. Open n8n UI
2. Settings → Import from File
3. Select all JSON files from `n8n/workflows/`

---

## 📞 Getting Help

1. **Check logs:**
   ```powershell
   docker compose logs backend
   ```

2. **Test components:**
   ```powershell
   .\scripts\test-suno.ps1
   ```

3. **API documentation:**
   http://localhost:8000/docs

4. **Project documentation:**
   - `docs/FEATURES.md` - All features
   - `docs/API_SPEC.md` - API reference
   - `docs/ARCHITECTURE.md` - System design

---

## ⭐ Next Steps

1. ✅ Basic setup complete
2. 🎯 Try the full pipeline workflow
3. 📥 Download additional models
4. 🎨 Explore style presets
5. 🔧 Customize workflows in n8n
6. 📚 Read the full documentation

---

**Happy Video Creating! 🍌🎬**
