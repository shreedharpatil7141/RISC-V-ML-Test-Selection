#!/usr/bin/env python3
"""Isolated, evidence-audited Stage 3.6 Verilator mutation campaign.

Run from Ubuntu WSL at the project root. Each mutant is applied to a fresh
scratch copy; source in the invoking checkout is never written. The Stage 1,
Stage 2, and Stage 3.5 regression runners and the historical Stage 1/2 mutant
tables are read unchanged. A result is CAUGHT only after all required builds
exist and a named verification check fails. Timeouts without proof that the
mutant's simulator started are INVALID.
"""
import argparse
import ast
import csv
import datetime
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
REPORT_ROOT = ROOT / 'reports'
STAGE35_XSIM = REPORT_ROOT / 'stage3_5_coverage_xsim_reanalysis.txt'
STAGE35_VERILATOR = REPORT_ROOT / 'stage3_5_coverage_verilator_reanalysis.txt'

# Each entry is an independently applied DUT defect. expected names the
# verification class/test to inspect; the actual detector is recorded from the
# produced unit marker or system/coverage report.
MUTANTS = [
    ('M01', 'MULH returns low product half', 'rtl/alu/rv_mul.sv',
     '3\'b001: y = product_ss[63:32];', '3\'b001: y = product_ss[31:0];', 'unit:wrapper'),
    ('M02', 'MULHSU treats rs2 as signed', 'rtl/alu/rv_mul.sv',
     '3\'b010: y = product_su[63:32];', '3\'b010: y = product_ss[63:32];', 'unit:wrapper'),
    ('M03', 'MULHU uses signed rs1 high product', 'rtl/alu/rv_mul.sv',
     'default: y = product_uu[63:32];', 'default: y = product_ss[63:32];', 'unit:wrapper'),
    ('M04', 'Signed quotient fails to restore quotient sign', 'rtl/alu/rv_div_iter.sv',
     'negate_quotient_q  <= !funct3[0] && (dividend[W-1] ^ divisor[W-1]);',
     'negate_quotient_q  <= 1\'b0;', 'unit:divider'),
    ('M05', 'Unsigned divide incorrectly takes divisor magnitude', 'rtl/alu/rv_div_iter.sv',
     'divisor_abs_q      <= (!funct3[0] && divisor[W-1]) ? -divisor : divisor;',
     'divisor_abs_q      <= (divisor[W-1]) ? -divisor : divisor;', 'unit:divider'),
    ('M06', 'Signed remainder follows divisor sign instead of dividend', 'rtl/alu/rv_div_iter.sv',
     'negate_remainder_q <= !funct3[0] && dividend[W-1];',
     'negate_remainder_q <= !funct3[0] && divisor[W-1];', 'unit:divider'),
    ('M07', 'DIV/DIVU by zero returns zero quotient', 'rtl/alu/rv_div_iter.sv',
     'result = quotient_mode_q ? {W{1\'b1}} : dividend_orig_q;',
     'result = quotient_mode_q ? {W{1\'b0}} : dividend_orig_q;', 'unit:divider'),
    ('M08', 'REM/REMU by zero returns zero remainder', 'rtl/alu/rv_div_iter.sv',
     'result = quotient_mode_q ? {W{1\'b1}} : dividend_orig_q;',
     'result = quotient_mode_q ? {W{1\'b1}} : {W{1\'b0}};', 'unit:divider'),
    ('M09', 'Signed overflow quotient result is wrong', 'rtl/alu/rv_div_iter.sv',
     "result = quotient_mode_q ? {1'b1, {(W-1){1'b0}}} : {W{1'b0}};",
     "result = quotient_mode_q ? {W{1'b1}} : {W{1'b0}};", 'unit:divider'),
    ('M10', 'Signed overflow remainder result is nonzero', 'rtl/alu/rv_div_iter.sv',
     "result = quotient_mode_q ? {1'b1, {(W-1){1'b0}}} : {W{1'b0}};",
     "result = quotient_mode_q ? {1'b1, {(W-1){1'b0}}} : dividend_orig_q;", 'unit:divider'),
    ('M11', 'Restoring divider terminates one iteration early', 'rtl/alu/rv_div_iter.sv',
     'if (iteration == W-1) begin', 'if (iteration == W-2) begin', 'unit:divider'),
    ('M12', 'Divider uses changing live divisor instead of latched magnitude', 'rtl/alu/rv_div_iter.sv',
     "divisor_ext       = {1'b0, divisor_abs_q};", "divisor_ext       = {1'b0, divisor};", 'unit:divider'),
    ('M13', 'Divide-by-zero remainder loses latched dividend', 'rtl/alu/rv_div_iter.sv',
     "dividend_orig_q    <= dividend;", "dividend_orig_q    <= '0;", 'unit:divider'),
    ('M14', 'DIV/REM quotient-versus-remainder operation decode is inverted', 'rtl/alu/rv_div_iter.sv',
     'quotient_mode_q    <= !funct3[1];', 'quotient_mode_q    <= funct3[1];', 'unit:divider'),
    ('M15', 'Divider busy omits the accepted start cycle', 'rtl/alu/rv_div_iter.sv',
     'assign busy     = ((state == S_RUN) || accepted) && !abort;',
     'assign busy     = (state == S_RUN) && !abort;', 'unit:wrapper'),
    ('M16', 'Divider done asserts during the final RUN iteration', 'rtl/alu/rv_div_iter.sv',
     'assign done     = (state == S_FIN) && !abort;',
     'assign done     = (state == S_RUN) && !abort;', 'unit:wrapper'),
    ('M17', 'Abort fails to suppress a pending FIN completion', 'rtl/alu/rv_div_iter.sv',
     'assign done     = (state == S_FIN) && !abort;', 'assign done     = (state == S_FIN);', 'unit:wrapper'),
    ('M18', 'Pipeline writes EX/MEM while divider is busy, duplicating transfer', 'rtl/pipeline/rv_pipe_regs.sv',
     'if (kill || md_hold) ex_mem <= \'0;', 'if (kill) ex_mem <= \'0;', 'test:pipe_div_back_to_back'),
    ('M19', 'Pipeline IF/ID advances during divider hold', 'rtl/pipeline/rv_pipe_regs.sv',
     'else if (!(stall || md_hold)) if_id <= if_id_next;', 'else if (!stall) if_id <= if_id_next;', 'test:pipe_div_dependencies'),
    ('M20', 'Pipeline ID/EX does not retain the active divider instruction', 'rtl/pipeline/rv_pipe_regs.sv',
     'if (md_hold && !kill && !redirect) id_ex <= id_ex;',
     'if (md_hold && !kill && !redirect) id_ex <= id_ex_next;', 'test:pipe_div_dependencies'),
    ('M21', 'DIV/REM rs1 ignores EX/MEM forwarding', 'rtl/pipeline/rv_ex_stage.sv',
     'FWD_EXMEM: rs1_f = exmem_alu_y;', 'FWD_EXMEM: rs1_f = id_ex.rs1_data;', 'test:pipe_div_forward_sources'),
    ('M22', 'DIV/REM rs2 uses EX/MEM data for a MEM/WB dependency', 'rtl/pipeline/rv_ex_stage.sv',
     'FWD_MEMWB: rs2_f = memwb_data;', 'FWD_MEMWB: rs2_f = exmem_alu_y;', 'test:pipe_div_forward_sources'),
    ('M23', 'Pipeline retirement reports an architectural write to x0', 'rtl/pipeline/rv_wb_stage.sv',
     "assign ret_rd_we     = mem_wb.valid && mem_wb.reg_we && (mem_wb.rd != 5'd0);",
     'assign ret_rd_we     = mem_wb.valid && mem_wb.reg_we;', 'test:pipe_m_back_to_back_x0'),
    ('M24', 'Forwarding unit forwards an in-flight x0 result', 'rtl/pipeline/rv_forward_unit.sv',
     "(exmem_rd != 5'd0)", "(exmem_rd == 5'd0)", 'test:pipe_m_back_to_back_x0'),
    ('M25', 'Older MEM fault no longer kills younger pipeline work', 'rtl/core/rv_core_pipe.sv',
     'assign kill = halted || fault;', 'assign kill = halted;', 'test:pipe_div_fault_illegal'),
    ('M26', 'Pipeline divider is not aborted when kill is asserted', 'rtl/pipeline/rv_ex_stage.sv',
     '.clk(clk), .rst_n(rst_n), .start(md_start_req), .abort(kill),',
     '.clk(clk), .rst_n(rst_n), .start(md_start_req), .abort(1\'b0),', 'test:pipe_div_fault_illegal'),
]


