#!/usr/bin/env python3
"""Run the isolated Stage 4 C-extension Verilator mutation campaign."""
import argparse, datetime, json, os, re, shutil, signal, subprocess, sys, tempfile, time
from pathlib import Path

HERE=Path(__file__).resolve().parent; ROOT=HERE.parents[1]; REPORTS=ROOT/'reports'
MUTANTS=[
 ('C01','ADDI16SP immediate bit mapping','rtl/decoder/rv32c_decompressor.sv',
  "imm = {{22{raw_halfword[12]}}, raw_halfword[12], raw_halfword[4:3],\n                       raw_halfword[5], raw_halfword[2], raw_halfword[6], 4'b0000};",
  "imm = {{22{raw_halfword[12]}}, raw_halfword[12], raw_halfword[4:3],\n                       raw_halfword[6], raw_halfword[2], raw_halfword[5], 4'b0000};",'decompress'),
 ('C02','C.ADDI4SPN zero immediate accepted','rtl/decoder/rv32c_decompressor.sv',"if (uimm == 0) illegal = 1'b1;","if (uimm == 0) illegal = 1'b0;",'decompress'),
 ('C03','C.ADDI HINT classification is lost','rtl/decoder/rv32c_decompressor.sv',
  "else begin hint = 1'b1; expanded_insn = 32'h00000013; end",
  "else begin hint = 1'b0; expanded_insn = 32'h00000013; end",'decompress'),
 ('C04','Compressed length prefix classified as 32-bit','rtl/decoder/rv32c_decompressor.sv',"if (raw_halfword[1:0] != 2'b11) begin","if (raw_halfword[1:0] == 2'b11) begin",'decompress'),
 ('C05','C-enabled sequential PC stride forced to four bytes','rtl/pipeline/rv_if_stage.sv',"else if (!stall)   pc <= pc + instruction_bytes;","else if (!stall)   pc <= pc + (ENABLE_C ? 5'd4 : instruction_bytes);",'system'),
 ('C06','Compressed jump link uses PC+4','rtl/pipeline/rv_ex_stage.sv',"id_ex.pc + (ENABLE_C ? id_ex.ilen_bytes : 5'd4)","id_ex.pc + 5'd4",'system'),
 ('C07','Offset-two instruction parcels concatenated in wrong order','rtl/pipeline/rv_if_stage.sv',"raw = {imem_rdata_next[15:0], parcel};","raw = {parcel, imem_rdata_next[15:0]};",'system'),
 ('C08','ID/EX metadata does not hold during divider busy','rtl/pipeline/rv_pipe_regs.sv',"if (md_hold && !kill && !redirect) id_ex <= id_ex;","if (md_hold && !kill && !redirect) id_ex <= id_ex_next;",'system'),
 ('C09','Redirect does not flush younger IF/ID instruction','rtl/pipeline/rv_pipe_regs.sv',"if (kill || redirect) if_id <= '0;","if (kill) if_id <= '0;",'system'),
 ('C10','Faulting memory operation is allowed to commit','rtl/pipeline/rv_mem_stage.sv',"assign commit = ex_mem.valid && (cause == HALT_NONE);","assign commit = ex_mem.valid;",'system'),
]

def ignore(directory,names):
    drop=[]
    for n in names:
        p=Path(directory)/n
        if n in ('.git','__pycache__','reports','.venv','venv') or n.startswith(('sim_out','obj_dir')):
            drop.append(n)
        elif p.is_file() and n.lower().endswith('.hex'):
            drop.append(n)
    return drop

def copy_project(dest):
    shutil.copytree(ROOT,dest,ignore=ignore)
    (dest/'reports').mkdir(exist_ok=True)

def run_capture(cmd,cwd,timeout):
    start=time.monotonic()
    p=subprocess.Popen(cmd,cwd=cwd,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,start_new_session=(os.name!='nt'))
    try: stdout,stderr=p.communicate(timeout=timeout); timed=False
    except subprocess.TimeoutExpired:
        timed=True
        if os.name=='nt': p.kill()
        else:
            try: os.killpg(p.pid,signal.SIGTERM)
            except ProcessLookupError: pass
            try: p.wait(timeout=3)
            except subprocess.TimeoutExpired:
                try: os.killpg(p.pid,signal.SIGKILL)
                except ProcessLookupError: pass
        stdout,stderr=p.communicate()
    except KeyboardInterrupt:
        if os.name=='nt': p.kill()
        else:
            try: os.killpg(p.pid,signal.SIGTERM)
            except ProcessLookupError: pass
        p.communicate(); raise
    output=stdout+'\n--- STDERR ---\n'+stderr
    return {'command':cmd,'cwd':str(cwd),'exit_code':p.returncode,'timeout':timed,'elapsed_s':round(time.monotonic()-start,2),'stdout':stdout,'stderr':stderr,'output':output}

