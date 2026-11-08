@echo off
setlocal
cd /d "%~dp0\..\.."
py -3 scripts\simulation\run_stage4_coverage.py --sim xsim
exit /b %ERRORLEVEL%
