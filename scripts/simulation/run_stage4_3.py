#!/usr/bin/env python3
"""Stage 4.3 combined golden-core and decompressor regression."""
import argparse,csv,datetime,os,shutil,subprocess,sys,traceback
HERE=os.path.dirname(os.path.abspath(__file__)); ROOT=os.path.normpath(os.path.join(HERE,'..','..'))
sys.path.insert(0,HERE)
from stage4_3_artifacts import c_image_path, c_reference_path
P=argparse.ArgumentParser(); P.add_argument('--sim',choices=('xsim','verilator'),required=True); P.add_argument('--resume',help='reuse a saved XSim output directory; validate artifacts and legacy results, then run only C cases'); ARGS=P.parse_args(); SIM=ARGS.sim; RESUME=ARGS.resume
STAMP=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
OUT=os.path.abspath(RESUME) if RESUME else os.path.join(ROOT,'sim_out_stage4_3_'+SIM+'_'+STAMP)
REPORT=os.path.join(ROOT,'reports',('stage4_3_golden_xsim_resume_'+STAMP+'.txt' if RESUME else 'stage4_3_golden_'+SIM+'_'+STAMP+'.txt'))
TOOLS={}; LAUNCH_DIAG=None; COMSPEC_PATH=None
def resolve_executable(name):
 return TOOLS.get(name) or shutil.which(name) or name
def sv_file_plusarg(name,path):
 return '+'+name+'='+os.path.abspath(path).replace('\\','/')
def command_for(cmd):
 resolved=resolve_executable(cmd[0])
 if os.path.splitext(resolved)[1].lower() in ('.bat','.cmd'):
  comspec=COMSPEC_PATH or os.environ.get('COMSPEC') or shutil.which('cmd.exe')
  if not comspec: raise RuntimeError('batch launcher requires COMSPEC or cmd.exe')
  rendered=[]; quote_next=False
  for arg in [resolved,*cmd[1:]]:
   if quote_next: rendered.append('"'+arg+'"'); quote_next=False
   else:
    rendered.append(subprocess.list2cmdline([arg])); quote_next=(arg in ('--testplusarg','-generic_top'))
  return '"'+comspec+'" /d /s /c "'+' '.join(rendered)+'"',resolved
 return [resolved,*cmd[1:]],resolved
