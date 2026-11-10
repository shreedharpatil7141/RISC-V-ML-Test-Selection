@echo off
rem Continue Stage 9 recovery, reusing the three validated XSim selections.
setlocal EnableExtensions
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
if not exist "%PYTHON_EXE%" (
  echo Windows Python not found: "%PYTHON_EXE%"
  popd
  exit /b 2
)
if not exist "%VIVADO_SETTINGS%" (
  echo Vivado environment script not found: "%VIVADO_SETTINGS%"
  popd
  exit /b 2
)
if exist "reports\stage9_coverage\recovery_prepared.json" (
  echo Refusing to overwrite existing recovery preparation.
  popd
  exit /b 2
)
if not exist "reports\stage9_coverage" (
  mkdir "reports\stage9_coverage"
  if errorlevel 1 goto :failed
)
set "RUN_ID=%RANDOM%_%RANDOM%"
set "RC="
for %%L in (x5verify x6verify x6verify_refreshed x8verify v5 v6 v8 python prepcheck wsl_python) do if exist "reports\stage9_recovery_%RUN_ID%_%%L.log" (
  echo Refusing to overwrite existing run log.
  popd
  exit /b 2
)
set "PREP=sim_out_stage9_recovery_prepare_schemaaudit"
if not exist "%PREP%\stage7\stage8_preparation.txt" goto :failed
"%PYTHON_EXE%" -c "import sys;from pathlib import Path;sys.path.insert(0,'scripts/simulation');from prepare_stage9 import verify_stage8_preparation;verify_stage8_preparation(Path(r'%PREP%\stage7\m_manifest.csv'))" > "reports\stage9_recovery_%RUN_ID%_prepcheck.log" 2>&1
if errorlevel 1 goto :failed

call "%VIVADO_SETTINGS%"
if errorlevel 1 goto :failed
where xvlog >nul 2>&1
if errorlevel 1 goto :failed
where xelab >nul 2>&1
if errorlevel 1 goto :failed
where xsim >nul 2>&1
if errorlevel 1 goto :failed
"%PYTHON_EXE%" --version
if errorlevel 1 goto :failed
set "WSL_EXE=C:\Windows\System32\wsl.exe"
if not exist "%WSL_EXE%" goto :failed
set "CMD_WSL_PYTHON="C:\Windows\System32\wsl.exe" --distribution Ubuntu --exec python3 --version"
> "reports\stage9_recovery_%RUN_ID%_wsl_python.log" echo COMMAND=%CMD_WSL_PYTHON%
%CMD_WSL_PYTHON% >> "reports\stage9_recovery_%RUN_ID%_wsl_python.log" 2>&1
if errorlevel 1 (
  set "RC=%ERRORLEVEL%"
  >> "reports\stage9_recovery_%RUN_ID%_wsl_python.log" echo WSL_EXIT_CODE=%ERRORLEVEL%
  >> "reports\stage9_recovery_%RUN_ID%_wsl_python.log" echo FAILED_WSL_COMMAND=%CMD_WSL_PYTHON%
  echo FAILED_WSL_COMMAND=%CMD_WSL_PYTHON%
  goto :failed
)
"%PYTHON_EXE%" scripts\simulation\test_stage9_coverage.py > "reports\stage9_recovery_%RUN_ID%_python.log" 2>&1
if errorlevel 1 goto :failed

set "X5=reports\stage9_ca_xsim_20261110T120117Z.txt"
"%PYTHON_EXE%" scripts\simulation\verify_stage9_saved_ca.py --sim xsim --report "%X5%" > "reports\stage9_recovery_%RUN_ID%_x5verify.log" 2>&1
if errorlevel 1 goto :failed
findstr /c:"STAGE9_SAVED_CA_REUSE PASS simulator=xsim selected=39 source_hashes_checked=" "reports\stage9_recovery_%RUN_ID%_x5verify.log" >nul
if errorlevel 1 goto :failed

