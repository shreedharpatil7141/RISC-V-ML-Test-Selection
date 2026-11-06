#!/usr/bin/env python3
"""Stage-2 regression with Verilator: Stage 1 golden core + 5-stage pipeline, all directed tests.
Usage: python run_stage2.py     (env SIM_DIR = build/output dir, default <root>/sim_out_s2)
Produces the same directory layout as run_stage2_xsim.bat so check_stage2_results.py evaluates both."""
import csv, os, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, '..', '..'))
SIM = os.environ.get('SIM_DIR', os.path.join(ROOT, 'sim_out_s2'))
def sh(cmd, **kw): return subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, **kw)
def build(listf, tb, top, exe):
    mdir = os.path.join(SIM, 'obj_' + exe)
    r = sh(['verilator', '-sv', '--binary', '--timing', '-Wno-fatal', '-Wno-lint', '-Wno-style', '-f', os.path.join(HERE, listf), tb,
            '--top-module', top, '-Mdir', mdir, '-o', exe])
    if r.returncode: print(r.stdout, r.stderr); sys.exit(f"BUILD FAILED: {top}")
    return os.path.join(mdir, exe)
os.makedirs(SIM, exist_ok=True)
r = sh([sys.executable, os.path.join(HERE, 'prepare_stage2.py'), SIM]); print(r.stdout.strip())
if r.returncode: print(r.stderr); sys.exit("prepare failed")
E = 'verification/environment/'
u1 = build('stage1_rtl.f', E + 'tb_rv_units.sv', 'tb_rv_units', 'Vunits1')
up = build('stage2_rtl.f', E + 'tb_rv_pipe_units.sv', 'tb_rv_pipe_units', 'Vunitsp')
c1 = build('stage1_rtl.f', E + 'tb_rv_core.sv', 'tb_rv_core', 'Vcore1')
cp = build('stage2_rtl.f', E + 'tb_rv_pipe.sv', 'tb_rv_pipe', 'Vpipe')
open(os.path.join(SIM, 'units_s1.log'), 'w').write(sh([u1]).stdout)
open(os.path.join(SIM, 'units_pipe.log'), 'w').write(sh([up]).stdout)
for row in csv.DictReader(open(os.path.join(SIM, 'manifest_all.csv'))):
    n = row['name']
    for exe, tag in ((c1, 's1'), (cp, 'pipe')):
        a = [exe, f"+HEX={row['hexpath']}", f"+TRACE={SIM}/{n}.{tag}.trace", f"+EXPECT_CAUSE={row['expect_cause']}", f"+CHECK_GP={row['check_gp']}"]
        open(os.path.join(SIM, f'{n}.{tag}.log'), 'w').write(sh(a).stdout)
rep = os.path.join(ROOT, 'reports', 'stage2_regression_verilator.txt')
os.makedirs(os.path.dirname(rep), exist_ok=True)
r = subprocess.run([sys.executable, os.path.join(HERE, 'check_stage2_results.py'), SIM, 'verilator', rep], cwd=ROOT)
sys.exit(r.returncode)
