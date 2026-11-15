# StoryForge AI - Windows Execution Launcher
# Starts the FastAPI backend with embedded Dark-Mode Dashboard on http://localhost:8000

$scriptDir = $PSScriptRoot
$venvPython = Join-Path $scriptDir ".venv\Scripts\python.exe"
if (-not (Test-Path $venvPython)) {
    $venvPython = "c:\Users\amara\OneDrive\Documents\yt\.venv\Scripts\python.exe"
}

# Ensure tools/ffmpeg is in PATH if present
$localFfmpeg = Get-ChildItem "C:\Users\$env:USERNAME\tools\ffmpeg" -Recurse -Filter "ffmpeg.exe" -ErrorAction SilentlyContinue | Select-Object -First 1
if ($localFfmpeg) {
    $binDir = Split-Path $localFfmpeg.FullName
    $env:PATH = "$binDir;$env:PATH"
}

$backendDir = Join-Path $scriptDir "backend"
$env:PYTHONPATH = $backendDir

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "                Launching StoryForge AI                   " -ForegroundColor Cyan
Write-Host "   Dashboard URL : http://localhost:8000                  " -ForegroundColor Yellow
Write-Host "   API Docs      : http://localhost:8000/docs             " -ForegroundColor Yellow
Write-Host "   Press Ctrl+C to terminate the server                   " -ForegroundColor Gray
Write-Host "==========================================================" -ForegroundColor Cyan

Set-Location $backendDir
& $venvPython -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