set "X6=reports\stage6_xsim_20261110T121507Z.txt"
"%PYTHON_EXE%" scripts\simulation\verify_stage9_saved_stage6.py --sim xsim --report "%X6%" --manifest sim_out_stage8_prepare_mem_footerfix\stage7\stage6_compat\z_manifest.csv > "reports\stage9_recovery_%RUN_ID%_x6verify.log" 2>&1
if errorlevel 1 goto :failed
findstr /c:"STAGE9_SAVED_STAGE6_REUSE PASS simulator=xsim selected=11 source_hashes_checked=" "reports\stage9_recovery_%RUN_ID%_x6verify.log" >nul
if errorlevel 1 goto :failed

set "PREP_WSL=%PREP:\=/%"
"%PYTHON_EXE%" scripts\simulation\verify_stage9_saved_stage6.py --sim xsim --report "%X6%" --manifest "%PREP%\stage7\stage6_compat\z_manifest.csv" > "reports\stage9_recovery_%RUN_ID%_x6verify_refreshed.log" 2>&1
if errorlevel 1 goto :failed
findstr /c:"STAGE9_SAVED_STAGE6_REUSE PASS simulator=xsim selected=11 source_hashes_checked=" "reports\stage9_recovery_%RUN_ID%_x6verify_refreshed.log" >nul
if errorlevel 1 goto :failed

set "X8=reports\stage8_xsim_selected_stage8_20261110T135003Z.txt"
"%PYTHON_EXE%" scripts\simulation\verify_stage9_saved_stage8.py --sim xsim --report "%X8%" --manifest "%PREP%\stage7\m_manifest.csv" > "reports\stage9_recovery_%RUN_ID%_x8verify.log" 2>&1
if errorlevel 1 goto :failed
findstr /c:"STAGE9_SAVED_STAGE8_REUSE PASS simulator=xsim selected=23 source_hashes_checked=" "reports\stage9_recovery_%RUN_ID%_x8verify.log" >nul
if errorlevel 1 goto :failed

set "CMD_V5="C:\Windows\System32\wsl.exe" --distribution Ubuntu --cd /mnt/c/RISC-V-ML-Test-Selection --exec python3 scripts/simulation/run_stage4_4.py --sim verilator --enable-a --stage9-ca-only"
> "reports\stage9_recovery_%RUN_ID%_v5.log" echo COMMAND=%CMD_V5%
%CMD_V5% >> "reports\stage9_recovery_%RUN_ID%_v5.log" 2>&1
if errorlevel 1 (
  set "RC=%ERRORLEVEL%"
  >> "reports\stage9_recovery_%RUN_ID%_v5.log" echo WSL_EXIT_CODE=%ERRORLEVEL%
  >> "reports\stage9_recovery_%RUN_ID%_v5.log" echo FAILED_WSL_COMMAND=%CMD_V5%
  echo FAILED_WSL_COMMAND=%CMD_V5%
  goto :failed
)
set "V5="
for /f "usebackq tokens=1,* delims==" %%A in (`findstr /b /c:"RUN_REPORT=" "reports\stage9_recovery_%RUN_ID%_v5.log"`) do set "V5=%%B"
if not defined V5 goto :failed
set "V5=C:\%V5:~7%"
set "V5=%V5:/=\%"
if not exist "%V5%" goto :failed
findstr /c:"STAGE9_STAGE5_CA_VERILATOR PASS c_cases=21 a_cases=18 selected_cases=39 full_trace_comparisons=78" "%V5%" >nul
if errorlevel 1 goto :failed

