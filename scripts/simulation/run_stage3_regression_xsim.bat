@echo off
rem Canonical Stage 3.7 XSim entry point; reuses the validated Stage 3.5 suite.
setlocal EnableDelayedExpansion
cd /d "%~dp0\..\.." || exit /b 1
if not exist reports mkdir reports
if exist "reports\stage3_7_regression_xsim.txt" del "reports\stage3_7_regression_xsim.txt"
where powershell >nul 2>nul
if errorlevel 1 (echo ERROR: required tool powershell not found on PATH & exit /b 1)
for /f %%i in ('powershell -NoProfile -Command "Get-Date -Format yyyyMMddTHHmmssZ"') do set "RUN_ID=%%i"
if not defined RUN_ID (echo ERROR: could not create a unique output directory & exit /b 1)
set "STAGE3_OUT=sim_out_stage3_7_xsim_!RUN_ID!"
if exist "!STAGE3_OUT!" (echo ERROR: output directory already exists: !STAGE3_OUT! & exit /b 1)
set "STAGE3_REPORT=reports\stage3_7_regression_xsim.txt"
call "%~dp0run_stage5_xsim.bat"
set "RC=!errorlevel!"
endlocal & exit /b %RC%
