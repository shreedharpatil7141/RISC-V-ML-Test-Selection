#!/usr/bin/env python3
"""Audit Stage-1 mutants without modifying the source checkout or mutation_check.py."""
import ast
import datetime
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
MUTATION_SCRIPT = ROOT / 'scripts' / 'simulation' / 'mutation_check.py'
REPORT_ROOT = ROOT / 'reports' / 'stage1_mutation_audit'
STAMP = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%d_%H%M%S_UTC')
RUN_DIR = REPORT_ROOT / ('run_' + STAMP)
REPORT = RUN_DIR / 'audit.txt'
COPY_DIRS = ('rtl', 'scripts/simulation', 'tests/directed/rv32i', 'verification/environment')
sys.path.insert(0, str(ROOT / 'scripts' / 'simulation'))
from rv32_asm import assemble
import rv32i_iss


def load_mutants():
    tree = ast.parse(MUTATION_SCRIPT.read_text(encoding='utf-8'))
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == 'MUT' for target in node.targets
        ):
            return ast.literal_eval(node.value)
    raise RuntimeError('Could not read MUT table from mutation_check.py')


def apply_change(source, old, new):
    pairs = old if new is None else [(old, new)]
    changed = source
    for before, after in pairs:
        if before not in changed:
            raise ValueError('mutation pattern not found: ' + repr(before))
        changed = changed.replace(before, after, 1)
    return changed