set "CMD_V6="C:\Windows\System32\wsl.exe" --distribution Ubuntu --cd /mnt/c/RISC-V-ML-Test-Selection --exec python3 scripts/simulation/run_stage6_enabled.py --sim verilator --prepared %PREP_WSL%/stage7/stage6_compat"
> "reports\stage9_recovery_%RUN_ID%_v6.log" echo COMMAND=%CMD_V6%
%CMD_V6% >> "reports\stage9_recovery_%RUN_ID%_v6.log" 2>&1
if errorlevel 1 (
  set "RC=%ERRORLEVEL%"
  >> "reports\stage9_recovery_%RUN_ID%_v6.log" echo WSL_EXIT_CODE=%ERRORLEVEL%
  >> "reports\stage9_recovery_%RUN_ID%_v6.log" echo FAILED_WSL_COMMAND=%CMD_V6%
  echo FAILED_WSL_COMMAND=%CMD_V6%
  goto :failed
)
set "V6="
for /f "usebackq tokens=1,* delims==" %%A in (`findstr /b /c:"RUN_REPORT=" "reports\stage9_recovery_%RUN_ID%_v6.log"`) do set "V6=%%B"
if not defined V6 goto :failed
set "V6=C:\%V6:~7%"
set "V6=%V6:/=\%"
if not exist "%V6%" goto :failed
findstr /c:"STAGE6_ENABLED_VERILATOR PASS cases=11 full_trace_comparisons=22 pipeline_golden=11 atomic_sidecars=22" "%V6%" >nul
if errorlevel 1 goto :failed

set "CMD_V8="C:\Windows\System32\wsl.exe" --distribution Ubuntu --cd /mnt/c/RISC-V-ML-Test-Selection --exec python3 scripts/simulation/run_stage7_enabled.py --sim verilator --prepared %PREP_WSL%/stage7 --stage8 --cases-only"
> "reports\stage9_recovery_%RUN_ID%_v8.log" echo COMMAND=%CMD_V8%
%CMD_V8% >> "reports\stage9_recovery_%RUN_ID%_v8.log" 2>&1
if errorlevel 1 (
  set "RC=%ERRORLEVEL%"
  >> "reports\stage9_recovery_%RUN_ID%_v8.log" echo WSL_EXIT_CODE=%ERRORLEVEL%
  >> "reports\stage9_recovery_%RUN_ID%_v8.log" echo FAILED_WSL_COMMAND=%CMD_V8%
  echo FAILED_WSL_COMMAND=%CMD_V8%
  goto :failed
)
set "V8="
for /f "usebackq tokens=1,* delims==" %%A in (`findstr /b /c:"RUN_REPORT=" "reports\stage9_recovery_%RUN_ID%_v8.log"`) do set "V8=%%B"
if not defined V8 goto :failed
set "V8=C:\%V8:~7%"
set "V8=%V8:/=\%"
if not exist "%V8%" goto :failed
findstr /c:"STAGE8_ENABLED_VERILATOR PASS" "%V8%" >nul
if errorlevel 1 goto :failed
findstr /c:"cases=23 traces=46 golden_pipeline=23" "%V8%" >nul
if errorlevel 1 goto :failed

"%PYTHON_EXE%" scripts\simulation\prepare_stage9_recovery.py ^
  --stage8-manifest "%PREP%\stage7\m_manifest.csv" ^
  --verilator-stage5-ca "%V5%" ^
  --verilator-legacy-report reports\stage9_gap_verilator_20261110T102959Z.txt ^
  --verilator-stage6 "%V6%" ^
  --verilator-stage8 "%V8%" ^
  --xsim-stage5-ca "%X5%" ^
  --xsim-legacy-report reports\stage9_gap_xsim_20261110T103419Z.txt ^
  --xsim-stage6 "%X6%" ^
  --xsim-stage8 "%X8%"
if errorlevel 1 goto :failed

echo Stage 9 recovery preparation succeeded.
echo Reused XSim reports: "%X5%" "%X6%" "%X8%"
echo New reports: "%V5%" "%V6%" "%V8%"
popd
exit /b 0

:failed
if not defined RC set "RC=%ERRORLEVEL%"
if "%RC%"=="0" set "RC=1"
echo Stage 9 continuation failed with exit code %RC%. See reports\stage9_recovery_%RUN_ID%_*.log
popd
exit /b %RC%
