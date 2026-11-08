#!/usr/bin/env python3
"""Preflight and prepare Stage 4.4 suites plus optional Stage 5 A inputs."""
import csv, os, re, subprocess, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
import rv32c_asm, rv32imc_iss
import rv32_asm, rv32i_iss

ENABLE_A = '--enable-a' in sys.argv[2:]
out = Path(next(arg for arg in sys.argv[1:] if arg != '--enable-a')).resolve()
if out.exists() and any(out.iterdir()):
    print(f'STAGE4_4_SOFTWARE_PREFLIGHT FAIL output_not_fresh={out}', file=sys.stderr)
    raise SystemExit(1)
legacy_suites = ('rv32i','pipeline','pipeline_m','m_extension','pipeline_div','pipeline_div_coverage')
software_suites = [('legacy', folder) for folder in legacy_suites] + [
    ('c', 'rv32imc'), ('c', 'rv32imc_pipeline')]
if ENABLE_A:
    software_suites += [('a', folder) for folder in
                        ('rv32ima_software', 'rv32imac_software', 'rv32imac_pipeline_a')]
structure_errors = []
suite_rows = {}
all_names = {}
suite_totals = {'legacy': 0, 'c': 0, 'a': 0}
for kind, folder in software_suites:
    suite_dir = ROOT/'tests'/'directed'/folder
    manifest = suite_dir/'manifest.csv'
    if not suite_dir.is_dir():
        structure_errors.append(f'missing suite directory: {suite_dir}')
        continue
    if not manifest.is_file():
        structure_errors.append(f'missing manifest: {manifest}')
        continue
    try:
        rows = list(csv.DictReader(manifest.open(newline='')))
    except Exception as exc:
        structure_errors.append(f'malformed manifest {manifest}: {type(exc).__name__}: {exc}')
        continue
    required_fields = {'name', 'expect_cause', 'check_gp'}
    if not rows and kind == 'a':
        structure_errors.append(f'empty A suite manifest: {manifest}')
    if rows and not required_fields.issubset(rows[0]):
        structure_errors.append(f'malformed manifest header {manifest}: expected fields={sorted(required_fields)}')
        continue
    suite_rows[folder] = rows
    suite_totals[kind] += len(rows)
    for row in rows:
        name = row.get('name', '').strip()
        if not name:
            structure_errors.append(f'empty test name in {manifest}')
            continue
        if name in all_names:
            structure_errors.append(f'duplicate output name {name}: {all_names[name]} and {manifest}')
        else:
            all_names[name] = manifest
        source = suite_dir/(name+'.s')
        if not source.is_file():
            structure_errors.append(f'missing source for {name}: {source}')
        try:
            if int(row['expect_cause']) < 0 or row['check_gp'] not in ('0', '1'):
                raise ValueError('invalid expected cause/check_gp value')
        except Exception as exc:
            structure_errors.append(f'invalid expectation for {name} in {manifest}: {exc}')
if suite_totals['legacy'] != 209:
    structure_errors.append(f'legacy inventory expected=209 actual={suite_totals["legacy"]}')
if suite_totals['c'] != 21:
    structure_errors.append(f'C inventory expected=21 actual={suite_totals["c"]}')
if ENABLE_A and suite_totals['a'] != 18:
    structure_errors.append(f'A/C+A inventory expected=18 actual={suite_totals["a"]}')
if structure_errors:
    for error in structure_errors:
        print('STRUCTURE_PREFLIGHT_ERROR '+error, file=sys.stderr)
    print(f'STAGE4_4_STRUCTURE_PREFLIGHT FAIL errors={len(structure_errors)}')
    raise SystemExit(1)
print(f'STAGE4_4_STRUCTURE_PREFLIGHT PASS legacy={suite_totals["legacy"]} c_cases={suite_totals["c"]} a_cases={suite_totals["a"]} total={sum(suite_totals.values())} unique_names={len(all_names)}', flush=True)
out.mkdir(parents=True, exist_ok=True)
legacy_sources = []
legacy_inventory = 0
source_errors = []
for folder in legacy_suites:
    for row in suite_rows[folder]:
        legacy_inventory += 1
        source = ROOT/'tests'/'directed'/folder/(row['name']+'.s')
        legacy_sources.append(source)
        if not source.is_file(): source_errors.append(f'missing source: {source}')
if legacy_inventory != 209: source_errors.append(f'legacy source inventory expected=209 actual={legacy_inventory}')
if source_errors:
    for error in source_errors: print('SOURCE_PREFLIGHT_ERROR '+error, file=sys.stderr)
    raise SystemExit(1)
