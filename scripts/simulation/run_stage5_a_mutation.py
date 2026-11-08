#!/usr/bin/env python3
"""Fresh-baseline, isolated Verilator mutation campaign for Stage 5 A logic."""
import argparse, datetime, difflib, hashlib, os, re, shutil, subprocess, sys, tempfile
from pathlib import Path, PurePosixPath, PureWindowsPath

HERE=Path(__file__).resolve().parent; ROOT=HERE.parents[1]; REPORTS=ROOT/'reports'
RUNNER='scripts/simulation/run_stage4_4.py'
MUTANTS=[
 ('A01','AMOMIN uses unsigned ordering','rtl/alu/rv_a_unit.sv',"(old_s < source_s) ? old_word : source_word","(old_word < source_word) ? old_word : source_word"),
 ('A02','LR.W rejects nonzero rs2','rtl/decoder/rv_decoder.sv',"(insn[31:27] == 5'b00010 && insn[24:20] == 5'b0)","(insn[31:27] == 5'b00010)"),
 ('A03','SC writes even without reservation','rtl/pipeline/rv_mem_stage.sv',"(!atomic_sc || sc_success)","1'b1"),
 ('A04','ordinary store fails to invalidate reservation','rtl/pipeline/rv_mem_stage.sv',"ex_mem.alu_y[31:2] == reservation_addr[31:2]","1'b0"),
 ('A05','A operation metadata lost between EX and MEM','rtl/pipeline/rv_ex_stage.sv',"ex_mem_next.is_a       = id_ex.is_a;","ex_mem_next.is_a       = 1'b0;"),
]
SOURCE_DIRS=('rv32i','pipeline','pipeline_m','m_extension','pipeline_div','pipeline_div_coverage',
             'rv32imc','rv32imc_pipeline','rv32ima_software','rv32imac_software','rv32imac_pipeline_a')
BASE_SOURCES=('scripts/simulation/run_stage4_4.py','scripts/simulation/prepare_stage4_4.py',
              'scripts/simulation/prepare_stage5.py','scripts/simulation/rv32_asm.py',
              'scripts/simulation/rv32i_iss.py','scripts/simulation/rv32c_asm.py',
              'scripts/simulation/rv32imc_iss.py','scripts/simulation/rv32a_model.py',
              'scripts/simulation/generate_stage4_2_vectors.py','scripts/simulation/validate_stage5_a.py',
              'scripts/simulation/stage4_4_rtl.f',
              'verification/environment/tb_rv_core.sv','verification/environment/tb_rv_pipe_stage4.sv',
              'verification/environment/tb_rv_a_unit.sv')

def digest(path): return hashlib.sha256(path.read_bytes()).hexdigest()

def host_path(value):
    """Translate report paths between Windows and WSL without altering identity."""
    raw=str(value)
    candidate=Path(raw)
    if candidate.exists(): return candidate
    win=PureWindowsPath(raw)
    if win.drive:
        if os.name=='nt': return Path(str(win))
        mapped=Path('/mnt')/win.drive[0].lower()
        for part in win.parts[1:]: mapped=mapped/part
        return mapped
    posix=PurePosixPath(raw)
    parts=posix.parts
    if os.name=='nt' and len(parts)>=3 and parts[0]=='/' and parts[1].lower()=='mnt' and len(parts[2])==1:
        return Path(parts[2].upper()+':\\',*parts[3:])
    return candidate

def expected_source_paths():
    paths=set(BASE_SOURCES)
    rtl_file=ROOT/'scripts/simulation/stage4_4_rtl.f'
    paths.update(x.strip().replace('\\','/') for x in rtl_file.read_text(encoding='utf-8').splitlines() if x.strip())
    for folder in SOURCE_DIRS:
        directory=ROOT/'tests'/'directed'/folder
        if directory.is_dir():
            paths.update(p.relative_to(ROOT).as_posix() for p in directory.iterdir()
                         if p.is_file() and p.suffix in ('.s','.csv'))
    return paths
def ignore(directory,names):
    drop=[]
    for name in names:
        p=Path(directory)/name
        if name in ('.git','__pycache__','.venv','venv','reports') or name.startswith(('sim_out','obj_dir')): drop.append(name)
        elif p.is_file() and name.lower().endswith(('.hex','.pyc')): drop.append(name)
    return drop
