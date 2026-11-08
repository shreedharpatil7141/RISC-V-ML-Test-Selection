#!/usr/bin/env python3
"""Check Stage 3.4 golden/ISS traces, fixed divider timing, protocol counters, and coverage."""
import csv,os,sys,time
HERE=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,HERE)
import stage4_lib as L
sim,label=sys.argv[1],sys.argv[2]
rows=list(csv.DictReader(open(os.path.join(sim,'manifest_all.csv'),newline='')))
expected={r['name']:r for r in csv.DictReader(open(os.path.join(sim,'expected.csv'),newline=''))}
unit_lines,unit_ok=L.unit_results(sim)
test_lines,test_ok,failed,covered=L.evaluate(sim,rows,expected,label)
result=unit_ok and test_ok
out=[f"Stage 3.4 iterative M regression  {time.strftime('%Y-%m-%d %H:%M:%S')}  simulator={label}",'']
out+=unit_lines+['']+test_lines
out.append(f"STAGE3_4_REGRESSION_{label.upper()} {'PASS' if result else 'FAIL'}")
report='\n'.join(out)+'\n'; print(report,end='')
if len(sys.argv)>3:
    os.makedirs(os.path.dirname(os.path.abspath(sys.argv[3])),exist_ok=True)
    open(sys.argv[3],'w',newline='\n').write(report)
sys.exit(0 if result else 1)
