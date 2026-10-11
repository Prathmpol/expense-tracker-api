
$ErrorActionPreference = "Stop"

$python = Join-Path $PSScriptRoot "venv\Scripts\python.exe"

if (-not (Test-Path $python)) {
    Write-Host "Virtual environment not found." -ForegroundColor Red
    exit 1
}

$api = Start-Process -FilePath $python `
    -ArgumentList "-m uvicorn app.main:app --host 127.0.0.1 --port 8000" `
    -WorkingDirectory $PSScriptRoot `
    -PassThru `
    -WindowStyle Hidden

try {
    Start-Sleep -Seconds 2

    if ($api.HasExited) {
        throw "FastAPI failed to start. Check port 8000 and backend configuration."
    }

    Write-Host "FastAPI: http://127.0.0.1:8000"
    Write-Host "Streamlit: http://localhost:8501"
    Write-Host "Press Ctrl+C to stop Streamlit."

    & $python -m streamlit run (Join-Path $PSScriptRoot "streamlit_app\streamlit_app\app.py")
}
finally {
    if (-not $api.HasExited) {
        Stop-Process -Id $api.Id -Force -ErrorAction SilentlyContinue
    }
}
