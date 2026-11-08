#!/usr/bin/env python3
"""Check fixed Stage 4 C bins from independent ISS and RTL sidecar evidence."""
import collections, datetime, re, sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
FAMILIES=('ADDI4SPN','LW','SW','NOP','ADDI','JAL','LI','ADDI16SP','LUI','SRLI','SRAI','ANDI','SUB','XOR','OR','AND','J','BEQZ','BNEZ','SLLI','LWSP','JR','MV','EBREAK','JALR','ADD','SWSP')
PIPE_EVENTS=16

def c_family(raw):
    q=raw&3; f3=(raw>>13)&7; rd=(raw>>7)&31; rs2=(raw>>2)&31; imm6=((raw>>12)&1)<<5|((raw>>2)&31)
    if q==0: return {(0,0):'ADDI4SPN',(0,2):'LW',(0,6):'SW'}.get((q,f3))
    if q==1:
        if f3==0: return 'NOP' if rd==0 and imm6==0 else 'ADDI'
        if f3==1: return 'JAL'
        if f3==2: return 'LI'
        if f3==3: return 'ADDI16SP' if rd==2 else 'LUI'
        if f3==4:
            sel=(raw>>10)&3
            if sel==0:return 'SRLI'
            if sel==1:return 'SRAI'
            if sel==2:return 'ANDI'
            return {0:'SUB',1:'XOR',2:'OR',3:'AND'}.get((raw>>5)&3)
        if f3==5:return 'J'
        if f3==6:return 'BEQZ'
        if f3==7:return 'BNEZ'
    if q==2:
        if f3==0:return 'SLLI'
        if f3==2:return 'LWSP'
        if f3==4:
            if not (raw>>12)&1: return 'JR' if rs2==0 else 'MV'
            return 'EBREAK' if rd==0 and rs2==0 else ('JALR' if rs2==0 else 'ADD')
        if f3==6:return 'SWSP'
    return None

def is_hint(raw):
    q=raw&3; f3=(raw>>13)&7; rd=(raw>>7)&31; rs2=(raw>>2)&31; imm=((raw>>12)&1)<<5|((raw>>2)&31)
    if q==1 and f3==0: return (rd==0 and imm!=0) or (rd!=0 and imm==0)
    if q==1 and f3==2:return rd==0
    if q==1 and f3==3 and rd==0:return ((raw>>12)&1 or ((raw>>2)&31))!=0
    if q==1 and f3==4 and ((raw>>10)&3) in (0,1):return (raw&31)==0
    if q==2 and f3==0:return rd==0 or (raw&0x7c)==0
    if q==2 and f3==4:return rd==0 and rs2!=0
    return False

def _parse_trace(path):
    retired=[]; stop=None
    for line in path.read_text(encoding='ascii').splitlines():
        p=line.split()
        if p and p[0]=='I' and len(p)==10:
            retired.append({'pc':int(p[1],16),'raw':int(p[2],16),'length':int(p[3]),'expanded':int(p[4],16),'rd':int(p[5]),'rdval':int(p[6],16)})
        elif p and p[0]=='STOP' and len(p)==5:
            stop={'pc':int(p[1],16),'raw':int(p[2],16),'length':int(p[3]),'cause':int(p[4])}
    if stop is None: raise ValueError(f'{path}: missing STOP row')
    return retired,stop

