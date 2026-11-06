@echo off
rem ============================================================================
rem Stage 2 regression for AMD Vivado XSim (Windows): Stage 1 golden core +
rem 5-stage pipeline, 164 directed tests (101 Stage 1 + 63 pipeline).
rem Vivado 2026.1. Requires: xvlog/xelab/xsim in PATH, Python launcher "py -3".
rem Usage (from anywhere):  scripts\simulation\run_stage2_xsim.bat
rem Output dir: sim_out_xsim_s2   Report: reports\stage2_regression_xsim.txt
rem Same flag style as the validated run_stage1_xsim.bat (--runall, --testplusarg).
rem ============================================================================

setlocal EnableDelayedExpansion

cd /d "%~dp0\..\.." || exit /b 1

set "OUT=sim_out_xsim_s2"

if not exist "%OUT%" mkdir "%OUT%"
if not exist reports mkdir reports

echo.
echo ==========================================
echo STAGE 2 - XSIM REGRESSION
echo ==========================================

rem ---- [1/5] Generate tests, hex, ISS traces, expected stats ----

echo.
echo [1/5] Preparing tests, ISS traces and expected statistics...

py -3 scripts\simulation\prepare_stage2.py "%OUT%"

if errorlevel 1 (
    echo ERROR: preparation failed or ISS mismatch.
    exit /b 1
)

rem ---- [2/5] Compile Stage 1 (golden) testbenches ----

echo.
echo [2/5] Compiling Stage 1 golden core testbenches...

call xvlog -sv -f scripts\simulation\stage1_rtl.f verification\environment\tb_rv_units.sv verification\environment\tb_rv_core.sv --log "%OUT%\xvlog_s1.log"

if errorlevel 1 (
    echo ERROR: Stage 1 compilation failed.
    exit /b 1
)

call xelab -debug off tb_rv_units -s units1_snap --log "%OUT%\xelab_units1.log"

if errorlevel 1 (
    echo ERROR: Stage 1 unit elaboration failed.
    exit /b 1
)

call xelab -debug off tb_rv_core -s core_snap --log "%OUT%\xelab_core.log"

if errorlevel 1 (
    echo ERROR: Stage 1 core elaboration failed.
    exit /b 1
)

rem ---- [3/5] Compile Stage 2 (pipeline) testbenches ----

echo.
echo [3/5] Compiling Stage 2 pipeline testbenches...

call xvlog -sv -f scripts\simulation\stage2_rtl.f verification\environment\tb_rv_pipe_units.sv verification\environment\tb_rv_pipe.sv --log "%OUT%\xvlog_s2.log"

if errorlevel 1 (
    echo ERROR: Stage 2 compilation failed.
    exit /b 1
)

call xelab -debug off tb_rv_pipe_units -s units2_snap --log "%OUT%\xelab_units2.log"

if errorlevel 1 (
    echo ERROR: Stage 2 unit elaboration failed.
    exit /b 1
)

call xelab -debug off tb_rv_pipe -s pipe_snap --log "%OUT%\xelab_pipe.log"

if errorlevel 1 (
    echo ERROR: Stage 2 pipeline elaboration failed.
    exit /b 1
)

rem ---- [4/5] Unit tests ----

echo.
echo [4/5] Running unit tests...

call xsim units1_snap --runall --log "%OUT%\units_s1.log" >nul
call xsim units2_snap --runall --log "%OUT%\units_pipe.log" >nul

findstr /C:"UNIT_RESULT: PASS" "%OUT%\units_s1.log" >nul
if errorlevel 1 ( echo STAGE 1 UNIT TESTS FAIL ) else ( echo STAGE 1 UNIT TESTS PASS )

findstr /C:"PIPE_UNIT_RESULT: PASS" "%OUT%\units_pipe.log" >nul
if errorlevel 1 ( echo STAGE 2 UNIT TESTS FAIL ) else ( echo STAGE 2 UNIT TESTS PASS )

rem ---- [5/5] System tests: every test on golden core AND pipeline ----

echo.
echo [5/5] Running directed tests on both cores...

for /f "skip=1 tokens=1-4 delims=," %%a in (%OUT%\manifest_all.csv) do (

    echo Running %%a...

    call xsim core_snap --runall --log "%OUT%\%%a.s1.log" ^
        --testplusarg "HEX=%%d" ^
        --testplusarg "TRACE=%OUT%/%%a.s1.trace" ^
        --testplusarg "EXPECT_CAUSE=%%b" ^
        --testplusarg "CHECK_GP=%%c" >nul

    call xsim pipe_snap --runall --log "%OUT%\%%a.pipe.log" ^
        --testplusarg "HEX=%%d" ^
        --testplusarg "TRACE=%OUT%/%%a.pipe.trace" ^
        --testplusarg "EXPECT_CAUSE=%%b" ^
        --testplusarg "CHECK_GP=%%c" >nul
)

rem ---- Evaluate (RTL pipe vs golden core vs ISS, stall/redirect/cycle model, coverage) ----

echo.
echo ==========================================
echo STAGE 2 XSIM REGRESSION SUMMARY
echo ==========================================

py -3 scripts\simulation\check_stage2_results.py "%OUT%" xsim "reports\stage2_regression_xsim.txt" > "%OUT%\summary.txt"
set "RC=!errorlevel!"

findstr /B /C:"Stage" /C:"SUITE" /C:"TOTAL" /C:"Coverage events" /C:"STAGE2_" "%OUT%\summary.txt"

echo.
echo Full per-test report: reports\stage2_regression_xsim.txt

endlocal & exit /b %RC%
