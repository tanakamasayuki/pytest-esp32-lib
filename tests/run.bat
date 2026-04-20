@echo off
setlocal

cd /d "%~dp0"
if exist ".venv" rmdir /s /q ".venv"
if exist "report.html" del /f /q "report.html"
set UV_LINK_MODE=copy
set "UV_PROJECT_ENVIRONMENT=.venv.win"

uv run pytest %*
set "EXIT_CODE=%ERRORLEVEL%"

if exist "report.html" start "" "report.html"

exit /b %EXIT_CODE%
