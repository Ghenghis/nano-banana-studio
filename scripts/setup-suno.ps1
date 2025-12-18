# =============================================================================
# NANO BANANA STUDIO PRO - SUNO SETUP SCRIPT
# =============================================================================
# One-click setup for Suno AI music generation integration
#
# Usage:
#   .\scripts\setup-suno.ps1                    # Interactive setup
#   .\scripts\setup-suno.ps1 -Method pip        # Python pip only
#   .\scripts\setup-suno.ps1 -Method docker     # Docker only
#   .\scripts\setup-suno.ps1 -Method vercel     # Show Vercel guide
# =============================================================================

param(
    [ValidateSet("auto", "pip", "docker", "vercel")]
    [string]$Method = "auto",
    
    [string]$Cookie = "",
    
    [switch]$SkipClone,
    
    [switch]$Help
)

$ErrorActionPreference = "Stop"

# Colors for output
function Write-Success { Write-Host $args -ForegroundColor Green }
function Write-Info { Write-Host $args -ForegroundColor Cyan }
function Write-Warn { Write-Host $args -ForegroundColor Yellow }
function Write-Error { Write-Host $args -ForegroundColor Red }

# Banner
function Show-Banner {
    Write-Host ""
    Write-Host "  ╔═══════════════════════════════════════════════════════════╗" -ForegroundColor Magenta
    Write-Host "  ║       🎵 NANO BANANA STUDIO PRO - SUNO SETUP 🎵           ║" -ForegroundColor Magenta
    Write-Host "  ╠═══════════════════════════════════════════════════════════╣" -ForegroundColor Magenta
    Write-Host "  ║  Integrate Suno AI music generation into your workflow    ║" -ForegroundColor White
    Write-Host "  ║  Protect your 10K credits with rate limiting & security   ║" -ForegroundColor White
    Write-Host "  ╚═══════════════════════════════════════════════════════════╝" -ForegroundColor Magenta
    Write-Host ""
}

# Help
function Show-Help {
    Write-Host "
USAGE:
    .\setup-suno.ps1 [OPTIONS]

OPTIONS:
    -Method <type>    Installation method: auto, pip, docker, vercel
    -Cookie <str>     Your Suno session cookie (or set SUNO_COOKIE env var)
    -SkipClone        Skip cloning gcui-art/suno-api repo
    -Help             Show this help message

METHODS:
    pip       Install SunoAI Python package (simplest)
    docker    Run gcui-art/suno-api in Docker (full control)
    vercel    Show guide for Vercel deployment (serverless)
    auto      Auto-detect best method for your system

EXAMPLES:
    # Interactive setup
    .\setup-suno.ps1

    # Quick pip install
    .\setup-suno.ps1 -Method pip

    # Docker with cookie
    .\setup-suno.ps1 -Method docker -Cookie 'your_cookie_here'
"
}

# Check prerequisites
function Test-Prerequisites {
    Write-Info "Checking prerequisites..."
    
    $results = @{
        Python = $false
        Docker = $false
        Node = $false
        Git = $false
    }
    
    # Python
    try {
        $pyVersion = python --version 2>&1
        if ($pyVersion -match "Python 3\.(\d+)") {
            $results.Python = [int]$Matches[1] -ge 9
            Write-Success "  ✓ Python: $pyVersion"
        }
    } catch {
        Write-Warn "  ✗ Python not found"
    }
    
    # Docker
    try {
        $dockerVersion = docker --version 2>&1
        if ($dockerVersion -match "Docker") {
            $results.Docker = $true
            Write-Success "  ✓ Docker: $dockerVersion"
        }
    } catch {
        Write-Warn "  ✗ Docker not found"
    }
    
    # Node.js
    try {
        $nodeVersion = node --version 2>&1
        if ($nodeVersion -match "v(\d+)") {
            $results.Node = [int]$Matches[1] -ge 18
            Write-Success "  ✓ Node.js: $nodeVersion"
        }
    } catch {
        Write-Warn "  ✗ Node.js not found"
    }
    
    # Git
    try {
        $gitVersion = git --version 2>&1
        if ($gitVersion -match "git") {
            $results.Git = $true
            Write-Success "  ✓ Git: $gitVersion"
        }
    } catch {
        Write-Warn "  ✗ Git not found"
    }
    
    return $results
}