def apply_mutation(work,ident,rel,old,new):
    path=work/rel; text=path.read_text(encoding='utf-8')
    count=text.count(old)
    if count!=1: raise ValueError(f'{ident}: expected exactly one anchor in {rel}, found {count}')
    changed=text.replace(old,new,1); path.write_text(changed,encoding='utf-8',newline='\n')
    return path

def fresh_out(text):
    m=re.search(r'TOOL PREFLIGHT PASS sim=verilator.*?output=(.+)',text)
    return Path(m.group(1).strip()) if m else None

def save_evidence(simout,dest,stdout):
    dest.mkdir(parents=True,exist_ok=True)
    (dest/'runner_output.log').write_text(stdout,encoding='utf-8',newline='\n')
    if not simout or not simout.is_dir(): return
    for name in ('unit_decompress.log','unit_pipe.log','software_preflight.log','stage4_4_rtl_abs.f','c_manifest.csv','manifest_all.csv'):
        src=simout/name
        if src.is_file(): shutil.copy2(src,dest/name)
    for dirname in ('c_iss','c_hex'):
        srcdir=simout/dirname
        if srcdir.is_dir(): shutil.copytree(srcdir,dest/dirname,dirs_exist_ok=True)
    for pattern in ('build_*.log','*.golden.log','*.golden.trace'):
        for src in simout.glob(pattern): shutil.copy2(src,dest/src.name)
    # Preserve every completed C case artifact; build trees and generated
    # vectors/images are reproducible and intentionally not copied here.
    for src in simout.glob('*.pipe.log'): shutil.copy2(src,dest/src.name)
    for src in simout.glob('*.pipe.trace'): shutil.copy2(src,dest/src.name)
    for src in simout.glob('*.pipe.ccov'): shutil.copy2(src,dest/src.name)

def _complete_trace(path):
    """Require a structurally complete architectural trace before comparing it."""
    if not path.is_file(): return None
    lines=path.read_text(encoding='ascii').splitlines()
    if not lines or lines[0]!='TRACE_V2 RV32IMC pc raw_insn ilen_bytes expanded_insn rd rdval st_size st_addr st_data': return None
    stops=[x for x in lines if x.startswith('STOP ')]
    halts=[x for x in lines if x.startswith('HALT ')]
    regs=[x for x in lines if x.startswith('REG ')]
    if len(stops)!=1 or len(halts)!=1 or len(regs)!=31: return None
    s=stops[0].split(); h=halts[0].split()
    if len(s)!=5 or len(h)!=3 or int(s[1],16)!=int(h[2],16) or int(s[4])!=int(h[1]): return None
    return lines

def _first_trace_difference(actual,expected):
    n=min(len(actual),len(expected))
    for i in range(n):
        if actual[i]!=expected[i]: return i+1,expected[i],actual[i]
    if len(actual)!=len(expected):
        return n+1, expected[n] if n<len(expected) else '<EOF>', actual[n] if n<len(actual) else '<EOF>'
    return None

def detector(ident, output, simout):
    if not simout: return None
    if ident in {'C01','C02','C03','C04'}:
        log=simout/'unit_decompress.log'
        if log.is_file():
            text=log.read_text(encoding='utf-8',errors='replace')
            if 'RV32C_DECOMPRESS_UNIT FAIL' in text or 'ANCHOR_DIFF' in text or 'mismatches=' in text and 'mismatches=0' not in text:
                return f'independent exhaustive decompressor unit failure ({log.name})'
    m=re.search(r'STAGE4_4 FAIL: ([A-Za-z0-9_]+)/pipe: timing model mismatch',output)
    if m:
        name=m.group(1); log=simout/(name+'.pipe.log')
        if log.is_file() and re.search(r'STATS stalls=\d+ redirects=\d+ cycles=\d+ instret=\d+',log.read_text(encoding='utf-8',errors='replace')):
            return f'{name}: independent cycle/protocol check rejected changed pipeline behavior'
    # The standard regression checks TEST_RESULT before comparing traces. A
    # mutant can therefore stop at a valid TEST_RESULT: FAIL, leaving a full
    # architectural trace that still provides an independent ISS detection.
    # Compare only against the separately generated software ISS reference;
    # never infer detection from a nonzero runner exit or failure marker alone.
    for trace in sorted([*simout.glob('*.golden.trace'),*simout.glob('*.pipe.trace')]):
        kind='golden' if trace.name.endswith('.golden.trace') else 'pipe'
        name=trace.name[:-len(f'.{kind}.trace')]
        expected_path=simout/'c_iss'/(name+'.trace')
        log=simout/(name+f'.{kind}.log')
        actual_lines=_complete_trace(trace); expected_lines=_complete_trace(expected_path)
        if actual_lines is None or expected_lines is None or not log.is_file(): continue
        text=log.read_text(encoding='utf-8',errors='replace')
        terminal=re.findall(r'^TEST_RESULT: (PASS|FAIL)\b',text,re.M)
        # Require normal simulator completion and one unambiguous result.
        if len(terminal)!=1 or 'Verilator: $finish' not in text: continue
        diff=_first_trace_difference(actual_lines,expected_lines)
        if diff:
            line,exp,act=diff
            return f'{name}: independent {kind}/ISS architectural trace mismatch line={line} expected={exp!r} actual={act!r}'
    return None

