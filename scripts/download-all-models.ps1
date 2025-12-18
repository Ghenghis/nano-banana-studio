# NANO BANANA STUDIO PRO - MODEL DOWNLOADER
# Downloads all required models for video, music, TTS, speech, and image generation
#
# Usage:
#   .\download-all-models.ps1               # Download all essential
#   .\download-all-models.ps1 -Category video  # Video models only
#   .\download-all-models.ps1 -List            # Show what will be downloaded

param(
    [ValidateSet("all", "video", "music", "tts", "speech", "image", "face")]
    [string]$Category = "all",
    [string]$OutputDir = "G:\models",
    [string]$LMStudioDir = "C:\Users\Admin\.lmstudio\models",
    [switch]$List,
    [switch]$Force,
    [switch]$Help
)

$ErrorActionPreference = "Stop"

function Write-Success { Write-Host $args -ForegroundColor Green }
function Write-Info { Write-Host $args -ForegroundColor Cyan }
function Write-Warn { Write-Host $args -ForegroundColor Yellow }
function Write-Err { Write-Host $args -ForegroundColor Red }

function Show-Banner {
    Write-Host ""
    Write-Host "  =================================================================" -ForegroundColor Magenta
    Write-Host "     NANO BANANA STUDIO PRO - MODEL DOWNLOADER                    " -ForegroundColor Magenta
    Write-Host "  =================================================================" -ForegroundColor Magenta
    Write-Host "  Output: $OutputDir" -ForegroundColor Gray
    Write-Host ""
}

# MODEL DEFINITIONS
$Models = @{
    video = @(
        @{name="LTX-Video-0.9.7-distilled"; repo="Lightricks/LTX-Video-0.9.7-distilled"; size="8GB"; vram="12GB"; priority="essential"; description="Fast video generation"}
        @{name="LTX-Video-GGUF"; repo="city96/LTX-Video-gguf"; size="4GB"; vram="8GB"; priority="recommended"; description="Quantized LTX-Video"}
        @{name="WanVideo-ComfyUI"; repo="Kijai/WanVideo_comfy"; size="12GB"; vram="16GB"; priority="recommended"; description="High-quality video for ComfyUI"}
        @{name="Stable-Video-Diffusion-XT"; repo="stabilityai/stable-video-diffusion-img2vid-xt-1-1"; size="10GB"; vram="12GB"; priority="essential"; description="Image-to-video"}
    )
    music = @(
        @{name="MusicGen-Large"; repo="facebook/musicgen-large"; size="6GB"; vram="8GB"; priority="essential"; description="Best quality local music"}
        @{name="MusicGen-Medium"; repo="facebook/musicgen-medium"; size="3GB"; vram="6GB"; priority="recommended"; description="Balanced music generation"}
        @{name="MusicGen-Melody"; repo="facebook/musicgen-melody"; size="3GB"; vram="6GB"; priority="optional"; description="Melody conditioning"}
    )
    tts = @(
        @{name="Bark"; repo="suno/bark"; size="5GB"; vram="8GB"; priority="essential"; description="Multilingual TTS"}
        @{name="Bark-Small"; repo="suno/bark-small"; size="2GB"; vram="4GB"; priority="recommended"; description="Fast Bark"}
        @{name="XTTS-v2"; repo="coqui/XTTS-v2"; size="2GB"; vram="4GB"; priority="essential"; description="Voice cloning TTS"}
    )
    speech = @(
        @{name="Whisper-Large-V3"; repo="openai/whisper-large-v3"; size="3GB"; vram="6GB"; priority="essential"; description="Best accuracy STT"}
        @{name="Whisper-Large-V3-Turbo"; repo="openai/whisper-large-v3-turbo"; size="1.5GB"; vram="4GB"; priority="recommended"; description="8x faster Whisper"}
        @{name="Faster-Whisper-Large-V3"; repo="Systran/faster-whisper-large-v3"; size="1.5GB"; vram="4GB"; priority="recommended"; description="CTranslate2 Whisper"}
    )
    image = @(
        @{name="FLUX.1-schnell"; repo="black-forest-labs/FLUX.1-schnell"; size="24GB"; vram="12GB"; priority="essential"; description="Fast image generation"}
        @{name="SDXL-Base-1.0"; repo="stabilityai/stable-diffusion-xl-base-1.0"; size="7GB"; vram="8GB"; priority="essential"; description="Industry standard"}
        @{name="SDXL-Turbo"; repo="stabilityai/sdxl-turbo"; size="7GB"; vram="8GB"; priority="recommended"; description="Fast 1-4 step SDXL"}
    )
    face = @(
        @{name="IPAdapter-FaceID"; repo="h94/IP-Adapter-FaceID"; size="500MB"; vram="2GB"; priority="essential"; description="Face identity preservation"}
        @{name="InstantID"; repo="InstantX/InstantID"; size="1GB"; vram="4GB"; priority="recommended"; description="Zero-shot identity generation"}
    )
}

