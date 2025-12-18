# =============================================================================
# NANO BANANA STUDIO PRO - MODEL DOWNLOAD MANAGER
# =============================================================================
# Downloads and manages AI models from HuggingFace Hub
# =============================================================================
# Usage:
#   .\scripts\download_models.ps1 --essential    # Core models (~20GB)
#   .\scripts\download_models.ps1 --recommended  # All recommended (~50GB)
#   .\scripts\download_models.ps1 --all          # Everything (~100GB)
#   .\scripts\download_models.ps1 --model <id>   # Specific model
#   .\scripts\download_models.ps1 --list         # List available models
# =============================================================================

param(
    [switch]$Essential,
    [switch]$Recommended,
    [switch]$All,
    [string]$Model,
    [switch]$List,
    [switch]$Check,
    [string]$ModelsDir = ".\models"
)

$ErrorActionPreference = "Stop"

# Model definitions
$Models = @{
    # Essential Models (for basic functionality)
    essential = @{
        # Image Generation
        "sdxl_turbo" = @{
            repo = "stabilityai/sdxl-turbo"
            size_gb = 7
            category = "image"
            description = "Fast 4-step SDXL"
        }
        
        # Video Generation
        "svd_xt" = @{
            repo = "stabilityai/stable-video-diffusion-img2vid-xt-1-1"
            size_gb = 10
            category = "video"
            description = "Stable Video Diffusion"
        }
        
        # Speech Recognition
        "whisper_medium" = @{
            repo = "openai/whisper-medium"
            size_gb = 1.5
            category = "speech"
            description = "Whisper Medium"
        }
        
        # Face Detection (InsightFace models are separate)
        "insightface_buffalo" = @{
            repo = "deepinsight/insightface"
            subfolder = "models/buffalo_l"
            size_gb = 0.5
            category = "face"
            description = "InsightFace Buffalo L"
        }
    }
    
    # Recommended Models (better quality)
    recommended = @{
        # Image Generation
        "flux_schnell" = @{
            repo = "black-forest-labs/FLUX.1-schnell"
            size_gb = 23
            category = "image"
            description = "FLUX.1 Schnell - Fast high-quality"
            requires_auth = $true
        }
        
        "flux_merged_fp8" = @{
            repo = "drbaph/FLUX.1-schnell-dev-merged-fp8-4step"
            size_gb = 12
            category = "image"
            description = "FLUX merged FP8 - Speed + quality"
        }
        
        # Video Generation
        "ltx_video_distilled" = @{
            repo = "Lightricks/LTX-Video-0.9.7-distilled"
            size_gb = 8
            category = "video"
            description = "LTX-Video with keyframe control"
        }
        
        "wan_video_fp8" = @{
            repo = "Kijai/WanVideo_comfy_fp8_scaled"
            size_gb = 8
            category = "video"
            description = "WanVideo FP8 scaled"
        }
        
        # Music Generation
        "musicgen_medium" = @{
            repo = "facebook/musicgen-medium"
            size_gb = 4
            category = "music"
            description = "MusicGen Medium"
        }
        
        # TTS
        "bark" = @{
            repo = "suno/bark"
            size_gb = 5
            category = "tts"
            description = "Bark multilingual TTS"
        }
        
        # Speech Recognition
        "whisper_large_v3" = @{
            repo = "openai/whisper-large-v3"
            size_gb = 3
            category = "speech"
            description = "Whisper Large V3 - Best accuracy"
        }
    }
    
    # All Models (for maximum flexibility)
    all = @{
        # Image Generation - Premium
        "flux_dev" = @{
            repo = "black-forest-labs/FLUX.1-dev"
            size_gb = 23
            category = "image"
            description = "FLUX.1 Dev - Best quality"
            requires_auth = $true
        }
        
        "sdxl_base" = @{
            repo = "stabilityai/stable-diffusion-xl-base-1.0"
            size_gb = 7
            category = "image"
            description = "SDXL Base 1.0"
        }
        
        # Video Generation - Premium
        "ltx_video_13b" = @{
            repo = "Lightricks/LTX-Video-0.9.8-13B-distilled"
            size_gb = 26
            category = "video"
            description = "LTX-Video 13B - Best quality"
        }
        
        "wan_video" = @{
            repo = "Kijai/WanVideo_comfy"
            size_gb = 15
            category = "video"
            description = "WanVideo ComfyUI"
        }
        
        "wan_video_gguf" = @{
            repo = "Kijai/WanVideo_comfy_GGUF"
            size_gb = 5
            category = "video"
            description = "WanVideo GGUF - Low VRAM"
        }
        
        # Music Generation - Premium
        "musicgen_large" = @{
            repo = "facebook/musicgen-large"
            size_gb = 7
            category = "music"
            description = "MusicGen Large - Best quality"
        }
        
        "musicgen_melody" = @{
            repo = "facebook/musicgen-melody"
            size_gb = 4
            category = "music"
            description = "MusicGen with melody conditioning"
        }
        
        "musicgen_stereo_large" = @{
            repo = "facebook/musicgen-stereo-large"
            size_gb = 7
            category = "music"
            description = "MusicGen Stereo Large"
        }
        
        # TTS - Premium
        "xtts_v2" = @{
            repo = "coqui/XTTS-v2"
            size_gb = 3
            category = "tts"
            description = "XTTS v2 - Voice cloning"
        }
        
        # LLM (for local storyboarding)
        "llama3_8b" = @{
            repo = "meta-llama/Meta-Llama-3.1-8B-Instruct"
            size_gb = 16
            category = "llm"
            description = "Llama 3.1 8B Instruct"
            requires_auth = $true
        }
        
        "qwen2_7b" = @{
            repo = "Qwen/Qwen2-7B-Instruct"
            size_gb = 14
            category = "llm"
            description = "Qwen 2 7B Instruct"
        }
        
        # Identity Preservation
        "ipadapter_faceid" = @{
            repo = "h94/IP-Adapter-FaceID"
            size_gb = 1
            category = "identity"
            description = "IPAdapter FaceID"
        }
    }
}