def run(cmd,cwd=ROOT,log=None):
 actual,resolved=command_for(cmd)
 try: r=subprocess.run(actual,cwd=cwd,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
 except OSError as exc:
  diagnostic=(f'LAUNCH_FAILURE executable={cmd[0]!r} args={cmd[1:]!r} resolved={resolved!r} cwd={os.path.abspath(cwd)!r} error={exc!r}\n'
              f'COMMAND={actual!r}\n\n{traceback.format_exc()}')
  print(diagnostic,file=sys.stderr,flush=True)
  if LAUNCH_DIAG:
   with open(LAUNCH_DIAG,'a',encoding='utf-8',newline='\n') as dst: dst.write(diagnostic+'\n')
  raise RuntimeError(diagnostic) from exc
 if log: open(log,'w',newline='\n').write(r.stdout)
 if r.returncode: print(r.stdout); raise RuntimeError(f'command failed exit={r.returncode} executable={cmd[0]!r} resolved={resolved!r} cwd={os.path.abspath(cwd)!r} args={cmd[1:]!r}')
 return r.stdout
def normalized(text): return text.replace('\r\n','\n')
def validate_c_artifacts(out_dir):
 import rv32c_asm,rv32imc_iss
 source_manifest=os.path.join(ROOT,'tests','directed','rv32imc','manifest.csv')
 generated_manifest=os.path.join(out_dir,'c_manifest.csv')
 if not os.path.isfile(generated_manifest): raise RuntimeError(f'missing C manifest: {generated_manifest}')
 expected_rows=list(csv.DictReader(open(source_manifest,newline='')))
 rows=list(csv.DictReader(open(generated_manifest,newline='')))
 problems=[]; missing=[]
 if len(rows)!=len(expected_rows): problems.append(f'C manifest row count expected={len(expected_rows)} actual={len(rows)}')
 for index,expected in enumerate(expected_rows):
  name=expected['name']; image=c_image_path(out_dir,name); reference=c_reference_path(out_dir,name)
  if not os.path.isfile(image): missing.append(image)
  if not os.path.isfile(reference): missing.append(reference)
  if index>=len(rows): continue
  row=rows[index]
  for key in ('name','expect_cause','check_gp'):
   if row.get(key)!=expected.get(key): problems.append(f'manifest row {index+2} field {key}: expected={expected.get(key)!r} actual={row.get(key)!r}')
  rel=os.path.relpath(image,ROOT).replace('\\','/')
  if row.get('hexpath')!=rel: problems.append(f'manifest {name} image path expected={rel!r} actual={row.get("hexpath")!r}')
 if missing:
  for path in missing: print(f'C_ARTIFACT_MISSING {path}',flush=True)
  raise RuntimeError('missing C images/references: '+'; '.join(missing))
 if len(rows)!=len(expected_rows) or problems:
  raise RuntimeError('C manifest/source mismatch: '+'; '.join(problems))
 for row in expected_rows:
  name=row['name']; src=os.path.join(ROOT,'tests','directed','rv32imc',name+'.s')
  image=rv32c_asm.assemble_bytes(open(src,encoding='utf-8').read(),c_enabled=True)
  expected_hex=rv32c_asm.to_hex(image)
  if normalized(open(c_image_path(out_dir,name),encoding='ascii').read())!=normalized(expected_hex):
   problems.append(f'image differs from current source assembly: {c_image_path(out_dir,name)}')
  cause,regs,trace,footer,oob,_=rv32imc_iss.run(rv32c_asm.to_words(image),c_enabled=True)
  if cause!=int(row['expect_cause']) or oob:
   problems.append(f'{src}: reference cause expected={row["expect_cause"]} actual={cause} oob={oob}')
  expected_trace='TRACE_V2 RV32IMC pc raw_insn ilen_bytes expanded_insn rd rdval st_size st_addr st_data\n'+'\n'.join(trace+footer)+'\n'
  if normalized(open(c_reference_path(out_dir,name),encoding='ascii').read())!=normalized(expected_trace):
   problems.append(f'reference trace differs from current source/ISS: {c_reference_path(out_dir,name)}')
 if problems: raise RuntimeError('C artifact/source preflight failed: '+'; '.join(problems))
 print(f'STAGE4_3_C_ARTIFACT_PREFLIGHT PASS rows={len(rows)} images={len(rows)} references={len(rows)}',flush=True)
 return rows
def validate_saved_legacy(out_dir):
 import rv32_asm,rv32i_iss
 suites=[('rv32i','rv32i'),('pipeline','pipeline'),('pipeline_m','pipeline_m'),('m_extension','m_extension'),('pipeline_div','pipeline_div'),('pipeline_div_coverage','pipeline_div_coverage')]
 manifest_path=os.path.join(out_dir,'manifest_all.csv')
 if not os.path.isfile(manifest_path): raise RuntimeError(f'missing legacy manifest: {manifest_path}')
 saved={r['name']:r for r in csv.DictReader(open(manifest_path,newline=''))}
 problems=[]; expected_count=0
 for suite,folder in suites:
  srcdir=os.path.join(ROOT,'tests','directed',folder)
  for row in csv.DictReader(open(os.path.join(srcdir,'manifest.csv'),newline='')):
   name=row['name']; expected_count+=1
   hexpath=os.path.join(out_dir,'hex',name+'.hex')
   refpath=os.path.join(out_dir,'iss',name+'.iss.trace')
   rtlpath=os.path.join(out_dir,name+'.legacy.trace')
   logpath=rtlpath+'.run.log'
   if name not in saved: problems.append(f'manifest missing test {name}'); continue
   sm=saved[name]
   for key in ('expect_cause','check_gp'):
    if sm.get(key)!=row.get(key): problems.append(f'{name}: saved manifest {key} differs from source manifest')
   rel=os.path.relpath(hexpath,ROOT).replace('\\','/')
   if sm.get('hexpath')!=rel: problems.append(f'{name}: saved image path mismatch expected={rel} actual={sm.get("hexpath")}')
   missing=[path for path in (hexpath,refpath,rtlpath,logpath) if not os.path.isfile(path)]
   if missing:
    for path in missing: print(f'LEGACY_ARTIFACT_MISSING {path}',flush=True)
    problems.extend(f'{name}: missing {path}' for path in missing); continue
   try:
    mem=rv32_asm.assemble(open(os.path.join(srcdir,name+'.s'),encoding='utf-8').read())
    expected_hex=rv32_asm.to_hex(mem)
    words=[mem.get(4*i,0) for i in range(max(mem)//4+1)]
    cause,regs,tr,foot,oob,_=rv32i_iss.run(words)
    expected_trace='\n'.join(tr+foot)+'\n'
   except Exception as exc:
    problems.append(f'{name}: current source/reference generation error {exc}'); continue
   if normalized(open(hexpath,encoding='ascii').read())!=normalized(expected_hex): problems.append(f'{name}: saved image differs from current assembly')
   if cause!=int(row['expect_cause']) or oob or (row['check_gp']=='1' and regs[3]!=1): problems.append(f'{name}: current ISS cause expected={row["expect_cause"]} actual={cause} oob={oob} gp={regs[3]:08x}')
   if normalized(open(refpath,encoding='ascii').read())!=normalized(expected_trace): problems.append(f'{name}: saved ISS trace differs from current source/reference')
   actual=normalized(open(rtlpath,encoding='ascii').read())
   if actual!=normalized(expected_trace): problems.append(f'{name}: saved RTL retirement trace differs from current ISS')
   result=open(logpath,encoding='utf-8',errors='replace').read()
   if result.count('TEST_RESULT: PASS')!=1 or 'TEST_RESULT: FAIL' in result or 'FATAL' in result.upper(): problems.append(f'{name}: saved simulator log lacks one clean PASS')
 if expected_count!=209 or len(saved)!=expected_count: problems.append(f'legacy inventory mismatch source={expected_count} saved={len(saved)}')
 if problems: raise RuntimeError('saved legacy validation failed: '+'; '.join(problems))
 print(f'STAGE4_3_RESUME_LEGACY_VALIDATION PASS tests={expected_count} traces=209 clean_pass_logs=209 source_consistent=209',flush=True)
def run_resume_c_cases(out_dir,xdir,rows):
 total=len(rows)
 for index,row in enumerate(rows,1):
  name=row['name']; hexp=c_image_path(out_dir,name)
  trace=os.path.join(out_dir,name+'.rv32imc.resume_'+STAMP+'.trace')
  simlog=trace+'.run.log'
  print(f'[resume rv32imc {index}/{total}] {name}',flush=True)
  plus=[sv_file_plusarg('HEX',hexp),sv_file_plusarg('TRACE',trace),'+EXPECT_CAUSE='+row['expect_cause'],'+CHECK_GP='+row['check_gp']]
  args=['xsim','core1','--runall','--log',simlog,*sum((['--testplusarg',v[1:]] for v in plus),[])]
  output=run(args,cwd=xdir)
  combined=open(simlog,encoding='utf-8',errors='replace').read() if os.path.isfile(simlog) else output
  if combined.count('TEST_RESULT: PASS')!=1 or 'TEST_RESULT: FAIL' in combined or not os.path.isfile(trace): raise RuntimeError(f'{name}: resumed simulator result/trace invalid')
  actual=normalized(open(trace,encoding='ascii').read()); expected=normalized(open(c_reference_path(out_dir,name),encoding='ascii').read())
  if actual!=expected: raise RuntimeError(f'{name}: resumed RTL/reference trace mismatch')
 print(f'STAGE4_3_RESUME_C PASS tests={total} trace_matches={total}',flush=True)
def main():
 global LAUNCH_DIAG,COMSPEC_PATH
 if RESUME and SIM!='xsim': raise RuntimeError('--resume is supported only for saved XSim outputs')
 required=['xvlog','xelab','xsim'] if SIM=='xsim' else ['verilator','make']
 miss=[]
 if not os.path.isfile(sys.executable): miss.append(f'active Python interpreter={sys.executable}')
 for tool in required:
  path=shutil.which(tool)
  if path is None or not os.path.isfile(path): miss.append(tool)
  else: TOOLS[tool]=os.path.abspath(path)
 if miss: raise RuntimeError('missing required tools: '+', '.join(miss))
 if SIM=='verilator' and not any(shutil.which(x) for x in ('g++','clang++','c++')): raise RuntimeError('missing C++ compiler')
 if RESUME:
  if not os.path.isdir(OUT): raise RuntimeError(f'resume output directory does not exist: {OUT}')
  if os.path.exists(REPORT): raise RuntimeError(f'resume report path already exists: {REPORT}')
 else:
  if os.path.exists(OUT) or os.path.exists(REPORT): raise RuntimeError('output/report is not fresh')
  os.makedirs(OUT)
 os.makedirs(os.path.dirname(REPORT),exist_ok=True)
 LAUNCH_DIAG=os.path.join(OUT,'launch_diagnostics.log')
 print('TOOL PREFLIGHT PASS '+SIM+'; PYTHON='+sys.executable+'; '+('RESUME_OUTPUT ' if RESUME else 'FRESH_OUTPUT ')+OUT,flush=True)
 if SIM=='xsim':
  for tool in ('xvlog','xelab','xsim'): print(f'TOOL {tool}={TOOLS[tool]}',flush=True)
  if any(os.path.splitext(TOOLS[t])[1].lower() in ('.bat','.cmd') for t in ('xvlog','xelab','xsim')):
   COMSPEC_PATH=os.environ.get('COMSPEC') or shutil.which('cmd.exe')
   if not COMSPEC_PATH or not os.path.isfile(COMSPEC_PATH): raise RuntimeError(f'Vivado batch launcher requires a valid COMSPEC/cmd.exe path; resolved={COMSPEC_PATH!r}')
 py=[sys.executable]
 if RESUME:
  xdir=os.path.join(OUT,'xsim'); vectors=os.path.join(OUT,'vectors.txt'); unitlog=os.path.join(OUT,'unit.log')
  if not os.path.isfile(vectors): raise RuntimeError(f'missing saved decompressor vectors: {vectors}')
  if not os.path.isfile(unitlog): raise RuntimeError(f'missing saved decompressor simulator log: {unitlog}')
  check=run(py+[os.path.join(HERE,'check_stage4_2_sim_log.py'),unitlog],log=os.path.join(OUT,'unit_check_resume.log'))
  if 'RV32C_SIM_LOG_CHECK PASS terminal_markers=1 pass_markers=1 halfwords=65536 mismatches=0 anchors=16' not in check: raise RuntimeError('saved decompressor unit result failed strict log validation')
  crows=validate_c_artifacts(OUT)
  validate_saved_legacy(OUT)
  snapshot=os.path.join(xdir,'xsim.dir','core1')
  if not os.path.isdir(snapshot): raise RuntimeError(f'missing saved C-enabled XSim snapshot: {snapshot}')
  run_resume_c_cases(OUT,xdir,crows)
  with open(REPORT,'w',newline='\n') as f:
   f.write('Simulator: XSim (resume from saved output)\n')
   f.write('legacy_c_disabled=209 validated from source, image, ISS trace, RTL trace, and PASS logs\n')
   f.write('rv32imc=12 rerun and matched against current-source ISS references\n')
   f.write('STAGE4_3_GOLDEN_XSIM_RESUME PASS legacy=209 rv32imc=12\n')
  print(open(REPORT).read(),flush=True)
  return
 legacy_prep=run(py+[os.path.join(HERE,'prepare_stage5.py'),OUT],log=os.path.join(OUT,'legacy_prepare.log'))
 if 'STAGE3_5_PREPARED tests=209' not in legacy_prep: raise RuntimeError('209-case legacy preparation marker missing')
 vector_prep=run(py+[os.path.join(HERE,'generate_stage4_2_vectors.py'),os.path.join(OUT,'vectors.txt')],log=os.path.join(OUT,'vectors.log'))
 if 'RV32C_VECTOR_GENERATION PASS halfwords=65536 oracle_mismatches=0' not in vector_prep: raise RuntimeError('independent vector-generation marker missing')
 c_prep=run(py+[os.path.join(HERE,'prepare_stage4_3.py'),OUT],log=os.path.join(OUT,'c_prepare.log'))
 if 'STAGE4_3_ASSEMBLY_PREFLIGHT PASS programs=12 errors=0' not in c_prep: raise RuntimeError('aggregate assembly preflight did not pass')
 if 'STAGE4_3_C_PREPARED tests=12 iss_failures=0' not in c_prep: raise RuntimeError('C software preparation marker missing')
 validate_c_artifacts(OUT)
 xdir=os.path.join(OUT,'xsim'); os.makedirs(xdir)
 if SIM=='xsim':
  absfl=os.path.join(OUT,'stage4_3_rtl_abs.f')
  with open(os.path.join(ROOT,'scripts/simulation/stage4_3_rtl.f')) as src,open(absfl,'w',newline='\n') as dst:
   for line in src:
    if line.strip(): dst.write(os.path.join(ROOT,line.strip().replace('/',os.sep))+'\n')
  run(['xvlog','-sv','-f',absfl,os.path.join(ROOT,'verification/environment/tb_rv_core.sv')],cwd=xdir)
  run(['xvlog','-sv',os.path.join(ROOT,'verification/environment/tb_rv32c_decompressor.sv')],cwd=xdir)
  run(['xelab','-debug','off','tb_rv_core','-s','core0'],cwd=xdir)
  run(['xelab','-debug','off','tb_rv_core','-s','core1','-generic_top','ENABLE_C=1'],cwd=xdir)
  core0=('xsim','core0'); core1=('xsim','core1')
 else:
  objs=[]
  for top,name,files,gen in [('tb_rv_core','core0',['-f','scripts/simulation/stage4_3_rtl.f','verification/environment/tb_rv_core.sv'],[]),('tb_rv_core','core1',['-f','scripts/simulation/stage4_3_rtl.f','verification/environment/tb_rv_core.sv'],['-GENABLE_C=1']),('tb_rv32c_decompressor','unit',['rtl/decoder/rv32c_decompressor.sv','verification/environment/tb_rv32c_decompressor.sv'],[])]:
   od=os.path.join(OUT,'obj_'+name); os.makedirs(od)
   run(['verilator','-sv','--binary','--timing','-Wno-fatal','-Wno-lint','-Wno-style','--top-module',top,*gen,*files,'-Mdir',od,'-o',name],log=os.path.join(OUT,name+'.build.log')); objs.append(os.path.join(od,name))
  core0=('verilator',objs[0]); core1=('verilator',objs[1]); unit=('verilator',objs[2])
 if SIM=='xsim': run(['xvlog','-sv',os.path.join(ROOT,'verification/environment/tb_rv32c_decompressor.sv')],cwd=xdir); run(['xelab','-debug','off','tb_rv32c_decompressor','-s','unit'],cwd=xdir); unit=('xsim','unit')
 # Exhaustive decompressor vectors and strict terminal-marker validation.
 vectors=os.path.abspath(os.path.join(OUT,'vectors.txt'))
 if not os.path.isfile(vectors): raise RuntimeError(f'missing decompressor vector file before simulation: {vectors}')
 vector_arg=sv_file_plusarg('VECTORS',vectors)
 if unit[0]=='verilator': log=run([unit[1],vector_arg],log=os.path.join(OUT,'unit.log'))
 else: run(['xsim','unit','--runall','--log',os.path.join(OUT,'unit.log'),'--testplusarg',vector_arg[1:]],cwd=xdir); log=open(os.path.join(OUT,'unit.log')).read()
 run(py+[os.path.join(HERE,'check_stage4_2_sim_log.py'),os.path.join(OUT,'unit.log')],log=os.path.join(OUT,'unit_check.log'))
 total=0
 for mode,exe,man,edir in [('legacy',core0,os.path.join(OUT,'manifest_all.csv'),os.path.join(OUT,'iss')),('rv32imc',core1,os.path.join(OUT,'c_manifest.csv'),os.path.join(OUT,'c_iss'))]:
  rows=list(csv.DictReader(open(man,newline='')))
  if len(rows)!=(209 if mode=='legacy' else 12): raise RuntimeError(f'{mode} manifest size {len(rows)} unexpected')
  for i,row in enumerate(rows,1):
   name=row['name']; total+=1; trace=os.path.join(OUT,name+'.'+mode+'.trace'); hexp=os.path.join(ROOT,row['hexpath'])
   print(f'[{mode} {i}/{len(rows)}] {name}',flush=True)
   if not os.path.isfile(hexp): raise RuntimeError(f'{mode}/{name}: missing hex image before simulation: {hexp}')
   plus=[sv_file_plusarg('HEX',hexp),sv_file_plusarg('TRACE',trace),'+EXPECT_CAUSE='+row['expect_cause'],'+CHECK_GP='+row['check_gp']]
   if exe[0]=='verilator': out=run([exe[1],*plus],log=trace+'.run.log')
   else: run(['xsim',exe[1],'--runall','--log',trace+'.run.log',*sum((['--testplusarg',v[1:]] for v in plus),[])],cwd=xdir); out=open(trace+'.run.log').read()
   if out.count('TEST_RESULT: PASS')!=1 or 'TEST_RESULT: FAIL' in out: raise RuntimeError(name+': terminal result invalid')
   exp_path=os.path.join(edir,name+'.iss.trace') if mode=='legacy' else c_reference_path(OUT,name)
   exp=open(exp_path,encoding='ascii').read(); act=open(trace,encoding='ascii').read()
   if act!=exp: raise RuntimeError(name+': RTL/ISS trace mismatch')
 print('STAGE4_3_TRACE_COMPARE PASS legacy=209 rv32imc=12 total=221',flush=True)
 with open(REPORT,'w',newline='\n') as f:
  f.write(f'Simulator: {SIM}\nlegacy_c_disabled={len(list(csv.DictReader(open(os.path.join(OUT,"manifest_all.csv"),newline=""))))}\nrv32imc={len(list(csv.DictReader(open(os.path.join(OUT,"c_manifest.csv"),newline=""))))}\nrtl_vs_iss={total}\n')
  f.write(f'STAGE4_3_GOLDEN_{SIM.upper()} PASS rtl_vs_iss={total}\n')
 print(open(REPORT).read())
try: main()
except Exception as e: print('STAGE4_3 FAIL: '+str(e),file=sys.stderr); raise SystemExit(1)
