@echo off
setlocal
if "%~1"=="" (
  echo Usage: %~nx0 ^<prepared-stage6-directory^>
  exit /b 2
)
findstr /C:"STAGE6_PREPARATION PASS stage5=248 stage6=11 total=259 images=259 references=259 errors=0" "%~1\stage6_preparation.txt" >nul
if errorlevel 1 (
  echo Prepared Stage 6 artifacts are missing or invalid: %~1
  exit /b 2
)
py -3 "%~dp0run_stage4_4.py" --sim xsim --enable-a
if errorlevel 1 exit /b %ERRORLEVEL%
py -3 "%~dp0run_stage6_enabled.py" --sim xsim --prepared "%~1"
exit /b %ERRORLEVEL%
