$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)
py -3.12 -m venv .venv
if ($LASTEXITCODE -ne 0) { throw "Python 3.12 x64 is required" }
& .venv\Scripts\python.exe -m pip install -r requirements-build.txt
if ($LASTEXITCODE -ne 0) { throw "Dependency installation failed" }
& .venv\Scripts\python.exe tools/prepare_assets.py
if ($LASTEXITCODE -ne 0) { throw "Asset preparation failed" }
& .venv\Scripts\python.exe -m unittest discover -s tests -v
if ($LASTEXITCODE -ne 0) { throw "Tests failed" }
& .venv\Scripts\python.exe -m PyInstaller --clean --noconfirm GlanceGuard.spec
if ($LASTEXITCODE -ne 0) { throw "Packaging failed" }
Write-Host "Built dist/GlanceGuard/GlanceGuard.exe; keep the entire folder together."
