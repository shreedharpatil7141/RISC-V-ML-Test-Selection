@echo off
setlocal
if "%~1"=="" (
  echo Usage: %~nx0 ^<prepared-stage7-directory^>
  exit /b 2
)
findstr /C:"STAGE7_PREPARATION READY stage6_compat=259 stage7_cases=13 images=13 references=13 errors=0" "%~1\stage7_preparation.txt" >nul
if errorlevel 1 (
  echo Prepared Stage 7 artifacts are missing or invalid: %~1
  exit /b 2
)
py -3 "%~dp0run_stage4_4.py" --sim xsim --enable-a
if errorlevel 1 exit /b %ERRORLEVEL%
py -3 "%~dp0run_stage6_enabled.py" --sim xsim --prepared "%~1\stage6_compat"
if errorlevel 1 exit /b %ERRORLEVEL%
py -3 "%~dp0run_stage7_enabled.py" --sim xsim --prepared "%~1"
exit /b %ERRORLEVEL%
