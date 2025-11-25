# Install all dependencies
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Installing Project Dependencies" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# Check conda environment
if ($env:CONDA_DEFAULT_ENV) {
    Write-Host "Current conda environment: $env:CONDA_DEFAULT_ENV" -ForegroundColor Green
} else {
    Write-Host "No conda environment detected" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "[1/4] Upgrading pip..." -ForegroundColor Yellow
python -m pip install --upgrade pip

Write-Host ""
Write-Host "[2/4] Installing basic dependencies..." -ForegroundColor Yellow
pip install streamlit plotly pandas numpy Pillow opencv-python-headless scipy

Write-Host ""
Write-Host "[3/4] Installing PyTorch..." -ForegroundColor Yellow
Write-Host "Installing CPU version (compatible with all systems)..." -ForegroundColor White
Write-Host "If you have NVIDIA GPU, you can install GPU version later:" -ForegroundColor Yellow
Write-Host "  pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118" -ForegroundColor White
pip install torch torchvision torchaudio

Write-Host ""
Write-Host "[4/4] Installing YOLO..." -ForegroundColor Yellow
pip install ultralytics

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Installation Complete!" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Verifying installation..." -ForegroundColor Yellow
python -c "import torch; print('PyTorch version:', torch.__version__); print('CUDA available:', torch.cuda.is_available())"