vectors = subprocess.run([sys.executable, str(HERE/'generate_stage4_2_vectors.py'), str(out/'vectors.txt')], cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
(out/'vectors_prepare.log').write_text(vectors.stdout, encoding='utf-8')
if vectors.returncode or 'RV32C_VECTOR_GENERATION PASS halfwords=65536 oracle_mismatches=0' not in vectors.stdout:
    print(vectors.stdout, file=sys.stderr); raise SystemExit(vectors.returncode or 1)
# Stage 3.7's preparation remains the source of the released C-disabled 209-case set.
legacy = subprocess.run([sys.executable, str(HERE/'prepare_stage5.py'), str(out)], cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
(out/'legacy_prepare.log').write_text(legacy.stdout, encoding='utf-8')
if legacy.returncode:
    print(legacy.stdout, file=sys.stderr); raise SystemExit(legacy.returncode)
if 'STAGE3_5_PREPARED tests=209' not in legacy.stdout:
    raise SystemExit('legacy preparation did not report STAGE3_5_PREPARED tests=209')
legacy_rows = list(csv.DictReader((out/'manifest_all.csv').open(newline='')))
if len(legacy_rows) != 209: raise SystemExit(f'legacy manifest count expected=209 actual={len(legacy_rows)}')
legacy_sources_by_name = {}; legacy_manifest_by_name = {}
for folder in legacy_suites:
    for row in suite_rows[folder]:
        legacy_sources_by_name[row['name']] = ROOT/'tests'/'directed'/folder/(row['name']+'.s')
        legacy_manifest_by_name[row['name']] = row
legacy_errors = []
for index, row in enumerate(legacy_rows, 1):
    name = row['name']; src = legacy_sources_by_name.get(name)
    if src is None:
        legacy_errors.append(f'{name}: no current source manifest entry'); continue
    image_path = ROOT/row['hexpath']; reference_path = out/'iss'/(name+'.iss.trace')
    missing = [p for p in (src, image_path, reference_path) if not p.is_file()]
    if missing:
        legacy_errors.extend(f'{name}: missing {p}' for p in missing); continue
    try:
        mem = rv32_asm.assemble(src.read_text(encoding='utf-8'))
        expected_hex = rv32_asm.to_hex(mem)
        words = [mem.get(4*i, 0) for i in range(max(mem)//4+1)]
        cause, regs, trace, footer, oob, _ = rv32i_iss.run(words)
        expected_trace = '\n'.join(trace+footer)+'\n'
        source_manifest = legacy_manifest_by_name[name]
        if image_path.read_text(encoding='ascii') != expected_hex: legacy_errors.append(f'{name}: image differs from current source')
        if reference_path.read_text(encoding='ascii') != expected_trace: legacy_errors.append(f'{name}: ISS reference differs from current source/model')
        if cause != int(source_manifest['expect_cause']) or oob or (source_manifest['check_gp']=='1' and regs[3] != 1):
            legacy_errors.append(f'{name}: ISS expected_cause={source_manifest["expect_cause"]} actual_cause={cause} gp={regs[3]:08x} oob={oob}')
    except Exception as exc:
        legacy_errors.append(f'{name}: {type(exc).__name__}: {exc}')
if legacy_errors:
    for error in legacy_errors: print('LEGACY_REFERENCE_ERROR '+error, file=sys.stderr)
    print(f'STAGE4_4_LEGACY_PREFLIGHT FAIL tests=209 errors={len(legacy_errors)}')
    raise SystemExit(1)
print('STAGE4_4_LEGACY_PREFLIGHT PASS tests=209 source_consistent=209 images=209 references=209', flush=True)

suites = [('rv32imc', 'rv32imc'), ('rv32imc_pipeline', 'rv32imc_pipeline')]
all_rows = []; sources = []; errors = []
expected_total = sum(len(suite_rows[folder]) for _, folder in suites)
for suite, folder in suites:
    suite_path = ROOT/'tests'/'directed'/folder
    rows = suite_rows[folder]
    for row in rows:
        src = suite_path/(row['name']+'.s'); sources.append(src)
        try:
            image = rv32c_asm.assemble_bytes(src.read_text(encoding='utf-8'), c_enabled=True)
            words = rv32c_asm.to_words(image)
            cause, regs, trace, footer, oob, instret = rv32imc_iss.run(words, c_enabled=True)
            expected = int(row['expect_cause'])
            if cause != expected or oob:
                errors.append(f'{src}: expected_cause={expected} actual_cause={cause} oob={oob}')
            hp = out/'c_hex'/(row['name']+'.hex'); hp.parent.mkdir(exist_ok=True)
            tp = out/'c_iss'/(row['name']+'.trace'); tp.parent.mkdir(exist_ok=True)
            hp.write_text(rv32c_asm.to_hex(image), encoding='ascii', newline='\n')
            tp.write_text('TRACE_V2 RV32IMC pc raw_insn ilen_bytes expanded_insn rd rdval st_size st_addr st_data\n'+'\n'.join(trace+footer)+'\n', encoding='ascii', newline='\n')
            all_rows.append({**row, 'suite': suite, 'hexpath': hp.relative_to(ROOT).as_posix()})
            print(f'PREPARED {suite} {len(all_rows)}/{expected_total} {row["name"]} cause={cause} instret={instret}', flush=True)
        except Exception as exc:
            errors.append(f'{src}: {type(exc).__name__}: {exc}')
for src in sources:
    if not src.is_file(): errors.append(f'missing source: {src}')
if errors:
    for error in errors: print('C_PREPARATION_ERROR '+error, file=sys.stderr)
    print(f'STAGE4_4_SOFTWARE_PREFLIGHT FAIL legacy={len(legacy_rows)} c_sources={len(sources)} errors={len(errors)}')
    raise SystemExit(1)
with (out/'c_manifest.csv').open('w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=['name','expect_cause','check_gp','suite','hexpath'], lineterminator='\n')
    writer.writeheader(); writer.writerows(all_rows)
# Validate every generated reference and image against current source/ISS before any simulator compilation.
problems=[]
for row in all_rows:
    src=ROOT/'tests'/'directed'/row['suite']/(row['name']+'.s')
    image=rv32c_asm.assemble_bytes(src.read_text(encoding='utf-8'), c_enabled=True)
    trace_result=rv32imc_iss.run(rv32c_asm.to_words(image), c_enabled=True)
    expected='TRACE_V2 RV32IMC pc raw_insn ilen_bytes expanded_insn rd rdval st_size st_addr st_data\n'+'\n'.join(trace_result[2]+trace_result[3])+'\n'
    if (out/'c_hex'/(row['name']+'.hex')).read_text(encoding='ascii') != rv32c_asm.to_hex(image): problems.append(f'image/source mismatch {src}')
    if (out/'c_iss'/(row['name']+'.trace')).read_text(encoding='ascii') != expected: problems.append(f'ISS/source mismatch {src}')
if problems:
    for problem in problems: print('REFERENCE_PREFLIGHT_ERROR '+problem, file=sys.stderr)
    raise SystemExit(1)
print(f'STAGE4_4_SOFTWARE_PREFLIGHT PASS legacy=209 c_cases={len(all_rows)} total={209+len(all_rows)} images={209+len(all_rows)} references={209+len(all_rows)} errors=0', flush=True)

if ENABLE_A:
    a_suites = ('rv32ima_software', 'rv32imac_software', 'rv32imac_pipeline_a')
    a_rows = []; a_errors = []
    for folder in a_suites:
        suite_dir = ROOT/'tests'/'directed'/folder
        for row in suite_rows[folder]:
            source = suite_dir/(row['name']+'.s')
            try:
                if not source.is_file(): raise FileNotFoundError(source)
                image = rv32c_asm.assemble_bytes(source.read_text(encoding='utf-8'), c_enabled=True, a_enabled=True)
                events = []
                result = rv32imc_iss.run(rv32c_asm.to_words(image), c_enabled=True, a_enabled=True, a_events=events)
                cause, oob = result[0], result[4]
                if cause != int(row['expect_cause']) or oob:
                    raise ValueError(f'expected_cause={row["expect_cause"]} actual_cause={cause} oob={oob}')
                hp = out/'a_hex'/(row['name']+'.hex'); hp.parent.mkdir(exist_ok=True)
                tp = out/'a_iss'/(row['name']+'.trace'); tp.parent.mkdir(exist_ok=True)
                ap = out/'a_iss'/(row['name']+'.a.tsv')
                hp.write_text(rv32c_asm.to_hex(image), encoding='ascii', newline='\n')
                tp.write_text('TRACE_V3 RV32IMAC pc raw_insn ilen_bytes expanded_insn rd rdval st_size st_addr st_data atomic_sidecar\n'+'\n'.join(result[2]+result[3])+'\n', encoding='ascii', newline='\n')
                with ap.open('w', newline='', encoding='ascii') as dst:
                    import csv as _csv
                    writer = _csv.writer(dst, delimiter='\t', lineterminator='\n')
                    writer.writerow(['pc','raw','op','aq','rl','rd','rs1','rs2','address','old','source','new','sc_status','reservation_before','reservation_after'])
                    writer.writerows((f'{row[0]:08x}', f'{row[1]:08x}', *row[2:8], f'{row[8]:08x}',
                                      '-' if row[9] is None else f'{row[9]:08x}', f'{row[10]:08x}',
                                      '-' if row[11] is None else f'{row[11]:08x}', *row[12:]) for row in events)
                a_rows.append({**row, 'suite': folder, 'hexpath': hp.relative_to(ROOT).as_posix()})
                print(f'PREPARED A {len(a_rows)} {source.name} cause={cause} instret={result[5]} atomics={len(events)}', flush=True)
            except Exception as exc:
                a_errors.append(f'{source}: {type(exc).__name__}: {exc}')
    if a_errors:
        for error in a_errors: print('A_PREPARATION_ERROR '+error, file=sys.stderr)
        raise SystemExit(1)
    if len(a_rows) != 18:
        raise SystemExit(f'STAGE5_A_ARTIFACT_PREFLIGHT FAIL expected_cases=18 actual={len(a_rows)}')
    with (out/'a_manifest.csv').open('w', newline='', encoding='utf-8') as dst:
        writer=csv.DictWriter(dst, fieldnames=['name','expect_cause','check_gp','suite','hexpath'], lineterminator='\n')
        writer.writeheader(); writer.writerows(a_rows)
    print(f'STAGE5_A_ARTIFACT_PREFLIGHT PASS cases={len(a_rows)} images={len(a_rows)} references={len(a_rows)} atomic_sidecars={len(a_rows)}', flush=True)
