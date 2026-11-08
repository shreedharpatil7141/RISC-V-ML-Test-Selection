#!/usr/bin/env python3
"""Stage 3.5 manual M bins, with ISS architectural and RTL microarchitectural evidence."""
import csv, os, re
from collections import Counter
import stage2_lib as L

OPS=['MUL','MULH','MULHSU','MULHU','DIV','DIVU','REM','REMU']
OP_BY_F3=dict(enumerate(OPS))
MASK=0xffffffff

def _bins():
    ids=[]
    for op in OPS:
        ids += [f'A.OP.{op}',f'P.ISSUE.{op}',f'P.COMPLETE.{op}',f'P.RETIRE.{op}']
    for src in ('RS1','RS2'):
        ids += [f'A.{src}.SIGN.{x}' for x in ('NEG','NONNEG')]
        ids += [f'A.{src}.CLASS.{x}' for x in ('ZERO','POS_ONE','NEG_ONE','SMIN','SMAX','OTHER','UMAX')]
    ids += ['A.ALIAS.RD_EQ_RS1','A.ALIAS.RD_EQ_RS2','A.RD.X0',
            'A.CORNER.DIV_ZERO_QUOT','A.CORNER.DIV_ZERO_REM',
            'A.CORNER.SIGNED_OVERFLOW_QUOT','A.CORNER.SIGNED_OVERFLOW_REM',
            'A.CORNER.QUOT_ZERO','A.CORNER.QUOT_ONE','A.CORNER.QUOT_NEGATIVE','A.CORNER.REM_ZERO','A.CORNER.REM_NEGATIVE',
            'P.SQUASH.REDIRECT.M','P.SQUASH.FAULT.M','P.FAULT.DIV_START_SUPPRESSED',
            'P.FWD.RS1.EXMEM','P.FWD.RS1.MEMWB','P.FWD.RS2.EXMEM','P.FWD.RS2.MEMWB',
            'P.LOAD_USE.RS1','P.LOAD_USE.RS2','P.DIV.CONSECUTIVE',
            'P.DIV.WRONG_PATH_SUPPRESSED','P.RD.X0']
    ids += ['B.ABORT.START_CYCLE']+[f'B.ABORT.C{i:02d}' for i in range(1,34)]
    return ids

def _op(insn):
    if (insn & 0x7f)!=0x33 or ((insn>>25)&0x7f)!=1: return None
    return OP_BY_F3[(insn>>12)&7]

def _class(v):
    v &= MASK
    if v==0: return 'ZERO'
    if v==1: return 'POS_ONE'
    if v==MASK: return 'NEG_ONE'
    if v==0x80000000: return 'SMIN'
    if v==0x7fffffff: return 'SMAX'
    return 'OTHER'

def _arch_operand_bins(insn,a,b):
    op=_op(insn); rd=(insn>>7)&31; rs1=(insn>>15)&31; rs2=(insn>>20)&31
    keys=[f'A.OP.{op}']
    for src,val,reg in (('RS1',a,rs1),('RS2',b,rs2)):
        keys.append(f'A.{src}.SIGN.'+('NEG' if val&0x80000000 else 'NONNEG'))
        keys.append(f'A.{src}.CLASS.{_class(val)}')
        if val&MASK==MASK: keys.append(f'A.{src}.CLASS.UMAX')
        if rd!=0 and rd==reg: keys.append('A.ALIAS.RD_EQ_'+src)
    if rd==0: keys.append('A.RD.X0')
    return keys

def _arch_corner_bins(insn,a,b,y):
    """Result bins from an architectural M retirement and its source operands."""
    f3=(insn>>12)&7; keys=[]
    if f3>=4 and b==0:
        keys.append('A.CORNER.DIV_ZERO_QUOT' if f3 in (4,5) else 'A.CORNER.DIV_ZERO_REM')
    if f3 in (4,6) and a==0x80000000 and b==MASK:
        keys.append('A.CORNER.SIGNED_OVERFLOW_QUOT' if f3==4 else 'A.CORNER.SIGNED_OVERFLOW_REM')
    if f3 in (4,5) and b!=0 and y==0: keys.append('A.CORNER.QUOT_ZERO')
    if f3 in (4,5) and b!=0 and y==1: keys.append('A.CORNER.QUOT_ONE')
    if f3==4 and b!=0 and y&0x80000000: keys.append('A.CORNER.QUOT_NEGATIVE')
    if f3 in (6,7) and b!=0 and y==0: keys.append('A.CORNER.REM_ZERO')
    if f3==6 and y&0x80000000: keys.append('A.CORNER.REM_NEGATIVE')
    return keys

