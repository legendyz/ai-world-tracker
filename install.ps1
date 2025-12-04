# AI World Tracker - Installation & Setup Script
# This script sets up a virtual environment and installs dependencies.

$ErrorActionPreference = "Stop"

function Write-Header {
    param($Text)
    Write-Host "" 
    Write-Host "=====================================================" -ForegroundColor Cyan
    Write-Host "    $Text" -ForegroundColor Cyan
    Write-Host "=====================================================" -ForegroundColor Cyan
    Write-Host "" 
}

function Write-Success {
    param($Text)
    Write-Host " $Text" -ForegroundColor Green
}

function Write-ErrorMsg {
    param($Text)
    Write-Host " $Text" -ForegroundColor Red
}

function Write-Info {
    param($Text)
    Write-Host "? $Text" -ForegroundColor Yellow
}

Write-Header "AI World Tracker - Setup Wizard"

# 1. Check Python
Write-Info "Checking Python installation..."
try {
    $pythonVersion = python --version 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Found Python: $pythonVersion"
    } else {
        throw "Python command returned error code."
    }
} catch {
    Write-ErrorMsg "Python not found or not in PATH."
    Write-Host "Please install Python 3.8+ from https://www.python.org/downloads/"
    exit 1
}

# 2. Virtual Environment Setup
Write-Info "Setting up Virtual Environment..."
$venvName = ".venv"

if (-not (Test-Path $venvName)) {
    Write-Host "Creating new virtual environment in '$venvName'..."
    python -m venv $venvName
    if ($LASTEXITCODE -ne 0) {
        Write-ErrorMsg "Failed to create virtual environment."
        exit 1
    }
    Write-Success "Virtual environment created."
} else {
    Write-Info "Virtual environment '$venvName' already exists."
}

# 3. Activate Virtual Environment (for this script session)
$venvScript = ".\$venvName\Scripts\Activate.ps1"
if (Test-Path $venvScript) {
    # We can't easily "activate" it for the parent shell, but we can use the venv's python/pip directly
    $venvPython = ".\$venvName\Scripts\python.exe"
    $venvPip = ".\$venvName\Scripts\pip.exe"
    Write-Success "Found Virtual Environment executables."
} else {
    Write-ErrorMsg "Could not find activation script at $venvScript"
    exit 1
}

# 4. Install Dependencies
Write-Info "Installing/Updating dependencies..."
try {
    # Upgrade pip first
    & $venvPython -m pip install --upgrade pip | Out-Null
    
    # Install requirements
    if (Test-Path "requirements.txt") {
        & $venvPip install -r requirements.txt
        if ($LASTEXITCODE -eq 0) {
            Write-Success "Dependencies installed successfully."
        } else {
            throw "Pip install failed."
        }
    } else {
        Write-ErrorMsg "requirements.txt not found!"
        exit 1
    }
} catch {
    Write-ErrorMsg "Failed to install dependencies. Check your internet connection."
    Write-Host $_
    exit 1
}

# 5. Create Project Directories
Write-Info "Verifying project structure..."
$dirs = @("visualizations", "web_output")
foreach ($dir in $dirs) {
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir | Out-Null
        Write-Success "Created directory: $dir"
    }
}

# 6. Completion
Write-Header "Setup Complete!"

Write-Host "To run the application:" -ForegroundColor Yellow
Write-Host "1. Activate the virtual environment:" -ForegroundColor White
Write-Host "   $venvScript" -ForegroundColor Gray
Write-Host "2. Run the main script:" -ForegroundColor White
Write-Host "   python TheWorldOfAI.py" -ForegroundColor Gray
Write-Host "" 

# Optional: Run now
$run = Read-Host "Do you want to run AI World Tracker now? (Y/N)"
if ($run -eq "Y" -or $run -eq "y") {
    Write-Host "" 
    Write-Host "Starting application..." -ForegroundColor Green
    & $venvPython TheWorldOfAI.py
}
