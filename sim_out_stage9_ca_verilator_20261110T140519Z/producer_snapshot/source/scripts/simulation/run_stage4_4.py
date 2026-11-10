#!/usr/bin/env python3
"""Stage 4.4 C-enabled five-stage pipeline and C-disabled compatibility regression."""
import argparse, csv, datetime, hashlib, json, os, shutil, subprocess, sys, traceback
from pathlib import Path
HERE=Path(__file__).resolve().parent; ROOT=HERE.parents[1]
sys.path.insert(0,str(HERE))
from stage9_run_provenance import capture_snapshot, verify_snapshot
p=argparse.ArgumentParser(description=__doc__); p.add_argument('--sim',choices=('xsim','verilator'),required=True); p.add_argument('--only-c',action='store_true',help='run all C cases after software preflight; reserved for isolated C mutation checks'); p.add_argument('--enable-a',action='store_true'); p.add_argument('--a-only',action='store_true',help='run only the A cases after complete software/artifact preflight'); p.add_argument('--stage9-legacy-gap',action='store_true',help='run only the 209 C-disabled legacy pipeline cases with versioned dynamic MCOV'); p.add_argument('--stage9-ca-only',action='store_true',help='run only the 21 C and 18 A Stage 5 cases'); a=p.parse_args(); SIM=a.sim; ONLY_C=a.only_c; ENABLE_A=a.enable_a; A_ONLY=a.a_only; GAP_ONLY=a.stage9_legacy_gap; CA_ONLY=a.stage9_ca_only
STAMP=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
OUT=ROOT/(f'sim_out_stage9_gap_{SIM}_{STAMP}' if GAP_ONLY else (f'sim_out_stage9_ca_{SIM}_{STAMP}' if CA_ONLY else (f'sim_out_stage5_a_{SIM}_{STAMP}' if ENABLE_A else f'sim_out_stage4_4_{SIM}_{STAMP}'))); REPORT=ROOT/'reports'/(f'stage9_gap_{SIM}_{STAMP}.txt' if GAP_ONLY else (f'stage9_ca_{SIM}_{STAMP}.txt' if CA_ONLY else (f'stage5_a_pipeline_{SIM}_{STAMP}.txt' if ENABLE_A else f'stage4_4_pipeline_{SIM}_{STAMP}.txt')))
TOOLS={}; COMSPEC=None
EXPECTED_C_CASES=21
COMMAND_LOG=[]
STAGE5_INPUT_FIELDS=("name","expect_cause","check_gp","suite","hexpath")
STAGE5_SELECTION_FIELDS=("configuration",)+STAGE5_INPUT_FIELDS
LEGACY_INPUT_FIELDS=("name","expect_cause","check_gp","hexpath")
LEGACY_SELECTION_FIELDS=("configuration",)+LEGACY_INPUT_FIELDS


def selection_record(configuration,row):
    fields=STAGE5_INPUT_FIELDS if "suite" in row else LEGACY_INPUT_FIELDS
    if set(row)!=set(fields):
        raise ValueError(f"Stage 5 producer row schema mismatch for {row.get('name')}: expected={fields} actual={tuple(row)}")
    return {"configuration":configuration,**row}


