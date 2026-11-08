#!/usr/bin/env python3
"""Stage 4.4 C-enabled five-stage pipeline and C-disabled compatibility regression."""
import argparse, csv, datetime, os, shutil, subprocess, sys, traceback
from pathlib import Path
HERE=Path(__file__).resolve().parent; ROOT=HERE.parents[1]
p=argparse.ArgumentParser(description=__doc__); p.add_argument('--sim',choices=('xsim','verilator'),required=True); a=p.parse_args(); SIM=a.sim
STAMP=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
OUT=ROOT/f'sim_out_stage4_4_{SIM}_{STAMP}'; REPORT=ROOT/'reports'/f'stage4_4_pipeline_{SIM}_{STAMP}.txt'
TOOLS={}; COMSPEC=None

def resolve(name): return TOOLS.get(name) or shutil.which(name) or name
def command_for(argv):
    exe=resolve(argv[0])
    if Path(exe).suffix.lower() in ('.bat','.cmd'):
        shell=COMSPEC or os.environ.get('COMSPEC') or shutil.which('cmd.exe')
        if not shell: raise RuntimeError('batch launcher requires COMSPEC/cmd.exe')
        pieces=[]; quote=False
        for arg in [exe,*argv[1:]]:
            if quote: pieces.append('"'+arg+'"'); quote=False
            else:
                pieces.append(subprocess.list2cmdline([arg])); quote=arg in ('--testplusarg','-generic_top')
        return '"'+shell+'" /d /s /c "'+' '.join(pieces)+'"',exe
    return [exe,*argv[1:]],exe