def _read_mutation_table(path):
    tree = ast.parse(path.read_text(encoding='utf-8'))
    env = {}
    for node in tree.body:
        if isinstance(node, ast.Assign):
            targets=[t.id for t in node.targets if isinstance(t,ast.Name)]
            if not any(t in ('F','MUT') for t in targets):
                continue
            value = _literal(node.value, env)
            for target in node.targets:
                if isinstance(target, ast.Name):
                    env[target.id] = value
                    if target.id == 'MUT':
                        return value
    raise ValueError(f'could not read literal MUT table from unchanged {path.name}')


def _literal(node, env):
    if isinstance(node, ast.Constant): return node.value
    if isinstance(node, ast.Name) and node.id in env: return env[node.id]
    if isinstance(node, ast.List): return [_literal(x,env) for x in node.elts]
    if isinstance(node, ast.Tuple): return tuple(_literal(x,env) for x in node.elts)
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        return _literal(node.left,env) + _literal(node.right,env)
    raise ValueError(f'unsupported literal expression in unchanged mutation table: {ast.dump(node)}')


def _replacements(old, new):
    return old if new is None else [(old, new)]


def _apply(root, relpath, old, new):
    path = root / relpath
    original = path.read_text(encoding='utf-8')
    changed = original
    changes = []
    for before, after in _replacements(old, new):
        count = changed.count(before)
        if count == 0:
            raise ValueError(f'pattern absent: {relpath}: {before!r}')
        mutated = changed.replace(before, after, 1)
        if mutated == changed:
            raise ValueError(f'pattern replacement made no change: {relpath}: {before!r}')
        changes.append({'file': relpath, 'before': before, 'after': after,
                        'matches_before': count, 'actual_change': True})
        changed = mutated
    path.write_text(changed, encoding='utf-8', newline='\n')
    return changes


