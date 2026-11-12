@echo off
setlocal EnableExtensions
cd /d "%~dp0\..\.."
if errorlevel 1 exit /b 1

echo [1/5] Checking release lineage...
git rev-parse --verify stage14-complete >nul 2>&1
if errorlevel 1 (echo ERROR: stage14-complete tag is missing.& exit /b 2)
for %%T in (stage10-complete stage11-complete stage12-complete stage13-complete) do (
  git rev-parse --verify %%T >nul 2>&1
  if errorlevel 1 (echo ERROR: required release tag %%T is missing.& exit /b 2)
  git merge-base --is-ancestor %%T stage14-complete
  if errorlevel 1 (echo ERROR: release tag %%T is not an ancestor of stage14-complete.& exit /b 2)
)
git merge-base --is-ancestor stage14-complete HEAD
if errorlevel 1 (echo ERROR: HEAD does not descend from stage14-complete.& exit /b 2)
git lfs fsck --objects
if errorlevel 1 (echo ERROR: Git LFS object verification failed.& exit /b 1)

set "PYTHON_EXE="
if exist "%USERPROFILE%\AppData\Local\Programs\Python\Python311\python.exe" set "PYTHON_EXE=%USERPROFILE%\AppData\Local\Programs\Python\Python311\python.exe"
echo [2/5] Auditing current Stage 11-14 hashes and producer source...
if defined PYTHON_EXE (
  "%PYTHON_EXE%" scripts\machine_learning\audit_stage15_lineage.py
) else (
  py -3 scripts\machine_learning\audit_stage15_lineage.py
)
if errorlevel 1 (echo ERROR: Stage 11-14 hash/source audit failed.& exit /b 1)

echo [3/5] Validating frozen Stage 10 dataset...
set "STAGE15_STAGE10_TMP=%TEMP%\stage15-dataset-%RANDOM%-%RANDOM%"
set "STAGE10_DATASET_OUT=%STAGE15_STAGE10_TMP%\stage10_dataset"
mkdir "%STAGE15_STAGE10_TMP%"
if errorlevel 1 (echo ERROR: could not create isolated Stage 10 validation directory.& exit /b 1)
powershell -NoProfile -Command "Copy-Item -LiteralPath 'reports\stage10_dataset' -Destination $env:STAGE15_STAGE10_TMP -Recurse"
if errorlevel 1 (echo ERROR: could not copy frozen Stage 10 artifacts for isolated validation.& exit /b 1)
call scripts\dataset\validate_stage10_dataset.bat
set "STAGE15_DATASET_RC=%ERRORLEVEL%"
powershell -NoProfile -Command "$base=[IO.Path]::GetFullPath($env:TEMP).TrimEnd('\','/')+[IO.Path]::DirectorySeparatorChar; $target=[IO.Path]::GetFullPath($env:STAGE15_STAGE10_TMP); if(-not $target.StartsWith($base,[StringComparison]::OrdinalIgnoreCase)){Write-Error 'Refusing to remove a path outside TEMP'; exit 2}; Remove-Item -LiteralPath $target -Recurse -Force"
if errorlevel 1 (echo ERROR: could not clean isolated Stage 10 validation directory.& exit /b 1)
if not "%STAGE15_DATASET_RC%"=="0" (echo ERROR: Stage 10 dataset validation failed.& exit /b 1)
set "STAGE10_DATASET_OUT="

echo [4/5] Locating MATLAB R2025a...
set "MATLAB_EXE=%STAGE15_MATLAB_EXE%"
if not defined MATLAB_EXE if exist "%ProgramFiles%\MATLAB\R2025a\bin\matlab.exe" set "MATLAB_EXE=%ProgramFiles%\MATLAB\R2025a\bin\matlab.exe"
if not defined MATLAB_EXE if exist "%ProgramFiles(x86)%\MATLAB\R2025a\bin\matlab.exe" set "MATLAB_EXE=%ProgramFiles(x86)%\MATLAB\R2025a\bin\matlab.exe"
if not defined MATLAB_EXE (
  echo ERROR: MATLAB R2025a not found. Set STAGE15_MATLAB_EXE to its matlab.exe path.
  exit /b 2
)
set "MATLAB_PREFDIR=%TEMP%\stage15-matlab-pref"
if not exist "%MATLAB_PREFDIR%" mkdir "%MATLAB_PREFDIR%"
set "STAGE15_HIST_ROOT=%CD%\.stage15-historical-%RANDOM%-%RANDOM%"
if exist "%STAGE15_HIST_ROOT%" (echo ERROR: isolated checkout path already exists.& exit /b 2)
echo [5/5] Preparing exact producer sources and validating saved Stage 11-14 evidence...
git -c core.autocrlf=true -c core.longpaths=true worktree add --detach "%STAGE15_HIST_ROOT%" stage14-complete
if errorlevel 1 (echo ERROR: could not create historical validation checkout.& exit /b 1)
if defined PYTHON_EXE (
  "%PYTHON_EXE%" scripts\machine_learning\audit_stage15_lineage.py --prepare-historical "%STAGE15_HIST_ROOT%"
) else (
  py -3 scripts\machine_learning\audit_stage15_lineage.py --prepare-historical "%STAGE15_HIST_ROOT%"
)
if errorlevel 1 (set "STAGE15_RC=1"& goto :stage15_cleanup)
"%MATLAB_EXE%" -batch "cd(getenv('STAGE15_HIST_ROOT')); addpath('scripts/machine_learning'); stage11_run('validate'); stage12_run('validate'); stage13_run('validate'); stage14_run('validate_corrected')"
if errorlevel 1 (set "STAGE15_RC=1"& goto :stage15_cleanup)
set "STAGE15_RC=0"
:stage15_cleanup
git -c core.longpaths=true worktree remove --force "%STAGE15_HIST_ROOT%"
if errorlevel 1 (echo ERROR: could not remove isolated historical checkout.& exit /b 1)
if not "%STAGE15_RC%"=="0" (echo ERROR: one or more historical saved-evidence validators failed.& exit /b 1)
echo STAGE15_HISTORICAL_EVIDENCE_VALIDATION PASS
echo STAGE15_SAVED_EVIDENCE_VALIDATION PASS
endlocal
