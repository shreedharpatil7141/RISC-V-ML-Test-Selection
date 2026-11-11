@echo off
setlocal
cd /d "%~dp0\..\.."
set "MATLAB_EXE=C:\Program Files\MATLAB\R2025a\bin\matlab.exe"
if not exist "%MATLAB_EXE%" (
  echo MATLAB R2025a not found at "%MATLAB_EXE%".
  exit /b 2
)
set "APPDATA=%TEMP%\stage14-matlab-appdata"
set "MATLAB_PREFDIR=%APPDATA%\MathWorks\MATLAB\R2025a"
if not exist "%MATLAB_PREFDIR%" mkdir "%MATLAB_PREFDIR%"
"%MATLAB_EXE%" -batch "addpath('scripts/machine_learning'); stage14_run('validate_corrected')"
exit /b %ERRORLEVEL%