def _ignore_copy(directory, names):
    rel = Path(directory).resolve().relative_to(ROOT)
    ignored = []
    for name in names:
        if name == '.git' or name == 'reports' or name == '__pycache__' or name in ('.venv', 'venv'):
            ignored.append(name)
        elif name.startswith('sim_out') or name.startswith('obj_dir'):
            ignored.append(name)
        elif (Path(directory) / name).is_file() and name.endswith('.hex'):
            ignored.append(name)
    return ignored


def _copy_project(destination):
    shutil.copytree(ROOT, destination, ignore=_ignore_copy)
    (destination / 'reports').mkdir(exist_ok=True)


def _kill_process_group(proc):
    if os.name == 'nt':
        proc.kill()
        return
    try:
        os.killpg(proc.pid, signal.SIGTERM)
        try:
            proc.wait(timeout=3)
        except subprocess.TimeoutExpired:
            os.killpg(proc.pid, signal.SIGKILL)
    except ProcessLookupError:
        pass


def _command(cmd, cwd, env, timeout):
    start = time.monotonic()
    proc = subprocess.Popen(cmd, cwd=cwd, env=env, text=True,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            start_new_session=(os.name != 'nt'))
    timed_out = False
    try:
        stdout, stderr = proc.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        timed_out = True
        _kill_process_group(proc)
        stdout, stderr = proc.communicate()
    except KeyboardInterrupt:
        _kill_process_group(proc)
        proc.communicate()
        raise
    return {'command': cmd, 'cwd': str(cwd), 'exit_code': proc.returncode,
            'timeout': timed_out, 'elapsed_seconds': round(time.monotonic()-start, 2),
            'stdout': stdout, 'stderr': stderr}


def _save_command_result(folder, result):
    folder.mkdir(parents=True, exist_ok=True)
    (folder / 'command.json').write_text(json.dumps({k: v for k, v in result.items()
                                                     if k not in ('stdout', 'stderr')}, indent=2) + '\n', encoding='utf-8')
    (folder / 'stdout.log').write_text(result['stdout'], encoding='utf-8')
    (folder / 'stderr.log').write_text(result['stderr'], encoding='utf-8')


def _command_hook(folder):
    """Record exact subprocess argument lists issued by unchanged runners."""
    hookdir=folder/'command_hook'; hookdir.mkdir(parents=True,exist_ok=True)
    source='''import json, os, subprocess\n_orig_run=subprocess.run\ndef _audit_run(*args, **kwargs):\n    cmd=args[0] if args else kwargs.get("args")\n    try:\n        with open(os.environ["MUTATION_COMMAND_LOG"], "a", encoding="utf-8") as f:\n            f.write(json.dumps({"command":cmd,"cwd":kwargs.get("cwd"),"shell":kwargs.get("shell",False)})+"\\n")\n    except Exception:\n        pass\n    return _orig_run(*args, **kwargs)\nsubprocess.run=_audit_run\n'''
    (hookdir/'sitecustomize.py').write_text(source,encoding='utf-8')
    (folder/'command_hook_source.py.txt').write_text(source,encoding='utf-8')
    return hookdir


