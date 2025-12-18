# SUNO INTEGRATION TEST SCRIPT
# Tests Suno API connectivity and basic generation
#
# Usage:
#   .\scripts\test-suno.ps1              # Test connectivity only
#   .\scripts\test-suno.ps1 -Generate    # Test actual generation (uses credits!)
#   .\scripts\test-suno.ps1 -Cookie "your_cookie"  # Test with specific cookie

param(
    [switch]$Generate,
    [switch]$Lyrics,
    [string]$Cookie = "",
    [string]$ApiUrl = "",
    [switch]$Help
)

$ErrorActionPreference = "Stop"

function Write-Success { Write-Host $args -ForegroundColor Green }
function Write-Info { Write-Host $args -ForegroundColor Cyan }
function Write-Warn { Write-Host $args -ForegroundColor Yellow }
function Write-Err { Write-Host $args -ForegroundColor Red }

# Banner
Write-Host ""
Write-Host "  =================================================================" -ForegroundColor Magenta
Write-Host "     SUNO INTEGRATION TEST                                        " -ForegroundColor Magenta
Write-Host "  =================================================================" -ForegroundColor Magenta
Write-Host ""

if ($Help) {
    Write-Host @"
USAGE:
    .\test-suno.ps1 [OPTIONS]

OPTIONS:
    -Generate       Test actual music generation (USES CREDITS!)
    -Lyrics         Test lyrics generation only (FREE)
    -Cookie <str>   Use specific Suno cookie
    -ApiUrl <url>   Use specific API URL
    -Help           Show this help

TESTS PERFORMED:
    1. Check environment variables
    2. Test API connectivity
    3. Check credit balance
    4. (Optional) Generate lyrics
    5. (Optional) Generate music

EXAMPLES:
    # Test connectivity only (safe, no credits used)
    .\test-suno.ps1

    # Test lyrics generation (free)
    .\test-suno.ps1 -Lyrics

    # Test full generation (uses 10 credits!)
    .\test-suno.ps1 -Generate
"@
    exit 0
}

# Determine API URL
$apiUrl = if ($ApiUrl) { $ApiUrl }
          elseif ($env:SUNO_LOCAL_URL) { $env:SUNO_LOCAL_URL }
          elseif ($env:SUNO_VERCEL_URL) { $env:SUNO_VERCEL_URL }
          else { "http://localhost:3100" }

Write-Info "API URL: $apiUrl"

# Test 1: Environment Check
Write-Host ""
Write-Host "[TEST 1] Environment Check" -ForegroundColor Yellow
Write-Host "----------------------------------------"

$envChecks = @{
    "SUNO_COOKIE" = if ($Cookie) { "Provided via -Cookie" } elseif ($env:SUNO_COOKIE) { "Set (length: $($env:SUNO_COOKIE.Length))" } else { "NOT SET" }
    "SUNO_LOCAL_URL" = if ($env:SUNO_LOCAL_URL) { $env:SUNO_LOCAL_URL } else { "Not set" }
    "SUNO_VERCEL_URL" = if ($env:SUNO_VERCEL_URL) { $env:SUNO_VERCEL_URL } else { "Not set" }
    "TWOCAPTCHA_API_KEY" = if ($env:TWOCAPTCHA_API_KEY) { "Set (hidden)" } else { "Not set (optional)" }
}

foreach ($key in $envChecks.Keys) {
    $value = $envChecks[$key]
    $color = if ($value -match "NOT SET" -and $key -eq "SUNO_COOKIE") { "Red" } 
             elseif ($value -match "Not set") { "Gray" } 
             else { "Green" }
    Write-Host "  $key : " -NoNewline
    Write-Host $value -ForegroundColor $color
}

if (-not $Cookie -and -not $env:SUNO_COOKIE) {
    Write-Err ""
    Write-Err "  WARNING: SUNO_COOKIE not set!"
    Write-Err "  Get your cookie from suno.com (F12 > Network > Cookie header)"
    Write-Err ""
}

# Test 2: API Connectivity
Write-Host ""
Write-Host "[TEST 2] API Connectivity" -ForegroundColor Yellow
Write-Host "----------------------------------------"

try {
    $response = Invoke-RestMethod -Uri "$apiUrl/api/get_limit" -TimeoutSec 10 -ErrorAction Stop
    Write-Success "  [OK] API is reachable"
    Write-Host "  Credits Left: $($response.credits_left)" -ForegroundColor Cyan
    Write-Host "  Monthly Limit: $($response.monthly_limit)" -ForegroundColor Gray
    Write-Host "  Monthly Usage: $($response.monthly_usage)" -ForegroundColor Gray
    
    if ($response.credits_left -lt 100) {
        Write-Warn "  WARNING: Low credits! Consider recharging."
    }
} catch {
    Write-Err "  [FAIL] Cannot reach API at $apiUrl"
    Write-Host "  Error: $_" -ForegroundColor Red
    Write-Host ""
    Write-Host "  Possible causes:" -ForegroundColor Yellow
    Write-Host "    1. Suno API service not running"
    Write-Host "    2. Wrong API URL"
    Write-Host "    3. Cookie expired or invalid"
    Write-Host ""
    Write-Host "  Solutions:" -ForegroundColor Yellow
    Write-Host "    - Start Docker: docker compose -f docker/docker-compose.suno.yml up -d"
    Write-Host "    - Or run locally: cd suno-api && npm run dev"
    Write-Host "    - Refresh your Suno cookie from suno.com"
    exit 1
}

