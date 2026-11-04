@echo off
rem ============================================================================
rem Stage 1 regression for AMD Vivado XSim (Windows).
rem Vivado 2026.1
rem ============================================================================

setlocal EnableDelayedExpansion

cd /d "%~dp0\..\.." || exit /b 1

set "OUT=sim_out_xsim"
set "FAILS=0"
set "PASS=0"
set "FAIL=0"

if not exist "%OUT%" mkdir "%OUT%"

echo.
echo ==========================================
echo STAGE 1 - XSIM REGRESSION
echo ==========================================

rem ---- Generate ISS reference traces ----

echo.
echo [1/4] Generating ISS reference traces...

py -3 scripts\simulation\assemble_all.py "%OUT%\iss"

if errorlevel 1 (
    echo ERROR: ISS generation failed.
    exit /b 1
)

rem ---- Unit testbench ----

echo.
echo [2/4] Running unit tests...

call xvlog -sv -f scripts\simulation\stage1_rtl.f verification\environment\tb_rv_units.sv --log "%OUT%\xvlog_units.log"

if errorlevel 1 (
    echo ERROR: Unit test compilation failed.
    exit /b 1
)

call xelab -debug off tb_rv_units -s units_snap --log "%OUT%\xelab_units.log"

if errorlevel 1 (
    echo ERROR: Unit test elaboration failed.
    exit /b 1
)

call xsim units_snap --runall --log "%OUT%\xsim_units.log"

if errorlevel 1 (
    echo ERROR: Unit simulation failed to execute.
    set "FAILS=1"
) else (
    findstr /C:"UNIT_RESULT: PASS" "%OUT%\xsim_units.log" >nul

    if errorlevel 1 (
        echo UNIT TESTS FAIL
        set "FAILS=1"
    ) else (
        echo UNIT TESTS PASS
    )
)

rem ---- System testbench compilation ----

echo.
echo [3/4] Compiling system testbench...

call xvlog -sv -f scripts\simulation\stage1_rtl.f verification\environment\tb_rv_core.sv --log "%OUT%\xvlog_core.log"

if errorlevel 1 (
    echo ERROR: System testbench compilation failed.
    exit /b 1
)

call xelab -debug off tb_rv_core -s core_snap --log "%OUT%\xelab_core.log"

if errorlevel 1 (
    echo ERROR: System testbench elaboration failed.
    exit /b 1
)

rem ---- System regression ----

echo.
echo [4/4] Running directed RV32I tests...

for /f "skip=1 tokens=1-3 delims=," %%a in (tests\directed\rv32i\manifest.csv) do (

    echo Running %%a...

    call xsim core_snap --runall --log "%OUT%\%%a.log" ^
        --testplusarg "HEX=tests/directed/rv32i/%%a.hex" ^
        --testplusarg "TRACE=%OUT%/%%a.rtl.trace" ^
        --testplusarg "EXPECT_CAUSE=%%b" ^
        --testplusarg "CHECK_GP=%%c" >nul

    if errorlevel 1 (
        echo SIMULATION ERROR: %%a
        set /a FAIL+=1
    ) else (

        findstr /C:"TEST_RESULT: PASS" "%OUT%\%%a.log" >nul

        if errorlevel 1 (
            echo TEST FAIL: %%a
            set /a FAIL+=1
        ) else (

            if not exist "%OUT%\%%a.rtl.trace" (
                echo TRACE MISSING: %%a
                set /a FAIL+=1
            ) else if not exist "%OUT%\iss\%%a.iss.trace" (
                echo ISS TRACE MISSING: %%a
                set /a FAIL+=1
            ) else (

                fc "%OUT%\%%a.rtl.trace" "%OUT%\iss\%%a.iss.trace" >nul

                if errorlevel 1 (
                    echo TRACE-DIFF: %%a
                    set /a FAIL+=1
                ) else (
                    set /a PASS+=1
                )
            )
        )
    )
)

rem ---- Final summary ----

echo.
echo ==========================================
echo STAGE 1 XSIM REGRESSION SUMMARY
echo ==========================================

echo UNIT TEST FAILURE FLAG: !FAILS!
echo SYSTEM TESTS: !PASS! passed, !FAIL! failed

if "!FAIL!"=="0" if "!FAILS!"=="0" (
    echo.
    echo STAGE1_REGRESSION_XSIM PASS
    endlocal
    exit /b 0
) else (
    echo.
    echo STAGE1_REGRESSION_XSIM FAIL
    endlocal
    exit /b 1
)