function Show-Banner {
    Write-Host ""
    Write-Host "  ╔══════════════════════════════════════════════════════════════╗" -ForegroundColor Yellow
    Write-Host "  ║         🍌 NANO BANANA STUDIO PRO - Model Manager 🍌         ║" -ForegroundColor Yellow
    Write-Host "  ╚══════════════════════════════════════════════════════════════╝" -ForegroundColor Yellow
    Write-Host ""
}

function Get-AllModels {
    $allModels = @{}
    foreach ($tier in @("essential", "recommended", "all")) {
        foreach ($key in $Models[$tier].Keys) {
            if (-not $allModels.ContainsKey($key)) {
                $allModels[$key] = $Models[$tier][$key]
                $allModels[$key]["tier"] = $tier
            }
        }
    }
    return $allModels
}

function Show-ModelList {
    Write-Host "Available Models:" -ForegroundColor Cyan
    Write-Host ""
    
    $allModels = Get-AllModels
    $categories = @("image", "video", "music", "tts", "speech", "face", "identity", "llm")
    
    foreach ($category in $categories) {
        $categoryModels = $allModels.GetEnumerator() | Where-Object { $_.Value.category -eq $category }
        if ($categoryModels) {
            Write-Host "  $($category.ToUpper()):" -ForegroundColor Yellow
            foreach ($model in $categoryModels) {
                $tier = $model.Value.tier
                $tierColor = switch ($tier) {
                    "essential" { "Green" }
                    "recommended" { "Cyan" }
                    "all" { "Gray" }
                }
                $sizeStr = "$($model.Value.size_gb)GB".PadRight(6)
                $authStr = if ($model.Value.requires_auth) { "[AUTH]" } else { "" }
                Write-Host "    • $($model.Key.PadRight(25)) $sizeStr [$tier] $authStr" -ForegroundColor $tierColor
                Write-Host "      $($model.Value.description)" -ForegroundColor DarkGray
            }
            Write-Host ""
        }
    }
    
    # Calculate sizes
    $essentialSize = ($Models.essential.Values | Measure-Object -Property size_gb -Sum).Sum
    $recommendedSize = ($Models.recommended.Values | Measure-Object -Property size_gb -Sum).Sum
    $allSize = ($Models.all.Values | Measure-Object -Property size_gb -Sum).Sum
    
    Write-Host "Download Options:" -ForegroundColor Cyan
    Write-Host "  --essential    ~$([math]::Round($essentialSize))GB (core functionality)"
    Write-Host "  --recommended  ~$([math]::Round($essentialSize + $recommendedSize))GB (better quality)"
    Write-Host "  --all          ~$([math]::Round($essentialSize + $recommendedSize + $allSize))GB (maximum flexibility)"
    Write-Host ""
}

function Test-HuggingFaceAuth {
    $token = $env:HF_TOKEN
    if (-not $token) {
        $tokenFile = "$env:USERPROFILE\.cache\huggingface\token"
        if (Test-Path $tokenFile) {
            $token = Get-Content $tokenFile -Raw
        }
    }
    return [bool]$token
}

function Install-HuggingFaceCLI {
    Write-Host "Checking huggingface_hub installation..." -ForegroundColor Cyan
    
    try {
        python -c "from huggingface_hub import snapshot_download" 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  ✓ huggingface_hub is installed" -ForegroundColor Green
            return $true
        }
    } catch {}
    
    Write-Host "  Installing huggingface_hub..." -ForegroundColor Yellow
    pip install huggingface_hub --quiet
    
    return $true
}

