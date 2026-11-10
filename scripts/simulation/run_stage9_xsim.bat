@echo off
setlocal
if "%~1"=="" (
  echo Usage: %~nx0 ^<prepared-stage9.json^>
  exit /b 2
)
py -3 "%~dp0test_stage9_coverage.py"
if errorlevel 1 exit /b %ERRORLEVEL%
py -3 "%~dp0stage9_coverage.py" --sim xsim --prepared "%~1"
exit /b %ERRORLEVEL%
