# =============================================================================
# NANO BANANA STUDIO PRO - WINDOWS SETUP SCRIPT
# =============================================================================
# Run this script first to set up the complete environment
# Usage: .\scripts\setup.ps1
# =============================================================================

param(
    [switch]$SkipDocker,
    [switch]$SkipPython,
    [switch]$GPU,
    [switch]$Full
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot

Write-Host "======================================" -ForegroundColor Cyan
Write-Host "  NANO BANANA STUDIO PRO - SETUP     " -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan
Write-Host ""

# -----------------------------------------------------------------------------
# Step 1: Check Prerequisites
# -----------------------------------------------------------------------------
Write-Host "[1/8] Checking prerequisites..." -ForegroundColor Yellow

# Check Docker
if (-not $SkipDocker) {
    try {
        $dockerVersion = docker --version
        Write-Host "  ✓ Docker: $dockerVersion" -ForegroundColor Green
    } catch {
        Write-Host "  ✗ Docker not found. Please install Docker Desktop." -ForegroundColor Red
        Write-Host "    Download: https://www.docker.com/products/docker-desktop/" -ForegroundColor Gray
        exit 1
    }
    
    # Check Docker Compose
    try {
        $composeVersion = docker compose version
        Write-Host "  ✓ Docker Compose: $composeVersion" -ForegroundColor Green
    } catch {
        Write-Host "  ✗ Docker Compose not found." -ForegroundColor Red
        exit 1
    }
}

# Check Python
if (-not $SkipPython) {
    try {
        $pythonVersion = python --version
        Write-Host "  ✓ Python: $pythonVersion" -ForegroundColor Green
    } catch {
        Write-Host "  ✗ Python not found. Please install Python 3.11+." -ForegroundColor Red
        exit 1
    }
}

# Check FFmpeg (optional but recommended)
try {
    $ffmpegVersion = ffmpeg -version 2>&1 | Select-Object -First 1
    Write-Host "  ✓ FFmpeg: Available" -ForegroundColor Green
} catch {
    Write-Host "  ⚠ FFmpeg not found (optional - will use Docker)" -ForegroundColor Yellow
}

# Check NVIDIA GPU (optional)
if ($GPU) {
    try {
        $nvidiaSmi = nvidia-smi --query-gpu=name --format=csv,noheader 2>&1
        Write-Host "  ✓ NVIDIA GPU: $nvidiaSmi" -ForegroundColor Green
    } catch {
        Write-Host "  ⚠ NVIDIA GPU not detected (GPU features disabled)" -ForegroundColor Yellow
    }
}

# -----------------------------------------------------------------------------
# Step 2: Create Directory Structure
# -----------------------------------------------------------------------------
Write-Host ""
Write-Host "[2/8] Creating directory structure..." -ForegroundColor Yellow

$directories = @(
    "data/uploads",
    "data/outputs",
    "data/cache",
    "data/temp",
    "models/face",
    "models/animation",
    "logs"
)

foreach ($dir in $directories) {
    $fullPath = Join-Path $ProjectRoot $dir
    if (-not (Test-Path $fullPath)) {
        New-Item -ItemType Directory -Path $fullPath -Force | Out-Null
        Write-Host "  ✓ Created: $dir" -ForegroundColor Green
    } else {
        Write-Host "  • Exists: $dir" -ForegroundColor Gray
    }
}

# -----------------------------------------------------------------------------
# Step 3: Setup Environment File
# -----------------------------------------------------------------------------
Write-Host ""
Write-Host "[3/8] Setting up environment..." -ForegroundColor Yellow

$envExample = Join-Path $ProjectRoot "env/.env.example"
$envFile = Join-Path $ProjectRoot ".env"

if (-not (Test-Path $envFile)) {
    if (Test-Path $envExample) {
        Copy-Item $envExample $envFile
        Write-Host "  ✓ Created .env from template" -ForegroundColor Green
        Write-Host "  ⚠ IMPORTANT: Edit .env and add your API keys!" -ForegroundColor Yellow
    } else {
        Write-Host "  ✗ .env.example not found" -ForegroundColor Red
    }
} else {
    Write-Host "  • .env already exists" -ForegroundColor Gray
}

# -----------------------------------------------------------------------------
# Step 4: Setup Python Virtual Environment
# -----------------------------------------------------------------------------
if (-not $SkipPython) {
    Write-Host ""
    Write-Host "[4/8] Setting up Python environment..." -ForegroundColor Yellow
    
    $venvPath = Join-Path $ProjectRoot ".venv"
    
    if (-not (Test-Path $venvPath)) {
        Write-Host "  Creating virtual environment..." -ForegroundColor Gray
        python -m venv $venvPath
        Write-Host "  ✓ Virtual environment created" -ForegroundColor Green
    }
    
    # Activate and install dependencies
    $activateScript = Join-Path $venvPath "Scripts/Activate.ps1"
    if (Test-Path $activateScript) {
        & $activateScript
        
        Write-Host "  Installing dependencies..." -ForegroundColor Gray
        pip install --upgrade pip | Out-Null
        pip install -r (Join-Path $ProjectRoot "requirements.txt") | Out-Null
        Write-Host "  ✓ Dependencies installed" -ForegroundColor Green
    }
} else {
    Write-Host ""
    Write-Host "[4/8] Skipping Python setup..." -ForegroundColor Gray
}

# -----------------------------------------------------------------------------
# Step 5: Pull Docker Images
# -----------------------------------------------------------------------------
if (-not $SkipDocker) {
    Write-Host ""
    Write-Host "[5/8] Pulling Docker images..." -ForegroundColor Yellow
    
    $images = @(
        "n8nio/n8n:latest",
        "redis:7-alpine",
        "python:3.11-slim"
    )
    
    foreach ($image in $images) {
        Write-Host "  Pulling $image..." -ForegroundColor Gray
        docker pull $image 2>&1 | Out-Null
        Write-Host "  ✓ $image" -ForegroundColor Green
    }
    
    if ($GPU) {
        Write-Host "  Pulling nvidia/cuda..." -ForegroundColor Gray
        docker pull nvidia/cuda:12.1-runtime-ubuntu22.04 2>&1 | Out-Null
        Write-Host "  ✓ nvidia/cuda:12.1" -ForegroundColor Green
    }
} else {
    Write-Host ""
    Write-Host "[5/8] Skipping Docker image pull..." -ForegroundColor Gray
}

# -----------------------------------------------------------------------------
# Step 6: Build Custom Docker Images
# -----------------------------------------------------------------------------
if (-not $SkipDocker) {
    Write-Host ""
    Write-Host "[6/8] Building custom Docker images..." -ForegroundColor Yellow
    
    Push-Location $ProjectRoot
    
    Write-Host "  Building nano-banana-api..." -ForegroundColor Gray
    docker build -t nano-banana-api:latest -f Dockerfile . 2>&1 | Out-Null
    Write-Host "  ✓ nano-banana-api:latest" -ForegroundColor Green
    
    Write-Host "  Building nano-banana-ffmpeg..." -ForegroundColor Gray
    docker build -t nano-banana-ffmpeg:latest -f Dockerfile.ffmpeg . 2>&1 | Out-Null
    Write-Host "  ✓ nano-banana-ffmpeg:latest" -ForegroundColor Green
    
    if ($GPU) {
        Write-Host "  Building nano-banana-gpu..." -ForegroundColor Gray
        docker build -t nano-banana-gpu:latest -f Dockerfile.gpu . 2>&1 | Out-Null
        Write-Host "  ✓ nano-banana-gpu:latest" -ForegroundColor Green
    }
    
    Pop-Location
} else {
    Write-Host ""
    Write-Host "[6/8] Skipping Docker build..." -ForegroundColor Gray
}

# -----------------------------------------------------------------------------
# Step 7: Initialize n8n Workflows
# -----------------------------------------------------------------------------
Write-Host ""
Write-Host "[7/8] Preparing n8n workflows..." -ForegroundColor Yellow

$workflowsDir = Join-Path $ProjectRoot "n8n/workflows"
$workflowCount = (Get-ChildItem $workflowsDir -Filter "*.json").Count
Write-Host "  ✓ Found $workflowCount workflow files" -ForegroundColor Green
Write-Host "  • Import these manually in n8n at http://localhost:5678" -ForegroundColor Gray

# -----------------------------------------------------------------------------
# Step 8: Final Summary
# -----------------------------------------------------------------------------
Write-Host ""
Write-Host "[8/8] Setup complete!" -ForegroundColor Yellow
Write-Host ""
Write-Host "======================================" -ForegroundColor Cyan
Write-Host "  SETUP COMPLETE - NEXT STEPS        " -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "1. Edit your API keys in .env file:" -ForegroundColor White
Write-Host "   notepad $envFile" -ForegroundColor Gray
Write-Host ""
Write-Host "2. Start the services:" -ForegroundColor White
Write-Host "   .\scripts\run-dev.ps1" -ForegroundColor Gray
Write-Host ""
Write-Host "3. Access the services:" -ForegroundColor White
Write-Host "   • n8n Workflows:  http://localhost:5678" -ForegroundColor Gray
Write-Host "   • API Docs:       http://localhost:8000/docs" -ForegroundColor Gray
Write-Host "   • Redis:          localhost:6379" -ForegroundColor Gray
Write-Host ""
Write-Host "4. Import workflows in n8n:" -ForegroundColor White
Write-Host "   • Open n8n → Settings → Import" -ForegroundColor Gray
Write-Host "   • Import files from: $workflowsDir" -ForegroundColor Gray
Write-Host ""

if (-not (Test-Path $envFile) -or (Get-Content $envFile | Select-String "your_.*_here")) {
    Write-Host "⚠ WARNING: Don't forget to add your API keys to .env!" -ForegroundColor Yellow
}