def run(argv,cwd=ROOT,log=None):
    actual,resolved=command_for(list(map(str,argv)))
    try: r=subprocess.run(actual,cwd=cwd,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    except OSError as exc:
        msg=f'LAUNCH_FAILURE executable={argv[0]!r} args={list(argv[1:])!r} resolved={resolved!r} cwd={str(Path(cwd).resolve())!r} error={exc!r}\nCOMMAND={actual!r}\n{traceback.format_exc()}'
        print(msg,file=sys.stderr,flush=True)
        if log: Path(log).write_text(msg,encoding='utf-8')
        raise RuntimeError(msg) from exc
    if log: Path(log).write_text(r.stdout,encoding='utf-8',newline='\n')
    if r.returncode:
        excerpt='\n'.join(line for line in r.stdout.splitlines() if line.strip())[:1800]
        print(f'FIRST_TOOL_ERROR exit={r.returncode} log={log or "<captured>"}\n{excerpt}',file=sys.stderr,flush=True)
        raise RuntimeError(f'command failed exit={r.returncode} executable={argv[0]!r} resolved={resolved!r} cwd={Path(cwd).resolve()} args={list(argv[1:])!r} log={log or "<captured>"}')
    return r.stdout
def compile_run(argv,cwd=ROOT,log=None):
    """Require a clean compiler log as well as a zero process exit."""
    output=run(argv,cwd=cwd,log=log)
    bad=[line for line in output.splitlines() if line.lstrip().startswith(('ERROR:', 'FATAL:'))]
    if bad:
        for line in bad[:20]: print(f'COMPILER_DIAGNOSTIC {line}',file=sys.stderr,flush=True)
        raise RuntimeError(f'compiler reported {len(bad)} error/fatal diagnostic(s); first: {bad[0]} (log={log})')
    return output
def plusarg(name,path): return '+'+name+'='+str(Path(path).resolve()).replace('\\','/')
def terminal(log,marker):
    s=Path(log).read_text(encoding='utf-8',errors='replace')
    if 'FAIL' in s or s.count(marker)!=1 or not Path(log).stat().st_size:
        first=next((line for line in s.splitlines() if 'FAIL' in line), '<no explicit FAIL record>')
        raise RuntimeError(f'invalid terminal record in {log}; required exactly once: {marker}; first_error={first}')
    return s
def compare_trace(actual,expected,label):
    if actual==expected: return
    a=actual.splitlines(); e=expected.splitlines(); n=min(len(a),len(e)); i=next((j for j in range(n) if a[j]!=e[j]),n)
    av=a[i] if i<len(a) else '<EOF>'; ev=e[i] if i<len(e) else '<EOF>'
    raise RuntimeError(f'{label}: trace mismatch at line {i+1}; actual={av!r}; expected={ev!r}; actual_lines={len(a)} expected_lines={len(e)}')
def instruction_stats(trace, image, compressed):
    """Derive bubbles/redirects from independent architectural records and the fetch contract."""
    rows=[]; stop=None; halt=None
    for line in trace.splitlines():
        fields=line.split()
        if not fields: continue
        if fields[0]=='I':
            rows.append((int(fields[1],16),int(fields[4],16),int(fields[3])))
        elif fields[0]=='STOP':
            stop=(int(fields[1],16),int(fields[2],16),int(fields[3]),int(fields[4]))
        elif fields[0]=='HALT': halt=(int(fields[1]),int(fields[2],16))
        elif fields[0] not in ('REG','MEM','TRACE_V2'):
            try: rows.append((int(fields[0],16),int(fields[1],16),4))
            except (ValueError,IndexError): pass
    cause,hpc=halt if halt else ((stop[3],stop[0]) if stop else (0,0))
    fault=None
    if stop:
        pc,raw,ilen,_=stop
        expanded=raw
        if compressed and ilen==2:
            # A faulting compressed instruction can only be illegal or C.EBREAK
            # in the current profile; neither can cause a load-use interlock.
            expanded=0
        fault=(pc,expanded,ilen)
    elif cause in (4,5,6):
        words=[int(x,16) for x in Path(image).read_text(encoding='ascii').split()]
        if hpc//4<len(words): fault=(hpc,words[hpc//4],4)
    seq=rows+([fault] if fault else [])
    stalls=redirects=ndiv=0
    USES1={0x67,0x63,0x03,0x23,0x13,0x33}; USES2={0x63,0x23,0x33}
    for i,(pc,insn,ilen) in enumerate(seq):
        op=insn&0x7f
        if i and (seq[i-1][1]&0x7f)==0x03:
            prev=seq[i-1][1]; rd=(prev>>7)&31
            u1=op in USES1; u2=op in USES2
            if rd and ((u1 and ((insn>>15)&31)==rd) or (u2 and ((insn>>20)&31)==rd)): stalls+=1
        if i<len(rows):
            if op in (0x6f,0x67): redirects+=1
            elif op==0x63:
                next_pc=seq[i+1][0] if i+1<len(seq) else hpc
                if next_pc != pc+ilen: redirects+=1
            if op==0x33 and (insn>>25)==1 and ((insn>>12)&7)>=4: ndiv+=1
    return len(rows),stalls,redirects,ndiv
def check_pipeline_log(log,trace,image,compressed):
    import re
    s=Path(log).read_text(encoding='utf-8',errors='replace')
    result=re.search(r'TEST_RESULT: PASS .*?instret=(\d+) cycles=(\d+) oob=(\d+)',s)
    stats=re.search(r'STATS stalls=(\d+) redirects=(\d+) cycles=(\d+) instret=(\d+) assert_fail=(\d+)',s)
    md=re.search(r'MD_STATS starts=(\d+) dones=(\d+) busy_cycles=(\d+) aborts_started=(\d+)',s)
    cov=re.search(r'COV ((?:\d+\s*){16})',s)
    if not result or not stats or not md or not cov: raise RuntimeError(f'{log}: missing result/stats/protocol/event records')
    instret,cycles,oob=map(int,result.groups()); stalls,redirects,scycles,sinstret,assert_fail=map(int,stats.groups())
    starts,dones,busy,aborts=map(int,md.groups())
    model_i,model_s,model_r,ndiv=instruction_stats(Path(trace).read_text(encoding='ascii'),image,compressed)
    expected_cycles=model_i+5+model_s+2*model_r+33*ndiv
    if (instret,cycles,oob)!=(model_i,expected_cycles,0) or (stalls,redirects,scycles,sinstret,assert_fail)!=(model_s,model_r,expected_cycles,model_i,0):
        raise RuntimeError(f'{log}: timing model mismatch actual instret/cycles/stalls/redirects={instret}/{cycles}/{stalls}/{redirects}; expected={model_i}/{expected_cycles}/{model_s}/{model_r}; divisions={ndiv}')
    if (starts,dones,busy,aborts)!=(ndiv,ndiv,33*ndiv,0):
        raise RuntimeError(f'{log}: divider protocol actual={starts}/{dones}/{busy}/{aborts} expected={ndiv}/{ndiv}/{33*ndiv}/0')
    return [int(x) for x in cov.group(1).split()], (stalls,redirects,expected_cycles,ndiv,starts,dones,busy)

def main():
    global COMSPEC
    required=['xvlog','xelab','xsim'] if SIM=='xsim' else ['verilator','make']
    missing=[]
    for t in required:
        q=shutil.which(t)
        if q is None or not Path(q).is_file(): missing.append(t)
        else: TOOLS[t]=str(Path(q).resolve())
    if SIM=='verilator' and not any(shutil.which(x) for x in ('g++','clang++','c++')): missing.append('C++ compiler')
    if not Path(sys.executable).is_file(): missing.append(f'active Python {sys.executable}')
    if missing: raise RuntimeError('tool preflight missing: '+', '.join(missing))
    if OUT.exists() or REPORT.exists(): raise RuntimeError(f'output/report is not fresh: {OUT} / {REPORT}')
    OUT.mkdir(parents=True); REPORT.parent.mkdir(parents=True,exist_ok=True)
    if SIM=='xsim' and any(Path(TOOLS[x]).suffix.lower() in ('.bat','.cmd') for x in required):
        COMSPEC=os.environ.get('COMSPEC') or shutil.which('cmd.exe')
        if not COMSPEC or not Path(COMSPEC).is_file(): raise RuntimeError('Vivado batch wrapper requires COMSPEC/cmd.exe')
    print(f'TOOL PREFLIGHT PASS sim={SIM} python={sys.executable} output={OUT}',flush=True)
    # All images and references are prepared and checked before compile or simulator launch.
    prep=run([sys.executable,HERE/'prepare_stage4_4.py',OUT],log=OUT/'software_preflight.log')
    if 'STAGE4_4_LEGACY_PREFLIGHT PASS tests=209 source_consistent=209 images=209 references=209' not in prep:
        raise RuntimeError('complete 209-case legacy software preflight marker missing')
    if 'STAGE4_4_SOFTWARE_PREFLIGHT PASS legacy=209 c_cases=20 total=229 images=229 references=229 errors=0' not in prep:
        raise RuntimeError('complete Stage 4.4 software preflight marker missing')
    legacy=list(csv.DictReader((OUT/'manifest_all.csv').open(newline='')))
    crows=list(csv.DictReader((OUT/'c_manifest.csv').open(newline='')))
    if len(legacy)!=209 or len(crows)!=20: raise RuntimeError(f'suite inventory mismatch legacy={len(legacy)} C={len(crows)}')
    names=[r['name'] for r in legacy+crows]
    if len(set(names))!=len(names): raise RuntimeError('legacy and C manifests contain duplicate output basenames')
    missing_artifacts=[]
    for row in legacy:
        for f in (ROOT/row['hexpath'], OUT/'iss'/(row['name']+'.iss.trace')):
            if not f.is_file(): missing_artifacts.append(f)
    for row in crows:
        for f in (OUT/'c_hex'/(row['name']+'.hex'),OUT/'c_iss'/(row['name']+'.trace')):
            if not f.is_file(): missing_artifacts.append(f)
    if not (OUT/'vectors.txt').is_file(): missing_artifacts.append(OUT/'vectors.txt')
    if missing_artifacts:
        for f in missing_artifacts: print(f'PREFLIGHT_MISSING {f}',file=sys.stderr,flush=True)
        raise RuntimeError(f'artifact preflight failed; missing={len(missing_artifacts)} paths listed above')
    print(f'STAGE4_4_ARTIFACT_PREFLIGHT PASS legacy=209 C={len(crows)} images=229 references=229',flush=True)
    rtl=ROOT/'scripts/simulation/stage4_4_rtl.f'
    tbdir=ROOT/'verification/environment'
    tops=[('arith','tb_rv_units','tb_rv_units.sv','UNIT_RESULT: PASS'),('md','tb_rv_md','tb_rv_md.sv','MD_UNIT_RESULT: PASS'),('decoder','tb_rv_decoder_m','tb_rv_decoder_m.sv','DECODER_M_RESULT: PASS checks=1024 errors=0'),('pipe','tb_rv_pipe_units','tb_rv_pipe_units.sv','PIPE_UNIT_RESULT: PASS'),('diviter','tb_rv_div_iter','tb_rv_div_iter.sv','DIV_ITER_RESULT: PASS'),('mdexec','tb_rv_md_exec','tb_rv_md_exec.sv','MD_EXEC_RESULT: PASS'),('decompress','tb_rv32c_decompressor','tb_rv32c_decompressor.sv','RV32C_DECOMPRESS_UNIT PASS halfwords=65536 mismatches=0 anchors=16')]
    if SIM=='xsim':
        xdir=OUT/'xsim'; xdir.mkdir()
        absfl=OUT/'stage4_4_rtl_abs.f'; absfl.write_text(''.join(str((ROOT/line.strip()).resolve())+'\n' for line in rtl.read_text().splitlines() if line.strip()),encoding='utf-8',newline='\n')
        compile_run(['xvlog','-sv','-f',absfl],cwd=xdir,log=OUT/'xvlog_rtl.log')
        for key,top,tb,marker in tops: compile_run(['xvlog','-sv',tbdir/tb],cwd=xdir,log=OUT/f'xvlog_{key}.log')
        compile_run(['xvlog','-sv',tbdir/'tb_rv_core.sv',tbdir/'tb_rv_pipe_stage4.sv'],cwd=xdir,log=OUT/'xvlog_system_tbs.log')
        for key,top,tb,marker in tops: run(['xelab','-debug','off',top,'-s',key],cwd=xdir,log=OUT/f'xelab_{key}.log')
        for name,top,generic in [('golden0','tb_rv_core',None),('golden1','tb_rv_core','ENABLE_C=1'),('pipe0','tb_rv_pipe_stage4',None),('pipe1','tb_rv_pipe_stage4','ENABLE_C=1')]:
            args=['xelab','-debug','off',top,'-s',name]
            if generic: args+=['-generic_top',generic]
            run(args,cwd=xdir,log=OUT/f'xelab_{name}.log')
        snaps={x:('xsim',x) for x in ('golden0','golden1','pipe0','pipe1')}
        units={key:('xsim',key) for key,_,_,_ in tops}
    else:
        units={}
        for key,top,tb,marker in tops:
            od=OUT/f'obj_{key}'; od.mkdir()
            compile_run(['verilator','-sv','--binary','--timing','-Wno-fatal','-Wno-lint','-Wno-style','-f',rtl,tbdir/tb,'--top-module',top,'-Mdir',od,'-o',key],log=OUT/f'build_{key}.log')
            units[key]=('verilator',od/key)
        snaps={}
        for name,top,gen in [('golden0','tb_rv_core',[]),('golden1','tb_rv_core',['-GENABLE_C=1']),('pipe0','tb_rv_pipe_stage4',[]),('pipe1','tb_rv_pipe_stage4',['-GENABLE_C=1'])]:
            od=OUT/f'obj_{name}'; od.mkdir()
            compile_run(['verilator','-sv','--binary','--timing','-Wno-fatal','-Wno-lint','-Wno-style','-f',rtl,tbdir/(top+'.sv'),'--top-module',top,*gen,'-Mdir',od,'-o',name],log=OUT/f'build_{name}.log')
            snaps[name]=('verilator',od/name)
    for key,top,tb,marker in tops:
        print(f'[unit {key}] running',flush=True); engine,exe=units[key]; log=OUT/f'unit_{key}.log'
        if key=='decompress': args=[exe,plusarg('VECTORS',OUT/'vectors.txt')] if engine=='verilator' else ['xsim',exe,'--runall','--log',log,'--testplusarg',plusarg('VECTORS',OUT/'vectors.txt')[1:]]
        else: args=[exe] if engine=='verilator' else ['xsim',exe,'--runall','--log',log]
        out=run(args,cwd=(OUT/'xsim') if engine=='xsim' else ROOT,log=log if engine=='verilator' else None)
        if engine=='xsim' and not log.is_file(): raise RuntimeError(f'unit {key}: XSim did not create log {log}')
        terminal(log,marker)
    compare_count=0; pipeline_golden_count=0; case_counts={'legacy':0,'rv32imc':0}; event_totals=[0]*16; protocol=[]
    modes=[('legacy',legacy,snaps['golden0'],snaps['pipe0'],OUT/'iss',False),('rv32imc',crows,snaps['golden1'],snaps['pipe1'],OUT/'c_iss',True)]
    for mode,rows,golden,pipe,refdir,cmode in modes:
        for index,row in enumerate(rows,1):
            name=row['name']; case_counts[mode]+=1; print(f'[{mode} {index}/{len(rows)}] {name}',flush=True)
            image=ROOT/row['hexpath'] if not cmode else OUT/'c_hex'/(name+'.hex')
            expected=(OUT/'iss'/(name+'.iss.trace')) if not cmode else OUT/'c_iss'/(name+'.trace')
            ref=expected.read_text(encoding='ascii')
            traces={}
            for kind,engine,exe in [('golden',*golden),('pipe',*pipe)]:
                trace=OUT/f'{name}.{kind}.trace'; log=OUT/f'{name}.{kind}.log'
                if trace.exists() or log.exists(): raise RuntimeError(f'fresh-run collision: {trace} / {log}')
                args=[exe,plusarg('HEX',image),plusarg('TRACE',trace),f'+EXPECT_CAUSE={row["expect_cause"]}',f'+CHECK_GP={row["check_gp"]}']
                if engine=='xsim': args=['xsim',exe,'--runall','--log',log,*sum((['--testplusarg',x[1:]] for x in args[1:]),[])]
                out=run(args,cwd=(OUT/'xsim') if engine=='xsim' else ROOT,log=log if engine=='verilator' else None)
                if engine=='xsim' and not log.is_file(): raise RuntimeError(f'{name}/{kind}: missing simulator log')
                record=terminal(log,'TEST_RESULT: PASS')
                if 'TIMEOUT' in record or not trace.is_file(): raise RuntimeError(f'{name}/{kind}: failed/timeout or missing trace')
                actual=trace.read_text(encoding='ascii')
                compare_trace(actual,ref,f'{name}/{kind} vs ISS')
                traces[kind]=actual
                compare_count+=1
            compare_trace(traces['pipe'],traces['golden'],f'{name}/pipeline vs golden RTL')
            pipeline_golden_count+=1
            event,counts=check_pipeline_log(OUT/f'{name}.pipe.log',OUT/f'{name}.pipe.trace',image,cmode)
            event_totals=[a+b for a,b in zip(event_totals,event)]; protocol.append(counts)
    if case_counts != {'legacy':209,'rv32imc':20}: raise RuntimeError(f'actual case totals unexpected {case_counts}')
    if compare_count!=458 or pipeline_golden_count!=229: raise RuntimeError(f'full trace inventory mismatch rtl_vs_iss={compare_count} pipeline_vs_golden={pipeline_golden_count}')
    if not all(event_totals): raise RuntimeError(f'pipeline event bins not all exercised: {event_totals}')
    with REPORT.open('w',encoding='utf-8',newline='\n') as f:
        f.write(f'Simulator: {SIM}\nlegacy_c_disabled=209\nrv32imc_existing=12\nrv32imc_pipeline_specific=8\nrtl_vs_iss_and_golden={compare_count}\nunit_suites={len(tops)}\nunit_decompress_halfwords=65536\ndivider_protocol_records={len(protocol)}\n')
        f.write(f'pipeline_vs_golden_full_traces={pipeline_golden_count}\n')
        f.write('pipeline_event_hits='+','.join(map(str,event_totals))+'\n')
        f.write(f'divider_protocol_checked_cases={len(protocol)} starts={sum(x[4] for x in protocol)} dones={sum(x[5] for x in protocol)} busy_cycles={sum(x[6] for x in protocol)} aborts=0\n')
        f.write(f'STAGE4_4_PIPELINE_{SIM.upper()} PASS legacy=209 rv32imc=20 full_trace_comparisons={compare_count} units={len(tops)}\n')
    terminal(REPORT,f'STAGE4_4_PIPELINE_{SIM.upper()} PASS legacy=209 rv32imc=20 full_trace_comparisons=458 units=7')
    print(REPORT.read_text(),flush=True)
if __name__=='__main__':
    try: main()
    except Exception as exc: print(f'STAGE4_4 FAIL: {exc}',file=sys.stderr); raise SystemExit(1)
