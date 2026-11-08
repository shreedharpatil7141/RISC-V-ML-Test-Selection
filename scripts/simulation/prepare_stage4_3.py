#!/usr/bin/env python3
"""Prepare C-mode images/reference traces; legacy cases come from Stage 3.5 prep."""
import csv, os, re, sys
HERE=os.path.dirname(os.path.abspath(__file__)); ROOT=os.path.normpath(os.path.join(HERE,'..','..'))
sys.path.insert(0,HERE)
import rv32c_asm, rv32imc_iss
from stage4_3_artifacts import c_image_path, c_reference_path
OUT=sys.argv[1]
os.makedirs(os.path.join(OUT,'c_hex'),exist_ok=True); os.makedirs(os.path.join(OUT,'c_iss'),exist_ok=True)
suite=os.path.join(ROOT,'tests','directed','rv32imc')
rows=list(csv.DictReader(open(os.path.join(suite,'manifest.csv'),newline='')))
assembled=[]; errors=[]
for row in rows:
    name=row['name']; source=open(os.path.join(suite,name+'.s'),encoding='utf-8').read()
    try:
        image=rv32c_asm.assemble_bytes(source,c_enabled=True)
        assembled.append((row,image,rv32c_asm.to_words(image)))
    except Exception as exc:
        match=re.search(r'line\s+(\d+)',str(exc),re.IGNORECASE)
        line=match.group(1) if match else 'unknown'
        errors.append((name,line,str(exc)))
        print(f'ASSEMBLY_ERROR file={name}.s line={line} detail={exc}',flush=True)
if errors:
    print(f'STAGE4_3_ASSEMBLY_PREFLIGHT FAIL programs={len(rows)} errors={len(errors)}',flush=True)
    raise SystemExit(1)
print(f'STAGE4_3_ASSEMBLY_PREFLIGHT PASS programs={len(rows)} errors=0',flush=True)
with open(os.path.join(OUT,'c_manifest.csv'),'w',newline='') as mf:
    w=csv.writer(mf,lineterminator='\n'); w.writerow(['name','expect_cause','check_gp','hexpath'])
    iss_failures=[]
    for index,(row,image,words) in enumerate(assembled,1):
        name=row['name']
        hp=c_image_path(OUT,name)
        open(hp,'w',newline='\n').write(rv32c_asm.to_hex(image))
        expected=int(row['expect_cause'])
        try:
            cause,regs,trace,footer,oob,n=rv32imc_iss.run(words,c_enabled=True)
            if cause!=expected or oob:
                iss_failures.append((name,expected,cause,f'oob={oob}'))
                print(f'ISS_CASE_FAIL file={name}.s expected_cause={expected} actual_cause={cause} oob={oob}',flush=True)
        except Exception as exc:
            cause='ERROR'; trace=[]; footer=[]; n=0
            iss_failures.append((name,expected,cause,str(exc)))
            print(f'ISS_CASE_FAIL file={name}.s expected_cause={expected} actual_cause=ERROR detail={exc}',flush=True)
        tp=c_reference_path(OUT,name)
        open(tp,'w',newline='\n').write('TRACE_V2 RV32IMC pc raw_insn ilen_bytes expanded_insn rd rdval st_size st_addr st_data\n'+'\n'.join(trace+footer)+'\n')
        w.writerow([name,row['expect_cause'],row['check_gp'],os.path.relpath(hp,ROOT).replace('\\','/')])
        print(f'PREPARED C [{index}/{len(rows)}] {name} cause={cause} instret={n}',flush=True)
if iss_failures:
    print(f'STAGE4_3_ISS_PREFLIGHT FAIL cases={len(rows)} failures={len(iss_failures)}',flush=True)
    for name,expected,actual,detail in iss_failures:
        print(f'ISS_FAILURE_SUMMARY file={name}.s expected_cause={expected} actual_cause={actual} detail={detail}',flush=True)
    raise SystemExit(1)
print(f'STAGE4_3_ISS_PREFLIGHT PASS cases={len(rows)} failures=0',flush=True)
print(f'STAGE4_3_C_PREPARED tests={len(rows)} iss_failures=0',flush=True)
