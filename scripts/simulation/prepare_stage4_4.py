#!/usr/bin/env python3
"""Prepare and independently validate Stage 4.4 legacy and RV32IMC pipeline inputs."""
import csv, os, re, subprocess, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
import rv32c_asm, rv32imc_iss
import rv32_asm, rv32i_iss

out = Path(sys.argv[1]).resolve()
if out.exists() and any(out.iterdir()):
    print(f'STAGE4_4_SOFTWARE_PREFLIGHT FAIL output_not_fresh={out}', file=sys.stderr)
    raise SystemExit(1)
out.mkdir(parents=True, exist_ok=True)
legacy_suites = ('rv32i','pipeline','pipeline_m','m_extension','pipeline_div','pipeline_div_coverage')
legacy_sources = []
legacy_inventory = 0
source_errors = []
for folder in legacy_suites:
    manifest = ROOT/'tests'/'directed'/folder/'manifest.csv'
    if not manifest.is_file():
        source_errors.append(f'missing manifest: {manifest}'); continue
    for row in csv.DictReader(manifest.open(newline='')):
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
    for row in csv.DictReader((ROOT/'tests'/'directed'/folder/'manifest.csv').open(newline='')):
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
expected_total = sum(len(list(csv.DictReader((ROOT/'tests'/'directed'/folder/'manifest.csv').open(newline='')))) for _, folder in suites)
for suite, folder in suites:
    suite_path = ROOT/'tests'/'directed'/folder
    rows = list(csv.DictReader((suite_path/'manifest.csv').open(newline='')))
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
