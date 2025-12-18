# 🎵 SUNO INTEGRATION - QUICK REFERENCE

## Your 3 Options (Choose One)

### Option 1: Python Pip (Simplest) ⭐ Recommended
```powershell
# Install
pip install SunoAI

# Set cookie in .env
SUNO_COOKIE=your_cookie_here

# Use in code
from backend.services.suno_pip_client import get_unified_suno
client = get_unified_suno()
songs = await client.generate("upbeat pop song")
```

### Option 2: Docker (Full Control)
```powershell
# Clone and start
git clone https://github.com/gcui-art/suno-api.git
docker compose -f docker/docker-compose.suno.yml up -d

# Set in .env
SUNO_LOCAL_URL=http://localhost:3100
SUNO_COOKIE=your_cookie_here

# Test
curl http://localhost:3100/api/get_limit
```

### Option 3: Vercel (Serverless)
```
1. Fork: github.com/gcui-art/suno-api
2. Deploy to Vercel
3. Add env var: SUNO_COOKIE
4. Set in .env: SUNO_VERCEL_URL=https://your-app.vercel.app
```

---

## Getting Your Cookie (2 minutes)
1. Go to **suno.com/create**
2. Press **F12** → **Network** tab
3. Refresh page (**F5**)
4. Find request with `client?_clerk_js_version`
5. Copy entire **Cookie** header value (~2000+ chars)

---

## Files Created

| File | Purpose |
|------|---------|
| `backend/services/suno_service.py` | Full REST API client (1015 lines) |
| `backend/services/suno_pip_client.py` | SunoAI pip package wrapper (562 lines) |
| `docker/docker-compose.suno.yml` | Docker service config |
| `scripts/setup-suno.ps1` | One-click setup script |
| `docs/SUNO_INTEGRATION_GUIDE.md` | Complete documentation |
| `env/.env.example` | Environment variables |

---

## Quick Commands

```powershell
# Setup (interactive)
.\scripts\setup-suno.ps1

# Setup (pip only)
.\scripts\setup-suno.ps1 -Method pip

# Check credits
curl http://localhost:3100/api/get_limit

# Generate music (Python)
python -c "
import asyncio
from backend.services.suno_pip_client import get_unified_suno

async def main():
    client = get_unified_suno()
    credits = await client.get_credits()
    print(f'Credits: {credits}')
    await client.close()

asyncio.run(main())
"
```

---

## Rate Limiting (Protect 10K Credits!)

```env
# In .env - Conservative settings
SUNO_RATE_LIMIT=5       # Requests per minute
SUNO_MAX_CONCURRENT=1   # Concurrent generations
SUNO_KEEP_ALIVE=180     # Keep session alive (seconds)
```

---

## Credit Costs

| Action | Credits |
|--------|---------|
| Generate (2 songs) | 10 |
| Extend song | 10 |
| Generate lyrics | 0 |
| Get info | 0 |

**10,000 credits = ~1,000 generations = ~2,000 songs**

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "Cookie invalid" | Get fresh cookie from suno.com |
| "Rate limited" | Reduce SUNO_RATE_LIMIT |
| "hCaptcha required" | Add TWOCAPTCHA_API_KEY |
| "This is a fake app" | CAPTCHA failed, configure 2Captcha |

---

## Full Documentation
📖 **docs/SUNO_INTEGRATION_GUIDE.md**