def _parse_sidecar(path):
    ev=collections.defaultdict(set); holds=[]; issues=[]
    for line in path.read_text(encoding='ascii').splitlines():
        p=line.split()
        if not p: continue
        if p[0]=='C' and p[1] in ('ATTEMPT','RETIRE','FAULT','SQUASH_REDIRECT','SQUASH_FAULT'):
            if p[1]=='FAULT':
                if len(p)!=6: raise ValueError(f'{path}: malformed fault event {line!r}')
                ev[p[1]].add((int(p[2],16),int(p[3],16),int(p[4]),int(p[5])))
            else:
                if len(p)!=5: raise ValueError(f'{path}: malformed event {line!r}')
                ev[p[1]].add((int(p[2],16),int(p[3],16),int(p[4])))
        elif p[0]=='C' and p[1]=='DIV_HOLD' and len(p)==5:
            holds.append((int(p[2],16),int(p[3],16),int(p[4])))
        elif p[0]=='M' and len(p)==7:
            pc,insn=int(p[1],16),int(p[2],16)
            for v in p[3:5]: int(v,16)
            if int(p[5]) not in (0,1,2) or int(p[6]) not in (0,1,2): raise ValueError(f'{path}: invalid forwarding field {line!r}')
            issues.append((pc,insn))
        elif p[0]=='EV' and len(p)==4 and p[1] in {'ISSUE','COMPLETE','RETIRE','SQUASH_REDIRECT','SQUASH_FAULT_IDEX','SQUASH_FAULT_IFID','FAULT_DIV_SUPPRESS','LOAD_USE_RS1','LOAD_USE_RS2','DIV_CONSECUTIVE'}:
            int(p[2],16); int(p[3],16)
        else: raise ValueError(f'{path}: unknown sidecar record {line!r}')
    return ev,holds,issues

