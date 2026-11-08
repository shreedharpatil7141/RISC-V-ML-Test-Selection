@echo off
rem Standalone Stage 4.2 RV32C decompressor unit sweep (AMD Vivado XSim).
setlocal EnableDelayedExpansion
cd /d "%~dp0\..\.." || exit /b 1

for %%T in (py xvlog xelab xsim powershell) do (
  where %%T >nul 2>nul
  if errorlevel 1 (echo ERROR: required tool %%T not found on PATH & exit /b 1)
)
py -3 --version >nul 2>nul
if errorlevel 1 (echo ERROR: Python 3 launcher unavailable & exit /b 1)

for /f %%i in ('powershell -NoProfile -Command "Get-Date -Format yyyyMMddTHHmmss"') do set "RUN_ID=%%i"
if not defined RUN_ID (echo ERROR: unable to create run identifier & exit /b 1)
set "OUT=sim_out_stage4_2_xsim_!RUN_ID!"
set "REPORT=reports\stage4_2_decompressor_xsim_!RUN_ID!.txt"
if exist "!OUT!" (echo ERROR: fresh output path already exists: !OUT! & exit /b 1)
if exist "!REPORT!" (echo ERROR: report path already exists: !REPORT! & exit /b 1)
mkdir "!OUT!" || exit /b 1
if not exist reports mkdir reports
set "OUT_ABS=%CD%\!OUT!"
set "REPORT_ABS=%CD%\!REPORT!"

echo [Stage 4.2 XSim] Generating independent vectors...
py -3 scripts\simulation\generate_stage4_2_vectors.py "!OUT_ABS!\vectors.txt" > "!OUT_ABS!\vectors.log" 2>&1
if errorlevel 1 (type "!OUT_ABS!\vectors.log" & echo ERROR: vector generation failed & exit /b 1)
findstr /C:"RV32C_VECTOR_GENERATION PASS halfwords=65536 oracle_mismatches=0" "!OUT_ABS!\vectors.log" >nul
if errorlevel 1 (type "!OUT_ABS!\vectors.log" & echo ERROR: vector generation marker missing & exit /b 1)
if not exist "!OUT_ABS!\vectors.txt" (echo ERROR: vectors file missing & exit /b 1)

echo [Stage 4.2 XSim] Compiling standalone decompressor testbench...
pushd "!OUT_ABS!" || exit /b 1
call xvlog -sv ..\rtl\decoder\rv32c_decompressor.sv ..\verification\environment\tb_rv32c_decompressor.sv --log xvlog.log
if errorlevel 1 (popd & echo ERROR: xvlog failed & exit /b 1)
call xelab -debug off tb_rv32c_decompressor -s rv32c_decompress_snap --log xelab.log
if errorlevel 1 (popd & echo ERROR: xelab failed & exit /b 1)

echo [Stage 4.2 XSim] Running 65,536 halfword patterns and hand anchors...
call xsim rv32c_decompress_snap --runall --log xsim.log --testplusarg "VECTORS=vectors.txt"
if errorlevel 1 (popd & echo ERROR: XSim execution failed & exit /b 1)
popd
py -3 scripts\simulation\check_stage4_2_sim_log.py "!OUT_ABS!\xsim.log" > "!OUT_ABS!\logcheck.log" 2>&1
if errorlevel 1 (type "!OUT_ABS!\xsim.log" & type "!OUT_ABS!\logcheck.log" & echo ERROR: XSim log validation failed & exit /b 1)
findstr /C:"RV32C_SIM_LOG_CHECK PASS terminal_markers=1 pass_markers=1 halfwords=65536 mismatches=0 anchors=16" "!OUT_ABS!\logcheck.log" >nul
if errorlevel 1 (type "!OUT_ABS!\logcheck.log" & echo ERROR: XSim log checker marker missing & exit /b 1)

(
  echo Simulator: AMD Vivado XSim
  echo Run: !RUN_ID!
  type "!OUT_ABS!\vectors.log"
  type "!OUT_ABS!\logcheck.log"
  findstr /C:"RV32C_DECOMPRESS_UNIT PASS" "!OUT_ABS!\xsim.log"
  echo STAGE4_2_DECOMPRESSOR_XSIM PASS halfwords=65536 anchors=16
) > "!REPORT_ABS!"
type "!REPORT_ABS!"
echo Output: !OUT!
echo Report: !REPORT!
endlocal & exit /b 0
