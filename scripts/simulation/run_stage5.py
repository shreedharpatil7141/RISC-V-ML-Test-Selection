#!/usr/bin/env python3
"""Consolidated Stage 3 Verilator regression (implemented by the Stage 3.5 suite)."""
import argparse,csv,datetime,os,shutil,subprocess,sys
HERE=os.path.dirname(os.path.abspath(__file__)); ROOT=os.path.normpath(os.path.join(HERE,'..','..'))
STAMP=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--stage3-regression',action='store_true',help='use isolated Stage 3.7 output and report paths')
ARGS=parser.parse_args()
SIM=os.environ.get('SIM_DIR') or os.path.join(ROOT,('sim_out_stage3_7_verilator_'+STAMP if ARGS.stage3_regression else 'sim_out_stage3_5'))
REPORT=os.path.join(ROOT,'reports',('stage3_7_regression_verilator.txt' if ARGS.stage3_regression else 'stage3_5_coverage_verilator.txt'))
def preflight():
    missing=[name for name in ('verilator','make') if shutil.which(name) is None]
    if not any(shutil.which(name) for name in ('g++','clang++','c++')):
        missing.append('C++ compiler (g++, clang++, or c++)')
    if missing: raise RuntimeError('missing required tools: '+', '.join(missing))
    print('TOOL PREFLIGHT PASS: '+', '.join(f'{name}={shutil.which(name)}' for name in ('verilator','make')))
    print('C++ compiler='+next(shutil.which(n) for n in ('g++','clang++','c++') if shutil.which(n)))
def run(args,log=None):
    r=subprocess.run(args,cwd=ROOT,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    if log: open(log,'w',newline='\n').write(r.stdout+('\n--- STDERR ---\n'+r.stderr if r.stderr else ''))
    if r.returncode:
        print(r.stdout); print(r.stderr,file=sys.stderr)
        raise RuntimeError(f"command failed ({r.returncode}): {' '.join(args)}")
    return r.stdout
def build(listf,tb,top,exe):
    mdir=os.path.join(SIM,'obj_'+exe); os.makedirs(mdir,exist_ok=True)
    run(['verilator','-sv','--binary','--timing','-Wno-fatal','-Wno-lint','-Wno-style','-f',os.path.join(HERE,listf),tb,'--top-module',top,'-Mdir',mdir,'-o',exe],os.path.join(SIM,exe+'.build.log'))
    return os.path.join(mdir,exe)
try:
    os.makedirs(os.path.dirname(REPORT),exist_ok=True)
    if os.path.exists(REPORT): os.remove(REPORT)
    preflight()
    if ARGS.stage3_regression and os.path.exists(SIM) and os.listdir(SIM):
        raise RuntimeError(f'output directory is not fresh: {SIM}; set SIM_DIR to a new path')
    os.makedirs(SIM,exist_ok=True)
    print(f'Fresh simulator output: {SIM}')
    run([sys.executable,os.path.join(HERE,'prepare_stage5.py'),SIM],os.path.join(SIM,'prepare.log'))
    e='verification/environment/'
    u1=build('stage1_rtl.f',e+'tb_rv_units.sv','tb_rv_units','Vunits1')
    um=build('stage1_rtl.f',e+'tb_rv_md.sv','tb_rv_md','Vunitmd')
    ud=build('stage1_rtl.f',e+'tb_rv_decoder_m.sv','tb_rv_decoder_m','Vunitdecoderm')
    up=build('stage2_rtl.f',e+'tb_rv_pipe_units.sv','tb_rv_pipe_units','Vunitsp')
    di=build('stage2_rtl.f',e+'tb_rv_div_iter.sv','tb_rv_div_iter','Vdiviter')
    md=build('stage2_rtl.f',e+'tb_rv_md_exec.sv','tb_rv_md_exec','Vmdexec')
    c1=build('stage1_rtl.f',e+'tb_rv_core.sv','tb_rv_core','Vcore1')
    cp=build('stage2_rtl.f',e+'tb_rv_pipe_stage4.sv','tb_rv_pipe_stage4','Vpipe35')
    for exe,fn in ((u1,'units_s1.log'),(um,'units_md.log'),(ud,'units_decoder_m.log'),
                   (up,'units_pipe.log'),(di,'units_div_iter.log'),(md,'units_md_exec.log')):
        print(f'UNIT {fn}',flush=True)
        run([exe],os.path.join(SIM,fn))
    rows=list(csv.DictReader(open(os.path.join(SIM,'manifest_all.csv'),newline='')))
    if len(rows)!=209: raise RuntimeError(f'expected 209 prepared tests, found {len(rows)}')
    for index,row in enumerate(rows,1):
        n=row['name']
        print(f'[{index}/209] {n}',flush=True)
        for exe,tag in ((c1,'s1'),(cp,'pipe')):
            trace=os.path.join(SIM,n+'.'+tag+'.trace')
            paths=[trace,os.path.join(SIM,n+'.'+tag+'.log')]
            if tag=='pipe': paths.append(os.path.join(SIM,n+'.pipe.m.tsv'))
            for path in paths:
                if os.path.exists(path): os.remove(path)
            args=[exe,f"+HEX={row['hexpath']}",f"+TRACE={trace.replace(os.sep,'/')}",
                  f"+EXPECT_CAUSE={row['expect_cause']}",f"+CHECK_GP={row['check_gp']}"]
            if tag=='pipe': args.append(f"+MCOV={os.path.join(SIM,n+'.pipe.m.tsv').replace(os.sep,'/')}")
            run(args,os.path.join(SIM,n+'.'+tag+'.log'))
    gate='stage3_7' if ARGS.stage3_regression else 'stage3_5'
    r=subprocess.run([sys.executable,os.path.join(HERE,'check_stage5_results.py'),SIM,'verilator',REPORT,gate],cwd=ROOT)
    sys.exit(r.returncode)
except Exception as exc:
    gate='STAGE3_7' if ARGS.stage3_regression else 'STAGE3_5'
    print(f'{gate}_REGRESSION_VERILATOR FAIL: {exc}'); sys.exit(1)