def evaluate(simout, sim):
    errors=[]; arch=collections.Counter(); rtl=collections.Counter(); c_events=collections.Counter(); names=[]; pipe_events=[0]*PIPE_EVENTS
    c_manifest=simout/'c_manifest.csv'
    import csv
    rows=list(csv.DictReader(c_manifest.open(newline='',encoding='utf-8')))
    if len(rows)!=21: errors.append(f'C case inventory expected=21 actual={len(rows)}')
    for row in rows:
        name=row['name']; names.append(name)
        try:
            ins,stop=_parse_trace(simout/'c_iss'/(name+'.trace'))
            ev,holds,issues=_parse_sidecar(simout/(name+'.pipe.ccov'))
            # The independent ISS retirement/fault stream must be contained in
            # the independently sampled DUT lifecycle sets.
            retired_ids={(x['pc'],x['raw'],x['length']) for x in ins}
            iss_fault=(stop['pc'],stop['raw'],stop['length'],stop['cause'])
            if not retired_ids <= ev['RETIRE']: errors.append(f'{name}: DUT retirement sidecar misses ISS retirement identities')
            if iss_fault not in ev['FAULT']:
                errors.append(f'{name}: DUT fault sidecar differs from ISS STOP {iss_fault}')
            for x in ins:
                if x['length']==2:
                    raw=x['raw']&0xffff; fam=c_family(raw)
                    if fam: arch['A.C.FAMILY.'+fam]+=1
                    if is_hint(raw): arch['A.C.HINT.RETIRED']+=1
                    if raw==1: arch['A.C.NOP.RETIRED']+=1
                    q=raw&3; f3=(raw>>13)&7; rd=(raw>>7)&31; rp=8+((raw>>7)&7)
                    if q==1 and (f3 in (0,2) or (f3==4 and ((raw>>10)&3)==2)):
                        imm=((raw>>12)&1)<<5|((raw>>2)&31); imm=imm-64 if imm&32 else imm
                        if imm==-32: arch['A.C.IMM.SIGNED6.MIN']+=1
                        if imm==31: arch['A.C.IMM.SIGNED6.MAX']+=1
                    if (q==1 and f3==4 and ((raw>>10)&3) in (0,1) or q==2 and f3==0) and (raw&0x7c)==0x7c:
                        arch['A.C.IMM.SHIFT.MAX']+=1
                    if q==0 and f3 in (2,6):
                        off=(((raw>>5)&1)<<6)|(((raw>>10)&7)<<3)|(((raw>>6)&1)<<2)
                        if off==124: arch['A.C.IMM.MEM.MAX']+=1
                    if q==2 and f3 in (2,6):
                        off=(((raw>>7)&3)<<6)|(((raw>>9)&15)<<2)
                        if off==252: arch['A.C.IMM.STACK.MAX']+=1
                    regs=[]
                    if q==0 and f3==0: regs += [8+((raw>>2)&7)]
                    if q==0 and f3 in (2,6): regs += [rp,8+((raw>>2)&7) if f3==6 else 8+((raw>>2)&7)]
                    if q==1 and f3 in (0,2): regs += [rd]
                    if q==1 and f3 in (4,6,7): regs += [rp]
                    if 8 in regs: arch['A.C.REG.PRIME.LOW']+=1
                    if 15 in regs: arch['A.C.REG.PRIME.HIGH']+=1
                    if is_hint(raw) and rd==0: arch['A.C.REG.X0.HINT']+=1
                    if (q==0 and f3==0 or q==1 and f3==3 and rd==2 or q==2 and f3 in (2,6)):
                        arch['A.C.REG.SP']+=1
                arch[f"A.PC.OFFSET.{x['pc']&3}"]+=1
                if x['length']==4 and x['pc']&3==2: arch['A.FETCH.CROSS_WORD']+=1
                if (x['expanded']&0x7f) in (0x6f,0x67) and x['rd']!=0:
                    expected=(x['pc']+x['length'])&0xffffffff
                    if x['rdval']!=expected: errors.append(f'{name}: ISS link at {x["pc"]:08x} expected={expected:08x} actual={x["rdval"]:08x}')
                    arch['A.LINK.COMPRESSED_PC_PLUS_2' if x['length']==2 else 'A.LINK.STANDARD_PC_PLUS_4']+=1
            # EBREAK is an architectural stop, not a retired instruction. Keep
            # it in family execution coverage from the independent ISS STOP row;
            # the sidecar/STOP identity check above independently confirms DUT
            # observation of the same faulting instruction.
            if stop['length']==2 and stop['cause']==2 and (stop['raw']&0xffff)==0x9002:
                arch['A.C.FAMILY.EBREAK']+=1
            for a,b in zip(ins,ins[1:]):
                if a['pc']+a['length']==b['pc']:
                    if a['length']==2 and b['length']==4: arch['A.WIDTH.16_TO_32']+=1
                    if a['length']==4 and b['length']==2: arch['A.WIDTH.32_TO_16']+=1
            if stop['pc']&3==0: arch['A.PC.OFFSET.0']+=1
            else: arch['A.PC.OFFSET.2']+=1
            if stop['length']==2 and stop['cause']==3: arch['A.C.ILLEGAL.FAULT']+=1
            if stop['length']>4: arch['A.C.UNSUPPORTED_LENGTH.FAULT']+=1
            if stop['cause'] not in (1,2):
                arch['A.FAULT.PRECISE']+=1
                arch['A.FAULT.NO_RETIRE']+=int(all(x['pc']!=stop['pc'] for x in ins))
            for key in ('ATTEMPT','RETIRE','FAULT','SQUASH_REDIRECT','SQUASH_FAULT'):
                c_events[key]+=len(ev[key])
            if not ev['RETIRE'] <= ev['ATTEMPT']: errors.append(f'{name}: retired event not attempted')
            if (stop['pc'],stop['raw'],stop['length']) not in ev['ATTEMPT']:
                errors.append(f'{name}: fault event identity not attempted')
            for k in ('SQUASH_REDIRECT','SQUASH_FAULT'):
                if not {(pc,raw,ilen) for pc,raw,ilen in ev[k]} <= ev['ATTEMPT']:
                    errors.append(f'{name}: {k} identity was not observed as attempted')
            for h in holds:
                rtl['P.DIV.METADATA_HOLD']+=1
            # Hold records are expected in contiguous groups of 33 with one identity.
            for i in range(0,len(holds),33):
                group=holds[i:i+33]
                if len(group)!=33 or len(set(group))!=1: errors.append(f'{name}: divider busy hold metadata group malformed at offset {i}')
                elif group[0][1]&0x7f!=0x33 or (group[0][1]>>25)&0x7f!=1 or (group[0][1]>>12)&7<4:
                    errors.append(f'{name}: busy hold identity at offset {i} is not a DIV/REM instruction')
            for pc,insn in issues:
                if pc&3==2 and insn&0x7f==0x33 and (insn>>25)&0x7f==1 and (insn>>12)&7>=4:
                    rtl['P.DIV.HALFWORD']+=1
            log=(simout/(name+'.pipe.log')).read_text(encoding='utf-8',errors='replace')
            cov=re.findall(r'^COV ((?:\d+\s*){16})$',log,re.M)
            if len(cov)!=1: errors.append(f'{name}: expected exactly one 16-event COV record')
            else:
                for i,v in enumerate(map(int,cov[0].split())): pipe_events[i]+=v
        except Exception as exc: errors.append(f'{name}: {type(exc).__name__}: {exc}')
    legacy_path=simout/'manifest_all.csv'
    try:
        legacy_rows=list(csv.DictReader(legacy_path.open(newline='',encoding='utf-8')))
        if len(legacy_rows)!=209: errors.append(f'legacy inventory expected=209 actual={len(legacy_rows)}')
        for row in legacy_rows:
            log=simout/(row['name']+'.pipe.log')
            cov=re.findall(r'^COV ((?:\d+\s*){16})$',log.read_text(encoding='utf-8',errors='replace'),re.M)
            if len(cov)!=1: errors.append(f'{row["name"]}: expected exactly one legacy 16-event COV record')
            else:
                for i,v in enumerate(map(int,cov[0].split())): pipe_events[i]+=v
    except Exception as exc: errors.append(f'legacy pipeline event evidence: {type(exc).__name__}: {exc}')
    for family in FAMILIES:
        key='A.C.FAMILY.'+family
        if not arch[key]: errors.append(f'uncovered {key}: expected>=1 actual={arch[key]} source=ISS retirement/STOP evidence')
    required_arch=('A.C.HINT.RETIRED','A.C.NOP.RETIRED','A.C.ILLEGAL.FAULT','A.C.UNSUPPORTED_LENGTH.FAULT','A.C.IMM.SIGNED6.MIN','A.C.IMM.SIGNED6.MAX','A.C.IMM.SHIFT.MAX','A.C.IMM.MEM.MAX','A.C.IMM.STACK.MAX','A.C.REG.PRIME.LOW','A.C.REG.PRIME.HIGH','A.C.REG.X0.HINT','A.C.REG.SP','A.PC.OFFSET.0','A.PC.OFFSET.2','A.WIDTH.16_TO_32','A.WIDTH.32_TO_16','A.FETCH.CROSS_WORD','A.LINK.COMPRESSED_PC_PLUS_2','A.LINK.STANDARD_PC_PLUS_4','A.FAULT.PRECISE','A.FAULT.NO_RETIRE')
    for k in required_arch:
        if not arch[k]: errors.append(f'uncovered {k}: expected>=1 actual={arch[k]} source=ISS trace evidence')
    for key in ('ATTEMPT','RETIRE','FAULT','SQUASH_REDIRECT','SQUASH_FAULT'):
        if not c_events[key]: errors.append(f'uncovered P lifecycle event {key}: expected>=1 actual={c_events[key]} source=DUT sidecar evidence')
    if not rtl['P.DIV.HALFWORD']: errors.append(f'uncovered P.DIV.HALFWORD: expected>=1 actual={rtl["P.DIV.HALFWORD"]} source=DUT sidecar ISSUE evidence')
    if not rtl['P.DIV.METADATA_HOLD']: errors.append(f'uncovered P.DIV.METADATA_HOLD: expected>=1 actual={rtl["P.DIV.METADATA_HOLD"]} source=DUT sidecar hold evidence')
    if any(x==0 for x in pipe_events): errors.append(f'zero RTL P.PIPE_EVENT bins: expected>=1 each actual={pipe_events}')
    unitlog=(simout/'unit_decompress.log').read_text(encoding='utf-8',errors='replace')
    if unitlog.count('RV32C_DECOMPRESS_UNIT PASS halfwords=65536 mismatches=0 anchors=16')!=1 or 'FAIL' in unitlog:
        errors.append('exhaustive decompressor unit evidence missing, contradictory, or malformed')
    prefix=f'sim_out_stage4_4_{sim}_'
    stamp=simout.name[len(prefix):] if simout.name.startswith(prefix) else ''
    runner_report=ROOT/'reports'/f'stage4_4_pipeline_{sim}_{stamp}.txt'
    runner_text=''
    if not runner_report.is_file(): errors.append(f'missing companion full regression report: {runner_report}')
    else:
        runner_text=runner_report.read_text(encoding='utf-8',errors='replace')
        if f'STAGE4_4_PIPELINE_{sim.upper()} PASS legacy=209 rv32imc=21 full_trace_comparisons=460 units=7' not in runner_text:
            errors.append('companion full regression report has missing/malformed 230-case terminal marker')
        if 'pipeline_vs_golden_full_traces=230' not in runner_text or 'unit_decompress_halfwords=65536' not in runner_text:
            errors.append('companion report lacks full trace/decompressor counts')
    stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    report=ROOT/'reports'/f'stage4_c_coverage_{sim}_{stamp}.txt'; report.parent.mkdir(exist_ok=True)
    if report.exists(): raise FileExistsError(f'coverage report path is not fresh: {report}')
    lines=[f'Simulator: {sim}',f'cases={209+len(rows)}',f'c_cases={len(rows)}',f'functional_regression_report={runner_report.as_posix()}','evidence=ISS_architecture_plus_DUT_pipeline_sidecar', 'E.C.HALFWORD.65536=65536 patterns,0 mismatches,16 anchors']
    if runner_text:
        lines += [line for line in runner_text.splitlines() if line.startswith(('rtl_vs_iss_and_golden=','pipeline_vs_golden_full_traces=','divider_protocol_checked_cases=','pipeline_event_hits='))]
    lines += [f'{k}={arch[k]}' for k in sorted(arch)]
    lines += [f'P.ATTEMPTED={c_events["ATTEMPT"]}',f'P.RETIRED={c_events["RETIRE"]}',f'P.FAULTING={c_events["FAULT"]}',f'P.SQUASH.REDIRECT={c_events["SQUASH_REDIRECT"]}',f'P.SQUASH.FAULT={c_events["SQUASH_FAULT"]}']
    lines += [f'P.DIV.HALFWORD={rtl["P.DIV.HALFWORD"]}',f'P.DIV.METADATA_HOLD_CYCLES={rtl["P.DIV.METADATA_HOLD"]}']
    lines += [f'P.PIPE_EVENT.{i:02d}={pipe_events[i]}' for i in range(16)]
    lines += [f'UNREACHABLE={"none identified" if not errors else "none adjudicated; see errors"}']
    lines += [f'coverage_errors={len(errors)}']
    lines += [f'ERROR[{i:03d}]={error}' for i,error in enumerate(errors,1)]
    lines += [f'STAGE4_C_COVERAGE_{sim.upper()} '+('PASS' if not errors else 'FAIL')+f' cases={209+len(rows)} c_cases={len(rows)} patterns=65536 pipeline_events=16']
    report.write_text('\n'.join(lines)+'\n',encoding='utf-8',newline='\n')
    print(report.read_text(encoding='utf-8'),end='')
    return 0 if not errors else 1

if __name__=='__main__':
    if len(sys.argv)!=3 or sys.argv[2] not in ('xsim','verilator'):
        raise SystemExit('usage: stage4_c_coverage.py <sim_out_stage4_4_dir> <xsim|verilator>')
    raise SystemExit(evaluate(Path(sys.argv[1]).resolve(),sys.argv[2]))
