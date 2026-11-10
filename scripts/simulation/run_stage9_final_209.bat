@echo off
rem Run only the two missing 209-case provenance recoveries, then replay/collect.
setlocal EnableExtensions EnableDelayedExpansion
pushd "%~dp0..\.." || exit /b 1
if not defined PYTHON_EXE (
  echo Set PYTHON_EXE to the full path of Windows Python 3.11 or newer.
  popd
  exit /b 2
)
if not defined VIVADO_SETTINGS (
  echo Set VIVADO_SETTINGS to the Vivado settings64.bat path.
  popd
  exit /b 2
)
if not exist "%PYTHON_EXE%" goto :failed
if not exist "%VIVADO_SETTINGS%" goto :failed
set "PREP=sim_out_stage9_recovery_prepare_schemaaudit"
set "FINAL_INDEX=reports\stage9_coverage\recovery_prepared_final.json"
if not exist "%PREP%\stage7\m_manifest.csv" goto :failed
if exist "%FINAL_INDEX%" (
  echo Refusing to overwrite %FINAL_INDEX%.
  popd
  exit /b 2
)
if not exist "reports\stage9_coverage" mkdir "reports\stage9_coverage"
if errorlevel 1 goto :failed
set "RUN_ID=%RANDOM%_%RANDOM%"
set "RC="
for %%L in (python prepcheck dispatch x5v x5x x6v x6x x8v x8x gapv_reuse gapv gapx prep collectv collectx) do if exist "reports\stage9_final_%RUN_ID%_%%L.log" goto :collision
set "WSL_EXE=C:\Windows\System32\wsl.exe"
if not exist "%WSL_EXE%" goto :failed

"%PYTHON_EXE%" scripts\simulation\test_stage9_coverage.py > "reports\stage9_final_%RUN_ID%_python.log" 2>&1
if errorlevel 1 goto :failed
"%PYTHON_EXE%" -c "import sys;from pathlib import Path;sys.path.insert(0,'scripts/simulation');from prepare_stage9 import verify_stage8_preparation;verify_stage8_preparation(Path(r'%PREP%\stage7\m_manifest.csv'))" > "reports\stage9_final_%RUN_ID%_prepcheck.log" 2>&1
if errorlevel 1 goto :failed

"%PYTHON_EXE%" scripts\simulation\verify_stage9_saved_ca.py --sim verilator --report reports\stage9_ca_verilator_20261110T140519Z.txt > "reports\stage9_final_%RUN_ID%_x5v.log" 2>&1
if errorlevel 1 goto :failed
"%PYTHON_EXE%" scripts\simulation\verify_stage9_saved_ca.py --sim xsim --report reports\stage9_ca_xsim_20261110T120117Z.txt > "reports\stage9_final_%RUN_ID%_x5x.log" 2>&1
if errorlevel 1 goto :failed
"%PYTHON_EXE%" scripts\simulation\verify_stage9_saved_stage6.py --sim verilator --report reports\stage6_verilator_20261110T140824Z.txt --manifest "%PREP%\stage7\stage6_compat\z_manifest.csv" > "reports\stage9_final_%RUN_ID%_x6v.log" 2>&1
if errorlevel 1 goto :failed
"%PYTHON_EXE%" scripts\simulation\verify_stage9_saved_stage6.py --sim xsim --report reports\stage6_xsim_20261110T121507Z.txt --manifest "%PREP%\stage7\stage6_compat\z_manifest.csv" > "reports\stage9_final_%RUN_ID%_x6x.log" 2>&1
if errorlevel 1 goto :failed
"%PYTHON_EXE%" scripts\simulation\verify_stage9_saved_stage8.py --sim verilator --report reports\stage8_verilator_selected_stage8_20261110T140921Z.txt --manifest "%PREP%\stage7\m_manifest.csv" > "reports\stage9_final_%RUN_ID%_x8v.log" 2>&1
if errorlevel 1 goto :failed
"%PYTHON_EXE%" scripts\simulation\verify_stage9_saved_stage8.py --sim xsim --report reports\stage8_xsim_selected_stage8_20261110T135003Z.txt --manifest "%PREP%\stage7\m_manifest.csv" > "reports\stage9_final_%RUN_ID%_x8x.log" 2>&1
if errorlevel 1 goto :failed

call "%VIVADO_SETTINGS%"
if errorlevel 1 goto :failed
where xvlog >nul 2>&1
if errorlevel 1 goto :failed
where xelab >nul 2>&1
if errorlevel 1 goto :failed
where xsim >nul 2>&1
if errorlevel 1 goto :failed
"%PYTHON_EXE%" scripts\simulation\verify_stage9_final_dispatch.py scripts\simulation\run_stage9_final_209.bat > "reports\stage9_final_%RUN_ID%_dispatch.log" 2>&1
if errorlevel 1 goto :failed

