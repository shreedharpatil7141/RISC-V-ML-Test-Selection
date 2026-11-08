@echo off
setlocal
cd /d "%~dp0\..\.." || exit /b 1
for %%T in (py xvlog xelab xsim) do (where %%T >nul 2>nul || (echo ERROR: missing %%T & exit /b 1))
py -3 scripts\simulation\run_stage4_3.py --sim xsim
exit /b %errorlevel%