def complete_trace(path):
    if not path.is_file(): return None
    lines=path.read_text(encoding='ascii',errors='replace').splitlines()
    if len([x for x in lines if x.startswith('STOP ')])!=1 or len([x for x in lines if x.startswith('HALT ')])!=1 or len([x for x in lines if x.startswith('REG ')])!=31: return None
    return lines

def first_diagnostic(output):
    patterns=('FIRST_TOOL_ERROR','COMPILER_DIAGNOSTIC','ERROR:','FATAL','Traceback',
              'STAGE4_4 FAIL','RuntimeError:','AssertionError:','TEST_RESULT: FAIL',
              'trace mismatch','missing','timeout','TIMEOUT','error:')
    lines=output.splitlines()
    for index,line in enumerate(lines):
        if index==0 and line.startswith('TOOL PREFLIGHT PASS'): continue
        if any(token.lower() in line.lower() for token in patterns):
            return line.strip()
    return next((line.strip() for line in lines if line.strip() and not line.startswith('TOOL PREFLIGHT PASS')),
                'no diagnostic after tool preflight')

def verified_unit_detection(ident, output_dir):
    """Accept only the specific independent A-unit assertion for this mutant."""
    log=output_dir/'unit_aunit.log' if output_dir else None
    if not log or not log.is_file(): return None
    text=log.read_text(encoding='utf-8',errors='replace')
    fatal=re.search(r'%Fatal: tb_rv_a_unit\.sv:58: Assertion failed .*RV32A_UNIT FAIL checks=9 legality_checks=2048 errors=(\d+)',text)
    if ident=='A01':
        expected='A_UNIT_DIFF op=10 old=80000000 src=7fffffff expected=80000000 actual=7fffffff'
        if expected in text and fatal and fatal.group(1)=='1':
            return f'unit_aunit.log independent arithmetic assertion: {expected}; {fatal.group(0)}'
    if ident=='A02':
        rows=re.findall(r'A_LEGALITY_DIFF raw=([0-9a-fA-F]{8}) expected_legal=0 actual_is_a=1 illegal=0',text)
        bad=[]
        for raw_text in rows:
            raw=int(raw_text,16)
            funct5=(raw>>27)&0x1f; rs2=(raw>>20)&0x1f
            funct3=(raw>>12)&7; opcode=raw&0x7f
            if funct5!=0b00010 or rs2==0 or funct3!=0b010 or opcode!=0x2f:
                bad.append(raw_text)
        if len(rows)==4 and len(set(rows))==4 and not bad and fatal and fatal.group(1)=='4':
            return ('unit_aunit.log independent legality sweep rejected the mutant: '
                    f'raw_values={",".join(rows)} all decode as LR.W with rs2!=0; '
                    f'{fatal.group(0)}')
    return None

def save_mutant_evidence(artifact, ident, rel, original, mutated, command, proc, output_dir, classification):
    artifact.mkdir(parents=True,exist_ok=False)
    patch=''.join(difflib.unified_diff(original.splitlines(True),mutated.splitlines(True),
                                      fromfile='baseline/'+rel,tofile=f'{ident}/'+rel))
    (artifact/'mutation.patch').write_text(patch,encoding='utf-8',newline='\n')
    (artifact/'command.txt').write_text('cwd='+str(command[0])+'\nargv='+repr(command[1])+
                                        f'\nexit_code={proc.returncode}\n',encoding='utf-8',newline='\n')
    (artifact/'stdout_stderr.log').write_text(proc.stdout,encoding='utf-8',newline='\n')
    (artifact/'first_diagnostic.txt').write_text(first_diagnostic(proc.stdout)+'\n',encoding='utf-8',newline='\n')
    (artifact/'classification.txt').write_text(classification+'\n',encoding='utf-8',newline='\n')
    if output_dir and output_dir.is_dir():
        shutil.copytree(output_dir,artifact/'simulator_output',dirs_exist_ok=True)