set "GAPV=reports\stage9_gap_verilator_20261110T170227Z.txt"
if exist "%GAPV%" goto :reuse_verilator
set "CMD_GAPV="C:\Windows\System32\wsl.exe" --distribution Ubuntu --cd /mnt/c/RISC-V-ML-Test-Selection --exec python3 scripts/simulation/run_stage4_4.py --sim verilator --stage9-legacy-gap"
> "reports\stage9_final_%RUN_ID%_gapv.log" echo COMMAND=%CMD_GAPV%
%CMD_GAPV% >> "reports\stage9_final_%RUN_ID%_gapv.log" 2>&1
if errorlevel 1 (
  set "RC=!ERRORLEVEL!"
  >> "reports\stage9_final_%RUN_ID%_gapv.log" echo WSL_EXIT_CODE=!ERRORLEVEL!
  >> "reports\stage9_final_%RUN_ID%_gapv.log" echo FAILED_WSL_COMMAND=%CMD_GAPV%
  goto :failed
)
set "GAPV="
for /f "usebackq tokens=1,* delims==" %%A in (`findstr /b /c:"RUN_REPORT=" "reports\stage9_final_%RUN_ID%_gapv.log"`) do set "GAPV=%%B"
if not defined GAPV goto :failed
set "GAPV=C:\%GAPV:~7%"
set "GAPV=%GAPV:/=\%"
if not exist "%GAPV%" goto :failed
findstr /c:"STAGE9_LEGACY_GAP_VERILATOR PASS legacy=209 full_trace_comparisons=418 dynamic_mcov=209" "%GAPV%" >nul
if errorlevel 1 goto :failed
goto :verilator_ready
:reuse_verilator
> "reports\stage9_final_%RUN_ID%_gapv_reuse.log" echo REUSED_VALIDATED_REPORT=%GAPV%
findstr /c:"STAGE9_LEGACY_GAP_VERILATOR PASS legacy=209 full_trace_comparisons=418 dynamic_mcov=209" "%GAPV%" >nul
if errorlevel 1 goto :failed
:verilator_ready

set "CMD_GAPX="%PYTHON_EXE%" scripts/simulation/run_stage4_4.py --sim xsim --stage9-legacy-gap"
> "reports\stage9_final_%RUN_ID%_gapx.log" echo COMMAND=%CMD_GAPX%
%CMD_GAPX% >> "reports\stage9_final_%RUN_ID%_gapx.log" 2>&1
if errorlevel 1 (
  set "RC=!ERRORLEVEL!"
  >> "reports\stage9_final_%RUN_ID%_gapx.log" echo WSL_EXIT_CODE=!ERRORLEVEL!
  >> "reports\stage9_final_%RUN_ID%_gapx.log" echo FAILED_WSL_COMMAND=%CMD_GAPX%
  goto :failed
)
set "GAPX="
for /f "usebackq tokens=1,* delims==" %%A in (`findstr /b /c:"RUN_REPORT=" "reports\stage9_final_%RUN_ID%_gapx.log"`) do set "GAPX=%%B"
if not defined GAPX goto :failed
if not exist "%GAPX%" goto :failed
findstr /c:"STAGE9_LEGACY_GAP_XSIM PASS legacy=209 full_trace_comparisons=418 dynamic_mcov=209" "%GAPX%" >nul
if errorlevel 1 goto :failed

"%PYTHON_EXE%" scripts\simulation\prepare_stage9_recovery.py ^
  --stage8-manifest "%PREP%\stage7\m_manifest.csv" ^
  --verilator-stage5-ca reports\stage9_ca_verilator_20261110T140519Z.txt ^
  --verilator-legacy-report "%GAPV%" ^
  --verilator-stage6 reports\stage6_verilator_20261110T140824Z.txt ^
  --verilator-stage8 reports\stage8_verilator_selected_stage8_20261110T140921Z.txt ^
  --xsim-stage5-ca reports\stage9_ca_xsim_20261110T120117Z.txt ^
  --xsim-legacy-report "%GAPX%" ^
  --xsim-stage6 reports\stage6_xsim_20261110T121507Z.txt ^
  --xsim-stage8 reports\stage8_xsim_selected_stage8_20261110T135003Z.txt ^
  --output "%FINAL_INDEX%" > "reports\stage9_final_%RUN_ID%_prep.log" 2>&1
if errorlevel 1 goto :failed

"%PYTHON_EXE%" scripts\simulation\stage9_coverage.py --sim verilator --prepared "%FINAL_INDEX%" > "reports\stage9_final_%RUN_ID%_collectv.log" 2>&1
if errorlevel 1 goto :failed
"%PYTHON_EXE%" scripts\simulation\stage9_coverage.py --sim xsim --prepared "%FINAL_INDEX%" > "reports\stage9_final_%RUN_ID%_collectx.log" 2>&1
if errorlevel 1 goto :failed
echo Final Stage 9 legacy recovery and both collections passed.
echo New legacy reports: "%GAPV%" "%GAPX%"
echo Prepared index: "%FINAL_INDEX%"
echo Per-command logs: reports\stage9_final_%RUN_ID%_*.log
popd
exit /b 0

:collision
echo Refusing to overwrite an existing log.
popd
exit /b 2
:failed
if not defined RC set "RC=%ERRORLEVEL%"
if "%RC%"=="0" set "RC=1"
echo Stage 9 final recovery stopped with exit code %RC%. See reports\stage9_final_%RUN_ID%_*.log
popd
exit /b %RC%