# Test 3: Lyrics Generation (if requested)
if ($Lyrics) {
    Write-Host ""
    Write-Host "[TEST 3] Lyrics Generation" -ForegroundColor Yellow
    Write-Host "----------------------------------------"
    
    $prompt = "a short happy song about coding and AI"
    Write-Info "  Generating lyrics for: $prompt"
    
    try {
        $body = @{ prompt = $prompt } | ConvertTo-Json
        $response = Invoke-RestMethod -Uri "$apiUrl/api/generate_lyrics" -Method POST -Body $body -ContentType "application/json" -TimeoutSec 60
        
        Write-Success "  [OK] Lyrics generated!"
        Write-Host ""
        Write-Host "  --- Generated Lyrics ---" -ForegroundColor Cyan
        $lyrics = if ($response.text) { $response.text } else { $response }
        Write-Host $lyrics -ForegroundColor White
        Write-Host "  --- End ---" -ForegroundColor Cyan
    } catch {
        Write-Err "  [FAIL] Lyrics generation failed"
        Write-Host "  Error: $_" -ForegroundColor Red
    }
}

# Test 4: Music Generation (if requested)
if ($Generate) {
    Write-Host ""
    Write-Host "[TEST 4] Music Generation" -ForegroundColor Yellow
    Write-Host "----------------------------------------"
    Write-Warn "  WARNING: This will use 10 credits!"
    
    $confirm = Read-Host "  Continue? (y/N)"
    if ($confirm -ne "y" -and $confirm -ne "Y") {
        Write-Info "  Skipped music generation"
    } else {
        $prompt = "calm ambient music for studying, lo-fi beats, peaceful"
        Write-Info "  Generating: $prompt"
        Write-Info "  This may take 1-3 minutes..."
        
        try {
            $body = @{
                prompt = $prompt
                make_instrumental = $true
                wait_audio = $true
            } | ConvertTo-Json
            
            $response = Invoke-RestMethod -Uri "$apiUrl/api/generate" -Method POST -Body $body -ContentType "application/json" -TimeoutSec 300
            
            Write-Success "  [OK] Music generated!"
            
            # Parse response
            $songs = if ($response.data) { $response.data } elseif ($response -is [array]) { $response } else { @($response) }
            
            foreach ($song in $songs) {
                Write-Host ""
                Write-Host "  Song: $($song.title)" -ForegroundColor Cyan
                Write-Host "    ID: $($song.id)" -ForegroundColor Gray
                Write-Host "    Status: $($song.status)" -ForegroundColor Gray
                Write-Host "    Duration: $($song.duration)s" -ForegroundColor Gray
                if ($song.audio_url) {
                    Write-Host "    Audio URL: $($song.audio_url)" -ForegroundColor Green
                }
            }
        } catch {
            Write-Err "  [FAIL] Music generation failed"
            Write-Host "  Error: $_" -ForegroundColor Red
            Write-Host ""
            Write-Host "  Common issues:" -ForegroundColor Yellow
            Write-Host "    - CAPTCHA required: Configure 2Captcha API key"
            Write-Host "    - Cookie expired: Refresh from suno.com"
            Write-Host "    - Rate limited: Wait a few minutes"
        }
    }
}

# Test 5: Python Integration
Write-Host ""
Write-Host "[TEST 5] Python Integration" -ForegroundColor Yellow
Write-Host "----------------------------------------"

$pythonTest = @"
import sys
sys.path.insert(0, r'G:\Github\nano-banana-projects\nano-1')

try:
    from backend.services.suno_pip_client import SUNO_AVAILABLE
    print(f'SunoAI package: {"OK" if SUNO_AVAILABLE else "NOT INSTALLED"}')
except ImportError as e:
    print(f'SunoAI package: NOT AVAILABLE ({e})')

try:
    from backend.services.captcha_solver import TWOCAPTCHA_AVAILABLE
    print(f'2Captcha package: {"OK" if TWOCAPTCHA_AVAILABLE else "NOT INSTALLED"}')
except ImportError as e:
    print(f'2Captcha package: NOT AVAILABLE ({e})')

try:
    from backend.services.suno_service import SunoClient
    print('SunoClient class: OK')
except ImportError as e:
    print(f'SunoClient class: ERROR ({e})')
"@

try {
    $result = python -c $pythonTest 2>&1
    $result | ForEach-Object { Write-Host "  $_" }
} catch {
    Write-Err "  Python test failed: $_"
}

# Summary
Write-Host ""
Write-Host "=================================================================" -ForegroundColor Cyan
Write-Host "  TEST SUMMARY" -ForegroundColor Cyan
Write-Host "=================================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "  API Status: " -NoNewline
Write-Success "Connected"
Write-Host "  Next steps:" -ForegroundColor White
Write-Host "    1. Ensure SUNO_COOKIE is set in .env" -ForegroundColor Gray
Write-Host "    2. Test lyrics: .\test-suno.ps1 -Lyrics" -ForegroundColor Gray
Write-Host "    3. Test generation: .\test-suno.ps1 -Generate" -ForegroundColor Gray
Write-Host ""
