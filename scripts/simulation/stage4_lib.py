#!/usr/bin/env python3
"""Stage 3.4 performance and trace checks; load-use stalls exclude md_busy cycles."""
import os,re,sys
HERE=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,HERE)
import stage2_lib as L
RE_MD=re.compile(r"MD_STATS starts=(\d+) dones=(\d+) busy_cycles=(\d+) aborts_started=(\d+)")

def evaluate(sim_dir,rows,expected,label):
    lines=[]; failures=0; cov=[0]*16; cov_tests=[0]*16; suites={}
    lines.append(f"{'test':38s} s1 pipe iss gold perf md starts/dones busy abort cycles")
    for row in rows:
        name=row['name']; e=expected[name]; ndiv=int(e['n_div'])
        iss=L.read(os.path.join(sim_dir,'iss',name+'.iss.trace'))
        st=L.read(os.path.join(sim_dir,name+'.s1.trace')); pt=L.read(os.path.join(sim_dir,name+'.pipe.trace'))
        s1=L.parse_log(L.read(os.path.join(sim_dir,name+'.s1.log')))
        pipe_text=L.read(os.path.join(sim_dir,name+'.pipe.log')); p=L.parse_log(pipe_text)
        md=RE_MD.search(pipe_text or '')
        s1_ok=s1['pass'] and st is not None
        pipe_ok=p['pass'] and pt is not None and p.get('assert_fail',1)==0
        iss_eq=pt is not None and iss is not None and pt==iss
        gold_eq=pt is not None and st is not None and pt==st
        stalls=int(e['model_stalls']); redirects=int(e['model_redirects']); instret=int(e['instret'])
        perf_ok=('stalls' in p and p['stalls']==stalls and p['redirects']==redirects and
                 p.get('instret')==instret and p['cycles']==instret+L.CYCLE_CONST+stalls+2*redirects+33*ndiv)
        es,er=int(e['exp_stalls']),int(e['exp_redirects'])
        if es>=0 and p.get('stalls')!=es: perf_ok=False
        if er>=0 and p.get('redirects')!=er: perf_ok=False
        md_ok=False; starts=dones=busy=aborts=-1
        if md:
            starts,dones,busy,aborts=map(int,md.groups())
            md_ok=starts==ndiv and dones==ndiv and busy==33*ndiv and aborts==0
        ok=s1_ok and pipe_ok and iss_eq and gold_eq and perf_ok and md_ok
        failures+=not ok
        sc=suites.setdefault(e['suite'],[0,0]); sc[0 if ok else 1]+=1
        if 'cov' in p:
            for i,v in enumerate(p['cov']): cov[i]+=v; cov_tests[i]+=int(v>0)
        lines.append(f"{name:38s} {'ok' if s1_ok else 'FAIL':3s} {'ok' if pipe_ok else 'FAIL':4s} "
                     f"{'ok' if iss_eq else 'DIFF':4s} {'ok' if gold_eq else 'DIFF':4s} "
                     f"{'ok' if perf_ok else 'FAIL':4s} {'ok' if md_ok else 'FAIL':4s} "
                     f"{starts:3d}/{dones:<3d} {busy:5d} {aborts:5d} {p.get('cycles',-1):7d}"+
                     ('' if ok else f" [n_div={ndiv} expected md={ndiv}/{ndiv}/{33*ndiv}/0 stalls={stalls} redir={redirects} instret={instret}]") )
    covered=sum(v!=0 for v in cov)
    lines += ['',f"Pipeline event coverage ({label}):"]
    for i,event in enumerate(L.EVENTS):
        lines.append(f"  {i:2d} {event:20s} hits={cov[i]:8d} tests={cov_tests[i]:3d} {'COVERED' if cov[i] else 'NOT COVERED'}")
    lines.append(f"Coverage events hit: {covered}/16")
    for suite,(passed,failed) in sorted(suites.items()): lines.append(f"SUITE {suite}: {passed} passed, {failed} failed, {passed+failed} total")
    lines.append(f"TOTAL: {len(rows)-failures} passed, {failures} failed, {len(rows)} total")
    return lines,failures==0 and covered==16,failures,covered

def unit_results(sim_dir):
    specs=[('units_s1.log',r"UNIT_RESULT: (PASS|FAIL) checks=(\d+) errors=(\d+)",'Stage 1'),
           ('units_md.log',r"MD_UNIT_RESULT: (PASS|FAIL) checks=(\d+) errors=(\d+)",'M arithmetic'),
           ('units_decoder_m.log',r"DECODER_M_RESULT: (PASS|FAIL) checks=(\d+) errors=(\d+)",'M decoder'),
           ('units_pipe.log',r"PIPE_UNIT_RESULT: (PASS|FAIL) checks=(\d+) errors=(\d+)",'Pipeline'),
           ('units_div_iter.log',r"DIV_ITER_RESULT: (PASS|FAIL) W8_checks=(\d+) W8_errors=(\d+) W32_checks=(\d+) W32_errors=(\d+)",'Divider'),
           ('units_md_exec.log',r"MD_EXEC_RESULT: (PASS|FAIL) checks=(\d+) errors=(\d+) abort_positions=(\d+)",'M wrapper')]
    out=[]; ok=True
    for filename,pattern,label in specs:
        text=L.read(os.path.join(sim_dir,filename)) or ''; m=re.search(pattern,text)
        if not m: out.append(f"{label} unit: NO RESULT ({filename})"); ok=False; continue
        vals=m.groups(); good=vals[0]=='PASS'
        if label=='Divider': good=good and int(vals[1])==262144 and int(vals[2])==0 and int(vals[3])==1600 and int(vals[4])==0
        elif label=='M wrapper': good=good and int(vals[1])==49 and int(vals[2])==0 and int(vals[3])==34
        else: good=good and int(vals[2])==0
        if label=='M arithmetic': good=good and int(vals[1])==1152
        if label=='M decoder': good=good and int(vals[1])==1024
        if label=='Pipeline': good=good and int(vals[1])==624576
        out.append(f"{label} unit: "+' '.join(vals)); ok &= good
    return out,ok
