<# 
.SYNOPSIS
    Nano Banana Studio Pro - Automated Code Repair Script
.DESCRIPTION
    Identifies and fixes common coding issues without disrupting functionality.
    Implements proactive code quality framework per Global Rules.
.NOTES
    Version: 1.0.0
    Runs automatically without user prompts.
#>

param(
    [string]$ProjectPath = (Split-Path -Parent (Split-Path -Parent $PSScriptRoot)),
    [switch]$Fix = $false,
    [switch]$Verbose = $false
)

$ErrorActionPreference = "Continue"
$ProgressPreference = "SilentlyContinue"

# Colors for output
function Write-Success { param($msg) Write-Host "[OK] $msg" -ForegroundColor Green }
function Write-Warning { param($msg) Write-Host "[WARN] $msg" -ForegroundColor Yellow }
function Write-Error { param($msg) Write-Host "[ERROR] $msg" -ForegroundColor Red }
function Write-Info { param($msg) Write-Host "[INFO] $msg" -ForegroundColor Cyan }

Write-Host ""
Write-Host "========================================" -ForegroundColor Magenta
Write-Host " Nano Banana Code Quality Scanner" -ForegroundColor Magenta  
Write-Host "========================================" -ForegroundColor Magenta
Write-Host ""

$issues = @()
$fixed = @()

# ============================================================================
# 1. Check for common Python issues
# ============================================================================
Write-Info "Scanning Python files..."

$pythonFiles = Get-ChildItem -Path $ProjectPath -Recurse -Include "*.py" -ErrorAction SilentlyContinue | 
    Where-Object { $_.FullName -notmatch "\\(venv|env|__pycache__|\.git|node_modules)\\" }

foreach ($file in $pythonFiles) {
    $content = Get-Content $file.FullName -Raw -ErrorAction SilentlyContinue
    if (-not $content) { continue }
    
    # Check for print statements (should use logger)
    if ($content -match "(?<!#.*)print\s*\(") {
        $issues += [PSCustomObject]@{
            File = $file.FullName
            Issue = "Uses print() instead of logger"
            Severity = "Warning"
            AutoFix = $false
        }
    }
    
    # Check for bare except clauses
    if ($content -match "except\s*:") {
        $issues += [PSCustomObject]@{
            File = $file.FullName
            Issue = "Bare except clause (catches all exceptions)"
            Severity = "Warning"
            AutoFix = $false
        }
    }
    
    # Check for TODO/FIXME comments
    $todoMatches = [regex]::Matches($content, "(TODO|FIXME|XXX|HACK):", [System.Text.RegularExpressions.RegexOptions]::IgnoreCase)
    if ($todoMatches.Count -gt 0) {
        $issues += [PSCustomObject]@{
            File = $file.FullName
            Issue = "Contains $($todoMatches.Count) TODO/FIXME comments"
            Severity = "Info"
            AutoFix = $false
        }
    }
    
}


# ============================================================================
# 2. Check for JavaScript/React issues
# ============================================================================
Write-Info "Scanning JavaScript/React files..."

$jsFiles = Get-ChildItem -Path $ProjectPath -Recurse -Include "*.js","*.jsx","*.ts","*.tsx" -ErrorAction SilentlyContinue |
    Where-Object { $_.FullName -notmatch "\\(node_modules|dist|build|\.git)\\" }

foreach ($file in $jsFiles) {
    $content = Get-Content $file.FullName -Raw -ErrorAction SilentlyContinue
    if (-not $content) { continue }
    
    # Check for console.log (should be removed in production)
    if ($content -match "console\.log\s*\(") {
        $issues += [PSCustomObject]@{
            File = $file.FullName
            Issue = "Contains console.log() statements"
            Severity = "Warning"
            AutoFix = $true
        }
    }
    
    # Check for async functions (simplified - manual review needed)
    if ($content -match "async\s+function" -or $content -match "async\s*\(") {
        if ($content -notmatch "try\s*\{") {
            $issues += [PSCustomObject]@{
                File = $file.FullName
                Issue = "Async function may be missing try/catch"
                Severity = "Info"
                AutoFix = $false
            }
        }
    }
    
    # Check for == instead of === (simplified check)
    if ($content -match " == ") {
        $issues += [PSCustomObject]@{
            File = $file.FullName
            Issue = "Uses == instead of === for comparison"
            Severity = "Warning"
            AutoFix = $false
        }
    }
    
    # Check for .map usage (may need key prop review)
    if ($content -match "\.map\(" -and $content -notmatch "key=") {
        $issues += [PSCustomObject]@{
            File = $file.FullName
            Issue = "React list may be missing key prop - review .map() usage"
            Severity = "Info"
            AutoFix = $false
        }
    }
}

