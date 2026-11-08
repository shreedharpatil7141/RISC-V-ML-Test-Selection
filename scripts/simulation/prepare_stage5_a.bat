@echo off
setlocal
if "%~1"=="" (
  echo Usage: %~nx0 ^<fresh-output-directory^>
  exit /b 2
)
py -3 "%~dp0prepare_stage4_4.py" "%~1" --enable-a
exit /b %ERRORLEVEL%
