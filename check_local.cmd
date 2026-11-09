@echo off
pushd "%~dp0"
if errorlevel 1 exit /b 1
py -3.14 repo-scripts\check_local.py
set "CHECK_EXIT=%errorlevel%"
popd
pause
exit /b %CHECK_EXIT%