function Show-ModelList {
    Write-Host ""
    Write-Host "  MODELS TO DOWNLOAD" -ForegroundColor Cyan
    Write-Host "  ==================" -ForegroundColor Cyan
    
    $totalSize = 0
    
    foreach ($cat in $Models.Keys) {
        if ($Category -ne "all" -and $Category -ne $cat) { continue }
        
        Write-Host ""
        Write-Host "  [DIR] $($cat.ToUpper())" -ForegroundColor Yellow
        Write-Host "  ----------------------------------------" -ForegroundColor Gray
        
        foreach ($model in $Models[$cat]) {
            $priority = switch ($model.priority) {
                "essential" { "[!]" }
                "recommended" { "[*]" }
                "optional" { "[-]" }
            }
            
            $sizeNum = [int]($model.size -replace "[^\d]", "")
            $totalSize += $sizeNum
            
            Write-Host "  $priority $($model.name)" -ForegroundColor White
            Write-Host "     $($model.description)" -ForegroundColor Gray
            Write-Host "     Size: $($model.size) | VRAM: $($model.vram)" -ForegroundColor DarkGray
        }
    }
    
    Write-Host ""
    Write-Host "  Total estimated: ~${totalSize}GB" -ForegroundColor Yellow
    Write-Host "  [!] Essential  [*] Recommended  [-] Optional" -ForegroundColor Gray
}

function Download-Model {
    param([hashtable]$Model, [string]$OutputDir)
    
    $modelDir = Join-Path $OutputDir $Model.name
    
    if ((Test-Path $modelDir) -and -not $Force) {
        Write-Warn "  [>>] $($Model.name) exists, skipping"
        return $true
    }
    
    Write-Info "  [DL] Downloading $($Model.name)..."
    Write-Host "      Size: $($Model.size) | VRAM: $($Model.vram)" -ForegroundColor Gray
    
    New-Item -ItemType Directory -Path $modelDir -Force | Out-Null
    
    try {
        $result = huggingface-cli download $Model.repo --local-dir $modelDir --local-dir-use-symlinks False 2>&1
        if ($LASTEXITCODE -ne 0) {
            Write-Err "  [X] Failed: $($Model.name)"
            return $false
        }
        Write-Success "  [OK] Downloaded $($Model.name)"
        return $true
    } catch {
        Write-Err "  [X] Error: $_"
        return $false
    }
}

function Check-LMStudioModels {
    Write-Info "Checking LM Studio models..."
    
    $found = @()
    if (Test-Path "$LMStudioDir\city96\t5-v1_1-xxl-encoder-gguf") { $found += "T5-XXL-Encoder" }
    if (Test-Path "$LMStudioDir\OuteAI\OuteTTS-0.3-1B-GGUF") { $found += "OuteTTS" }
    if (Test-Path "$LMStudioDir\befox\WAN2.2-14B-Rapid-AllInOne-GGUF") { $found += "WAN2.2-14B" }
    
    if ($found.Count -gt 0) {
        Write-Success "Found in LM Studio:"
        $found | ForEach-Object { Write-Host "  [OK] $_" -ForegroundColor Green }
    }
    return $found
}

function Main {
    Show-Banner
    
    if ($Help) {
        Write-Host "Usage: .\download-all-models.ps1 [-Category <type>] [-OutputDir <path>] [-List] [-Force]"
        Write-Host "Categories: all, video, music, tts, speech, image, face"
        return
    }
    
    Check-LMStudioModels
    
    if ($List) {
        Show-ModelList
        return
    }
    
    # Ensure directories exist
    New-Item -ItemType Directory -Path $OutputDir -Force | Out-Null
    foreach ($dir in @("video", "music", "tts", "speech", "image", "face")) {
        New-Item -ItemType Directory -Path (Join-Path $OutputDir $dir) -Force | Out-Null
    }
    
    # Check huggingface-cli
    try { $null = huggingface-cli --version 2>&1 } catch {
        Write-Warn "Installing huggingface-cli..."
        pip install --upgrade huggingface_hub[cli]
    }
    
    $downloaded = 0
    $failed = 0
    
    foreach ($cat in $Models.Keys) {
        if ($Category -ne "all" -and $Category -ne $cat) { continue }
        
        Write-Host ""
        Write-Host "  [PKG] DOWNLOADING: $($cat.ToUpper())" -ForegroundColor Yellow
        
        $catDir = Join-Path $OutputDir $cat
        
        foreach ($model in $Models[$cat]) {
            if ($model.priority -eq "optional" -and $Category -eq "all") {
                Write-Host "  [>>] Skipping optional: $($model.name)" -ForegroundColor Gray
                continue
            }
            
            if (Download-Model -Model $model -OutputDir $catDir) { $downloaded++ } else { $failed++ }
        }
    }
    
    Write-Host ""
    Write-Host "  [SUM] SUMMARY" -ForegroundColor Cyan
    Write-Success "  Downloaded: $downloaded models"
    if ($failed -gt 0) { Write-Err "  Failed: $failed models" }
    Write-Host "  Location: $OutputDir" -ForegroundColor Gray
}

Main
