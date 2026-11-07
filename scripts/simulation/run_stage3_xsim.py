#!/usr/bin/env python3
"""Stage 3.2 XSim gate: arithmetic/decode units and all M tests vs independent ISS."""
import csv, os, shutil, subprocess, sys, time
HERE=os.path.dirname(os.path.abspath(__file__)); ROOT=os.path.normpath(os.path.join(HERE,'..','..'))
sys.path.insert(0,HERE)
from rv32_asm import assemble,to_hex
import rv32i_iss
OUT=os.path.join(ROOT,'sim_out_stage3_xsim'); REPORT=os.path.join(ROOT,'reports','stage3_2_xsim.txt')
RTL=['-sv','-f','scripts/simulation/stage1_rtl.f']
log=[]; failures=0
TOOLS={}
def record(s): print(s); log.append(s)
def save_report():
    with open(REPORT,'w',encoding='utf-8',newline='\n') as f: f.write('\n'.join(log)+'\n')
def fresh(*paths):
    for path in paths:
        try: os.remove(path)
        except FileNotFoundError: pass
def command_for(tool,args):
    path=TOOLS[tool]
    if os.path.splitext(path)[1].lower() in ('.bat','.cmd'):
        comspec=os.environ.get('COMSPEC') or shutil.which('cmd.exe') or 'cmd.exe'
        # Mirror run_stage1_xsim.bat: quote each --testplusarg NAME=value payload
        # in the command text sent through cmd and Vivado's batch wrapper.
        rendered=[]; quote_next=False
        for arg in args:
            if quote_next:
                rendered.append('"'+arg+'"'); quote_next=False
            else:
                rendered.append(subprocess.list2cmdline([arg]))
                quote_next=(arg=='--testplusarg')
        command=subprocess.list2cmdline([path])+' '+' '.join(rendered)
        return f'"{comspec}" /d /s /c "{command}"'
    return [path]+args
def show_command(cmd):
    return cmd if isinstance(cmd,str) else subprocess.list2cmdline(cmd)
def run(tool,args,logfile,marker=None,stale=(),validation_log=None):
    global failures
    driver_log=os.path.join(OUT,logfile); fresh(driver_log,*stale)
    cmd=command_for(tool,args)
    try:
        with open(driver_log,'w',encoding='utf-8') as f:
            p=subprocess.run(cmd,cwd=ROOT,stdout=f,stderr=subprocess.STDOUT,text=True)
    except OSError as exc:
        failures+=1; record(f'FAIL launcher {tool}: {exc}'); return False
    content=open(driver_log,encoding='utf-8',errors='replace').read()
    if validation_log and os.path.isfile(validation_log):
        content+='\n'+open(validation_log,encoding='utf-8',errors='replace').read()
    has_error=any('ERROR:' in line.upper() for line in content.splitlines())
    if p.returncode or has_error or (marker and marker not in content):
        failures+=1; record(f"FAIL command={show_command(cmd)} exit={p.returncode} expected_marker={marker!r}")
        record(f'  driver log: {driver_log}')
        if validation_log: record(f'  simulator log: {validation_log}')
        first_error=next((line for line in content.splitlines() if 'ERROR' in line.upper() or 'EXPECTED A SWITCH' in line.upper()),None)
        if first_error: record('  first error: '+first_error)
        else:
            for line in content.splitlines()[:5]: record('  '+line)
        return False
    record(f"PASS command={show_command(cmd)}"+(f" marker={marker}" if marker else ''))
    return True
def unit(top,tb,snap,marker):
    xvlog_log=os.path.join(OUT,top+'_xvlog.log')
    if not run('xvlog',RTL+[tb,'--log',xvlog_log],top+'_compile_driver.log',stale=(xvlog_log,),validation_log=xvlog_log): return
    xelab_log=os.path.join(OUT,top+'_xelab.log')
    if not run('xelab',['-debug','off',top,'-s',snap,'--log',xelab_log],top+'_elab_driver.log',stale=(xelab_log,),validation_log=xelab_log): return
    xsim_log=os.path.join(OUT,top+'_xsim.log')
    run('xsim',[snap,'--runall','--log',xsim_log],top+'_sim_driver.log',marker,stale=(xsim_log,),validation_log=xsim_log)
