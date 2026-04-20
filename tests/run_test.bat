@echo off
setlocal

cd /d "%~dp0"
if exist ".venv" rmdir /s /q ".venv"
set UV_LINK_MODE=copy
set "UV_PROJECT_ENVIRONMENT=.venv.win"

uv run pytest %*

pause