# Get cookie from user
function Get-SunoCookie {
    if ($Cookie) {
        return $Cookie
    }
    
    if ($env:SUNO_COOKIE) {
        Write-Info "Using SUNO_COOKIE from environment"
        return $env:SUNO_COOKIE
    }
    
    Write-Host ""
    Write-Warn "═══════════════════════════════════════════════════════════"
    Write-Warn "  IMPORTANT: You need your Suno session cookie"
    Write-Warn "═══════════════════════════════════════════════════════════"
    Write-Host ""
    Write-Host "To get your cookie:" -ForegroundColor White
    Write-Host "  1. Go to https://suno.com/create" -ForegroundColor Gray
    Write-Host "  2. Press F12 → Network tab" -ForegroundColor Gray
    Write-Host "  3. Refresh the page (F5)" -ForegroundColor Gray
    Write-Host "  4. Find request with 'client?_clerk_js_version'" -ForegroundColor Gray
    Write-Host "  5. Copy the ENTIRE Cookie header value" -ForegroundColor Gray
    Write-Host ""
    
    $cookie = Read-Host "Paste your Suno cookie (or press Enter to skip)"
    
    if (-not $cookie) {
        Write-Warn "Skipping cookie setup. You'll need to set SUNO_COOKIE later."
        return ""
    }
    
    return $cookie
}

# Install via pip
function Install-PipMethod {
    Write-Info "Installing SunoAI Python package..."
    
    # Install package
    python -m pip install --upgrade SunoAI httpx tenacity pydantic
    
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Failed to install SunoAI package"
        return $false
    }
    
    Write-Success "✓ SunoAI package installed"
    
    # Get cookie
    $cookie = Get-SunoCookie
    
    if ($cookie) {
        # Update .env
        $envFile = Join-Path $PSScriptRoot "..\env\.env"
        $envExample = Join-Path $PSScriptRoot "..\env\.env.example"
        
        if (-not (Test-Path $envFile)) {
            if (Test-Path $envExample) {
                Copy-Item $envExample $envFile
            } else {
                New-Item $envFile -ItemType File | Out-Null
            }
        }
        
        # Add/update SUNO_COOKIE
        $content = Get-Content $envFile -Raw
        if ($content -match "SUNO_COOKIE=") {
            $content = $content -replace "SUNO_COOKIE=.*", "SUNO_COOKIE=$cookie"
        } else {
            $content += "`nSUNO_COOKIE=$cookie"
        }
        Set-Content $envFile $content
        
        Write-Success "✓ Cookie saved to .env file"
    }
    
    return $true
}

# Install via Docker
function Install-DockerMethod {
    param([hashtable]$Prerequisites)
    
    if (-not $Prerequisites.Docker) {
        Write-Error "Docker is required for this method"
        Write-Host "Install Docker Desktop from: https://docker.com/products/docker-desktop"
        return $false
    }
    
    Write-Info "Setting up Suno API Docker service..."
    
    # Clone suno-api if needed
    $sunoApiPath = Join-Path $PSScriptRoot "..\suno-api"
    
    if (-not $SkipClone -and -not (Test-Path $sunoApiPath)) {
        Write-Info "Cloning gcui-art/suno-api..."
        
        git clone https://github.com/gcui-art/suno-api.git $sunoApiPath
        
        if ($LASTEXITCODE -ne 0) {
            Write-Error "Failed to clone suno-api repository"
            return $false
        }
        
        Write-Success "✓ Repository cloned"
    }
    
    # Get cookie
    $cookie = Get-SunoCookie
    
    # Update .env
    $envFile = Join-Path $PSScriptRoot "..\env\.env"
    if (-not (Test-Path $envFile)) {
        $envExample = Join-Path $PSScriptRoot "..\env\.env.example"
        if (Test-Path $envExample) {
            Copy-Item $envExample $envFile
        }
    }
    
    if ($cookie) {
        $content = Get-Content $envFile -Raw
        if ($content -match "SUNO_COOKIE=") {
            $content = $content -replace "SUNO_COOKIE=.*", "SUNO_COOKIE=$cookie"
        } else {
            $content += "`nSUNO_COOKIE=$cookie"
        }
        
        # Also set LOCAL URL
        if ($content -notmatch "SUNO_LOCAL_URL=") {
            $content += "`nSUNO_LOCAL_URL=http://localhost:3100"
        }
        
        Set-Content $envFile $content
        Write-Success "✓ Environment configured"
    }
    
    # Create Docker network if needed
    $network = docker network ls --filter name=nano-network --format "{{.Name}}" 2>$null
    if (-not $network) {
        Write-Info "Creating Docker network..."
        docker network create nano-network
    }
    
    # Build and start
    Write-Info "Building and starting Suno API..."
    
    $composePath = Join-Path $PSScriptRoot "..\docker\docker-compose.suno.yml"
    
    Push-Location (Join-Path $PSScriptRoot "..")
    try {
        # Export cookie for docker-compose
        $env:SUNO_COOKIE = $cookie
        
        docker compose -f $composePath build suno-api
        docker compose -f $composePath up -d suno-api
        
        Write-Success "✓ Suno API container started"
        
        # Wait for health check
        Write-Info "Waiting for service to be ready..."
        Start-Sleep -Seconds 10
        
        # Test endpoint
        try {
            $response = Invoke-RestMethod -Uri "http://localhost:3100/api/get_limit" -TimeoutSec 30
            Write-Success "✓ Suno API is running!"
            Write-Host "  Credits: $($response.credits_left)" -ForegroundColor Cyan
        } catch {
            Write-Warn "Service started but health check pending. Check logs with:"
            Write-Host "  docker logs nano-suno-api" -ForegroundColor Gray
        }
    } finally {
        Pop-Location
    }
    
    return $true
}

