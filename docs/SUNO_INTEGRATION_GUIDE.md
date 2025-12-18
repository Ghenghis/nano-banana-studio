# 🎵 Suno AI Integration Guide for Nano Banana Studio Pro

## Protecting Your 10,000 Credits

This guide covers secure, production-grade Suno integration with multiple deployment options.

---

## 📋 Table of Contents

1. [Quick Start (5 minutes)](#quick-start)
2. [Option A: Vercel Deployment](#option-a-vercel-deployment)
3. [Option B: Docker Self-Hosted](#option-b-docker-self-hosted)
4. [Option C: Local Development](#option-c-local-development)
5. [Getting Your Suno Cookie](#getting-your-suno-cookie)
6. [Security Best Practices](#security-best-practices)
7. [Rate Limiting & Credit Protection](#rate-limiting--credit-protection)
8. [API Reference](#api-reference)
9. [Troubleshooting](#troubleshooting)

---

## ⚡ Quick Start

### Prerequisites
- Suno Pro/Premier account with credits
- Node.js 18+ (for Vercel) OR Docker (for self-hosted)
- Your Suno session cookie

### 1. Get Your Cookie (2 minutes)
```
1. Go to https://suno.com/create
2. Press F12 → Network tab
3. Refresh the page
4. Find request containing "client?_clerk_js_version"
5. Copy the entire Cookie header value
```

### 2. Choose Deployment Method
| Method | Best For | Setup Time | Cost |
|--------|----------|------------|------|
| **Vercel** | Quick setup, serverless | 5 min | Free |
| **Docker** | Full control, self-hosted | 15 min | Free |
| **Local** | Development, testing | 10 min | Free |

---

## 🚀 Option A: Vercel Deployment

The **gcui-art/suno-api** is the gold standard. One-click deployment.

### Step 1: Fork the Repository

1. Go to: https://github.com/gcui-art/suno-api
2. Click **Fork** (top right)
3. Keep all settings default, click **Create fork**

### Step 2: Deploy to Vercel

1. Go to: https://vercel.com/new
2. Click **Import** next to your forked `suno-api` repo
3. Configure project:
   - **Framework Preset**: Other
   - **Root Directory**: `./` (default)
4. Click **Deploy**

### Step 3: Configure Environment Variables

1. In Vercel dashboard, go to **Settings** → **Environment Variables**
2. Add these variables:

| Variable | Value | Required |
|----------|-------|----------|
| `SUNO_COOKIE` | Your full cookie string | ✅ Yes |
| `TWOCAPTCHA_API_KEY` | 2Captcha API key | Optional |

> ⚠️ **CRITICAL**: The cookie is ~2000+ characters. Paste the ENTIRE thing.

### Step 4: Redeploy

1. Go to **Deployments** tab
2. Click **...** on latest deployment → **Redeploy**
3. Wait for deployment to complete

### Step 5: Test Your API

```bash
# Replace with your Vercel URL
curl https://your-project.vercel.app/api/get_limit
```

Expected response:
```json
{
  "credits_left": 10000,
  "monthly_limit": 10000,
  "monthly_usage": 0
}
```

### Step 6: Configure Nano Banana

Add to your `.env` file:
```env
# Suno API Configuration
SUNO_VERCEL_URL=https://your-project.vercel.app
SUNO_COOKIE=  # Leave empty, Vercel handles it
```

---

## 🐳 Option B: Docker Self-Hosted

Best for privacy and full control. Runs on your own hardware.

### Step 1: Create Docker Compose Addition

Add to your `docker-compose.yml`:

```yaml
  # Suno API Service
  suno-api:
    image: node:18-slim
    container_name: nano-suno-api
    working_dir: /app
    volumes:
      - ./suno-api:/app
      - suno_node_modules:/app/node_modules
    environment:
      - SUNO_COOKIE=${SUNO_COOKIE}
      - TWOCAPTCHA_API_KEY=${TWOCAPTCHA_API_KEY:-}
      - PORT=3100
    ports:
      - "3100:3100"
    command: >
      sh -c "
        if [ ! -d /app/node_modules ]; then
          npm install
        fi &&
        npm run dev
      "
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3100/api/get_limit"]
      interval: 30s
      timeout: 10s
      retries: 3
    networks:
      - nano-network
    restart: unless-stopped

volumes:
  suno_node_modules:
```

### Step 2: Clone Suno API

```powershell
# From your project root
git clone https://github.com/gcui-art/suno-api.git suno-api
cd suno-api
```

### Step 3: Configure Environment

Add to `.env`:
```env
# Suno Configuration
SUNO_COOKIE=your_cookie_here
SUNO_LOCAL_URL=http://localhost:3100
TWOCAPTCHA_API_KEY=  # Optional, for CAPTCHA solving
```

### Step 4: Start the Service

```powershell
docker compose up suno-api -d

# Check logs
docker logs -f nano-suno-api
```

### Step 5: Verify

```bash
curl http://localhost:3100/api/get_limit
```

---

## 💻 Option C: Local Development

For testing and development without Docker.

### Step 1: Install Dependencies

```powershell
# Clone suno-api
git clone https://github.com/gcui-art/suno-api.git
cd suno-api

# Install dependencies
npm install
```

### Step 2: Create .env.local

```env
SUNO_COOKIE=your_cookie_here
```

### Step 3: Run Development Server

```powershell
npm run dev
```

Server runs at: http://localhost:3000

---

## 🍪 Getting Your Suno Cookie

### Method 1: Browser DevTools (Recommended)

1. **Open Suno**: Go to https://suno.com/create
2. **Open DevTools**: Press `F12` or `Ctrl+Shift+I`
3. **Network Tab**: Click the **Network** tab
4. **Refresh**: Press `F5` to refresh the page
5. **Find Request**: Look for a request containing `client?_clerk_js_version`
6. **Copy Cookie**: 
   - Click on the request
   - Go to **Headers** tab
   - Scroll to **Request Headers**
   - Find `Cookie:` header
   - Copy the **entire value** (it's very long!)

### Method 2: Browser Extension

Install a cookie manager extension:
- **Chrome**: EditThisCookie
- **Firefox**: Cookie Quick Manager

Export cookies for `suno.com` domain.

### Cookie Structure

Your cookie should look something like this (abbreviated):
```
__client=eyJhbGciOiJSUzI1NiIsInR...; __client_uat=1234567890; __cf_bm=abc123...
```

> ⚠️ **Important**: The cookie expires! You may need to refresh it every few days.

---

## 🔒 Security Best Practices

### DO ✅

1. **Use Environment Variables**
   ```env
   # .env (never commit this file!)
   SUNO_COOKIE=your_secret_cookie
   ```

2. **Add to .gitignore**
   ```
   .env
   .env.local
   .env.*.local
   ```

3. **Use Secret Management**
   - Vercel: Environment Variables (encrypted)
   - Docker: Docker Secrets
   - AWS: Secrets Manager
   - Local: `.env` files with restricted permissions

4. **Rotate Cookies Regularly**
   - Refresh cookie every 48 hours for safety
   - Log out of browser sessions you're not using

### DON'T ❌

1. **Never commit cookies to Git**
2. **Never share cookies in issues/Discord**
3. **Never hardcode cookies in source code**
4. **Never expose cookie in client-side JavaScript**

---

## ⚡ Rate Limiting & Credit Protection

### Built-in Protection

The `SunoClient` class includes automatic rate limiting:

```python
from backend.services.suno_service import SunoClient

client = SunoClient(use_rate_limiter=True)  # Default: ON

# Configure limits via environment
SUNO_RATE_LIMIT=10  # Max requests per minute
SUNO_MAX_CONCURRENT=2  # Max concurrent generations
```

### Recommended Settings for 10K Credits

```env
# Conservative (safest)
SUNO_RATE_LIMIT=5
SUNO_MAX_CONCURRENT=1

# Balanced (recommended)
SUNO_RATE_LIMIT=10
SUNO_MAX_CONCURRENT=2

# Aggressive (use with caution)
SUNO_RATE_LIMIT=20
SUNO_MAX_CONCURRENT=4
```

### Cost Estimation

| Action | Credit Cost |
|--------|-------------|
| Generate song (2 outputs) | 10 credits |
| Extend song | 10 credits |
| Generate lyrics | 0 credits |
| Get song info | 0 credits |

With 10,000 credits:
- ~1,000 song generations
- ~2,000 individual songs (2 per generation)

---

## 📚 API Reference

### Available Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/get_limit` | GET | Check credit balance |
| `/api/generate` | POST | Generate music (simple mode) |
| `/api/custom_generate` | POST | Generate with custom lyrics |
| `/api/generate_lyrics` | POST | Generate lyrics only |
| `/api/get` | GET | Get song by ID |
| `/api/extend_audio` | POST | Extend existing song |
| `/api/concat` | POST | Concatenate clips |
| `/v1/chat/completions` | POST | OpenAI-compatible endpoint |

### Python Usage Examples

```python
from backend.services.suno_service import get_suno_service, SunoStyle, SunoMood

# Initialize service
suno = get_suno_service()

# Check credits
credits = await suno.client.get_credits()
print(f"Credits: {credits.credits_left}")

# Generate background music
song = await suno.generate_background_music(
    description="peaceful nature scene with flowing water",
    duration=60,
    style="ambient"
)
print(f"Audio URL: {song.audio_url}")

# Generate with specific genre
song = await suno.generate_genre_music(
    genre=SunoStyle.CINEMATIC,
    mood=SunoMood.EPIC,
    context="hero's journey, triumph",
    instrumental=True
)

# Generate custom song with lyrics
lyrics = """
[Verse 1]
Walking through the morning light
Everything feels just right

[Chorus]
It's a beautiful day
Let's dance the night away
"""

songs = await suno.client.generate_custom(
    lyrics=lyrics,
    style="upbeat pop, summer vibes",
    title="Beautiful Day",
    instrumental=False
)

# Download the song
from pathlib import Path
files = await suno.client.download_song(
    song=songs[0],
    output_dir=Path("./downloads"),
    include_video=True
)
print(f"Downloaded: {files}")

# Cleanup
await suno.close()
```

### n8n Workflow Integration

The existing n8n workflow `08_suno_music_generator.json` already supports Suno. Configure it:

1. Open n8n: http://localhost:5678
2. Import workflow `08_suno_music_generator.json`
3. Configure the HTTP Request node:
   - URL: `http://suno-api:3100/api/generate` (Docker) or your Vercel URL
4. Set credentials if needed

---

## 🔧 Troubleshooting

### Common Issues

#### "Cookie invalid" or "Unauthorized"
```
✗ Error: Cookie expired or invalid
```
**Solution**: Get a fresh cookie from Suno.com

#### "Rate limited" 
```
✗ Error: 429 Too Many Requests
```
**Solution**: Wait 60 seconds, then reduce `SUNO_RATE_LIMIT`

#### "hCaptcha required"
```
✗ Error: CAPTCHA verification required
```
**Solutions**:
1. Add 2Captcha API key: `TWOCAPTCHA_API_KEY=your_key`
2. Run on macOS (fewer CAPTCHAs)
3. Use a residential proxy

#### "This is a fake app" watermark
```
✗ Generated audio has watermark
```
**Solution**: This happens when CAPTCHA fails. Ensure 2Captcha is configured.

#### "Connection timeout"
```
✗ Error: Connection timed out
```
**Solution**: Increase timeout in `.env`:
```env
SUNO_TIMEOUT=600
SUNO_POLL_INTERVAL=10
```

### Debug Logging

Enable verbose logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

Or in `.env`:
```env
LOG_LEVEL=DEBUG
```

### Health Check

```powershell
# Check if Suno API is responding
curl http://localhost:3100/api/get_limit

# Check from within Docker network
docker exec nano-api curl http://suno-api:3100/api/get_limit
```

---

## 📊 Integration Status

| Feature | Status | Notes |
|---------|--------|-------|
| Simple generation | ✅ Working | `/api/generate` |
| Custom mode (lyrics) | ✅ Working | `/api/custom_generate` |
| Lyrics generation | ✅ Working | `/api/generate_lyrics` |
| Song extension | ✅ Working | `/api/extend_audio` |
| Song concatenation | ✅ Working | `/api/concat` |
| Rate limiting | ✅ Built-in | Configurable |
| Keep-alive | ✅ Built-in | Prevents session timeout |
| Credit tracking | ✅ Working | `/api/get_limit` |
| 2Captcha integration | ✅ Optional | For CAPTCHA solving |
| OpenAI-compatible | ✅ Working | `/v1/chat/completions` |

---

## 🎯 Next Steps

1. **Get your Suno cookie** (see instructions above)
2. **Choose deployment method** (Vercel recommended for quick start)
3. **Configure `.env`** with your credentials
4. **Test the API** with a simple generation
5. **Integrate with Nano Banana workflows**

---

## 📞 Support

- **gcui-art/suno-api Issues**: https://github.com/gcui-art/suno-api/issues
- **2Captcha Support**: https://2captcha.com/support
- **Suno Discord**: https://discord.gg/suno

---

*Last Updated: December 2025*
