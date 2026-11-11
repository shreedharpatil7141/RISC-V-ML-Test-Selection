@echo off
setlocal
cd /d "%~dp0\..\.."
if exist "%USERPROFILE%\AppData\Local\Programs\Python\Python311\python.exe" (
  "%USERPROFILE%\AppData\Local\Programs\Python\Python311\python.exe" scripts\dataset\stage10_dataset.py validate
) else (
  py -3 scripts\dataset\stage10_dataset.py validate
)
if errorlevel 1 exit /b %errorlevel%
endlocal
