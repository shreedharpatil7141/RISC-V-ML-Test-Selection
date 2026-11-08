#!/usr/bin/env python3
"""Stage 3.3 Verilator regression: Stage 1 golden core vs M-enabled pipeline vs ISS."""
import csv, os, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.normpath(os.path.join(HERE, '..', '..'))
SIM = os.environ.get('SIM_DIR', os.path.join(ROOT, 'sim_out_stage3_3'))
os.makedirs(SIM, exist_ok=True)
REPORT = os.path.join(ROOT, 'reports', 'stage3_3_regression_verilator.txt')
if os.path.exists(REPORT): os.remove(REPORT)
def run(args, log=None):
    r = subprocess.run(args, cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if log: open(log, 'w', newline='\n').write(r.stdout + ('\n--- STDERR ---\n' + r.stderr if r.stderr else ''))
    if r.returncode:
        print(r.stdout); print(r.stderr, file=sys.stderr)
        raise RuntimeError(f"command failed ({r.returncode}): {' '.join(args)}")
    return r.stdout
def build(listf, tb, top, exe):
    mdir = os.path.join(SIM, 'obj_' + exe); os.makedirs(mdir, exist_ok=True)
    run(['verilator','-sv','--binary','--timing','-Wno-fatal','-Wno-lint','-Wno-style','-f',os.path.join(HERE,listf),tb,'--top-module',top,'-Mdir',mdir,'-o',exe], os.path.join(SIM, exe + '.build.log'))
    return os.path.join(mdir, exe)
try:
    run([sys.executable, os.path.join(HERE,'prepare_stage3.py'), SIM], os.path.join(SIM,'prepare.log'))
    e = 'verification/environment/'
    u1 = build('stage1_rtl.f', e+'tb_rv_units.sv', 'tb_rv_units', 'Vunits1')
    um = build('stage1_rtl.f', e+'tb_rv_md.sv', 'tb_rv_md', 'Vunitmd')
    ud = build('stage1_rtl.f', e+'tb_rv_decoder_m.sv', 'tb_rv_decoder_m', 'Vunitdecoderm')
    up = build('stage2_rtl.f', e+'tb_rv_pipe_units.sv', 'tb_rv_pipe_units', 'Vunitsp')
    c1 = build('stage1_rtl.f', e+'tb_rv_core.sv', 'tb_rv_core', 'Vcore1')
    cp = build('stage2_rtl.f', e+'tb_rv_pipe.sv', 'tb_rv_pipe', 'Vpipe')
    for exe, fn in ((u1,'units_s1.log'),(um,'units_md.log'),(ud,'units_decoder_m.log'),(up,'units_pipe.log')):
        run([exe], os.path.join(SIM,fn))
    rows = list(csv.DictReader(open(os.path.join(SIM,'manifest_all.csv'), newline='')))
    for row in rows:
        n = row['name']
        for exe, tag in ((c1,'s1'),(cp,'pipe')):
            trace = os.path.join(SIM,n+'.'+tag+'.trace');
            if os.path.exists(trace): os.remove(trace)
            run([exe, f"+HEX={row['hexpath']}", f"+TRACE={trace.replace(os.sep,'/')}", f"+EXPECT_CAUSE={row['expect_cause']}", f"+CHECK_GP={row['check_gp']}"], os.path.join(SIM,n+'.'+tag+'.log'))
    rc = subprocess.run([sys.executable,os.path.join(HERE,'check_stage3_results.py'),SIM,'verilator',REPORT],cwd=ROOT)
    sys.exit(rc.returncode)
except Exception as exc:
    print(f"STAGE3_3_REGRESSION_VERILATOR FAIL: {exc}")
    sys.exit(1)