# Show Vercel guide
function Show-VercelGuide {
    Write-Host ""
    Write-Info "═══════════════════════════════════════════════════════════"
    Write-Info "  VERCEL DEPLOYMENT GUIDE"
    Write-Info "═══════════════════════════════════════════════════════════"
    Write-Host ""
    Write-Host "Step 1: Fork the Repository" -ForegroundColor White
    Write-Host "  • Go to: https://github.com/gcui-art/suno-api" -ForegroundColor Gray
    Write-Host "  • Click 'Fork' (top right)" -ForegroundColor Gray
    Write-Host ""
    Write-Host "Step 2: Deploy to Vercel" -ForegroundColor White
    Write-Host "  • Go to: https://vercel.com/new" -ForegroundColor Gray
    Write-Host "  • Import your forked repo" -ForegroundColor Gray
    Write-Host "  • Click 'Deploy'" -ForegroundColor Gray
    Write-Host ""
    Write-Host "Step 3: Configure Environment" -ForegroundColor White
    Write-Host "  • Go to Settings → Environment Variables" -ForegroundColor Gray
    Write-Host "  • Add: SUNO_COOKIE = <your cookie>" -ForegroundColor Gray
    Write-Host "  • (Optional) Add: TWOCAPTCHA_API_KEY = <key>" -ForegroundColor Gray
    Write-Host ""
    Write-Host "Step 4: Redeploy" -ForegroundColor White
    Write-Host "  • Go to Deployments → Latest → Redeploy" -ForegroundColor Gray
    Write-Host ""
    Write-Host "Step 5: Update Your .env" -ForegroundColor White
    Write-Host "  SUNO_VERCEL_URL=https://your-project.vercel.app" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Full guide: docs/SUNO_INTEGRATION_GUIDE.md" -ForegroundColor Yellow
}

# Test installation
function Test-SunoInstallation {
    Write-Info "Testing Suno integration..."
    
    # Try Python test
    $testScript = @"
import asyncio
import os
os.chdir(r'$PSScriptRoot\..')

async def test():
    try:
        from backend.services.suno_pip_client import get_unified_suno
        client = get_unified_suno()
        credits = await client.get_credits()
        print(f"SUCCESS: Backend={client.backend}, Credits={credits['credits_left']}")
        await client.close()
        return True
    except Exception as e:
        print(f"ERROR: {e}")
        return False

asyncio.run(test())
"@

    $result = python -c $testScript 2>&1
    Write-Host $result
    
    if ($result -match "SUCCESS") {
        return $true
    }
    return $false
}

# Main
function Main {
    Show-Banner
    
    if ($Help) {
        Show-Help
        return
    }
    
    # Check prerequisites
    $prereqs = Test-Prerequisites
    
    # Auto-select method
    if ($Method -eq "auto") {
        if ($prereqs.Python) {
            $Method = "pip"
            Write-Info "Auto-selected method: pip (Python package)"
        } elseif ($prereqs.Docker) {
            $Method = "docker"
            Write-Info "Auto-selected method: docker"
        } else {
            $Method = "vercel"
            Write-Info "Auto-selected method: vercel (no local prerequisites)"
        }
    }
    
    Write-Host ""
    
    # Execute selected method
    switch ($Method) {
        "pip" {
            if (-not $prereqs.Python) {
                Write-Error "Python 3.9+ required for pip method"
                Write-Host "Install from: https://python.org"
                return
            }
            $success = Install-PipMethod
        }
        "docker" {
            $success = Install-DockerMethod -Prerequisites $prereqs
        }
        "vercel" {
            Show-VercelGuide
            return
        }
    }
    
    if ($success) {
        Write-Host ""
        Write-Success "═══════════════════════════════════════════════════════════"
        Write-Success "  ✓ SUNO INTEGRATION SETUP COMPLETE!"
        Write-Success "═══════════════════════════════════════════════════════════"
        Write-Host ""
        Write-Host "Next steps:" -ForegroundColor White
        Write-Host "  1. Verify with: python -c 'from backend.services.suno_pip_client import *'" -ForegroundColor Gray
        Write-Host "  2. Check credits: See API at http://localhost:3100/api/get_limit" -ForegroundColor Gray
        Write-Host "  3. Read full guide: docs/SUNO_INTEGRATION_GUIDE.md" -ForegroundColor Gray
        Write-Host ""
        
        # Run test
        Test-SunoInstallation
    }
}

# Run
Main
