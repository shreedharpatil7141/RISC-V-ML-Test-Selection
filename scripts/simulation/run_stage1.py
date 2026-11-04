#!/usr/bin/env python3
"""Stage-1 regression: unit TB + all directed system tests on rv_core_single (Verilator).
For every test: (1) RTL halt cause / gp vs manifest, (2) full RTL retirement trace + final regs/memory
vs independent Python ISS trace. Build dir defaults to <root>/sim_out (override with env SIM_DIR).
NOTE: simulator here is Verilator, not XSim. See run_stage1_xsim.bat for the (untested) XSim flow."""
import csv, os, subprocess, sys, time
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, '..', '..'))
SIM = os.environ.get('SIM_DIR', os.path.join(ROOT, 'sim_out'))
TD = os.path.join(ROOT, 'tests', 'directed', 'rv32i')
sys.path.insert(0, HERE)
from rv32_asm import assemble, to_hex
import rv32i_iss
RTL = ['-f', os.path.join(HERE, 'stage1_rtl.f')]
def sh(cmd, **kw): return subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, **kw)

def build(top, tb, mdir, exe):
    r = sh(['verilator', '-sv', '--binary', '--timing', '-Wno-fatal', '-Wno-lint', '-Wno-style'] + RTL +
           [tb, '--top-module', top, '-Mdir', mdir, '-o', exe])
    if r.returncode: print(r.stdout, r.stderr); sys.exit("BUILD FAILED")

def main():
    os.makedirs(SIM, exist_ok=True)
    out = []
    def log(s): print(s); out.append(s)
    log(f"Stage 1 regression  {time.strftime('%Y-%m-%d %H:%M:%S')}  simulator=Verilator {sh(['verilator','--version']).stdout.strip()}")
    r = sh(['python3', os.path.join(HERE, 'rv32_asm_selftest.py')]); log(r.stdout.strip().splitlines()[-1])
    log("Lint (verilator --lint-only -Wall, RTL): " + ("clean of errors" if sh(['verilator','--lint-only','-Wall','-Wno-UNUSEDSIGNAL','-Wno-DECLFILENAME','-sv']+RTL+['--top-module','rv_core_single']).returncode == 0 else "WARNINGS/ERRORS"))

    build('tb_rv_units', 'verification/environment/tb_rv_units.sv', f'{SIM}/obj_units', 'Vunits')
    ur = sh([f'{SIM}/obj_units/Vunits']); log([l for l in ur.stdout.splitlines() if l.startswith('UNIT_RESULT')][0])
    unit_ok = 'UNIT_RESULT: PASS' in ur.stdout

    build('tb_rv_core', 'verification/environment/tb_rv_core.sv', f'{SIM}/obj_core', 'Vcore')
    rows = list(csv.DictReader(open(os.path.join(TD, 'manifest.csv'))))
    npass = nfail = 0
    log(f"{'test':34s} {'rtl':5s} {'trace':6s} cause instret")
    for row in rows:
        n = row['name']; hexf = os.path.join(TD, n + '.hex')
        mem = assemble(open(os.path.join(TD, n + '.s')).read()); open(hexf, 'w').write(to_hex(mem))
        words = [mem.get(4*i, 0) for i in range(max(mem)//4 + 1)]
        cause, x, tr, foot, oob, cnt = rv32i_iss.run(words)
        iss_txt = "\n".join(tr + foot) + "\n"
        tfile = f'{SIM}/{n}.rtl.trace'
        r = sh([f'{SIM}/obj_core/Vcore', f'+HEX={hexf}', f'+TRACE={tfile}', f"+EXPECT_CAUSE={row['expect_cause']}", f"+CHECK_GP={row['check_gp']}"])
        res = [l for l in r.stdout.splitlines() if l.startswith('TEST_RESULT')]
        rtl_ok = bool(res) and res[0].startswith('TEST_RESULT: PASS')
        trace_ok = os.path.exists(tfile) and open(tfile).read() == iss_txt
        ok = rtl_ok and trace_ok and cause == int(row['expect_cause'])
        npass += ok; nfail += not ok
        log(f"{n:34s} {'PASS' if rtl_ok else 'FAIL':5s} {'match' if trace_ok else 'DIFF':6s} {cause:5d} {cnt}")
        if not ok:
            log("   " + (res[0] if res else r.stdout[-300:]))
    log(f"SYSTEM TESTS: {npass} passed, {nfail} failed, {len(rows)} total")
    log(f"UNIT TESTS:   {'PASS' if unit_ok else 'FAIL'}")
    log("STAGE1_REGRESSION " + ("PASS" if nfail == 0 and unit_ok else "FAIL"))
    if not os.environ.get('NO_REPORT'):
        os.makedirs(os.path.join(ROOT, 'reports'), exist_ok=True)
        open(os.path.join(ROOT, 'reports', 'stage1_regression.txt'), 'w').write("\n".join(out) + "\n")
    sys.exit(0 if nfail == 0 and unit_ok else 1)
main()
