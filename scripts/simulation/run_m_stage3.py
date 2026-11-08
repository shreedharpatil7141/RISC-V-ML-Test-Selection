#!/usr/bin/env python3
"""Run the directed RV32M suite on rv_core_single and compare retirement traces to the ISS."""
import csv, os, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, '..', '..'))
SIM = os.environ.get('SIM_DIR', os.path.join(ROOT, 'sim_out_m_stage3'))
sys.path.insert(0, HERE)
from rv32_asm import assemble, to_hex
import rv32i_iss
def sh(cmd): return subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
def main():
    os.makedirs(SIM, exist_ok=True)
    build = sh(['verilator','-sv','--binary','--timing','-Wno-fatal','-Wno-lint','-Wno-style','-f',os.path.join(HERE,'stage1_rtl.f'),
                'verification/environment/tb_rv_core.sv','--top-module','tb_rv_core','-Mdir',os.path.join(SIM,'obj_core'),'-o','Vcore'])
    if build.returncode: print(build.stdout,build.stderr); return 1
    rows = list(csv.DictReader(open(os.path.join(ROOT,'tests','directed','m_extension','manifest.csv'))))
    passed = 0
    for row in rows:
        name=row['name']; d=os.path.join(ROOT,'tests','directed','m_extension')
        mem=assemble(open(os.path.join(d,name+'.s')).read()); hexf=os.path.join(SIM,name+'.hex')
        open(hexf,'w').write(to_hex(mem)); words=[mem.get(4*i,0) for i in range(max(mem)//4+1)]
        cause,x,tr,foot,oob,cnt=rv32i_iss.run(words); expected='\n'.join(tr+foot)+'\n'; trace=os.path.join(SIM,name+'.rtl.trace')
        exe=os.path.join(SIM,'obj_core','Vcore')
        r=sh([exe,f'+HEX={hexf}',f'+TRACE={trace}',f"+EXPECT_CAUSE={row['expect_cause']}",f"+CHECK_GP={row['check_gp']}"])
        result=next((l for l in r.stdout.splitlines() if l.startswith('TEST_RESULT')), '')
        ok=result.startswith('TEST_RESULT: PASS') and os.path.exists(trace) and open(trace).read()==expected and cause==int(row['expect_cause']) and not oob
        passed += ok
        print(f"{name}: {'PASS' if ok else 'FAIL'}" + ('' if ok else f"; RTL={result!r} ISS_cause={cause} oob={oob}"))
    print(f"M RTL vs ISS: {passed}/{len(rows)}")
    return 0 if passed==len(rows) else 1
if __name__=='__main__': sys.exit(main())
