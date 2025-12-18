<#
.SYNOPSIS
    Run all code quality checks for Nano Banana Studio Pro
.DESCRIPTION
    Executes auto-repair scan, event handler audit, and tests.
    No interactive prompts - runs fully automatically.
#>

param(
    [switch]$Fix = $false,
    [switch]$SkipTests = $false
)

$ErrorActionPreference = "Continue"
$ProjectRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)

Write-Host ""
Write-Host "================================================" -ForegroundColor Magenta
Write-Host " Nano Banana Studio Pro - Full Quality Check" -ForegroundColor Magenta
Write-Host "================================================" -ForegroundColor Magenta
Write-Host ""

$exitCode = 0
$results = @()

# 1. Run Auto-Repair Scan
Write-Host "[1/3] Running Auto-Repair Scan..." -ForegroundColor Cyan
Write-Host ""

$autoRepairArgs = @()
if ($Fix) { $autoRepairArgs += "-Fix" }

$autoRepairScript = Join-Path $PSScriptRoot "auto-repair.ps1"
if (Test-Path $autoRepairScript) {
    & $autoRepairScript @autoRepairArgs
    $autoRepairResult = $LASTEXITCODE
    $results += [PSCustomObject]@{
        Check = "Auto-Repair Scan"
        Status = if ($autoRepairResult -eq 0) { "PASS" } else { "ISSUES FOUND" }
        ExitCode = $autoRepairResult
    }
    if ($autoRepairResult -ne 0) { $exitCode = 1 }
} else {
    Write-Host "  Auto-repair script not found" -ForegroundColor Yellow
    $results += [PSCustomObject]@{
        Check = "Auto-Repair Scan"
        Status = "SKIPPED"
        ExitCode = 0
    }
}

Write-Host ""

# 2. Run Event Handler Audit
Write-Host "[2/3] Running Event Handler Audit..." -ForegroundColor Cyan
Write-Host ""

$eventAuditScript = Join-Path $PSScriptRoot "event-handler-audit.js"
$frontendPath = Join-Path $ProjectRoot "frontend\src"

if ((Test-Path $eventAuditScript) -and (Get-Command node -ErrorAction SilentlyContinue)) {
    node $eventAuditScript $frontendPath
    $eventAuditResult = $LASTEXITCODE
    $results += [PSCustomObject]@{
        Check = "Event Handler Audit"
        Status = if ($eventAuditResult -eq 0) { "PASS" } else { "ISSUES FOUND" }
        ExitCode = $eventAuditResult
    }
    if ($eventAuditResult -ne 0) { $exitCode = 1 }
} else {
    Write-Host "  Event handler audit skipped (Node.js not available or script missing)" -ForegroundColor Yellow
    $results += [PSCustomObject]@{
        Check = "Event Handler Audit"
        Status = "SKIPPED"
        ExitCode = 0
    }
}

Write-Host ""

# 3. Run Tests
if (-not $SkipTests) {
    Write-Host "[3/3] Running Tests..." -ForegroundColor Cyan
    Write-Host ""
    
    if (Get-Command pytest -ErrorAction SilentlyContinue) {
        Push-Location $ProjectRoot
        pytest tests/ -v --tb=short 2>&1 | Out-Host
        $testResult = $LASTEXITCODE
        Pop-Location
        
        $results += [PSCustomObject]@{
            Check = "Test Suite"
            Status = if ($testResult -eq 0) { "PASS" } else { "FAILURES" }
            ExitCode = $testResult
        }
        if ($testResult -ne 0) { $exitCode = 1 }
    } else {
        Write-Host "  pytest not available - skipping tests" -ForegroundColor Yellow
        $results += [PSCustomObject]@{
            Check = "Test Suite"
            Status = "SKIPPED"
            ExitCode = 0
        }
    }
} else {
    Write-Host "[3/3] Tests skipped by request" -ForegroundColor Yellow
    $results += [PSCustomObject]@{
        Check = "Test Suite"
        Status = "SKIPPED"
        ExitCode = 0
    }
}

# Summary
Write-Host ""
Write-Host "================================================" -ForegroundColor Magenta
Write-Host " Summary" -ForegroundColor Magenta
Write-Host "================================================" -ForegroundColor Magenta
Write-Host ""

foreach ($result in $results) {
    $statusColor = switch ($result.Status) {
        "PASS" { "Green" }
        "SKIPPED" { "Yellow" }
        default { "Red" }
    }
    Write-Host "  $($result.Check): " -NoNewline
    Write-Host $result.Status -ForegroundColor $statusColor
}

Write-Host ""

if ($exitCode -eq 0) {
    Write-Host "All checks passed!" -ForegroundColor Green
} else {
    Write-Host "Some checks failed. Review issues above." -ForegroundColor Red
}

Write-Host ""
exit $exitCode
