@echo off
setlocal
if "%~1"=="" (
  echo Usage: %~nx0 ^<prepared-stage8-directory^>
  exit /b 2
)
py -3 "%~dp0run_stage8_enabled.py" --sim xsim --prepared "%~1"
exit /b %ERRORLEVEL%
