@echo off
rem Stage 3.3 combinational M pipeline regression (no iterative-divider penalty).
setlocal EnableDelayedExpansion
cd /d "%~dp0\..\.." || exit /b 1
set "OUT=sim_out_stage3_3_xsim"
if not exist "%OUT%" mkdir "%OUT%"
if not exist reports mkdir reports
if exist "reports\stage3_3_regression_xsim.txt" del "reports\stage3_3_regression_xsim.txt"
if exist "%OUT%\summary.txt" del "%OUT%\summary.txt"

echo [1/5] Preparing RV32I, pipeline and pipeline-M inputs plus independent ISS traces...
py -3 scripts\simulation\prepare_stage3.py "%OUT%"
if errorlevel 1 (echo ERROR: preparation failed & exit /b 1)

echo [2/5] Compiling golden and pipeline testbenches...
call xvlog -sv -f scripts\simulation\stage1_rtl.f verification\environment\tb_rv_units.sv verification\environment\tb_rv_md.sv verification\environment\tb_rv_decoder_m.sv verification\environment\tb_rv_core.sv --log "%OUT%\xvlog_s1.log"
if errorlevel 1 (echo ERROR: Stage 1 compile failed & exit /b 1)
call xelab -debug off tb_rv_units -s units1_snap --log "%OUT%\xelab_units1.log"
if errorlevel 1 (echo ERROR: Stage 1 unit elaboration failed & exit /b 1)
call xelab -debug off tb_rv_md -s units_md_snap --log "%OUT%\xelab_units_md.log"
if errorlevel 1 (echo ERROR: M arithmetic elaboration failed & exit /b 1)
call xelab -debug off tb_rv_decoder_m -s units_decoder_m_snap --log "%OUT%\xelab_units_decoder_m.log"
if errorlevel 1 (echo ERROR: M decoder elaboration failed & exit /b 1)
call xelab -debug off tb_rv_core -s core_snap --log "%OUT%\xelab_core.log"
if errorlevel 1 (echo ERROR: golden core elaboration failed & exit /b 1)
call xvlog -sv -f scripts\simulation\stage2_rtl.f verification\environment\tb_rv_pipe_units.sv verification\environment\tb_rv_pipe.sv --log "%OUT%\xvlog_pipe.log"
if errorlevel 1 (echo ERROR: pipeline compile failed & exit /b 1)
call xelab -debug off tb_rv_pipe_units -s units_pipe_snap --log "%OUT%\xelab_units_pipe.log"
if errorlevel 1 (echo ERROR: pipeline unit elaboration failed & exit /b 1)
call xelab -debug off tb_rv_pipe -s pipe_snap --log "%OUT%\xelab_pipe.log"
if errorlevel 1 (echo ERROR: pipeline elaboration failed & exit /b 1)

echo [3/5] Running unit testbenches...
call xsim units1_snap --runall --log "%OUT%\units_s1.log" >nul
if errorlevel 1 (echo ERROR: Stage 1 unit simulation failed & exit /b 1)
call xsim units_md_snap --runall --log "%OUT%\units_md.log" >nul
if errorlevel 1 (echo ERROR: M arithmetic unit simulation failed & exit /b 1)
call xsim units_decoder_m_snap --runall --log "%OUT%\units_decoder_m.log" >nul
if errorlevel 1 (echo ERROR: M decoder unit simulation failed & exit /b 1)
call xsim units_pipe_snap --runall --log "%OUT%\units_pipe.log" >nul
if errorlevel 1 (echo ERROR: pipeline unit simulation failed & exit /b 1)

echo [4/5] Running all tests on golden core and pipeline...
for /f "skip=1 tokens=1-4 delims=," %%a in (%OUT%\manifest_all.csv) do (
  if exist "%OUT%\%%a.s1.trace" del "%OUT%\%%a.s1.trace"
  if exist "%OUT%\%%a.pipe.trace" del "%OUT%\%%a.pipe.trace"
  call xsim core_snap --runall --log "%OUT%\%%a.s1.log" ^
      --testplusarg "HEX=%%d" ^
      --testplusarg "TRACE=%OUT%/%%a.s1.trace" ^
      --testplusarg "EXPECT_CAUSE=%%b" ^
      --testplusarg "CHECK_GP=%%c" >nul
  if errorlevel 1 (echo ERROR: golden simulation failed for %%a & exit /b 1)
  call xsim pipe_snap --runall --log "%OUT%\%%a.pipe.log" ^
      --testplusarg "HEX=%%d" ^
      --testplusarg "TRACE=%OUT%/%%a.pipe.trace" ^
      --testplusarg "EXPECT_CAUSE=%%b" ^
      --testplusarg "CHECK_GP=%%c" >nul
  if errorlevel 1 (echo ERROR: pipeline simulation failed for %%a & exit /b 1)
)

echo [5/5] Comparing full pipeline traces with the golden core and ISS...
py -3 scripts\simulation\check_stage3_results.py "%OUT%" xsim "reports\stage3_3_regression_xsim.txt" > "%OUT%\summary.txt"
set "RC=!errorlevel!"
findstr /B /C:"Stage" /C:"SUITE" /C:"TOTAL" /C:"Coverage events" /C:"STAGE3_3_" "%OUT%\summary.txt"
echo Full report: reports\stage3_3_regression_xsim.txt
endlocal & exit /b %RC%
