@echo off
setlocal

cd /d "%~dp0"
set "UV_PROJECT_ENVIRONMENT=.venv.win"

uv run pytest %*

pause