def built(simout):
    if not simout:return False
    return all((simout/f'obj_{n}'/n).is_file() for n in ('decompress','golden1','pipe1'))

def run_decompressor_only(work, folder, timeout):
    """Mutate/check the standalone decompressor without compiling a golden core."""
    out=folder/'standalone_decompressor'; out.mkdir(exist_ok=True)
    vectors=out/'vectors.txt'
    vg=run_capture([sys.executable,str(work/'scripts/simulation/generate_stage4_2_vectors.py'),str(vectors)],work,timeout)
    (out/'vectors.log').write_text(vg['output'],encoding='utf-8',newline='\n')
    (out/'vectors.stdout.log').write_text(vg['stdout'],encoding='utf-8',newline='\n'); (out/'vectors.stderr.log').write_text(vg['stderr'],encoding='utf-8',newline='\n')
    if vg['exit_code']!=0 or vg['timeout'] or 'RV32C_VECTOR_GENERATION PASS halfwords=65536 oracle_mismatches=0' not in vg['output'] or not vectors.is_file():
        return {'exit_code':vg['exit_code'],'timeout':vg['timeout'],'build_success':False,'simulator_started':False,'detector':None,'output':vg['output'],'reason':'independent vectors not prepared'}
    build=out/'build'; build.mkdir()
    cmd=['verilator','--binary','--timing','--top-module','tb_rv32c_decompressor','--Mdir',str(build),'-Wall','-Wno-fatal',str(work/'rtl/decoder/rv32c_decompressor.sv'),str(work/'verification/environment/tb_rv32c_decompressor.sv'),'-o','decompress']
    br=run_capture(cmd,work,timeout); (out/'build.log').write_text(br['output'],encoding='utf-8',newline='\n')
    (out/'build.stdout.log').write_text(br['stdout'],encoding='utf-8',newline='\n'); (out/'build.stderr.log').write_text(br['stderr'],encoding='utf-8',newline='\n')
    exe=build/'decompress'
    if br['exit_code']!=0 or br['timeout'] or not exe.is_file():
        return {'exit_code':br['exit_code'],'timeout':br['timeout'],'build_success':False,'simulator_started':False,'detector':None,'output':br['output'],'reason':'decompressor build failed or binary missing'}
    sim=run_capture([str(exe),f'+VECTORS={vectors.as_posix()}'],work,timeout)
    (out/'unit.log').write_text(sim['output'],encoding='utf-8',newline='\n')
    (out/'unit.stdout.log').write_text(sim['stdout'],encoding='utf-8',newline='\n'); (out/'unit.stderr.log').write_text(sim['stderr'],encoding='utf-8',newline='\n')
    checker=run_capture([sys.executable,str(work/'scripts/simulation/check_stage4_2_sim_log.py'),str(out/'unit.log')],work,timeout)
    (out/'logcheck.log').write_text(checker['output'],encoding='utf-8',newline='\n')
    (out/'logcheck.stdout.log').write_text(checker['stdout'],encoding='utf-8',newline='\n'); (out/'logcheck.stderr.log').write_text(checker['stderr'],encoding='utf-8',newline='\n')
    text=sim['output']+'\n'+checker['output']; caught=('RV32C_DECOMPRESS_UNIT FAIL' in sim['output'] or 'ANCHOR_DIFF' in sim['output'] or 'mismatches=' in sim['output'] and 'mismatches=0' not in sim['output'])
    strict_marker='RV32C_SIM_LOG_CHECK PASS terminal_markers=1 pass_markers=1 halfwords=65536 mismatches=0 anchors=16'
    complete_pass=(sim['exit_code']==0 and checker['exit_code']==0 and strict_marker in checker['output'])
    commands={'vectors':vg['command'],'build':cmd,'simulate':[str(exe),f'+VECTORS={vectors.as_posix()}'],'strict_log_check':checker['command']}
    (out/'commands.json').write_text(json.dumps(commands,indent=2)+'\n',encoding='utf-8')
    return {'command':commands,'cwd':str(work),'exit_code':sim['exit_code'] if sim['exit_code'] else checker['exit_code'],'timeout':sim['timeout'] or checker['timeout'],'build_success':True,'simulator_started':(out/'unit.log').is_file(),'complete_pass':complete_pass,'detector':'independent exhaustive decompressor vector/log checker failure' if caught and checker['exit_code']!=0 else None,'output':text,'reason':None}