def evaluate(sim_dir, rows):
    hits={k:0 for k in _bins()}; contributors={k:set() for k in hits}; errors=[]
    arch_iss_hits=Counter(); arch_rtl_hits=Counter()
    def add(key,test,n=1):
        if key not in hits: errors.append(f'unknown coverage ID {key} from {test}'); return
        if n>0: hits[key]+=n; contributors[key].add(test)
    for row in rows:
        name=row['name']; test_events=[]; iss_arch=Counter(); rtl_arch=Counter()
        iss_path=os.path.join(sim_dir,'iss',name+'.iss.m.tsv')
        rtl_path=os.path.join(sim_dir,name+'.pipe.m.tsv')
        iss_rows=[]; rtl_rows=[]
        try:
            with open(iss_path,newline='') as f:
                rd=csv.DictReader(f,delimiter='\t')
                if rd.fieldnames!=['pc','insn','op','rd','rs1','rs2','a','b','result']:
                    raise ValueError('bad ISS side-channel header')
                for x in rd:
                    rec={k:x[k] for k in rd.fieldnames}
                    rec['pc']=int(x['pc'],16); rec['insn']=int(x['insn'],16)
                    for k in ('op','rd','rs1','rs2'): rec[k]=int(x[k])
                    for k in ('a','b','result'): rec[k]=int(x[k],16)
                    op=_op(rec['insn'])
                    if op is None or rec['op']!=(rec['insn']>>12)&7:
                        raise ValueError('ISS side-channel has a non-M or inconsistent op row')
                    if (rec['rd'],rec['rs1'],rec['rs2'])!=((rec['insn']>>7)&31,(rec['insn']>>15)&31,(rec['insn']>>20)&31):
                        raise ValueError('ISS side-channel register fields disagree with instruction')
                    iss_rows.append(rec)
        except (OSError,ValueError,KeyError,TypeError) as ex:
            errors.append(f'{name}: malformed/missing ISS M side channel: {ex}')
        try:
            for ln in open(rtl_path,encoding='utf-8').read().splitlines():
                p=ln.split()
                if len(p)==7 and p[0]=='M':
                    pc,insn,a,b,fa,fb=(int(p[i],16) for i in (1,2,3,4,5,6))
                    if _op(insn) is None: raise ValueError('RTL M row has non-M instruction')
                    rtl_rows.append((pc,insn,a,b,fa,fb))
                elif len(p)==4 and p[0]=='EV':
                    ev,pc_s,insn_s=p[1],p[2],p[3]
                    if ev not in {'ISSUE','COMPLETE','RETIRE','SQUASH_REDIRECT','SQUASH_FAULT_IDEX',
                                  'SQUASH_FAULT_IFID','FAULT_DIV_SUPPRESS','LOAD_USE_RS1','LOAD_USE_RS2','DIV_CONSECUTIVE'}:
                        raise ValueError(f'unknown event {ev}')
                    test_events.append((ev,int(pc_s,16),int(insn_s,16)))
                else: raise ValueError(f'malformed side-channel row: {ln!r}')
        except (OSError,ValueError,IndexError) as ex:
            errors.append(f'{name}: malformed/missing RTL M side channel: {ex}')

        # Match the functional checker and prepare_stage5.py: ISS artifacts live in iss/.
        trace=L.read(os.path.join(sim_dir,'iss',name+'.iss.trace'))
        if trace is None: errors.append(f'{name}: missing ISS architectural trace'); trace=''
        rtl_trace=L.read(os.path.join(sim_dir,name+'.pipe.trace'))
        if rtl_trace is None: errors.append(f'{name}: missing RTL architectural trace'); rtl_trace=''
        def m_trace_rows(text,source):
            result=[]
            for ln in text.splitlines():
                p=ln.split()
                if len(p)==7:
                    try:
                        pc,insn,rd,rval=int(p[0],16),int(p[1],16),int(p[2]),int(p[3],16)
                        if _op(insn) is not None: result.append((pc,insn,rd,rval))
                    except ValueError: errors.append(f'{name}: malformed {source} architectural trace row: {ln!r}')
            return result
        trace_m_rows=m_trace_rows(trace,'ISS')
        rtl_trace_m_rows=m_trace_rows(rtl_trace,'RTL')
        if len(trace_m_rows)!=len(iss_rows): errors.append(f'{name}: ISS M side-channel count does not match M retirements in architectural trace')
        if len(rtl_trace_m_rows)!=len(rtl_rows): errors.append(f'{name}: RTL M side-channel count does not match M retirements in architectural trace')
        if len(iss_rows)!=len(rtl_rows): errors.append(f'{name}: ISS/RTL M side-channel count differs {len(iss_rows)} vs {len(rtl_rows)}')
        for i,ir in enumerate(iss_rows):
            op=OP_BY_F3[ir['op']]
            arch_keys=_arch_operand_bins(ir['insn'],ir['a'],ir['b'])
            iss_arch.update(arch_keys)
            arch_iss_hits.update(arch_keys)
            for key in arch_keys: add(key,name)
            if i>=len(rtl_rows): continue
            rr=rtl_rows[i]
            if (rr[0],rr[1],rr[2],rr[3])!=(ir['pc'],ir['insn'],ir['a'],ir['b']):
                errors.append(f"{name}: RTL/ISS pre-writeback operand mismatch at pc={ir['pc']:08x}")
            rtl_arch.update(_arch_operand_bins(rr[1],rr[2],rr[3]))
            arch_rtl_hits.update(_arch_operand_bins(rr[1],rr[2],rr[3]))
            for j,src in ((4,'RS1'),(5,'RS2')):
                fwd=rr[j]
                if fwd==1: add(f'P.FWD.{src}.EXMEM',name)
                elif fwd==2: add(f'P.FWD.{src}.MEMWB',name)
                elif fwd!=0: errors.append(f'{name}: invalid forwarding code {fwd}')
            if i>=len(trace_m_rows) or trace_m_rows[i][0:2]!=(ir['pc'],ir['insn']):
                errors.append(f"{name}: ISS M side-channel instruction missing from ordered retirement trace at {ir['pc']:08x}")
            else:
                _,_,trd,trval=trace_m_rows[i]
                trace_expected=(ir['rd'],ir['result']) if ir['rd'] else (0,0)
                if (trd,trval)!=trace_expected:
                    errors.append(f"{name}: ISS M result does not match architectural trace at {ir['pc']:08x}")
                for key in _arch_corner_bins(ir['insn'],ir['a'],ir['b'],trval):
                    arch_iss_hits[key]+=1
            if i<len(rtl_rows) and i<len(rtl_trace_m_rows):
                rtr=rtl_trace_m_rows[i]
                if rtr[0:2]!=(rtl_rows[i][0],rtl_rows[i][1]):
                    errors.append(f"{name}: RTL M side-channel instruction missing from ordered retirement trace at {rtl_rows[i][0]:08x}")
                else:
                    for key in _arch_corner_bins(rtl_rows[i][1],rtl_rows[i][2],rtl_rows[i][3],rtr[3]):
                        arch_rtl_hits[key]+=1
            a,b,y=ir['a'],ir['b'],ir['result']; f3=ir['op']
            for key in _arch_corner_bins(ir['insn'],a,b,y): add(key,name)
        if iss_arch!=rtl_arch:
            errors.append(f'{name}: architectural operation/operand-class counts differ between ISS and RTL side channels')
        for ev in ('ISSUE','COMPLETE','RETIRE'):
            ev_rows=[(pc,insn) for kind,pc,insn in test_events if kind==ev]
            if ev_rows!=[(r[0],r[1]) for r in rtl_rows]:
                errors.append(f'{name}: {ev} event stream does not match the ordered RTL M issue side channel')
        for ev,pc,insn in test_events:
            op=_op(insn)
            if ev in ('ISSUE','COMPLETE','RETIRE'):
                if op is None: errors.append(f'{name}: {ev} event names a non-M instruction'); continue
                add(f'P.{ev}.{op}',name)
                if ev in ('ISSUE','RETIRE') and ((insn>>7)&31)==0: add('P.RD.X0',name)
            elif ev=='SQUASH_REDIRECT':
                if op is not None:
                    add('P.SQUASH.REDIRECT.M',name)
                    if op in ('DIV','DIVU','REM','REMU'):
                        add('P.DIV.WRONG_PATH_SUPPRESSED',name)
                    if any(x['pc']==pc for x in iss_rows): errors.append(f'{name}: squashed redirect M instruction also appears in ISS')
                else: errors.append(f'{name}: redirect-squash event is not an M instruction')
            elif ev in ('SQUASH_FAULT_IDEX','SQUASH_FAULT_IFID'):
                if op is not None: add('P.SQUASH.FAULT.M',name)
            elif ev=='FAULT_DIV_SUPPRESS':
                if op not in ('DIV','DIVU','REM','REMU'): errors.append(f'{name}: fault-suppression event is not DIV/REM')
                else: add('P.FAULT.DIV_START_SUPPRESSED',name)
                if any(x['pc']==pc for x in iss_rows): errors.append(f'{name}: fault-suppressed DIV appears in ISS')
            elif ev=='DIV_CONSECUTIVE':
                if op not in ('DIV','DIVU','REM','REMU'): errors.append(f'{name}: consecutive-divider event is not DIV/REM')
                else: add('P.DIV.CONSECUTIVE',name)
            elif ev=='LOAD_USE_RS1':
                if op is None: errors.append(f'{name}: M rs1 load-use event is not an M instruction')
                else: add('P.LOAD_USE.RS1',name)
            elif ev=='LOAD_USE_RS2':
                if op is None: errors.append(f'{name}: M rs2 load-use event is not an M instruction')
                else: add('P.LOAD_USE.RS2',name)

    # Per-offset block markers are independent of pipeline event files.
    unit=L.read(os.path.join(sim_dir,'units_md_exec.log')) or ''
    markers=re.findall(r'MD_ABORT_BIN: pos=(\d+) hit=(\d+)',unit)
    pos_counts={int(p):int(h) for p,h in markers}
    if len(markers)!=34 or set(pos_counts)!=set(range(34)):
        errors.append('wrapper abort markers missing, duplicated, or malformed')
    for pos in range(34):
        if pos_counts.get(pos)==1: add('B.ABORT.START_CYCLE' if pos==0 else f'B.ABORT.C{pos:02d}','tb_rv_md_exec')
        elif pos in pos_counts: errors.append(f'wrapper abort position {pos} did not pass its checks')

    lines=['Stage 3.5 M-extension coverage dictionary',
           'Architectural operand bins show independent ISS/RTL counts; raw pre-writeback operand rows are compared in order.',
           'Pipeline and block-level protocol bins use RTL/unit evidence; the categories are not merged.',
           f"{'ID':42s} {'ISS/RTL or hits':>16s} {'tests':>6s} status  contributors"]
    missing=[]
    for key in hits:
        tests=sorted(contributors[key]); state='HIT' if hits[key] else 'MISS'
        if key.startswith('A.'):
            state='HIT' if arch_iss_hits[key]>0 and arch_iss_hits[key]==arch_rtl_hits[key] else 'MISS'
        if key.startswith('A.') and arch_iss_hits[key]!=arch_rtl_hits[key]:
            errors.append(f'{key}: ISS/RTL independent counts differ {arch_iss_hits[key]} vs {arch_rtl_hits[key]}')
        if state=='MISS': missing.append(key)
        hit_text=f'{arch_iss_hits[key]}/{arch_rtl_hits[key]}' if key.startswith('A.') else str(hits[key])
        lines.append(f"{key:42s} {hit_text:>16s} {len(tests):6d} {state:5s}  {','.join(tests) if tests else '-'}")
    lines.append(f"Defined bins hit: {len(hits)-len(missing)}/{len(hits)}")
    lines.append(f"Coverage data errors: {len(errors)}")
    lines += [f'ERROR: {e}' for e in errors]
    lines += [f'MISS: {k}' for k in missing]
    return lines,not errors and not missing,errors,missing
