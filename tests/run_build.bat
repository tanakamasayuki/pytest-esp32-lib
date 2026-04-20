@echo off
setlocal

cd /d "%~dp0"
call "%~dp0run.bat" --run-mode=build %*