def validated_report(simulator):
    marker=(f'STAGE5_A_PIPELINE_{simulator.upper()} PASS legacy=209 c_cases=21 a_cases=18 '
            'full_trace_comparisons=496 units=8')
    reports=sorted(REPORTS.glob(f'stage5_a_pipeline_{simulator}_*.txt'),key=lambda p:p.stat().st_mtime,reverse=True)
    expected_sources=expected_source_paths()
    accepted=None
    diagnostics=[]
    for report in reports:
        text=report.read_text(encoding='utf-8',errors='replace')
        reasons=[]
        if text.count(marker)!=1: reasons.append(f'terminal_marker_count={text.count(marker)} expected=1')
        if 'FAIL' in text: reasons.append('report contains FAIL')
        fields={line.partition('=')[0]:line.partition('=')[2] for line in text.splitlines() if '=' in line}
        prov_raw=fields.get('provenance_file','')
        prov=host_path(prov_raw) if prov_raw else Path()
        if not prov.is_file():
            out_raw=fields.get('output_dir','')
            out=host_path(out_raw) if out_raw else Path()
            fallback=out/'provenance.txt'
            if fallback.is_file():
                reasons.append(f'provenance_file path was not host-readable ({prov_raw!r}); output_dir mapping resolved to {fallback}')
                prov=fallback
            else:
                reasons.append(f'provenance file missing/unreadable: recorded={prov_raw!r}; output_dir={out_raw!r}; mapped={prov}')
        if prov.is_file():
            provenance=prov.read_text(encoding='utf-8',errors='replace')
            pfields={line.partition('=')[0]:line.partition('=')[2] for line in provenance.splitlines() if '=' in line}
            for key,value in (('simulator',simulator),('enable_a','True'),('a_only','False')):
                if pfields.get(key)!=value: reasons.append(f'provenance {key}={pfields.get(key)!r}, expected={value!r}')
            recorded={}; malformed=[]; mismatches=[]
            for line in provenance.splitlines():
                if not line.startswith('sha256 '): continue
                rel,sep,expected=line[7:].partition('=')
                if not sep or rel in recorded:
                    malformed.append(line); continue
                recorded[rel]=expected
                source=ROOT/Path(rel.replace('\\','/'))
                current=digest(source) if source.is_file() else 'MISSING'
                if current!=expected: mismatches.append((rel,expected,current))
            missing=sorted(expected_sources-set(recorded)); extra=sorted(set(recorded)-expected_sources)
            if missing: reasons.append(f'provenance missing source hashes: {missing}')
            if extra: reasons.append(f'provenance has unexpected hashed paths: {extra}')
            if malformed: reasons.append(f'malformed/duplicate provenance hash rows: {malformed}')
            if mismatches:
                reasons.append('source hash mismatches: '+repr(mismatches))
        for key,value in (('rtl_vs_iss_and_golden','496'),('pipeline_vs_golden_full_traces','248'),('a_cases','18'),('unit_suites','8')):
            if fields.get(key)!=value: reasons.append(f'report {key}={fields.get(key)!r}, expected={value!r}')
        if reasons:
            detail=f'REPORT_CANDIDATE REJECT simulator={simulator} path={report}: '+'; '.join(reasons)
            print(detail,flush=True); diagnostics.append(detail)
        else:
            detail=f'REPORT_CANDIDATE ACCEPT simulator={simulator} path={report} provenance={prov}'
            print(detail,flush=True)
            if accepted is None: accepted=report
    if accepted is not None: return accepted
    raise RuntimeError(f'no {simulator} full-suite PASS report with source-matched provenance for current tree; considered={len(reports)}\n'+'\n'.join(diagnostics))

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--preflight-only',action='store_true',help='validate source-matched XSim and Verilator reports; do not run a baseline or mutants')
    parser.add_argument('--mutants',help='comma-separated mutant IDs to run (for example A01,A02); default is all mutants')
    args=parser.parse_args()
    if args.preflight_only:
        xsim_report=validated_report('xsim')
        verilator_report=validated_report('verilator')
        print(f'STAGE5_A_MUTATION_PREFLIGHT PASS xsim={xsim_report} verilator={verilator_report} source_files={len(expected_source_paths())}',flush=True)
        return 0
    stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    report=REPORTS/f'stage5_a_mutation_verilator_{stamp}.txt'; REPORTS.mkdir(exist_ok=True)
    if report.exists(): raise SystemExit(f'STAGE5_A_MUTATION_PREFLIGHT FAIL report path is not fresh: {report}')
    missing=[x for x in ('verilator','make') if not shutil.which(x)]
    if not any(shutil.which(x) for x in ('g++','clang++','c++')): missing.append('C++ compiler')
    if not Path(sys.executable).is_file(): missing.append('active Python interpreter')
    if missing: raise SystemExit('STAGE5_A_MUTATION_PREFLIGHT FAIL missing='+','.join(missing))
    try:
        xsim_report=validated_report('xsim')
        verilator_report=validated_report('verilator')
    except Exception as exc:
        raise SystemExit(f'STAGE5_A_MUTATION_PREFLIGHT FAIL {exc}') from exc
    selected_ids=[x.strip().upper() for x in args.mutants.split(',')] if args.mutants else [x[0] for x in MUTANTS]
    unknown=sorted(set(selected_ids)-{x[0] for x in MUTANTS})
    if unknown or len(selected_ids)!=len(set(selected_ids)) or not selected_ids:
        raise SystemExit(f'STAGE5_A_MUTATION_PREFLIGHT FAIL invalid mutant selection={selected_ids}; unknown={unknown}')
    selected=[x for x in MUTANTS if x[0] in selected_ids]
    stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    artifact_root=REPORTS/f'stage5_a_mutation_artifacts_{stamp}'
    artifact_root.mkdir(parents=True,exist_ok=False)
    for ident,label,rel,old,new in selected:
        p=ROOT/rel
        if p.read_text(encoding='utf-8').count(old)!=1: raise SystemExit(f'{ident} mutation anchor is not unique: {rel}')
    # Mutation requires both source-matched simulator PASS reports and then
    # establishes one more fresh Verilator baseline before isolated mutants.
    baseline=subprocess.run([sys.executable,str(ROOT/RUNNER),'--sim','verilator','--enable-a'],cwd=ROOT,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    baseline_marker='STAGE5_A_PIPELINE_VERILATOR PASS legacy=209 c_cases=21 a_cases=18 full_trace_comparisons=496 units=8'
    if baseline.returncode or baseline.stdout.count(baseline_marker)!=1:
        print(baseline.stdout,file=sys.stderr)
        raise SystemExit(f'STAGE5_A_MUTATION_PREFLIGHT FAIL fresh full baseline exit={baseline.returncode} marker_count={baseline.stdout.count(baseline_marker)}')
    rows=[]
    with tempfile.TemporaryDirectory(prefix='stage5_a_mutation_') as temp:
        for ident,label,rel,old,new in selected:
            work=Path(temp)/ident
            shutil.copytree(ROOT,work,ignore=ignore)
            target=work/rel; before=digest(target); text=target.read_text(encoding='utf-8')
            if text.count(old)!=1: rows.append((ident,'INVALID','mutation anchor changed in isolated copy')); continue
            mutated=text.replace(old,new,1)
            target.write_text(mutated,encoding='utf-8',newline='\n')
            argv=[sys.executable,str(work/RUNNER),'--sim','verilator','--enable-a','--a-only']
            try:
                proc=subprocess.run(argv,cwd=work,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
            except OSError as exc:
                proc=subprocess.CompletedProcess(argv,127,stdout=f'LAUNCH_FAILURE {exc!r}\n')
            match=re.search(r'TOOL PREFLIGHT PASS sim=verilator.*?output=(.+)',proc.stdout)
            out=Path(match.group(1).strip()) if match else None
            if out and not out.is_absolute(): out=(work/out).resolve()
            evidence=None
            unit_evidence=verified_unit_detection(ident,out)
            if unit_evidence:
                evidence=unit_evidence
            if out and out.is_dir():
                trace_candidates=sorted([*out.glob('*.golden.trace'),*out.glob('*.pipe.trace')]) if not evidence else []
                for trace in trace_candidates:
                    name=trace.name.rsplit('.',2)[0]
                    kind=trace.name.rsplit('.',2)[1]
                    ref=out/'a_iss'/(name+'.trace')
                    actual=complete_trace(trace); expected=complete_trace(ref)
                    if actual is None or expected is None: continue
                    case_log=out/(name+'.'+kind+'.log')
                    log_text=case_log.read_text(encoding='utf-8',errors='replace') if case_log.is_file() else ''
                    terminals=[line for line in log_text.splitlines() if line.startswith('TEST_RESULT: ')]
                    if len(terminals)!=1 or not any(x in terminals[0] for x in ('TEST_RESULT: PASS','TEST_RESULT: FAIL')) or 'TIMEOUT' in terminals[0]:
                        continue
                    atomic=out/(name+'.'+trace.name.rsplit('.',2)[1]+'.a.tsv')
                    atomic_ref=out/'a_iss'/(name+'.a.tsv')
                    if actual!=expected:
                        n=min(len(actual),len(expected)); i=next((j for j in range(n) if actual[j]!=expected[j]),n)
                        evidence=f'{trace.name}:line={i+1}:expected={expected[i] if i<len(expected) else "<EOF>"}:actual={actual[i] if i<len(actual) else "<EOF>"}'
                        break
                    if atomic.is_file() and atomic_ref.is_file() and atomic.read_text(encoding='ascii')!=atomic_ref.read_text(encoding='ascii'):
                        evidence=f'{atomic.name}: complete architectural trace; atomic sidecar differs from independent ISS {atomic_ref.name}'
                        break
            if evidence:
                result='CAUGHT'
                artifact=artifact_root/ident
                try: save_mutant_evidence(artifact,ident,rel,text,mutated,(work,argv),proc,out,f'{result}: {evidence}')
                except Exception as exc: evidence+=f'; evidence-retention-error={exc!r}'
                rows.append((ident,result,evidence))
            elif proc.returncode==0 and proc.stdout.count('STAGE5_A_PIPELINE_VERILATOR_A_ONLY PASS a_cases=18 full_trace_comparisons=36 units=8')==1:
                result='MISSED'; evidence='complete focused A-only run passed'
                artifact=artifact_root/ident
                try: save_mutant_evidence(artifact,ident,rel,text,mutated,(work,argv),proc,out,f'{result}: {evidence}')
                except Exception as exc: evidence+=f'; evidence-retention-error={exc!r}'
                rows.append((ident,result,evidence))
            else:
                first=first_diagnostic(proc.stdout)
                artifact=artifact_root/ident
                try:
                    save_mutant_evidence(artifact,ident,rel,text,mutated,(work,argv),proc,out,f'INVALID: exit={proc.returncode}; first={first}')
                    rows.append((ident,'INVALID',f'exit={proc.returncode}; first={first}; diagnostics={artifact}'))
                except Exception as exc:
                    rows.append((ident,'INVALID',f'exit={proc.returncode}; first={first}; evidence-retention-error={exc!r}; stdout={artifact}/stdout_stderr.log'))
            _=before
    with report.open('w',encoding='utf-8',newline='\n') as f:
        f.write('Stage 5 A-extension mutation campaign (Verilator only)\n')
        f.write(f'Validated full-suite reports: XSim={xsim_report} Verilator={verilator_report}\n')
        f.write('Fresh full baseline: '+baseline_marker+'\n')
        f.write(f'Focused selection: {", ".join(selected_ids)}. Invalid-mutant diagnostics/artifacts: {artifact_root}\n')
        f.write('Mutant workspaces are disposable; every selected result retains full runner output, mutation patch, exit/command details, and simulator output (including references, traces, and build logs) outside the temporary workspace. CAUGHT requires the mutant-specific independent unit assertion or a complete trace/atomic-sidecar difference.\n')
        for ident,result,detail in rows: f.write(f'{ident} {result}: {detail}\n')
        f.write(f'STAGE5_A_MUTATION_VERILATOR {"PASS" if rows and all(x[1]=="CAUGHT" for x in rows) else "FAIL"} caught={sum(x[1]=="CAUGHT" for x in rows)} missed={sum(x[1]=="MISSED" for x in rows)} invalid={sum(x[1]=="INVALID" for x in rows)} total={len(rows)}\n')
    print(report.read_text(encoding='utf-8'),end='')
    return 0 if rows and all(x[1]=='CAUGHT' for x in rows) else 1
if __name__=='__main__': raise SystemExit(main())
