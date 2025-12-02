# AI World Tracker - Quick Install and Run Script

Write-Host "=====================================================" -ForegroundColor Cyan
Write-Host "    AI World Tracker - Installation Wizard" -ForegroundColor Cyan
Write-Host "=====================================================" -ForegroundColor Cyan
Write-Host ""

# Check Python version
Write-Host "Checking Python environment..." -ForegroundColor Yellow
$pythonVersion = python --version 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ Python installed: $pythonVersion" -ForegroundColor Green
} else {
    Write-Host "✗ Python not found, please install Python 3.8+" -ForegroundColor Red
    exit 1
}

Write-Host ""

# Install dependencies
Write-Host "Installing project dependencies..." -ForegroundColor Yellow
Write-Host "This may take a few minutes..." -ForegroundColor Gray
Write-Host ""

pip install -r requirements.txt

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "✓ Dependencies installed successfully!" -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "✗ Dependency installation failed, please check network connection" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "=====================================================" -ForegroundColor Cyan
Write-Host "    Installation Complete!" -ForegroundColor Green
Write-Host "=====================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "How to run:" -ForegroundColor Yellow
Write-Host "  1. Auto mode:    python TheWorldOfAI.py --auto" -ForegroundColor White
Write-Host "  2. Interactive:  python TheWorldOfAI.py" -ForegroundColor White
Write-Host ""

# Ask to run
$run = Read-Host "Run application now? (Y/N)"
if ($run -eq "Y" -or $run -eq "y") {
    Write-Host ""
    Write-Host "Starting AI World Tracker..." -ForegroundColor Green
    Write-Host ""
    python TheWorldOfAI.py
} else {
    Write-Host ""
    Write-Host "You can run later: python TheWorldOfAI.py" -ForegroundColor Cyan
    Write-Host ""
}
