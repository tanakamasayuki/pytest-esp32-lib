@echo off
setlocal

cd /d "%~dp0"

for /d /r %%D in (build __pycache__ .pytest_cache) do (
    if exist "%%D" rmdir /s /q "%%D"
)

if exist ".venv" rmdir /s /q ".venv"
if exist ".venv.linux" rmdir /s /q ".venv.linux"
if exist ".venv.win" rmdir /s /q ".venv.win"

if exist "report.html" del /f /q "report.html"
del /s /f /q "*.log" 2>nul

endlocal
