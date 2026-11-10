@echo off
rem Rebuild Stage 9 preparation and recollect saved evidence only. No simulator launch.
setlocal EnableExtensions
pushd "%~dp0..\.." || exit /b 1
if not defined PYTHON_EXE (
  echo Set PYTHON_EXE to the full path of Windows Python 3.11 or newer.
  popd
  exit /b 2
)
if not exist "%PYTHON_EXE%" goto :failed
set "PREP=sim_out_stage9_recovery_prepare_schemaaudit\stage7\m_manifest.csv"
set "INDEX=reports\stage9_coverage\recovery_prepared_recollected.json"
if not exist "%PREP%" goto :failed
if exist "%INDEX%" (
  echo Refusing to overwrite %INDEX%.
  popd
  exit /b 2
)
if not exist "reports\stage9_coverage" mkdir "reports\stage9_coverage"
if errorlevel 1 goto :failed
"%PYTHON_EXE%" scripts\simulation\prepare_stage9_recovery.py ^
  --stage8-manifest "%PREP%" ^
  --verilator-stage5-ca reports\stage9_ca_verilator_20261110T140519Z.txt ^
  --verilator-legacy-report reports\stage9_gap_verilator_20261110T170227Z.txt ^
  --verilator-stage6 reports\stage6_verilator_20261110T140824Z.txt ^
  --verilator-stage8 reports\stage8_verilator_selected_stage8_20261110T140921Z.txt ^
  --xsim-stage5-ca reports\stage9_ca_xsim_20261110T120117Z.txt ^
  --xsim-legacy-report reports\stage9_gap_xsim_20261110T173739Z.txt ^
  --xsim-stage6 reports\stage6_xsim_20261110T121507Z.txt ^
  --xsim-stage8 reports\stage8_xsim_selected_stage8_20261110T135003Z.txt ^
  --output "%INDEX%"
if errorlevel 1 goto :failed
"%PYTHON_EXE%" scripts\simulation\stage9_coverage.py --sim verilator --prepared "%INDEX%"
if errorlevel 1 goto :failed
"%PYTHON_EXE%" scripts\simulation\stage9_coverage.py --sim xsim --prepared "%INDEX%"
if errorlevel 1 goto :failed
echo Preparation and saved-evidence collection completed: "%INDEX%"
popd
exit /b 0
:failed
set "RC=%ERRORLEVEL%"
if "%RC%"=="0" set "RC=1"
echo Stage 9 preparation/collection failed with exit code %RC%.
popd
exit /b %RC%
