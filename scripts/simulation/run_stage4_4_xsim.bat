@echo off
setlocal
py -3 "%~dp0run_stage4_4.py" --sim xsim
exit /b %ERRORLEVEL%