def main():
    global failures
    os.makedirs(OUT,exist_ok=True); os.makedirs(os.path.dirname(REPORT),exist_ok=True)
    fresh(REPORT)
    record(f"Stage 3.2 XSim {time.strftime('%Y-%m-%d %H:%M:%S')} simulator=Vivado XSim")
    missing=[]
    for tool in ('xvlog','xelab','xsim'):
        found=shutil.which(tool)
        if not found: missing.append(tool)
        else: TOOLS[tool]=found
    if missing:
        failures+=1; record('FAIL missing required Vivado tools: '+', '.join(missing))
        record('Check that Vivado is initialized in this CMD and its bin directory is on PATH.')
        record('STAGE3_2_XSIM FAIL preflight failures=1')
        save_report(); return 1
    for tool in ('xvlog','xelab','xsim'): record(f'TOOL {tool}={TOOLS[tool]}')
    if any(os.path.splitext(TOOLS[t])[1].lower() in ('.bat','.cmd') for t in TOOLS):
        comspec=os.environ.get('COMSPEC') or shutil.which('cmd.exe')
        if not comspec:
            failures+=1; record('FAIL missing COMSPEC/cmd.exe required to invoke Vivado batch launchers')
            record('STAGE3_2_XSIM FAIL preflight failures=1'); save_report(); return 1
    unit('tb_rv_md','verification/environment/tb_rv_md.sv','md_stage3_snap','MD_UNIT_RESULT: PASS')
    unit('tb_rv_decoder_m','verification/environment/tb_rv_decoder_m.sv','decoder_m_stage3_snap','DECODER_M_RESULT: PASS')
    rows=list(csv.DictReader(open(os.path.join(ROOT,'tests/directed/m_extension/manifest.csv'),newline='')))
    if len(rows)!=22:
        failures+=1; record(f'FAIL expected 22 M manifest rows, found {len(rows)}')
    os.makedirs(os.path.join(OUT,'iss'),exist_ok=True)
    td=os.path.join(ROOT,'tests/directed/m_extension')
    for row in rows:
        n=row['name']; mem=assemble(open(os.path.join(td,n+'.s'),encoding='utf-8').read())
        open(os.path.join(td,n+'.hex'),'w',encoding='ascii',newline='\n').write(to_hex(mem))
        words=[mem.get(4*i,0) for i in range(max(mem)//4+1)]
        cause,x,tr,foot,oob,cnt=rv32i_iss.run(words)
        ref='\n'.join(tr+foot)+'\n'
        open(os.path.join(OUT,'iss',n+'.iss.trace'),'w',encoding='ascii',newline='\n').write(ref)
        if cause!=int(row['expect_cause']) or oob:
            failures+=1; record(f'FAIL ISS expectation {n} cause={cause} oob={oob}')
    if not failures:
        core_xvlog=os.path.join(OUT,'core_xvlog.log')
        core_xelab=os.path.join(OUT,'core_xelab.log')
        if run('xvlog',RTL+['verification/environment/tb_rv_core.sv','--log',core_xvlog],'core_compile_driver.log',stale=(core_xvlog,),validation_log=core_xvlog) and \
           run('xelab',['-debug','off','tb_rv_core','-s','core_stage3_snap','--log',core_xelab],'core_elab_driver.log',stale=(core_xelab,),validation_log=core_xelab):
            def run_case(row):
                global failures
                n=row['name']; trace=os.path.join(OUT,n+'.rtl.trace'); simlog=n+'_xsim.log'
                xsim_log=os.path.join(OUT,simlog)
                args=['core_stage3_snap','--runall','--log',xsim_log,
                     '--testplusarg',f"HEX=tests/directed/m_extension/{n}.hex",
                     '--testplusarg',f'TRACE={trace.replace(os.sep,"/")}',
                     '--testplusarg',f"EXPECT_CAUSE={row['expect_cause']}",
                     '--testplusarg',f"CHECK_GP={row['check_gp']}"]
                before=failures
                ok=run('xsim',args,n+'_driver.log','TEST_RESULT: PASS',stale=(trace,xsim_log),validation_log=xsim_log)
                issfile=os.path.join(OUT,'iss',n+'.iss.trace')
                if not ok or not os.path.isfile(trace) or not os.path.isfile(issfile):
                    if failures==before: failures+=1
                    record(f'FAIL trace missing for {n}'); return False
                if open(trace,encoding='ascii').read()!=open(issfile,encoding='ascii').read():
                    failures+=1; record(f'FAIL trace differs {n}')
                    return False
                record(f'PASS trace matches ISS {n}')
                return True
            # Gate the suite on a fresh, independently checked m_chain invocation.
            chain=next((row for row in rows if row['name']=='m_chain'),None)
            chain_ok=bool(chain) and run_case(chain)
            if not chain:
                failures+=1; record('FAIL m_chain missing from M manifest')
            if chain_ok:
                for row in rows:
                    if row['name']!='m_chain': run_case(row)
            else:
                record('SKIP remaining M tests because m_chain preflight did not pass')
    passed=sum(1 for s in log if s.startswith('PASS trace matches ISS '))
    record(f'STAGE3_2_XSIM {"PASS" if failures==0 and passed==22 else "FAIL"} arithmetic_decoder=see markers M={passed}/22 failures={failures}')
    save_report()
    return 0 if failures==0 and passed==22 else 1
if __name__=='__main__': sys.exit(main())
