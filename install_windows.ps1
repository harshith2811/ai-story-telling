# StoryForge AI - Windows Installation Script
# Automated setup for Python 3.12, FFmpeg verification, virtual environment, and dependencies.

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "   StoryForge AI - Windows Installation & Environment Setup " -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

# 1. Check Python
$pythonCmd = Get-Command python -ErrorAction SilentlyContinue
if (-not $pythonCmd) {
    $pythonCmd = Get-Command "C:\Users\$env:USERNAME\AppData\Roaming\uv\python\cpython-3.12*\python.exe" -ErrorAction SilentlyContinue | Select-Object -First 1
}
if (-not $pythonCmd) {
    Write-Host "[!] Python 3.12 not found in PATH. Please install Python 3.12+ from python.org" -ForegroundColor Red
    exit 1
}
Write-Host "[+] Python executable found: $($pythonCmd.Source)" -ForegroundColor Green

# 2. Check FFmpeg
$ffmpegCmd = Get-Command ffmpeg -ErrorAction SilentlyContinue
if (-not $ffmpegCmd) {
    Write-Host "[!] FFmpeg not found in PATH." -ForegroundColor Yellow
    Write-Host "[*] Looking in C:\Users\$env:USERNAME\tools\ffmpeg..." -ForegroundColor Yellow
    $localFfmpeg = Get-ChildItem "C:\Users\$env:USERNAME\tools\ffmpeg" -Recurse -Filter "ffmpeg.exe" -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($localFfmpeg) {
        $binDir = Split-Path $localFfmpeg.FullName
        $env:PATH = "$binDir;$env:PATH"
        Write-Host "[+] Temporarily added FFmpeg to session PATH: $binDir" -ForegroundColor Green
    } else {
        Write-Host "[!] Please install FFmpeg or place it in tools/ffmpeg/bin" -ForegroundColor Red
    }
} else {
    Write-Host "[+] FFmpeg verified in PATH." -ForegroundColor Green
}

# 3. Create & Activate Virtual Environment
$venvPath = Join-Path $PSScriptRoot ".venv"
if (-not (Test-Path $venvPath)) {
    Write-Host "[*] Creating Python virtual environment at $venvPath..." -ForegroundColor Yellow
    & $pythonCmd.Source -m venv $venvPath
}
$venvPython = Join-Path $venvPath "Scripts\python.exe"
Write-Host "[+] Virtual environment ready: $venvPython" -ForegroundColor Green

# 4. Install Dependencies
Write-Host "[*] Upgrading pip and installing required backend wheels..." -ForegroundColor Yellow
& $venvPython -m pip install --upgrade pip
& $venvPython -m pip install -r (Join-Path $PSScriptRoot "backend\requirements.txt")
& $venvPython -m pip install greenlet truststore faster-whisper pytest pytest-asyncio

# 5. Initialize Storage & Assets
$storageDirs = @(
    "backend\storage\assets\images",
    "backend\storage\assets\audio",
    "backend\storage\assets\music",
    "backend\storage\outputs\renders",
    "backend\storage\outputs\subtitles",
    "backend\storage\outputs\thumbnails",
    "backend\storage\temp",
    "backend\logs"
)
foreach ($dir in $storageDirs) {
    $full = Join-Path $PSScriptRoot $dir
    if (-not (Test-Path $full)) {
        New-Item -ItemType Directory -Path $full -Force | Out-Null
    }
}
Write-Host "[+] Storage directories created." -ForegroundColor Green

# 6. Initialize Environment File
$envFile = Join-Path $PSScriptRoot "backend\.env"
if (-not (Test-Path $envFile)) {
    Copy-Item (Join-Path $PSScriptRoot ".env.example") $envFile
    Write-Host "[+] Created backend\.env from template." -ForegroundColor Green
}

Write-Host "==========================================================" -ForegroundColor Green
Write-Host "   StoryForge AI installation completed successfully!    " -ForegroundColor Green
Write-Host "   Run './run_storyforge.ps1' to launch the application.  " -ForegroundColor Green
Write-Host "==========================================================" -ForegroundColor Green
