@echo off
setlocal
cd /d "%~dp0\..\.."
set "MATLAB_EXE="
for /f "usebackq delims=" %%I in (`powershell -NoProfile -Command "$r=Get-ChildItem -LiteralPath (Join-Path $env:ProgramFiles 'MATLAB') -Directory -Filter 'R2025*' -ErrorAction SilentlyContinue | Where-Object { $_.Name -match '^R2025[a-z]?$' } | Sort-Object Name -Descending | Select-Object -First 1; if($r){$e=Join-Path $r.FullName 'bin\matlab.exe'; if(Test-Path -LiteralPath $e){Write-Output $e}}"`) do set "MATLAB_EXE=%%I"
if not defined MATLAB_EXE (
  echo MATLAB R2025 executable not found under %%ProgramFiles%%\MATLAB.
  exit /b 2
)
set "MATLAB_PREFDIR=%TEMP%\stage13-matlab-pref-R2025"
if not exist "%MATLAB_PREFDIR%" mkdir "%MATLAB_PREFDIR%"
"%MATLAB_EXE%" -batch "addpath('scripts/machine_learning'); stage13_run('validate')"
exit /b %ERRORLEVEL%
