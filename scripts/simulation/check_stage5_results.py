#!/usr/bin/env python3
"""Stage 3.5 checker preserving Stage 3.4 trace, timing, protocol, and unit gates."""
import csv, os, sys, time
HERE=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,HERE)
import stage4_lib, stage5_coverage

sim,label,report=sys.argv[1],sys.argv[2],sys.argv[3]
gate=sys.argv[4] if len(sys.argv)>4 else 'stage3_5'
if gate not in ('stage3_5','stage3_7'):
    raise SystemExit(f'unsupported report gate: {gate}')
try:
    rows=list(csv.DictReader(open(os.path.join(sim,'manifest_all.csv'),newline='')))
    expected={r['name']:r for r in csv.DictReader(open(os.path.join(sim,'expected.csv'),newline=''))}
    names={r['name'] for r in rows}
    if len(rows)!=209 or len(expected)!=209 or len(names)!=209 or set(expected)!=names:
        raise ValueError(f'expected 209 unique manifest and performance rows, found {len(rows)} / {len(expected)}')
except (OSError,ValueError,KeyError) as ex:
    report_text=f'Stage {gate.replace("_", ".")} M-extension regression simulator={label}\nPREPARATION/INPUT ERROR: {ex}\n{gate.upper()}_REGRESSION_{label.upper()} FAIL\n'
    print(report_text,end=''); os.makedirs(os.path.dirname(os.path.abspath(report)),exist_ok=True)
    open(report,'w',newline='\n').write(report_text); sys.exit(1)

unit_lines,unit_ok=stage4_lib.unit_results(sim)
system_lines,system_ok,failures,covered=stage4_lib.evaluate(sim,rows,expected,label)
coverage_lines,coverage_ok,coverage_errors,coverage_misses=stage5_coverage.evaluate(sim,rows)
malformed_cov=[]
for row in rows:
    text=stage4_lib.L.read(os.path.join(sim,row['name']+'.pipe.log'))
    parsed=stage4_lib.L.parse_log(text)
    cov=parsed.get('cov')
    if cov is None or len(cov)!=16 or any(v<0 for v in cov):
        malformed_cov.append(f"{row['name']}: missing or malformed 16-event pipeline COV vector")
if malformed_cov:
    coverage_errors.extend(malformed_cov); coverage_ok=False
    coverage_lines=[(f'Coverage data errors: {len(coverage_errors)}' if x.startswith('Coverage data errors:') else x) for x in coverage_lines]
    coverage_lines += ['Additional pipeline coverage format errors:']+[f'ERROR: {e}' for e in malformed_cov]
passed=unit_ok and system_ok and coverage_ok
out=[f'Stage 3.5 M-extension coverage regression  {time.strftime("%Y-%m-%d %H:%M:%S")}  simulator={label}','']
out+=unit_lines+['']+system_lines+['']+coverage_lines
out += ['',f'SYSTEM_REGRESSION {"PASS" if system_ok else "FAIL"}',
        f'UNIT_REGRESSION {"PASS" if unit_ok else "FAIL"}',
        f'M_COVERAGE_DICTIONARY {"PASS" if coverage_ok else "FAIL"} bins_hit={len(stage5_coverage._bins())-len(coverage_misses)}/{len(stage5_coverage._bins())} missing={len(coverage_misses)} data_errors={len(coverage_errors)}',
        f'{gate.upper()}_REGRESSION_{label.upper()} {"PASS" if passed else "FAIL"}']
report_text='\n'.join(out)+'\n'
print(report_text,end=''); os.makedirs(os.path.dirname(os.path.abspath(report)),exist_ok=True)
open(report,'w',newline='\n').write(report_text)
sys.exit(0 if passed else 1)