def main():
    ap=argparse.ArgumentParser(description=__doc__); ap.add_argument('--timeout-seconds',type=int,default=3600); ap.add_argument('--preflight-only',action='store_true'); ap.add_argument('--mutants',help='comma-separated mutant IDs to run after one fresh full baseline, e.g. C07,C09'); args=ap.parse_args()
    selected=set(args.mutants.split(',')) if args.mutants else {m[0] for m in MUTANTS}
    unknown=selected-{m[0] for m in MUTANTS}
    if unknown: raise SystemExit('unknown mutant ID(s): '+','.join(sorted(unknown)))
    mutants=[m for m in MUTANTS if m[0] in selected]
    missing=[x for x in ('verilator','make') if not shutil.which(x)]
    if not any(shutil.which(x) for x in ('g++','clang++','c++')): missing.append('C++ compiler')
    if not Path(sys.executable).is_file(): missing.append(f'Python interpreter {sys.executable}')
    if missing: raise SystemExit('MUTATION PREFLIGHT FAIL missing: '+', '.join(missing))
    problems=[]
    for ident,name,rel,old,new,_ in mutants:
        try:
            if (ROOT/rel).read_text(encoding='utf-8').count(old)!=1: problems.append(f'{ident}: anchor count is not exactly one in {rel}')
        except OSError as e: problems.append(f'{ident}: {e}')
    if problems:
        print('\n'.join(problems),file=sys.stderr); raise SystemExit(1)
    print(f'STAGE4_C_MUTATION_PREFLIGHT PASS mutants={len(mutants)} tools=verilator,make,cxx anchors=unique')
    if args.preflight_only: return 0
    stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ'); root=REPORTS/'stage4_c_mutation_runs'/f'run_{stamp}'
    report=REPORTS/f'stage4_c_mutation_verilator_{stamp}.txt'
    if root.exists() or report.exists(): raise SystemExit(f'report paths are not fresh: {root} / {report}')
    root.mkdir(parents=True); results=[]
    with tempfile.TemporaryDirectory(prefix='stage4c_baseline_') as td:
        base=Path(td)/'project'; copy_project(base)
        cmd=[sys.executable,str(base/'scripts/simulation/run_stage4_coverage.py'),'--sim','verilator']
        res=run_capture(cmd,base,args.timeout_seconds); bout=res['output']; (root/'baseline').mkdir()
        (root/'baseline'/'runner_output.log').write_text(bout,encoding='utf-8',newline='\n')
        (root/'baseline'/'stdout.log').write_text(res['stdout'],encoding='utf-8',newline='\n'); (root/'baseline'/'stderr.log').write_text(res['stderr'],encoding='utf-8',newline='\n')
        if res['exit_code']!=0 or res['timeout'] or 'STAGE4_C_COVERAGE_VERILATOR PASS cases=230 c_cases=21 patterns=65536 pipeline_events=16' not in bout:
            (root/'SUMMARY.txt').write_text('Baseline failed or malformed; no mutations executed.\n',encoding='utf-8')
            print(f'STAGE4_C_MUTATION FAIL baseline exit={res["exit_code"]} timeout={res["timeout"]} evidence={root}')
            return 1
        (root/'baseline'/'baseline.json').write_text(json.dumps({k:v for k,v in res.items() if k not in ('output','stdout','stderr')},indent=2)+'\n',encoding='utf-8')
    for index,(ident,name,rel,old,new,kind) in enumerate(mutants,1):
        print(f'[mutation {index}/{len(mutants)}] {ident} {name}',flush=True)
        folder=root/'mutants'/ident; folder.mkdir(parents=True)
        rec={'id':ident,'name':name,'target':rel,'status':'INVALID','build_success':False,'simulator_started':False,'detector':None}
        with tempfile.TemporaryDirectory(prefix=f'stage4c_{ident}_') as td:
            work=Path(td)/'project'; copy_project(work)
            try:
                target=apply_mutation(work,ident,rel,old,new)
                (folder/'mutated_source.diff').write_text(f'--- {rel} original\n+++ {rel} {ident}\n- {old}\n+ {new}\n',encoding='utf-8')
                if kind=='decompress':
                    res=run_decompressor_only(work,folder,args.timeout_seconds); out=res['output']; simout=None
                else:
                    cmd=[sys.executable,str(work/'scripts/simulation/run_stage4_4.py'),'--sim','verilator','--only-c']
                    res=run_capture(cmd,work,args.timeout_seconds); out=res['output']; simout=fresh_out(out)
                rec.update({k:res.get(k) for k in ('command','cwd','exit_code','timeout','elapsed_s')})
                (folder/'stdout.log').write_text(res.get('stdout',''),encoding='utf-8',newline='\n'); (folder/'stderr.log').write_text(res.get('stderr',''),encoding='utf-8',newline='\n')
                rec['build_success']=res.get('build_success',built(simout))
                if 'simulator_started' in res: rec['simulator_started']=res['simulator_started']
                else:
                    rec['simulator_started']=False
                    if simout:
                        ul=simout/'unit_decompress.log'
                        if ul.is_file() and any(x in ul.read_text(encoding='utf-8',errors='replace') for x in ('RV32C_DECOMPRESS_UNIT','ANCHOR_DIFF','FATAL:')):
                            rec['simulator_started']=True
                        for pl in simout.glob('*.pipe.log'):
                            if re.search(r'TEST_RESULT: (?:PASS|FAIL)',pl.read_text(encoding='utf-8',errors='replace')) and pl.with_suffix('.trace').is_file():
                                rec['simulator_started']=True; break
                det=res.get('detector') or detector(ident,out,simout); rec['detector']=det
                if simout: save_evidence(simout,folder/'evidence',out)
                elif out: (folder/'runner_output.log').write_text(out,encoding='utf-8',newline='\n')
                if res.get('timeout'): rec['status']='INVALID'; rec['reason']='timeout; no complete explicit detector result'
                elif not rec['build_success'] or not rec['simulator_started']:
                    rec['status']='INVALID'; rec['reason']='build or simulator startup not proven'
                elif res['exit_code']!=0 and det:
                    rec['status']='CAUGHT'
                elif res['exit_code']==0 and ((kind=='decompress' and res.get('complete_pass')) or 'STAGE4_4_PIPELINE_VERILATOR_C_ONLY PASS rv32imc=21 full_trace_comparisons=42 units=7' in out):
                    rec['status']='MISSED'; rec['reason']='complete C-only verification passed with mutation'
                else: rec['status']='INVALID'; rec['reason']='no independent named detection or valid complete PASS'
            except Exception as exc:
                rec['reason']=repr(exc)
            (folder/'result.json').write_text(json.dumps(rec,indent=2)+'\n',encoding='utf-8')
        results.append(rec)
        print(f'{ident} {rec["status"]}: {rec.get("detector") or rec.get("reason","no result")}',flush=True)
    counts={k:sum(r['status']==k for r in results) for k in ('CAUGHT','MISSED','INVALID','EQUIVALENT')}
    summary=['Stage 4 RV32C mutation campaign (Verilator only)',f'Generated UTC: {stamp}',f'Baseline: full coverage regression PASS (230 cases)',f'Mutants: {len(results)}',*[f'{k}: {v}' for k,v in counts.items()], '']
    summary += [f'{r["id"]} {r["status"]}: {r.get("detector") or r.get("reason","")}' for r in results]
    summary += [f'STAGE4_C_MUTATION_VERILATOR '+('PASS' if counts['MISSED']==0 and counts['INVALID']==0 else 'FAIL')+f' caught={counts["CAUGHT"]} missed={counts["MISSED"]} invalid={counts["INVALID"]} equivalent={counts["EQUIVALENT"]}']
    (root/'SUMMARY.txt').write_text('\n'.join(summary)+'\n',encoding='utf-8',newline='\n')
    shutil.copy2(root/'SUMMARY.txt',report)
    print(report.read_text(encoding='utf-8'),end='')
    return 0 if counts['MISSED']==0 and counts['INVALID']==0 else 1

if __name__=='__main__': raise SystemExit(main())
