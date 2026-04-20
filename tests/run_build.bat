@echo off
setlocal

pushd "%~dp0"
call "%~dp0run.bat" --run-mode=build %*
popd
