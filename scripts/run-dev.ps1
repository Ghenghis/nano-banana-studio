# =============================================================================
# NANO BANANA STUDIO PRO - DEVELOPMENT MODE
# =============================================================================
# Start all services in development mode
# Usage: .\scripts\run-dev.ps1
# =============================================================================

param(
    [switch]$Rebuild,
    [switch]$GPU,
    [switch]$Logs,
    [switch]$Stop
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot

Write-Host ""
Write-Host "🍌 NANO BANANA STUDIO PRO" -ForegroundColor Yellow
Write-Host "   Development Mode" -ForegroundColor Gray
Write-Host ""

# Stop services if requested
if ($Stop) {
    Write-Host "Stopping all services..." -ForegroundColor Yellow
    Push-Location $ProjectRoot
    docker compose down
    Pop-Location
    Write-Host "✓ All services stopped" -ForegroundColor Green
    exit 0
}

# Load environment variables
$envFile = Join-Path $ProjectRoot ".env"
if (Test-Path $envFile) {
    Get-Content $envFile | ForEach-Object {
        if ($_ -match "^([^#][^=]+)=(.*)$") {
            [Environment]::SetEnvironmentVariable($matches[1], $matches[2], "Process")
        }
    }
    Write-Host "✓ Environment loaded from .env" -ForegroundColor Green
} else {
    Write-Host "⚠ No .env file found - using defaults" -ForegroundColor Yellow
}

# Change to project root
Push-Location $ProjectRoot

try {
    # Build if requested
    if ($Rebuild) {
        Write-Host ""
        Write-Host "Rebuilding Docker images..." -ForegroundColor Yellow
        docker compose build --no-cache
    }
    
    # Start services
    Write-Host ""
    Write-Host "Starting services..." -ForegroundColor Yellow
    
    $profiles = @()
    if ($GPU) {
        $profiles += "--profile", "gpu"
        Write-Host "  • GPU mode enabled" -ForegroundColor Cyan
    }
    
    # Start Docker Compose
    if ($profiles.Count -gt 0) {
        docker compose $profiles up -d
    } else {
        docker compose up -d
    }
    
    # Wait for services
    Write-Host ""
    Write-Host "Waiting for services to start..." -ForegroundColor Yellow
    Start-Sleep -Seconds 5
    
    # Check service health
    Write-Host ""
    Write-Host "Service Status:" -ForegroundColor Yellow
    
    $services = @(
        @{Name="n8n"; Port=5678; URL="http://localhost:5678"},
        @{Name="API"; Port=8000; URL="http://localhost:8000/health"},
        @{Name="Redis"; Port=6379; URL=$null}
    )
    
    foreach ($svc in $services) {
        try {
            if ($svc.URL) {
                $response = Invoke-WebRequest -Uri $svc.URL -TimeoutSec 5 -UseBasicParsing -ErrorAction SilentlyContinue
                if ($response.StatusCode -eq 200) {
                    Write-Host "  ✓ $($svc.Name): Running (port $($svc.Port))" -ForegroundColor Green
                }
            } else {
                # Check port for non-HTTP services
                $connection = Test-NetConnection -ComputerName localhost -Port $svc.Port -WarningAction SilentlyContinue
                if ($connection.TcpTestSucceeded) {
                    Write-Host "  ✓ $($svc.Name): Running (port $($svc.Port))" -ForegroundColor Green
                } else {
                    Write-Host "  • $($svc.Name): Starting..." -ForegroundColor Yellow
                }
            }
        } catch {
            Write-Host "  • $($svc.Name): Starting..." -ForegroundColor Yellow
        }
    }
    
    # Show URLs
    Write-Host ""
    Write-Host "======================================" -ForegroundColor Cyan
    Write-Host "  SERVICES READY                     " -ForegroundColor Cyan
    Write-Host "======================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "n8n Workflows:" -ForegroundColor White
    Write-Host "  http://localhost:5678" -ForegroundColor Gray
    Write-Host "  Login: admin / nanobanana" -ForegroundColor Gray
    Write-Host ""
    Write-Host "API Documentation:" -ForegroundColor White
    Write-Host "  http://localhost:8000/docs" -ForegroundColor Gray
    Write-Host ""
    Write-Host "Commands:" -ForegroundColor White
    Write-Host "  Stop:    .\scripts\run-dev.ps1 -Stop" -ForegroundColor Gray
    Write-Host "  Logs:    docker compose logs -f" -ForegroundColor Gray
    Write-Host "  Rebuild: .\scripts\run-dev.ps1 -Rebuild" -ForegroundColor Gray
    Write-Host ""
    
    # Show logs if requested
    if ($Logs) {
        Write-Host "Showing logs (Ctrl+C to exit)..." -ForegroundColor Yellow
        docker compose logs -f
    }
    
} finally {
    Pop-Location
}
