@echo off
setlocal

pushd "%~dp0"
if exist "run.local.bat" call "run.local.bat"
if exist ".venv" rmdir /s /q ".venv"
if exist "report.html" del /f /q "report.html"
set UV_LINK_MODE=copy
if not defined UV_PROJECT_ENVIRONMENT set "UV_PROJECT_ENVIRONMENT=%~dp0.venv.win"

uv run pytest %*
set "EXIT_CODE=%ERRORLEVEL%"

if exist "report.html" start "" "report.html"

popd

exit /b %EXIT_CODE%
