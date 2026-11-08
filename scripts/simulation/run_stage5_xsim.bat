@echo off
rem Consolidated Stage 3 XSim regression. Uses the Stage 3.5 verification suite.
setlocal EnableDelayedExpansion
cd /d "%~dp0\..\.." || exit /b 1
if not defined STAGE3_OUT set "STAGE3_OUT=sim_out_stage3_5_xsim"
if not defined STAGE3_REPORT set "STAGE3_REPORT=reports\stage3_5_coverage_xsim.txt"
set "OUT=%STAGE3_OUT%"
set "REPORT=%STAGE3_REPORT%"
if not exist reports mkdir reports
if exist "%REPORT%" del "%REPORT%"
for %%T in (xvlog xelab xsim py) do (
  where %%T >nul 2>nul
  if errorlevel 1 (echo ERROR: required tool %%T not found on PATH & exit /b 1)
)
py -3 --version >nul 2>nul
if errorlevel 1 (echo ERROR: Python 3 required; install it for the py launcher & exit /b 1)
for %%T in (xvlog xelab xsim) do echo TOOL %%T is available
if not exist "%OUT%" mkdir "%OUT%"
if exist "%OUT%\summary.txt" del "%OUT%\summary.txt"
for %%f in (units_s1.log units_md.log units_decoder_m.log units_pipe.log units_div_iter.log units_md_exec.log xvlog_s1.log xvlog_pipe.log xelab_units1.log xelab_units_md.log xelab_units_decoder_m.log xelab_core.log xelab_units_pipe.log xelab_div_iter.log xelab_md_exec.log xelab_pipe35.log) do if exist "%OUT%\%%f" del "%OUT%\%%f"

echo [1/6] Preparing 209 tests and independent ISS M operand side channels...
py -3 scripts\simulation\prepare_stage5.py "%OUT%"
if errorlevel 1 (echo ERROR: preparation failed or ISS mismatch & exit /b 1)

echo [2/6] Compiling and elaborating single-cycle/reference units...
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

echo [3/6] Compiling divider, wrapper, and pipeline units...
call xvlog -sv -f scripts\simulation\stage2_rtl.f verification\environment\tb_rv_pipe_units.sv verification\environment\tb_rv_div_iter.sv verification\environment\tb_rv_md_exec.sv verification\environment\tb_rv_pipe_stage4.sv --log "%OUT%\xvlog_pipe.log"
if errorlevel 1 (echo ERROR: iterative pipeline compile failed & exit /b 1)
call xelab -debug off tb_rv_pipe_units -s units_pipe_snap --log "%OUT%\xelab_units_pipe.log"
if errorlevel 1 (echo ERROR: pipeline unit elaboration failed & exit /b 1)
call xelab -debug off tb_rv_div_iter -s units_div_iter_snap --log "%OUT%\xelab_div_iter.log"
if errorlevel 1 (echo ERROR: divider unit elaboration failed & exit /b 1)
call xelab -debug off tb_rv_md_exec -s units_md_exec_snap --log "%OUT%\xelab_md_exec.log"
if errorlevel 1 (echo ERROR: wrapper unit elaboration failed & exit /b 1)
call xelab -debug off tb_rv_pipe_stage4 -s pipe35_snap --log "%OUT%\xelab_pipe35.log"
if errorlevel 1 (echo ERROR: Stage 3.5 pipeline elaboration failed & exit /b 1)

echo [4/6] Running unit and protocol suites...
call xsim units1_snap --runall --log "%OUT%\units_s1.log" >nul
if errorlevel 1 (echo ERROR: Stage 1 unit simulation failed & exit /b 1)
call xsim units_md_snap --runall --log "%OUT%\units_md.log" >nul
if errorlevel 1 (echo ERROR: M arithmetic simulation failed & exit /b 1)
call xsim units_decoder_m_snap --runall --log "%OUT%\units_decoder_m.log" >nul
if errorlevel 1 (echo ERROR: M decoder simulation failed & exit /b 1)
call xsim units_pipe_snap --runall --log "%OUT%\units_pipe.log" >nul
if errorlevel 1 (echo ERROR: pipeline unit simulation failed & exit /b 1)
call xsim units_div_iter_snap --runall --log "%OUT%\units_div_iter.log" >nul
if errorlevel 1 (echo ERROR: divider exhaustive simulation failed & exit /b 1)
call xsim units_md_exec_snap --runall --log "%OUT%\units_md_exec.log" >nul
if errorlevel 1 (echo ERROR: M wrapper simulation failed & exit /b 1)

echo [5/6] Running all tests on the golden core and coverage-instrumented pipeline...
set /a CASE=0
for /f "skip=1 tokens=1-4 delims=," %%a in (%OUT%\manifest_all.csv) do (
  set /a CASE+=1
  echo [!CASE!/209] %%a
  if exist "%OUT%\%%a.s1.trace" del "%OUT%\%%a.s1.trace"
  if exist "%OUT%\%%a.pipe.trace" del "%OUT%\%%a.pipe.trace"
  if exist "%OUT%\%%a.s1.log" del "%OUT%\%%a.s1.log"
  if exist "%OUT%\%%a.pipe.log" del "%OUT%\%%a.pipe.log"
  if exist "%OUT%\%%a.pipe.m.tsv" del "%OUT%\%%a.pipe.m.tsv"
  call xsim core_snap --runall --log "%OUT%\%%a.s1.log" ^
      --testplusarg "HEX=%%d" ^
      --testplusarg "TRACE=%OUT%/%%a.s1.trace" ^
      --testplusarg "EXPECT_CAUSE=%%b" ^
      --testplusarg "CHECK_GP=%%c" >nul
  if errorlevel 1 (echo ERROR: golden simulation failed for %%a & exit /b 1)
  call xsim pipe35_snap --runall --log "%OUT%\%%a.pipe.log" ^
      --testplusarg "HEX=%%d" ^
      --testplusarg "TRACE=%OUT%/%%a.pipe.trace" ^
      --testplusarg "MCOV=%OUT%/%%a.pipe.m.tsv" ^
      --testplusarg "EXPECT_CAUSE=%%b" ^
      --testplusarg "CHECK_GP=%%c" >nul
  if errorlevel 1 (echo ERROR: pipeline simulation failed for %%a & exit /b 1)
)

echo [6/6] Checking traces, timing, protocol and M coverage bins...
set "GATE=stage3_5"
if /I "%REPORT%"=="reports\stage3_7_regression_xsim.txt" set "GATE=stage3_7"
py -3 scripts\simulation\check_stage5_results.py "%OUT%" xsim "%REPORT%" "%GATE%" > "%OUT%\summary.txt"
set "RC=!errorlevel!"
findstr /B /C:"Stage" /C:"SUITE" /C:"TOTAL" /C:"Defined bins" /C:"M_COVERAGE_DICTIONARY" /C:"STAGE3_5_" /C:"STAGE3_7_" "%OUT%\summary.txt"
echo Full per-bin report: %REPORT%
endlocal & exit /b %RC%
