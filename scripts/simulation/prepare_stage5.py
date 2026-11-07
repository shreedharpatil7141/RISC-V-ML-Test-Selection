#!/usr/bin/env python3
"""Stage 3.5 preparation: Stage 3.4 suites plus an independent M operand side channel."""
import csv, os, sys
HERE=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,HERE)
from rv32_asm import assemble,to_hex
import rv32i_iss,stage2_lib
ROOT=os.path.normpath(os.path.join(HERE,'..','..'))
OUT=sys.argv[1] if len(sys.argv)>1 else os.path.join(ROOT,'sim_out_stage3_5')
SUITES=[('rv32i','rv32i'),('pipeline','pipeline'),('pipeline_m','pipeline_m'),
        ('m_extension','m_extension'),('pipeline_div','pipeline_div'),
        ('pipeline_div_coverage','pipeline_div_coverage')]
os.makedirs(os.path.join(OUT,'iss'),exist_ok=True); os.makedirs(os.path.join(OUT,'hex'),exist_ok=True)
bad=total=0; seen=set(); suite_counts={}
with open(os.path.join(OUT,'manifest_all.csv'),'w',newline='') as mf, \
     open(os.path.join(OUT,'expected.csv'),'w',newline='') as ef:
    man=csv.writer(mf,lineterminator='\n'); man.writerow(['name','expect_cause','check_gp','hexpath'])
    exp=csv.writer(ef,lineterminator='\n'); exp.writerow(['name','suite','iss_cause','instret','model_stalls','model_redirects','n_div','exp_stalls','exp_redirects'])
    for suite,folder in SUITES:
        d=os.path.join(ROOT,'tests','directed',folder)
        rows=list(csv.DictReader(open(os.path.join(d,'manifest.csv'),newline='')))
        suite_counts[suite]=len(rows)
        pp=os.path.join(d,'expected_perf.csv')
        perf={r['name']:(r['exp_stalls'],r['exp_redirects']) for r in csv.DictReader(open(pp,newline=''))} if os.path.isfile(pp) else {}
        for row in rows:
            name=row['name']
            if name in seen: raise SystemExit(f'duplicate test name across suites: {name}')
            seen.add(name); total+=1
            src=os.path.join(d,name+'.s')
            mem=assemble(open(src,encoding='utf-8').read())
            words=[mem.get(4*i,0) for i in range(max(mem)//4+1)]
            m_events=[]
            cause,regs,trace,footer,oob,_=rv32i_iss.run(words,m_events=m_events)
            trace_text='\n'.join(trace+footer)+'\n'
            open(os.path.join(OUT,'iss',name+'.iss.trace'),'w',newline='\n').write(trace_text)
            side=os.path.join(OUT,'iss',name+'.iss.m.tsv')
            with open(side,'w',newline='') as sf:
                sw=csv.writer(sf,delimiter='\t',lineterminator='\n')
                sw.writerow(['pc','insn','op','rd','rs1','rs2','a','b','result'])
                sw.writerows((f'{pc:08x}',f'{insn:08x}',op,rd,rs1,rs2,f'{a:08x}',f'{b:08x}',f'{result:08x}')
                             for pc,insn,op,rd,rs1,rs2,a,b,result in m_events)
            check_gp=row['check_gp']
            if cause!=int(row['expect_cause']) or (check_gp=='1' and regs[3]!=1) or oob:
                bad+=1; print(f'ISS expectation mismatch: {name} cause={cause} gp={regs[3]:#x} oob={oob}')
            inst,stalls,redirects=stage2_lib.perf_model('\n'.join(trace+footer),words)
            n_div=sum(1 for _,insn in stage2_lib.parse_trace(trace_text)[0]
                      if (insn&0x7f)==0x33 and ((insn>>25)&0x7f)==1 and ((insn>>12)&7)>=4)
            exp_stall,exp_redirect=perf.get(name,('-1','-1'))
            hexf=os.path.join(OUT,'hex',name+'.hex'); open(hexf,'w',newline='\n').write(to_hex(mem))
            relhex=os.path.relpath(hexf,ROOT).replace('\\','/')
            man.writerow([name,row['expect_cause'],check_gp,relhex])
            exp.writerow([name,suite,cause,inst,stalls,redirects,n_div,exp_stall,exp_redirect])
if suite_counts!={'rv32i':106,'pipeline':63,'pipeline_m':8,'m_extension':22,'pipeline_div':8,'pipeline_div_coverage':2}:
    print(f'suite size mismatch: {suite_counts}'); bad+=1
if total!=209: print(f'expected 209 total tests, found {total}'); bad+=1
print(f'STAGE3_5_PREPARED tests={total} suites={suite_counts} iss_mismatches={bad} out={OUT}')
sys.exit(1 if bad else 0)