def _expected_trace(root, test):
    sys.path.insert(0, str(root / 'scripts' / 'simulation'))
    try:
        import rv32_asm
        import rv32i_iss
        src = root / 'tests' / 'directed' / 'rv32i' / (test + '.s')
        mem = rv32_asm.assemble(src.read_text(encoding='utf-8'))
        words = [mem.get(4*i, 0) for i in range(max(mem)//4 + 1)]
        _, _, trace, footer, _, _ = rv32i_iss.run(words)
        return '\n'.join(trace + footer) + '\n'
    finally:
        sys.path.pop(0)
        sys.modules.pop('rv32_asm', None)
        sys.modules.pop('rv32i_iss', None)


def _built_stage1(sim):
    return (sim / 'obj_units' / 'Vunits').is_file() and (sim / 'obj_core' / 'Vcore').is_file()


def _complete_trace(path):
    if not path.is_file(): return False
    return any(line.startswith('HALT ') for line in path.read_text(encoding='utf-8',errors='replace').splitlines())


def _stage1_detection(root, sim, output):
    lines = []
    def explicit_fail(test):
        trace=sim/(test+'.rtl.trace')
        return _complete_trace(trace) and any('TEST_RESULT: FAIL' in line and f'{test}.hex' in line
                                              for line in output.splitlines())
    for line in output.splitlines():
        m = re.match(r'^([A-Za-z0-9_]+)\s+(PASS|FAIL)\s+(match|DIFF)\s+', line)
        if not m:
            continue
        test, rtl, trace_status = m.groups()
        if rtl == 'FAIL' and explicit_fail(test):
            lines.append(f'{test}: explicit Stage 1 TEST_RESULT FAIL')
        elif trace_status == 'DIFF':
            path = sim / (test + '.rtl.trace')
            if _complete_trace(path):
                actual = path.read_text(encoding='utf-8', errors='replace')
                expected = _expected_trace(root, test)
                if actual != expected:
                    ai, ei = actual.splitlines(), expected.splitlines()
                    idx = next((i for i, pair in enumerate(zip(ai, ei), 1) if pair[0] != pair[1]),
                               min(len(ai), len(ei)) + 1)
                    lines.append(f'{test}: independently confirmed RTL/ISS trace difference at line {idx}')
    if 'UNIT_RESULT: FAIL' in output:
        lines.append('Stage 1 unit: explicit UNIT_RESULT FAIL')
    return lines


def _built_stage2(sim):
    targets = [('obj_Vunits1', 'Vunits1'), ('obj_Vunitsp', 'Vunitsp'),
               ('obj_Vcore1', 'Vcore1'), ('obj_Vpipe', 'Vpipe')]
    return all((sim / d / exe).is_file() for d, exe in targets)


def _stage2_detection(sim, output):
    lines = []
    for line in output.splitlines():
        m = re.match(r'^([A-Za-z0-9_]+)\s+(ok|FAIL)\s+(ok|FAIL)\s+(ok|DIFF)\s+(ok|DIFF)\s+(ok|FAIL)\s+', line)
        if m and any(x in ('FAIL', 'DIFF') for x in m.groups()[1:]):
            test = m.group(1)
            _,s1,pipe,iss,gold,perf=m.groups()
            for label,status in (('s1',s1),('pipe',pipe)):
                log=sim/f'{test}.{label}.log'
                trace=sim/(test+f'.{label}.trace')
                if status=='FAIL' and log.is_file() and _complete_trace(trace) and f'TEST_RESULT: FAIL' in log.read_text(encoding='utf-8',errors='replace'):
                    lines.append(f'{test}: explicit {label} TEST_RESULT FAIL')
            pipe_trace = sim / (test + '.pipe.trace')
            iss_trace = sim / 'iss' / (test + '.iss.trace')
            gold_trace=sim/(test+'.s1.trace')
            if iss=='DIFF' and _complete_trace(pipe_trace) and _complete_trace(iss_trace) and pipe_trace.read_bytes()!=iss_trace.read_bytes():
                lines.append(f'{test}: independently confirmed pipeline/ISS trace difference')
            if gold=='DIFF' and _complete_trace(pipe_trace) and _complete_trace(gold_trace) and pipe_trace.read_bytes()!=gold_trace.read_bytes():
                lines.append(f'{test}: independently confirmed pipeline/golden trace difference')
            if perf=='FAIL':
                log=sim/(test+'.pipe.log')
                expected_file=sim/'expected.csv'
                if log.is_file() and expected_file.is_file():
                    stats=re.search(r'STATS stalls=(\d+) redirects=(\d+) cycles=(\d+) instret=(\d+)',log.read_text(encoding='utf-8',errors='replace'))
                    exp=next((x for x in csv.DictReader(expected_file.open(newline='')) if x['name']==test),None)
                    if stats and exp:
                        actual=tuple(map(int,stats.groups()))
                        required=(int(exp['model_stalls']),int(exp['model_redirects']),
                                  int(exp['instret'])+5+int(exp['model_stalls'])+2*int(exp['model_redirects']),int(exp['instret']))
                        if actual!=required:
                            lines.append(f'{test}: independently checked Stage 2 timing mismatch actual={actual} expected={required}')
    for filename in ('units_s1.log','units_pipe.log'):
        p=sim/filename
        if p.is_file():
            text=p.read_text(encoding='utf-8',errors='replace')
            for marker in ('UNIT_RESULT: FAIL','PIPE_UNIT_RESULT: FAIL'):
                if marker in text: lines.append(f'{filename}: explicit {marker}')
            if re.search(r'errors=(?:[1-9]\d*)',text):
                lines.append(f'{filename}: explicit nonzero unit error count')
    return lines


def _stage3_binaries(sim):
    targets = [('obj_Vunits1', 'Vunits1'), ('obj_Vunitmd', 'Vunitmd'),
               ('obj_Vunitdecoderm', 'Vunitdecoderm'), ('obj_Vunitsp', 'Vunitsp'),
               ('obj_Vdiviter', 'Vdiviter'), ('obj_Vmdexec', 'Vmdexec'),
               ('obj_Vcore1', 'Vcore1'), ('obj_Vpipe35', 'Vpipe35')]
    return all((sim / d / exe).is_file() for d, exe in targets)


def _stage3_detection(report, sim, expected):
    if not report.is_file():
        return []
    text = report.read_text(encoding='utf-8', errors='replace')
    detected = []
    if expected == 'unit:wrapper':
        detected += [ln.strip() for ln in text.splitlines() if ln.startswith('M wrapper unit: FAIL')]
    elif expected == 'unit:divider':
        detected += [ln.strip() for ln in text.splitlines() if ln.startswith('Divider unit: FAIL')]
    elif expected.startswith('test:'):
        test = expected.split(':', 1)[1]
        for ln in text.splitlines():
            if not ln.startswith(test.ljust(38)):
                continue
            fields=ln.split()
            if len(fields)<7: continue
            _,s1,pipe,iss,gold,perf,md=fields[:7]
            for label,status in (('s1',s1),('pipe',pipe)):
                log=sim/(test+'.'+label+'.log')
                trace=sim/(test+f'.{label}.trace')
                if status=='FAIL' and log.is_file() and _complete_trace(trace) and 'TEST_RESULT: FAIL' in log.read_text(encoding='utf-8',errors='replace'):
                    detected.append(f'{test}: explicit {label} TEST_RESULT FAIL')
            pt=sim/(test+'.pipe.trace'); it=sim/'iss'/(test+'.iss.trace'); gt=sim/(test+'.s1.trace')
            if iss=='DIFF' and _complete_trace(pt) and _complete_trace(it) and pt.read_bytes()!=it.read_bytes():
                detected.append(f'{test}: independently confirmed full pipeline/ISS trace difference')
            if gold=='DIFF' and _complete_trace(pt) and _complete_trace(gt) and pt.read_bytes()!=gt.read_bytes():
                detected.append(f'{test}: independently confirmed full pipeline/golden trace difference')
            # Require produced timing/protocol records before using those
            # columns as detection; absent records are invalid/missing results.
            logpath=sim/(test+'.pipe.log')
            log=logpath.read_text(encoding='utf-8',errors='replace') if logpath.is_file() else ''
            if perf=='FAIL' and re.search(r'STATS stalls=\d+ redirects=\d+ cycles=\d+ instret=\d+',log):
                detected.append(f'{test}: explicit timing checker failure with complete STATS record')
            if md=='FAIL' and re.search(r'MD_STATS starts=\d+ dones=\d+ busy_cycles=\d+ aborts_started=\d+',log):
                detected.append(f'{test}: explicit divider protocol checker failure with complete MD_STATS record')
    # Coverage counts are independent RTL/ISS evidence. Accept a coverage
    # failure only when its actual failing ID/test is printed, never on a bare
    # nonzero process result.
    return detected


def _baseline(report_dir, timeout, py, verilator_version):
    results = {}
    with tempfile.TemporaryDirectory(prefix='stage36_baseline_') as tmp:
        work = Path(tmp) / 'project'
        _copy_project(work)
        for stage, runner, sim_name, pass_marker in (
            ('stage1', 'run_stage1.py', 'sim_mut_baseline_s1', 'STAGE1_REGRESSION PASS'),
            ('stage2', 'run_stage2.py', 'sim_mut_baseline_s2', 'STAGE2_REGRESSION_VERILATOR PASS'),
            ('stage35', 'run_stage5.py', 'sim_mut_baseline_s35', 'STAGE3_5_REGRESSION_VERILATOR PASS')):
            env = dict(os.environ, SIM_DIR=str(work / sim_name))
            hook=_command_hook(report_dir/'baseline'/stage)
            env['PYTHONPATH']=str(hook)+(os.pathsep+env['PYTHONPATH'] if env.get('PYTHONPATH') else '')
            env['MUTATION_COMMAND_LOG']=str(report_dir/'baseline'/stage/'actual_commands.jsonl')
            cmd = [py, str(work / 'scripts' / 'simulation' / runner)]
            r = _command(cmd, work, env, timeout)
            outdir = report_dir / 'baseline' / stage
            _save_command_result(outdir, r)
            # Preserve canonical current reports without wildcard guessing.
            canonical = {'stage1': work/'reports'/'stage1_regression.txt',
                         'stage2': work/'reports'/'stage2_regression_verilator.txt',
                         'stage35': work/'reports'/'stage3_5_coverage_verilator.txt'}[stage]
            if canonical.is_file():
                shutil.copy2(canonical, outdir / 'report.txt')
            ok = (r['exit_code'] == 0 and not r['timeout'] and pass_marker in r['stdout'])
            results[stage] = {'status': 'PASS' if ok else 'FAIL', 'exit_code': r['exit_code'],
                              'pass_marker': pass_marker, 'tool_version': verilator_version}
            if not ok:
                break
    return results


def _run_one(report_dir, stage, ident, name, relpath, old, new, expected,
             timeout, py, verilator_version):
    outdir = report_dir / 'mutants' / ident
    outdir.mkdir(parents=True, exist_ok=True)
    rec = {'id': ident, 'name': name, 'stage': stage, 'expected_check': expected,
           'tool_version': verilator_version, 'status': 'INVALID', 'build_success': False,
           'detectors': [], 'changes': [], 'runner_exit_code': None, 'timeout': False}
    tmp = tempfile.TemporaryDirectory(prefix=f'stage36_{ident}_')
    try:
        work = Path(tmp.name) / 'project'
        _copy_project(work)
        try:
            rec['changes'] = _apply(work, relpath, old, new)
            (outdir / 'source_change.json').write_text(json.dumps(rec['changes'], indent=2)+'\n', encoding='utf-8')
        except Exception as exc:
            rec['pattern_error'] = str(exc)
            rec['status'] = 'INVALID'
            return rec

        if stage == 'stage1':
            sim = work / 'sim_mut_stage1'
            runner = 'run_stage1.py'
            cmd = [py, str(work/'scripts'/'simulation'/runner)]
        elif stage == 'stage2':
            sim = work / 'sim_mut_stage2'
            runner = 'run_stage2.py'
            cmd = [py, str(work/'scripts'/'simulation'/runner)]
        else:
            sim = work / 'sim_mut_stage35'
            runner = 'run_stage5.py'
            cmd = [py, str(work/'scripts'/'simulation'/runner)]
        env = dict(os.environ, SIM_DIR=str(sim))
        hook=_command_hook(outdir)
        env['PYTHONPATH']=str(hook)+(os.pathsep+env['PYTHONPATH'] if env.get('PYTHONPATH') else '')
        env['MUTATION_COMMAND_LOG']=str(outdir/'actual_commands.jsonl')
        r = _command(cmd, work, env, timeout)
        rec.update({'runner_exit_code': r['exit_code'], 'timeout': r['timeout'],
                    'elapsed_seconds': r['elapsed_seconds']})
        _save_command_result(outdir, r)

        if stage == 'stage1':
            rec['build_success'] = _built_stage1(sim)
            rec['detectors'] = _stage1_detection(work, sim, r['stdout'])
            report = work/'reports'/'stage1_regression.txt'
        elif stage == 'stage2':
            rec['build_success'] = _built_stage2(sim)
            rec['detectors'] = _stage2_detection(sim, r['stdout'])
            report = work/'reports'/'stage2_regression_verilator.txt'
        else:
            rec['build_success'] = _stage3_binaries(sim)
            report = work/'reports'/'stage3_5_coverage_verilator.txt'
            rec['detectors'] = _stage3_detection(report, sim, expected)
            if not rec['detectors'] and r['stdout']:
                # Include named unit failures if checker failed before report write.
                rec['detectors'] = _stage3_detection_from_console(r['stdout'], expected)
        if report.is_file():
            shutil.copy2(report, outdir/'verification_report.txt')

        if r['timeout']:
            rec['status'] = 'CAUGHT' if rec['build_success'] and _started_and_incomplete(stage, sim) else 'INVALID'
            rec['detectors'] = ([f'timeout after {timeout}s: simulator startup proven, completion requirement violated']
                                if rec['status']=='CAUGHT' else ['timeout without proof of simulator startup; INVALID'])
        elif not rec['build_success']:
            rec['status'] = 'INVALID'
            rec['detectors'] = ['required build outputs missing; not counted as detection']
        elif rec['detectors'] and r['exit_code'] != 0:
            rec['status'] = 'CAUGHT'
        elif r['exit_code'] == 0 and _pass_marker(stage, r['stdout']):
            rec['status'] = 'MISSED'
            rec['detectors'] = ['unmutated regression passed with mutant applied']
        else:
            rec['status'] = 'INVALID'
            rec['detectors'] = ['missing or malformed verification result; INVALID']
        return rec
    except KeyboardInterrupt:
        rec['status'] = 'INVALID'
        rec['detectors'] = ['interrupted; partial scratch evidence retained in run directory']
        (outdir/'result.json').write_text(json.dumps(rec,indent=2)+'\n',encoding='utf-8')
        raise
    except Exception as exc:
        rec['status'] = 'INVALID'
        rec['error'] = repr(exc)
        return rec
    finally:
        tmp.cleanup()


def _stage3_detection_from_console(text, expected):
    if expected == 'unit:wrapper':
        return [ln.strip() for ln in text.splitlines() if
                'M wrapper unit: FAIL' in ln or 'MD_EXEC_RESULT: FAIL' in ln]
    if expected == 'unit:divider':
        return [ln.strip() for ln in text.splitlines() if
                'Divider unit: FAIL' in ln or 'DIV_ITER_RESULT: FAIL' in ln]
    found=[]
    failed=expected.split(':',1)[1] if expected.startswith('test:') else ''
    for ln in text.splitlines():
        if 'TEST_RESULT: FAIL' in ln:
            if f'/{failed}.hex' in ln or f'\\{failed}.hex' in ln:
                found.append(f'{failed}: explicit TEST_RESULT: FAIL')
    return found


def _started_and_incomplete(stage, sim):
    def incomplete(path):
        return path.is_file() and not any(line.startswith('HALT ') for line in path.read_text(encoding='utf-8',errors='replace').splitlines())
    if stage == 'stage1':
        if not _built_stage1(sim): return False
        man=sim.parent/'tests'/'directed'/'rv32i'/'manifest.csv'
        if not man.is_file(): return False
        for row in csv.DictReader(man.open(newline='')):
            if incomplete(sim/(row['name']+'.rtl.trace')): return True
            if not (sim/(row['name']+'.rtl.trace')).is_file(): return False
        return False
    if stage == 'stage2':
        if not _built_stage2(sim): return False
        manifest=sim/'manifest_all.csv'
        if not manifest.is_file(): return False
        for row in csv.DictReader(manifest.open(newline='')):
            n=row['name']
            if incomplete(sim/(n+'.s1.trace')): return True
            if not (sim/(n+'.s1.trace')).is_file(): return False
            if incomplete(sim/(n+'.pipe.trace')): return True
            if not (sim/(n+'.pipe.trace')).is_file(): return False
        return False
    # Stage 3.5 starts paired golden/pipeline runs in manifest order. A trace
    # created without its corresponding completed log proves simulator entry.
    if not _stage3_binaries(sim):
        return False
    manifest = sim/'manifest_all.csv'
    if not manifest.is_file():
        return False
    for row in csv.DictReader(manifest.open(newline='')):
        n = row['name']
        if not (sim/(n+'.s1.log')).is_file():
            return False
        if not (sim/(n+'.pipe.log')).is_file():
            return (sim/(n+'.pipe.trace')).is_file()
    return False


def _pass_marker(stage, text):
    marker = {'stage1':'STAGE1_REGRESSION PASS',
              'stage2':'STAGE2_REGRESSION_VERILATOR PASS',
              'stage35':'STAGE3_5_REGRESSION_VERILATOR PASS'}[stage]
    return marker in text


def _write_summary(path, body):
    lines = ['Stage 3.6 M-extension mutation audit (Verilator only)',
             f"Generated UTC: {datetime.datetime.now(datetime.timezone.utc).isoformat()}",
             'The Stage 3.5 finite dictionary is not full RISC-V coverage.',
             '', body]
    path.write_text('\n'.join(lines)+'\n', encoding='utf-8')


def _preflight():
    problems = []
    for path in (STAGE35_XSIM, STAGE35_VERILATOR):
        if not path.is_file():
            problems.append(f'missing saved Stage 3.5 report: {path.relative_to(ROOT)}')
            continue
        text = path.read_text(encoding='utf-8', errors='replace')
        label = 'XSIM' if 'xsim' in path.name else 'VERILATOR'
        for marker in ('TOTAL: 209 passed, 0 failed, 209 total',
                       'Defined bins hit: 108/108', 'Coverage data errors: 0',
                       f'STAGE3_5_REGRESSION_{label} PASS'):
            if marker not in text:
                problems.append(f'{path.name}: missing marker {marker}')
    for path in (REPORT_ROOT/'stage3_5_coverage_xsim.txt',REPORT_ROOT/'stage3_5_coverage_verilator.txt'):
        if not path.is_file(): problems.append(f'original failed report not preserved: {path.relative_to(ROOT)}')
    for ident, _, relpath, old, new, _ in MUTANTS:
        try:
            changes = _preview(ROOT, relpath, old, new)
            if not changes:
                problems.append(f'{ident}: no source change')
        except Exception as exc:
            problems.append(f'{ident}: {exc}')
    legacy_counts={}
    for script in ('mutation_check.py', 'mutation_check_stage2.py'):
        try:
            table=_read_mutation_table(HERE / script)
            legacy_counts[script]=len(table)
            for i,(_,relpath,old,new) in enumerate(table):
                source=(ROOT/relpath).read_text(encoding='utf-8')
                for before,_ in _replacements(old,new):
                    if before not in source:
                        problems.append(f'{script}[{i}]: mutation pattern absent in current source {relpath}')
        except Exception as exc:
            problems.append(str(exc))
    return problems,legacy_counts


def _preview(root, relpath, old, new):
    text = (root/relpath).read_text(encoding='utf-8')
    result=[]
    for before, after in _replacements(old,new):
        count=text.count(before)
        if not count:
            raise ValueError(f'pattern absent in current source {relpath}: {before!r}')
        mutated=text.replace(before,after,1)
        if mutated==text:
            raise ValueError(f'no-op replacement in {relpath}')
        result.append((before,after,count))
        text=mutated
    return result


def _main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--preflight-only',action='store_true',help='check saved Stage 3.5 evidence and mutation patterns without running Verilator')
    ap.add_argument('--baseline-timeout',type=int,default=3600)
    ap.add_argument('--mutant-timeout',type=int,default=1800)
    args=ap.parse_args()
    problems,legacy_counts=_preflight()
    if problems:
        print('STAGE3_6_PREFLIGHT FAIL')
        for p in problems: print('ERROR:',p)
        return 2
    print('STAGE3_5_SAVED_REANALYSIS PASS XSim=209/209 bins=108/108 errors=0; Verilator=209/209 bins=108/108 errors=0')
    if args.preflight_only:
        print(f'STAGE3_6_MUTATION_PREFLIGHT PASS M_mutants={len(MUTANTS)} stage1_patterns={legacy_counts["mutation_check.py"]} stage2_patterns={legacy_counts["mutation_check_stage2.py"]} baseline=not-run')
        return 0
    if not sys.platform.startswith('linux'):
        print('INVALID: full campaign requires Ubuntu/WSL Linux; no mutation run started')
        return 2
    verilator=shutil.which('verilator')
    if not verilator:
        print('INVALID: Verilator not found in initialized Ubuntu environment; no mutation run started')
        return 2
    v=_command([verilator,'--version'],ROOT,os.environ.copy(),30)
    if v['exit_code'] != 0 or v['timeout']:
        print('INVALID: Verilator version probe failed; no mutation run started')
        return 2
    version=v['stdout'].strip()
    stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%d_%H%M%S_UTC')
    run_dir=REPORT_ROOT/'stage3_6_mutation_runs'/('run_'+stamp)
    run_dir.mkdir(parents=True,exist_ok=False)
    summary_path=REPORT_ROOT/'stage3_6_mutation_verilator.txt'
    py=sys.executable
    body_lines=[f'Branch baseline source: {ROOT}',f'Python: {sys.version.split()[0]}',f'Verilator: {version}',
                'Mutation source changes are applied only in per-run scratch copies.',
                'Legacy Stage 1/2 patterns are loaded from unchanged mutation_check.py and mutation_check_stage2.py.',
                'CAUGHT requires successful builds plus named failing checks. Missing builds/results => INVALID.', '']
    by_id={}
    baseline=_baseline(run_dir,args.baseline_timeout,py,version)
    for stage,record in baseline.items():
        body_lines.append(f'BASELINE {stage}: {record["status"]} exit={record["exit_code"]} required={record["pass_marker"]}')
    if len(baseline)!=3 or any(x['status']!='PASS' for x in baseline.values()):
        body_lines += ['', 'CAMPAIGN NOT STARTED: passing Stage 1, Stage 2, and Stage 3.5 baselines are required.']
        _write_summary(summary_path,'\n'.join(body_lines))
        print('\n'.join(body_lines)); print(f'RUN_REPORT={run_dir}'); return 1

    tables=[]
    for stage, script in (('stage1','mutation_check.py'),('stage2','mutation_check_stage2.py')):
        for i, item in enumerate(_read_mutation_table(HERE/script)):
            name, relpath, old, new = item
            tables.append((stage,f'{stage.upper()}-{i:02d}',name,relpath,old,new,'legacy regression check'))
    for ident,name,relpath,old,new,expected in MUTANTS:
        tables.append(('stage35',ident,name,relpath,old,new,expected))
    for stage,ident,name,relpath,old,new,expected in tables:
        rec=_run_one(run_dir,stage,ident,name,relpath,old,new,expected,
                     args.mutant_timeout,py,version)
        by_id[ident]=rec
        (run_dir/'mutants'/ident/'result.json').write_text(json.dumps(rec,indent=2)+'\n',encoding='utf-8')
        body_lines.append(f'{ident} [{stage}] {rec["status"]}: {name}; build={rec["build_success"]} '
                          f'exit={rec["runner_exit_code"]} elapsed={rec.get("elapsed_seconds","-")}s')
        body_lines.append(f'  expected={expected}; detected=' + ('; '.join(rec.get('detectors',[])) or 'none'))
        if rec.get('pattern_error'): body_lines.append('  pattern_error='+rec['pattern_error'])
        _write_summary(summary_path,'\n'.join(body_lines))
        print(body_lines[-2]); print(body_lines[-1],flush=True)
    counts={s:sum(r['stage']==s and r['status']=='CAUGHT' for r in by_id.values()) for s in ('stage1','stage2','stage35')}
    statuses={s:{k:sum(r['stage']==s and r['status']==k for r in by_id.values())
                  for k in ('CAUGHT','MISSED','INVALID','EQUIVALENT')} for s in ('stage1','stage2','stage35')}
    body_lines += ['', 'SUMMARY (Verilator-only; no XSim mutation evidence):']
    for s in ('stage1','stage2','stage35'): body_lines.append(f'{s}: {statuses[s]}')
    body_lines.append(f'STAGE3_6_MUTATION_AUDIT: {sum(1 for x in by_id.values() if x["status"]=="CAUGHT")}/{len(by_id)} CAUGHT; MISSED={sum(x["status"]=="MISSED" for x in by_id.values())}; INVALID={sum(x["status"]=="INVALID" for x in by_id.values())}')
    body_lines += ['', 'Scope limitation: this finite mutation set measures the listed defect classes only; it is not full RISC-V coverage.']
    _write_summary(summary_path,'\n'.join(body_lines))
    print(body_lines[-3]); print(f'RUN_REPORT={run_dir}'); print(f'SUMMARY_REPORT={summary_path}')
    return 0 if all(not s['INVALID'] and not s['MISSED'] for s in statuses.values()) else 1


if __name__=='__main__':
    try:
        raise SystemExit(_main())
    except KeyboardInterrupt:
        print('INTERRUPTED: original checkout was never mutated; current scratch may be incomplete',file=sys.stderr)
        raise SystemExit(130)