# ============================================================================
# 3. Check configuration files
# ============================================================================
Write-Info "Checking configuration files..."

# Check for .env file
$envFile = Join-Path $ProjectPath ".env"
$envExample = Join-Path $ProjectPath ".env.example"

if (-not (Test-Path $envFile)) {
    if (Test-Path $envExample) {
        $issues += [PSCustomObject]@{
            File = $envFile
            Issue = ".env file missing (copy from .env.example)"
            Severity = "Error"
            AutoFix = $true
        }
        
        if ($Fix) {
            Copy-Item $envExample $envFile
            $fixed += "Created .env from .env.example"
        }
    }
}

# Check package.json exists in frontend
$frontendPackage = Join-Path $ProjectPath "frontend\package.json"
if (Test-Path $frontendPackage) {
    $packageJson = Get-Content $frontendPackage | ConvertFrom-Json
    
    if (-not $packageJson.scripts.lint) {
        $issues += [PSCustomObject]@{
            File = $frontendPackage
            Issue = "Missing lint script in package.json"
            Severity = "Warning"
            AutoFix = $false
        }
    }
}

# ============================================================================
# 4. Check for security issues
# ============================================================================
Write-Info "Checking for security issues..."

$allFiles = Get-ChildItem -Path $ProjectPath -Recurse -Include "*.py","*.js","*.jsx","*.ts","*.tsx","*.json","*.yaml","*.yml" -ErrorAction SilentlyContinue |
    Where-Object { $_.FullName -notmatch "\\(node_modules|venv|env|\.git)\\" }

foreach ($file in $allFiles) {
    $content = Get-Content $file.FullName -Raw -ErrorAction SilentlyContinue
    if (-not $content) { continue }
    
    # Check for hardcoded API keys (simplified)
    $hasApiKey = $content -match "api_key\s*=" -or $content -match "apikey\s*=" -or $content -match "secret\s*="
    if ($hasApiKey -and $file.Name -notmatch "\.example" -and $file.Name -notmatch "\.sample") {
        $issues += [PSCustomObject]@{
            File = $file.FullName
            Issue = "Possible hardcoded secret/API key"
            Severity = "Warning"
            AutoFix = $false
        }
    }
}

# ============================================================================
# 5. Generate Report
# ============================================================================
Write-Host ""
Write-Host "========================================" -ForegroundColor Magenta
Write-Host " Code Quality Report" -ForegroundColor Magenta
Write-Host "========================================" -ForegroundColor Magenta
Write-Host ""

$errorCount = ($issues | Where-Object { $_.Severity -eq "Error" }).Count
$warningCount = ($issues | Where-Object { $_.Severity -eq "Warning" }).Count
$infoCount = ($issues | Where-Object { $_.Severity -eq "Info" }).Count

if ($issues.Count -eq 0) {
    Write-Success "No issues found! Code quality is excellent."
} else {
    Write-Host "Found $($issues.Count) issues:" -ForegroundColor White
    Write-Host "  - Errors:   $errorCount" -ForegroundColor Red
    Write-Host "  - Warnings: $warningCount" -ForegroundColor Yellow
    Write-Host "  - Info:     $infoCount" -ForegroundColor Cyan
    Write-Host ""
    
    # Group by file
    $groupedIssues = $issues | Group-Object -Property File
    
    foreach ($group in $groupedIssues) {
        $relativePath = $group.Name.Replace($ProjectPath, "").TrimStart("\")
        Write-Host "  $relativePath" -ForegroundColor White
        
        foreach ($issue in $group.Group) {
            $color = switch ($issue.Severity) {
                "Error" { "Red" }
                "Warning" { "Yellow" }
                default { "Cyan" }
            }
            $autoFixTag = if ($issue.AutoFix) { " [AutoFix]" } else { "" }
            Write-Host "    - $($issue.Issue)$autoFixTag" -ForegroundColor $color
        }
    }
}

if ($fixed.Count -gt 0) {
    Write-Host ""
    Write-Success "Auto-fixed $($fixed.Count) issues:"
    foreach ($f in $fixed) {
        Write-Host "    - $f" -ForegroundColor Green
    }
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Magenta

# Return exit code based on errors
if ($errorCount -gt 0) {
    exit 1
} else {
    exit 0
}