def has_real_failure(stdout, shadow, sim_dir):
    unit = re.search(r'^UNIT_RESULT: FAIL\b.*\berrors=[1-9][0-9]*.*$', stdout, re.M)
    if unit:
        assertion = re.search(r'^FAIL: .*$', stdout, re.M)
        detail = 'unit test failure: ' + unit.group(0)
        if assertion:
            detail += ' | first assertion: ' + assertion.group(0)
        return True, detail
    test = re.search(r'^\s*TEST_RESULT: FAIL\b.*$', stdout, re.M)
    if test:
        return True, 'system testbench failure: ' + test.group(0).strip()
    # A testbench can PASS its halt-cause check while the architectural trace differs.
    for diff in re.finditer(r'^(\S+)\s+(?:PASS|FAIL)\s+DIFF\s+.*$', stdout, re.M):
        name = diff.group(1)
        rtl_trace = sim_dir / (name + '.rtl.trace')
        source = shadow / 'tests' / 'directed' / 'rv32i' / (name + '.s')
        if not rtl_trace.is_file() or not source.is_file():
            continue
        mem = assemble(source.read_text(encoding='utf-8'))
        words = [mem.get(4 * i, 0) for i in range(max(mem) // 4 + 1)]
        _, _, trace, footer, _, _ = rv32i_iss.run(words)
        expected = '\n'.join(trace + footer) + '\n'
        if rtl_trace.read_text(encoding='utf-8') != expected:
            return True, 'RTL/ISS trace mismatch: ' + diff.group(0)
    return False, ''


def write_text(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding='utf-8', newline='\n')


def make_shadow(index):
    shadow = RUN_DIR / 'workspaces' / f'mutant_{index:02d}'
    shadow.mkdir(parents=True)
    for rel in COPY_DIRS:
        src = ROOT / rel
        dst = shadow / rel
        shutil.copytree(src, dst, ignore=shutil.ignore_patterns('__pycache__', '*.pyc', 'sim_out*'))
    return shadow


def run_one(index, item):
    name, relpath, old, new = item
    target_rel = Path(relpath)
    shadow = make_shadow(index)
    target = shadow / target_rel
    original = target.read_text(encoding='utf-8')
    try:
        mutated = apply_change(original, old, new)
    except Exception as exc:
        return {'index': index, 'name': name, 'classification': 'INVALID',
                'pattern_found': False, 'mutation_applied': False, 'build_success': False,
                'returncode': None, 'detection': '', 'detail': str(exc)}

    target.write_text(mutated, encoding='utf-8', newline='\n')
    applied = target.read_text(encoding='utf-8') == mutated and mutated != original
    sim_dir = RUN_DIR / 'sim' / f'mutant_{index:02d}'
    env = dict(os.environ, SIM_DIR=str(sim_dir), NO_REPORT='1')
    cmd = [sys.executable, str(shadow / 'scripts/simulation/run_stage1.py')]
    try:
        result = subprocess.run(cmd, cwd=shadow, env=env, capture_output=True, text=True)
        stdout, stderr, returncode = result.stdout or '', result.stderr or '', result.returncode
    except Exception as exc:
        stdout, stderr, returncode = '', repr(exc), None
    finally:
        # The original checkout is never mutated; restore the scratch copy as well.
        target.write_text(original, encoding='utf-8', newline='\n')

    stem = RUN_DIR / 'mutants' / f'mutant_{index:02d}'
    write_text(stem.with_suffix('.stdout.log'), stdout)
    write_text(stem.with_suffix('.stderr.log'), stderr)
    regression = re.search(r'^STAGE1_REGRESSION (PASS|FAIL)\b', stdout, re.M)
    build_success = bool(regression) and 'BUILD FAILED' not in (stdout + '\n' + stderr)
    real_failure, detection = has_real_failure(stdout, shadow, sim_dir)
    if not applied:
        classification, detail = 'INVALID', 'mutation change could not be confirmed in scratch source'
    elif not build_success:
        classification, detail = 'INVALID', 'build/startup/regression completion not established'
    elif returncode == 0 and regression.group(1) == 'PASS':
        classification, detail = 'MISSED', 'mutant completed regression without a detected failure'
    elif returncode != 0 and regression.group(1) == 'FAIL' and real_failure:
        classification, detail = 'CAUGHT', detection
    else:
        classification, detail = 'INVALID', 'nonzero/inconsistent result without a qualifying test failure'
    return {'index': index, 'name': name, 'classification': classification,
            'pattern_change': repr(old if new is None else (old, new)),
            'pattern_found': True, 'mutation_applied': applied, 'build_success': build_success,
            'returncode': returncode, 'detection': detection, 'detail': detail,
            'regression': regression.group(1) if regression else 'NO_FINAL_MARKER',
            'stdout_log': str(stem.with_suffix('.stdout.log').relative_to(RUN_DIR)),
            'stderr_log': str(stem.with_suffix('.stderr.log').relative_to(RUN_DIR))}


def main():
    RUN_DIR.mkdir(parents=True, exist_ok=False)
    mutants = load_mutants()
    lines = [f'Stage-1 mutation audit UTC {STAMP}', f'root={ROOT}',
             f'mutation_script_sha256={__import__("hashlib").sha256(MUTATION_SCRIPT.read_bytes()).hexdigest()}',
             'Classification rules: CAUGHT requires applied mutation, complete regression (both builds reached final marker), nonzero exit, and explicit unit/system failure. Build/startup/ambiguous failures are INVALID.']
    results = []
    for index, item in enumerate(mutants):
        result = run_one(index, item)
        results.append(result)
        lines.append(' | '.join(f'{key}={value}' for key, value in result.items()))
        write_text(REPORT, '\n'.join(lines) + '\n')
        print(f"mutant {index:02d}: {result['classification']} - {result['name']} - {result['detail']}", flush=True)
    caught = sum(r['classification'] == 'CAUGHT' for r in results)
    missed = sum(r['classification'] == 'MISSED' for r in results)
    invalid = sum(r['classification'] == 'INVALID' for r in results)
    lines.append(f'MUTATION_AUDIT: {caught}/{len(mutants)} CAUGHT, {missed} MISSED, {invalid} INVALID')
    write_text(REPORT, '\n'.join(lines) + '\n')
    print(f'MUTATION_AUDIT: {caught}/{len(mutants)} CAUGHT, {missed} MISSED, {invalid} INVALID')
    print(f'REPORT: {REPORT}')
    return 0 if caught == len(mutants) and missed == 0 and invalid == 0 else 1


if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print(f'Interrupted. Source checkout remains unchanged. Partial audit: {REPORT}', file=sys.stderr)
        sys.exit(130)