def write_selection_manifest(path, selection, legacy=False):
    fields=LEGACY_SELECTION_FIELDS if legacy else STAGE5_SELECTION_FIELDS
    for line,row in enumerate(selection,2):
        if set(row)!=set(fields):
            raise ValueError(f"Stage 5 selection row {line} schema mismatch: expected={fields} actual={tuple(row)}")
    with Path(path).open('w',encoding='utf-8',newline='') as target:
        writer=csv.DictWriter(target,fieldnames=fields,extrasaction='raise',lineterminator='\n')
        writer.writeheader(); writer.writerows(selection)
    with Path(path).open(newline='',encoding='utf-8') as source:
        reader=csv.DictReader(source)
        if tuple(reader.fieldnames or ())!=fields: raise ValueError(f'Stage 5 selection round-trip header mismatch: {path}')
        actual=list(reader)
    if actual!=selection: raise ValueError(f'Stage 5 selection round-trip mismatch: {path}')

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
    COMMAND_LOG.append({'argv':[str(x) for x in argv],'cwd':str(Path(cwd).resolve()),'log':str(Path(log).resolve()) if log else ''})
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
    fatal_lines=[line for line in s.splitlines()
                 if 'FATAL_ERROR' in line.upper() or line.lstrip().upper().startswith('FATAL:')]
    if fatal_lines or 'FAIL' in s or s.count(marker)!=1 or not Path(log).stat().st_size:
        first=fatal_lines[0] if fatal_lines else next((line for line in s.splitlines() if 'FAIL' in line), '<no explicit FAIL record>')
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
    if A_ONLY and not ENABLE_A: raise RuntimeError('--a-only requires --enable-a')
    if GAP_ONLY and (ONLY_C or ENABLE_A or A_ONLY or CA_ONLY): raise RuntimeError('--stage9-legacy-gap cannot be combined with C/A-only options')
    if CA_ONLY and (not ENABLE_A or ONLY_C or A_ONLY or GAP_ONLY): raise RuntimeError('--stage9-ca-only requires --enable-a and cannot be combined with other selection modes')
    if OUT.exists() or REPORT.exists(): raise RuntimeError(f'output/report is not fresh: {OUT} / {REPORT}')
    OUT.mkdir(parents=True); REPORT.parent.mkdir(parents=True,exist_ok=True)
    commit=subprocess.run(['git','rev-parse','HEAD'],cwd=ROOT,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    provenance=[f'git_head={commit.stdout.strip() if commit.returncode==0 else "unavailable"}',f'simulator={SIM}',f'enable_a={ENABLE_A}',f'a_only={A_ONLY}']
    tracked_sources=[ROOT/'scripts/simulation/run_stage4_4.py',ROOT/'scripts/simulation/stage9_run_provenance.py',ROOT/'scripts/simulation/prepare_stage4_4.py',ROOT/'scripts/simulation/prepare_stage5.py',ROOT/'scripts/simulation/rv32_asm.py',ROOT/'scripts/simulation/rv32i_iss.py',ROOT/'scripts/simulation/rv32c_asm.py',ROOT/'scripts/simulation/rv32imc_iss.py',ROOT/'scripts/simulation/rv32a_model.py',ROOT/'scripts/simulation/generate_stage4_2_vectors.py',ROOT/'scripts/simulation/validate_stage5_a.py',ROOT/'scripts/simulation/stage4_4_rtl.f',ROOT/'verification/environment/tb_rv_core.sv',ROOT/'verification/environment/tb_rv_pipe_stage4.sv',ROOT/'verification/environment/tb_rv_a_unit.sv']
    tracked_sources += [ROOT/x.strip() for x in (ROOT/'scripts/simulation/stage4_4_rtl.f').read_text(encoding='utf-8').splitlines() if x.strip()]
    test_dirs=('rv32i','pipeline','pipeline_m','m_extension','pipeline_div','pipeline_div_coverage','rv32imc','rv32imc_pipeline','rv32ima_software','rv32imac_software','rv32imac_pipeline_a')
    tracked_sources += [p for name in test_dirs for d in [ROOT/'tests'/'directed'/name] if d.is_dir() for p in d.iterdir() if p.is_file() and p.suffix in ('.s','.csv')]
    if SIM=='xsim' and any(Path(TOOLS[x]).suffix.lower() in ('.bat','.cmd') for x in required):
        COMSPEC=os.environ.get('COMSPEC') or shutil.which('cmd.exe')
        if not COMSPEC or not Path(COMSPEC).is_file(): raise RuntimeError('Vivado batch wrapper requires COMSPEC/cmd.exe')
    print(f'TOOL PREFLIGHT PASS sim={SIM} python={sys.executable} output={OUT}',flush=True)
    # All images and references are prepared and checked before compile or simulator launch.
    prep_args=[sys.executable,HERE/'prepare_stage4_4.py',OUT]+(['--enable-a'] if ENABLE_A else [])
    prep=run(prep_args,log=OUT/'software_preflight.log')
    # Preparation requires a fresh empty output directory; write provenance
    # after it has generated and verified its artifacts.
    (OUT/'provenance.txt').write_text('\n'.join(provenance)+'\n',encoding='utf-8',newline='\n')
    if 'STAGE4_4_LEGACY_PREFLIGHT PASS tests=209 source_consistent=209 images=209 references=209' not in prep:
        raise RuntimeError('complete 209-case legacy software preflight marker missing')
    if f'STAGE4_4_SOFTWARE_PREFLIGHT PASS legacy=209 c_cases={EXPECTED_C_CASES} total={209+EXPECTED_C_CASES} images={209+EXPECTED_C_CASES} references={209+EXPECTED_C_CASES} errors=0' not in prep:
        raise RuntimeError('complete Stage 4.4 software preflight marker missing')
    legacy=list(csv.DictReader((OUT/'manifest_all.csv').open(newline='')))
    crows=list(csv.DictReader((OUT/'c_manifest.csv').open(newline='')))
    if len(legacy)!=209 or len(crows)!=EXPECTED_C_CASES: raise RuntimeError(f'suite inventory mismatch legacy={len(legacy)} C={len(crows)} expected_C={EXPECTED_C_CASES}')
    arows=list(csv.DictReader((OUT/'a_manifest.csv').open(newline=''))) if ENABLE_A else []
    if ENABLE_A and (len(arows)!=18 or 'STAGE5_A_ARTIFACT_PREFLIGHT PASS cases=18 images=18 references=18 atomic_sidecars=18' not in prep): raise RuntimeError(f'A artifact preflight mismatch cases={len(arows)}')
    names=[r['name'] for r in legacy+crows+arows]
    if len(set(names))!=len(names): raise RuntimeError('legacy and C manifests contain duplicate output basenames')
    early_selection=([('rv32im',r) for r in legacy] if GAP_ONLY else
                     ([('rv32imc',r) for r in crows]+[('rv32imac',r) for r in arows] if CA_ONLY else []))
    write_selection_manifest(OUT/'selection_manifest.csv',
                             [selection_record(mode,row) for mode,row in early_selection],legacy=GAP_ONLY)
    missing_artifacts=[]
    for row in legacy:
        for f in (ROOT/row['hexpath'], OUT/'iss'/(row['name']+'.iss.trace')):
            if not f.is_file(): missing_artifacts.append(f)
    for row in crows:
        for f in (OUT/'c_hex'/(row['name']+'.hex'),OUT/'c_iss'/(row['name']+'.trace')):
            if not f.is_file(): missing_artifacts.append(f)
    for row in arows:
        for f in (OUT/'a_hex'/(row['name']+'.hex'),OUT/'a_iss'/(row['name']+'.trace'),OUT/'a_iss'/(row['name']+'.a.tsv')):
            if not f.is_file(): missing_artifacts.append(f)
    if not (OUT/'vectors.txt').is_file(): missing_artifacts.append(OUT/'vectors.txt')
    if missing_artifacts:
        for f in missing_artifacts: print(f'PREFLIGHT_MISSING {f}',file=sys.stderr,flush=True)
        raise RuntimeError(f'artifact preflight failed; missing={len(missing_artifacts)} paths listed above')
    selected_inputs=[OUT/'manifest_all.csv',OUT/'c_manifest.csv',OUT/'selection_manifest.csv']+([OUT/'a_manifest.csv'] if ENABLE_A else [])+[OUT/'vectors.txt']
    if CA_ONLY:
        selected_inputs += [OUT/'c_hex'/(r['name']+'.hex') for r in crows]
        selected_inputs += [OUT/'c_iss'/(r['name']+'.trace') for r in crows]
        selected_inputs += [OUT/'a_hex'/(r['name']+'.hex') for r in arows]
        selected_inputs += [OUT/'a_iss'/(r['name']+'.trace') for r in arows]
        selected_inputs += [OUT/'a_iss'/(r['name']+'.a.tsv') for r in arows]
    elif GAP_ONLY:
        selected_inputs += [ROOT/r['hexpath'] for r in legacy]
        selected_inputs += [OUT/'iss'/(r['name']+'.iss.trace') for r in legacy]
        selected_inputs += [OUT/'iss'/(r['name']+'.iss.m.tsv') for r in legacy]
    snapshot_file=capture_snapshot(OUT/'producer_snapshot',tracked_sources,selected_inputs,[sys.executable,str(HERE/'run_stage4_4.py'),*sys.argv[1:]])
    verify_snapshot(snapshot_file)
    for source in sorted(set(tracked_sources),key=str):
        if source.is_file(): provenance.append(f'sha256 {source.relative_to(ROOT).as_posix()}={hashlib.sha256(source.read_bytes()).hexdigest()}')
    (OUT/'commands.json').write_text(json.dumps({'owner_command':[sys.executable,str(HERE/'run_stage4_4.py'),*sys.argv[1:]],'commands':COMMAND_LOG},indent=2)+'\n',encoding='utf-8',newline='\n')
    provenance += [f'producer_snapshot={snapshot_file.resolve()}',
                   f'producer_snapshot_sha256={hashlib.sha256(snapshot_file.read_bytes()).hexdigest()}']
    (OUT/'provenance.txt').write_text('\n'.join(provenance)+'\n',encoding='utf-8',newline='\n')
    total_configs=len(legacy)+len(crows)
    print(f'STAGE4_4_ARTIFACT_PREFLIGHT PASS legacy=209 C={len(crows)} images={total_configs} references={total_configs}',flush=True)
    rtl=ROOT/'scripts/simulation/stage4_4_rtl.f'
    tbdir=ROOT/'verification/environment'
    tops=[('arith','tb_rv_units','tb_rv_units.sv','UNIT_RESULT: PASS'),('md','tb_rv_md','tb_rv_md.sv','MD_UNIT_RESULT: PASS'),('decoder','tb_rv_decoder_m','tb_rv_decoder_m.sv','DECODER_M_RESULT: PASS checks=1024 errors=0'),('pipe','tb_rv_pipe_units','tb_rv_pipe_units.sv','PIPE_UNIT_RESULT: PASS'),('diviter','tb_rv_div_iter','tb_rv_div_iter.sv','DIV_ITER_RESULT: PASS'),('mdexec','tb_rv_md_exec','tb_rv_md_exec.sv','MD_EXEC_RESULT: PASS'),('decompress','tb_rv32c_decompressor','tb_rv32c_decompressor.sv','RV32C_DECOMPRESS_UNIT PASS halfwords=65536 mismatches=0 anchors=16')]
    if ENABLE_A: tops.append(('aunit','tb_rv_a_unit','tb_rv_a_unit.sv','RV32A_UNIT PASS checks=9 errors=0'))
    if SIM=='xsim':
        xdir=OUT/'xsim'; xdir.mkdir()
        absfl=OUT/'stage4_4_rtl_abs.f'; absfl.write_text(''.join(str((ROOT/line.strip()).resolve())+'\n' for line in rtl.read_text().splitlines() if line.strip()),encoding='utf-8',newline='\n')
        compile_run(['xvlog','-sv','-f',absfl],cwd=xdir,log=OUT/'xvlog_rtl.log')
        for key,top,tb,marker in tops: compile_run(['xvlog','-sv',tbdir/tb],cwd=xdir,log=OUT/f'xvlog_{key}.log')
        compile_run(['xvlog','-sv',tbdir/'tb_rv_core.sv',tbdir/'tb_rv_pipe_stage4.sv'],cwd=xdir,log=OUT/'xvlog_system_tbs.log')
        for key,top,tb,marker in tops: run(['xelab','-debug','off',top,'-s',key],cwd=xdir,log=OUT/f'xelab_{key}.log')
        snapshot_specs=[('golden0','tb_rv_core',None),('golden1','tb_rv_core','ENABLE_C=1'),('pipe0','tb_rv_pipe_stage4',None),('pipe1','tb_rv_pipe_stage4','ENABLE_C=1')]
        if ENABLE_A: snapshot_specs += [('golden_a','tb_rv_core','ENABLE_A=1'),('pipe_a','tb_rv_pipe_stage4','ENABLE_A=1')]
        for name,top,generic in snapshot_specs:
            args=['xelab','-debug','off',top,'-s',name]
            if generic: args+=['-generic_top',generic]
            run(args,cwd=xdir,log=OUT/f'xelab_{name}.log')
        # Keep every elaborated system snapshot under the exact snapshot key.
        snaps={name:('xsim',name) for name,_,_ in snapshot_specs}
        units={key:('xsim',key) for key,_,_,_ in tops}
    else:
        units={}
        for key,top,tb,marker in tops:
            od=OUT/f'obj_{key}'; od.mkdir()
            compile_run(['verilator','-sv','--binary','--timing','-Wno-fatal','-Wno-lint','-Wno-style','-f',rtl,tbdir/tb,'--top-module',top,'-Mdir',od,'-o',key],log=OUT/f'build_{key}.log')
            units[key]=('verilator',od/key)
        snaps={}
        snapshot_specs=[('golden0','tb_rv_core',[]),('golden1','tb_rv_core',['-GENABLE_C=1']),('pipe0','tb_rv_pipe_stage4',[]),('pipe1','tb_rv_pipe_stage4',['-GENABLE_C=1'])]
        if ENABLE_A: snapshot_specs += [('golden_a','tb_rv_core',['-GENABLE_A=1']),('pipe_a','tb_rv_pipe_stage4',['-GENABLE_A=1'])]
        for name,top,gen in snapshot_specs:
            od=OUT/f'obj_{name}'; od.mkdir()
            compile_run(['verilator','-sv','--binary','--timing','-Wno-fatal','-Wno-lint','-Wno-style','-f',rtl,tbdir/(top+'.sv'),'--top-module',top,*gen,'-Mdir',od,'-o',name],log=OUT/f'build_{name}.log')
            snaps[name]=('verilator',od/name)
    required_snapshots=set()
    if not ONLY_C and not A_ONLY and not CA_ONLY: required_snapshots.update(('golden0','pipe0'))
    if not A_ONLY: required_snapshots.update(('golden1','pipe1'))
    if ENABLE_A: required_snapshots.update(('golden_a','pipe_a'))
    missing_snapshots=sorted(required_snapshots-set(snaps))
    if missing_snapshots:
        raise RuntimeError(f'system snapshot mapping incomplete before unit/system execution: missing={missing_snapshots}; available={sorted(snaps)}')
    expected_engine='xsim' if SIM=='xsim' else 'verilator'
    malformed_snapshots={key:snaps[key] for key in sorted(required_snapshots)
                         if len(snaps[key])!=2 or snaps[key][0]!=expected_engine or
                         (SIM=='xsim' and snaps[key][1]!=key)}
    if malformed_snapshots:
        raise RuntimeError(f'system snapshot mapping malformed: {malformed_snapshots}')
    if ENABLE_A:
        specs={name:(top,generic) for name,top,generic in snapshot_specs}
        a_generic='ENABLE_A=1' if SIM=='xsim' else ['-GENABLE_A=1']
        expected_a_specs={'golden_a':('tb_rv_core',a_generic),
                          'pipe_a':('tb_rv_pipe_stage4',a_generic)}
        wrong_a_specs={key:(specs.get(key),value) for key,value in expected_a_specs.items()
                       if specs.get(key)!=value}
        if wrong_a_specs:
            raise RuntimeError(f'A/mixed C+A snapshot elaboration specs malformed: {wrong_a_specs}')
    if SIM=='verilator':
        missing_binaries=[(key,str(snaps[key][1])) for key in sorted(required_snapshots)
                          if not Path(snaps[key][1]).is_file()]
        if missing_binaries:
            raise RuntimeError(f'system snapshot binaries missing before unit/system execution: {missing_binaries}')
    for key,top,tb,marker in tops:
        print(f'[unit {key}] running',flush=True); engine,exe=units[key]; log=OUT/f'unit_{key}.log'
        if key=='decompress': args=[exe,plusarg('VECTORS',OUT/'vectors.txt')] if engine=='verilator' else ['xsim',exe,'--runall','--log',log,'--testplusarg',plusarg('VECTORS',OUT/'vectors.txt')[1:]]
        else: args=[exe] if engine=='verilator' else ['xsim',exe,'--runall','--log',log]
        out=run(args,cwd=(OUT/'xsim') if engine=='xsim' else ROOT,log=log if engine=='verilator' else None)
        if engine=='xsim' and not log.is_file(): raise RuntimeError(f'unit {key}: XSim did not create log {log}')
        terminal(log,marker)
        if key=='aunit' and 'RV32A_LEGALITY_UNIT PASS checks=2048 legal=84 errors=0' not in log.read_text(encoding='utf-8',errors='replace'):
            raise RuntimeError(f'A unit legality sweep marker missing or malformed: {log}')
    compare_count=0; pipeline_golden_count=0; case_counts={'legacy':0,'rv32imc':0, **({'rv32imac':0} if ENABLE_A else {})}; event_totals=[0]*16; protocol=[]
    atomic_ops_seen=set(); atomic_sc_status=set(); atomic_orders=set(); a_commits=0; a_writes=0
    modes=[] if ONLY_C or A_ONLY or CA_ONLY else [('legacy',legacy,snaps['golden0'],snaps['pipe0'],OUT/'iss',False,False)]
    if not A_ONLY and not GAP_ONLY: modes.append(('rv32imc',crows,snaps['golden1'],snaps['pipe1'],OUT/'c_iss',True,False))
    if ENABLE_A: modes.append(('rv32imac',arows,snaps['golden_a'],snaps['pipe_a'],OUT/'a_iss',True,True))
    selection=[selection_record('rv32im' if mode=='legacy' else mode,row) for mode,rows,*_ in modes for row in rows]
    if CA_ONLY:
        if len(selection)!=39 or sum(r['configuration']=='rv32imc' for r in selection)!=21 or sum(r['configuration']=='rv32imac' for r in selection)!=18:
            raise RuntimeError(f'Stage 9 C/A selection must be exactly 21 C + 18 A, got {len(selection)}')
    if CA_ONLY or GAP_ONLY:
        manifest_rows=list(csv.DictReader((OUT/'selection_manifest.csv').open(newline='')))
        if manifest_rows!=selection:
            raise RuntimeError('pre-execution selection manifest differs from complete producer rows')
    for mode,rows,golden,pipe,refdir,cmode,amode in modes:
        for index,row in enumerate(rows,1):
            name=row['name']; case_counts[mode]+=1; print(f'[{mode} {index}/{len(rows)}] {name}',flush=True)
            image=ROOT/row['hexpath'] if not cmode else (OUT/'a_hex'/(name+'.hex') if amode else OUT/'c_hex'/(name+'.hex'))
            expected=(OUT/'iss'/(name+'.iss.trace')) if not cmode else ((OUT/'a_iss'/(name+'.trace')) if amode else (OUT/'c_iss'/(name+'.trace')))
            ref=expected.read_text(encoding='ascii')
            atomic_rows=[]
            if amode:
                with (OUT/'a_iss'/(name+'.a.tsv')).open(newline='') as af:
                    atomic_rows=list(csv.DictReader(af,delimiter='\t'))
                atomic_ops_seen.update(x['op'] for x in atomic_rows)
                atomic_sc_status.update(x['sc_status'] for x in atomic_rows if x['op']=='sc.w')
                atomic_orders.update((x['aq'],x['rl']) for x in atomic_rows)
                a_commits += len(atomic_rows); a_writes += sum(x['new']!='-' for x in atomic_rows)
            traces={}
            for kind,engine,exe in [('golden',*golden),('pipe',*pipe)]:
                trace=OUT/f'{name}.{kind}.trace'; log=OUT/f'{name}.{kind}.log'
                if trace.exists() or log.exists(): raise RuntimeError(f'fresh-run collision: {trace} / {log}')
                args=[exe,plusarg('HEX',image),plusarg('TRACE',trace),f'+EXPECT_CAUSE={row["expect_cause"]}',f'+CHECK_GP={row["check_gp"]}']
                acov=OUT/f'{name}.{kind}.a.tsv' if amode else None
                if acov is not None:
                    if acov.exists(): raise RuntimeError(f'fresh-run collision: {acov}')
                    args.append(plusarg('ACOV',acov))
                ccov=OUT/f'{name}.{kind}.ccov'
                if (cmode or GAP_ONLY) and kind=='pipe':
                    if ccov.exists(): raise RuntimeError(f'fresh-run collision: {ccov}')
                    args.append(plusarg('MCOV',ccov))
                if engine=='xsim': args=['xsim',exe,'--runall','--log',log,*sum((['--testplusarg',x[1:]] for x in args[1:]),[])]
                out=run(args,cwd=(OUT/'xsim') if engine=='xsim' else ROOT,log=log if engine=='verilator' else None)
                if engine=='xsim' and not log.is_file(): raise RuntimeError(f'{name}/{kind}: missing simulator log')
                record=terminal(log,'TEST_RESULT: PASS')
                if 'TIMEOUT' in record or not trace.is_file(): raise RuntimeError(f'{name}/{kind}: failed/timeout or missing trace')
                if acov is not None:
                    if not acov.is_file(): raise RuntimeError(f'{name}/{kind}: missing RTL atomic evidence {acov}')
                    compare_trace(acov.read_text(encoding='ascii'),(OUT/'a_iss'/(name+'.a.tsv')).read_text(encoding='ascii'),f'{name}/{kind} atomic MEM evidence vs independent ISS')
                if (cmode or GAP_ONLY) and kind=='pipe' and not ccov.is_file(): raise RuntimeError(f'{name}/pipe: missing MCOV sidecar {ccov}')
                if amode and kind=='pipe':
                    covtext=ccov.read_text(encoding='ascii',errors='replace')
                    if 'A ATTEMPT ' not in covtext: raise RuntimeError(f'{name}: RTL A attempted-instruction evidence missing from {ccov}')
                    arows_cov=list(csv.DictReader((OUT/'a_iss'/(name+'.a.tsv')).open(newline=''),delimiter='\t'))
                    retired={(x.split()[2],x.split()[3]) for x in covtext.splitlines() if x.startswith('A RETIRE ')}
                    committed={(x['pc'],x['raw']) for x in arows_cov}
                    if retired!=committed: raise RuntimeError(f'{name}: RTL A retirement coverage differs from atomic commits; rtl={sorted(retired)} reference={sorted(committed)}')
                    if name in {'lr_misaligned','sc_misaligned','amo_misaligned','lr_access_fault','sc_access_fault','amo_access_fault'} and 'A FAULT ' not in covtext:
                        raise RuntimeError(f'{name}: expected faulting atomic missing from RTL A_FAULT coverage')
                    if name=='wrong_path_atomic' and ('A SQUASH_REDIRECT ' not in covtext or 'A RETIRE ' in covtext):
                        raise RuntimeError(f'{name}: wrong-path atomic was not independently recorded as redirect-squashed')
                    if name=='atomic_fault_squash' and not any(x in covtext for x in ('A SQUASH_FAULT ','A SQUASH_FAULT_IFID ')):
                        raise RuntimeError(f'{name}: younger atomic missing from fault-squash coverage')
                actual=trace.read_text(encoding='ascii')
                compare_trace(actual,ref,f'{name}/{kind} vs ISS')
                if amode:
                    import re
                    stat=re.search(r'ATOMIC_STATS commits=(\d+) writes=(\d+)',record)
                    expected_writes=sum(bool(row['new']!='-') for row in atomic_rows)
                    if not stat or tuple(map(int,stat.groups()))!=(len(atomic_rows),expected_writes):
                        raise RuntimeError(f'{name}/{kind}: atomic counters actual={stat.groups() if stat else None} expected_commits={len(atomic_rows)} expected_writes={expected_writes}')
                traces[kind]=actual
                compare_count+=1
            compare_trace(traces['pipe'],traces['golden'],f'{name}/pipeline vs golden RTL')
            pipeline_golden_count+=1
            event,counts=check_pipeline_log(OUT/f'{name}.pipe.log',OUT/f'{name}.pipe.trace',image,cmode)
            event_totals=[a+b for a,b in zip(event_totals,event)]; protocol.append(counts)
    expected_cases={'legacy':0 if ONLY_C or A_ONLY or CA_ONLY else 209,'rv32imc':0 if A_ONLY or GAP_ONLY else EXPECTED_C_CASES}
    if ENABLE_A: expected_cases['rv32imac']=18
    expected_comparisons=2*sum(expected_cases.values()); expected_pairs=sum(expected_cases.values())
    if case_counts != expected_cases: raise RuntimeError(f'suite inventory mismatch actual={case_counts} expected={expected_cases}')
    if compare_count!=expected_comparisons or pipeline_golden_count!=expected_pairs: raise RuntimeError(f'full trace inventory mismatch rtl_vs_iss={compare_count} pipeline_vs_golden={pipeline_golden_count}')
    if not ONLY_C and not A_ONLY and not CA_ONLY and not all(event_totals): raise RuntimeError(f'pipeline event bins not all exercised: {event_totals}')
    if ENABLE_A:
        required_ops={'lr.w','sc.w','amoswap.w','amoadd.w','amoxor.w','amoand.w','amoor.w','amomin.w','amomax.w','amominu.w','amomaxu.w'}
        if atomic_ops_seen != required_ops or atomic_sc_status != {'0','1'} or atomic_orders != {('0','0'),('0','1'),('1','0'),('1','1')}:
            raise RuntimeError(f'A architectural coverage incomplete ops={sorted(atomic_ops_seen)} SC={sorted(atomic_sc_status)} aqrl={sorted(atomic_orders)}')
    verify_snapshot(snapshot_file)
    with REPORT.open('w',encoding='utf-8',newline='\n') as f:
        f.write(f'Simulator: {SIM}\noutput_dir={OUT.resolve()}\nprovenance_file={(OUT/"provenance.txt").resolve()}\n'
                f'producer_snapshot={snapshot_file.resolve()}\nproducer_snapshot_sha256={hashlib.sha256(snapshot_file.read_bytes()).hexdigest()}\n'
                f'legacy_c_disabled={expected_cases["legacy"]}\nrv32imc_existing=12\nrv32imc_pipeline_specific=9\nrtl_vs_iss_and_golden={compare_count}\nunit_suites={len(tops)}\nunit_decompress_halfwords=65536\ndivider_protocol_records={len(protocol)}\n')
        if ENABLE_A: f.write(f'a_cases={expected_cases["rv32imac"]}\na_atomic_reference_events={a_commits}\na_atomic_reference_writes={a_writes}\na_operation_bins={len(atomic_ops_seen)}\na_sc_status_bins={len(atomic_sc_status)}\na_aqrl_bins={len(atomic_orders)}\n')
        f.write(f'pipeline_vs_golden_full_traces={pipeline_golden_count}\n')
        f.write('pipeline_event_hits='+','.join(map(str,event_totals))+'\n')
        f.write(f'divider_protocol_checked_cases={len(protocol)} starts={sum(x[4] for x in protocol)} dones={sum(x[5] for x in protocol)} busy_cycles={sum(x[6] for x in protocol)} aborts=0\n')
        if CA_ONLY: marker=f'STAGE9_STAGE5_CA_{SIM.upper()} PASS c_cases=21 a_cases=18 selected_cases=39 full_trace_comparisons={compare_count}'
        elif GAP_ONLY: marker=f'STAGE9_LEGACY_GAP_{SIM.upper()} PASS legacy=209 full_trace_comparisons={compare_count} dynamic_mcov=209'
        elif A_ONLY: marker=f'STAGE5_A_PIPELINE_{SIM.upper()}_A_ONLY PASS a_cases=18 full_trace_comparisons={compare_count} units={len(tops)}'
        elif ENABLE_A: marker=f'STAGE5_A_PIPELINE_{SIM.upper()} PASS legacy=209 c_cases={EXPECTED_C_CASES} a_cases=18 full_trace_comparisons={compare_count} units={len(tops)}'
        elif ONLY_C: marker=f'STAGE4_4_PIPELINE_{SIM.upper()}_C_ONLY PASS rv32imc={EXPECTED_C_CASES} full_trace_comparisons={compare_count} units={len(tops)}'
        else: marker=f'STAGE4_4_PIPELINE_{SIM.upper()} PASS legacy=209 rv32imc={EXPECTED_C_CASES} full_trace_comparisons={compare_count} units={len(tops)}'
        f.write(marker+'\n')
    marker=(f'STAGE9_STAGE5_CA_{SIM.upper()} PASS c_cases=21 a_cases=18 selected_cases=39 full_trace_comparisons={expected_comparisons}' if CA_ONLY else (f'STAGE9_LEGACY_GAP_{SIM.upper()} PASS legacy=209 full_trace_comparisons={expected_comparisons} dynamic_mcov=209' if GAP_ONLY else (f'STAGE5_A_PIPELINE_{SIM.upper()}_A_ONLY PASS a_cases=18 full_trace_comparisons={expected_comparisons} units={len(tops)}' if A_ONLY else (f'STAGE5_A_PIPELINE_{SIM.upper()} PASS legacy=209 c_cases={EXPECTED_C_CASES} a_cases=18 full_trace_comparisons={expected_comparisons} units={len(tops)}' if ENABLE_A else (f'STAGE4_4_PIPELINE_{SIM.upper()}_C_ONLY PASS rv32imc={EXPECTED_C_CASES} full_trace_comparisons={expected_comparisons} units={len(tops)}' if ONLY_C else f'STAGE4_4_PIPELINE_{SIM.upper()} PASS legacy=209 rv32imc={EXPECTED_C_CASES} full_trace_comparisons={expected_comparisons} units={len(tops)}')))))
    terminal(REPORT,marker)
    print(REPORT.read_text(),flush=True)
    print(f'RUN_REPORT={REPORT.resolve()}',flush=True)
if __name__=='__main__':
    try:
        main()
    except Exception as exc:
        detail=f'STAGE4_4 FAIL: {exc}\n{traceback.format_exc()}'
        try:
            if OUT.exists() and OUT.is_dir():
                diagnostic=OUT/'runner_diagnostic.log'
                suffix=1
                while diagnostic.exists():
                    diagnostic=OUT/f'runner_diagnostic_{suffix}.log'; suffix+=1
                diagnostic.write_text(detail,encoding='utf-8',newline='\n')
                print(f'RUNNER_DIAGNOSTIC {diagnostic}',file=sys.stderr,flush=True)
        except Exception as log_exc:
            detail+=f'\nDIAGNOSTIC_WRITE_FAILURE: {log_exc!r}\n{traceback.format_exc()}'
        print(detail,file=sys.stderr,flush=True)
        raise SystemExit(1)