function Download-Model {
    param(
        [string]$ModelId,
        [hashtable]$ModelInfo,
        [string]$OutputDir
    )
    
    $repo = $ModelInfo.repo
    $targetDir = Join-Path $OutputDir $ModelId
    
    # Check if already downloaded
    if (Test-Path $targetDir) {
        $files = Get-ChildItem $targetDir -Recurse -File
        if ($files.Count -gt 0) {
            Write-Host "  ✓ $ModelId already downloaded" -ForegroundColor Green
            return $true
        }
    }
    
    # Check auth requirement
    if ($ModelInfo.requires_auth) {
        if (-not (Test-HuggingFaceAuth)) {
            Write-Host "  ⚠ $ModelId requires HuggingFace authentication" -ForegroundColor Yellow
            Write-Host "    Run: huggingface-cli login" -ForegroundColor DarkGray
            return $false
        }
    }
    
    Write-Host "  ↓ Downloading $ModelId (~$($ModelInfo.size_gb)GB)..." -ForegroundColor Cyan
    
    # Create Python script for download
    $pythonScript = @"
from huggingface_hub import snapshot_download
import os

repo_id = "$repo"
local_dir = r"$targetDir"

try:
    snapshot_download(
        repo_id=repo_id,
        local_dir=local_dir,
        local_dir_use_symlinks=False,
        resume_download=True
    )
    print("SUCCESS")
except Exception as e:
    print(f"ERROR: {e}")
"@
    
    $result = python -c $pythonScript 2>&1
    
    if ($result -match "SUCCESS") {
        Write-Host "  ✓ $ModelId downloaded successfully" -ForegroundColor Green
        return $true
    } else {
        Write-Host "  ✗ Failed to download $ModelId" -ForegroundColor Red
        Write-Host "    $result" -ForegroundColor DarkGray
        return $false
    }
}

function Check-Models {
    Write-Host "Checking installed models..." -ForegroundColor Cyan
    Write-Host ""
    
    $allModels = Get-AllModels
    $installed = 0
    $missing = 0
    
    foreach ($model in $allModels.GetEnumerator()) {
        $targetDir = Join-Path $ModelsDir $model.Key
        if (Test-Path $targetDir) {
            $files = Get-ChildItem $targetDir -Recurse -File
            if ($files.Count -gt 0) {
                Write-Host "  ✓ $($model.Key)" -ForegroundColor Green
                $installed++
                continue
            }
        }
        Write-Host "  ✗ $($model.Key)" -ForegroundColor Red
        $missing++
    }
    
    Write-Host ""
    Write-Host "Summary: $installed installed, $missing missing" -ForegroundColor Cyan
}

# =============================================================================
# Main Script
# =============================================================================

Show-Banner

# Ensure models directory exists
if (-not (Test-Path $ModelsDir)) {
    New-Item -ItemType Directory -Path $ModelsDir -Force | Out-Null
}

# Handle commands
if ($List) {
    Show-ModelList
    exit 0
}

if ($Check) {
    Check-Models
    exit 0
}

if ($Model) {
    # Download specific model
    $allModels = Get-AllModels
    if ($allModels.ContainsKey($Model)) {
        Install-HuggingFaceCLI
        Download-Model -ModelId $Model -ModelInfo $allModels[$Model] -OutputDir $ModelsDir
    } else {
        Write-Host "Unknown model: $Model" -ForegroundColor Red
        Write-Host "Use --list to see available models" -ForegroundColor Yellow
    }
    exit 0
}

# Install huggingface_hub if needed
Install-HuggingFaceCLI

$modelsToDownload = @()

if ($Essential) {
    $modelsToDownload += $Models.essential.Keys
}

if ($Recommended) {
    $modelsToDownload += $Models.essential.Keys
    $modelsToDownload += $Models.recommended.Keys
}

if ($All) {
    $modelsToDownload += $Models.essential.Keys
    $modelsToDownload += $Models.recommended.Keys
    $modelsToDownload += $Models.all.Keys
}

if ($modelsToDownload.Count -eq 0) {
    Write-Host "No download option specified." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Usage:" -ForegroundColor Cyan
    Write-Host "  .\download_models.ps1 --essential    # Core models (~20GB)"
    Write-Host "  .\download_models.ps1 --recommended  # All recommended (~50GB)"
    Write-Host "  .\download_models.ps1 --all          # Everything (~100GB)"
    Write-Host "  .\download_models.ps1 --model <id>   # Specific model"
    Write-Host "  .\download_models.ps1 --list         # List available models"
    Write-Host "  .\download_models.ps1 --check        # Check installed models"
    exit 1
}

# Remove duplicates
$modelsToDownload = $modelsToDownload | Select-Object -Unique

$allModels = Get-AllModels
$totalSize = 0
foreach ($modelId in $modelsToDownload) {
    if ($allModels.ContainsKey($modelId)) {
        $totalSize += $allModels[$modelId].size_gb
    }
}

Write-Host "Downloading $($modelsToDownload.Count) models (~$([math]::Round($totalSize))GB total)..." -ForegroundColor Cyan
Write-Host ""

$success = 0
$failed = 0

foreach ($modelId in $modelsToDownload) {
    if ($allModels.ContainsKey($modelId)) {
        $result = Download-Model -ModelId $modelId -ModelInfo $allModels[$modelId] -OutputDir $ModelsDir
        if ($result) { $success++ } else { $failed++ }
    }
}

Write-Host ""
Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Yellow
Write-Host "Download Complete!" -ForegroundColor Green
Write-Host "  Successfully downloaded: $success models"
if ($failed -gt 0) {
    Write-Host "  Failed: $failed models" -ForegroundColor Red
}
Write-Host ""
Write-Host "Models are stored in: $((Resolve-Path $ModelsDir).Path)" -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Yellow
