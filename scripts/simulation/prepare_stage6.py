#!/usr/bin/env python3
"""Preflight the unchanged 248-case Stage 5 suite plus Stage 6 software."""
import csv
import hashlib
import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
import rv32c_asm
import rv32imc_iss


def fail(message):
    print(f"STAGE6_PREPARE FAIL: {message}", file=sys.stderr)
    raise SystemExit(1)


def main():
    if len(sys.argv) != 2:
        fail(f"usage: {Path(sys.argv[0]).name} <fresh-output-directory>")
    out = Path(sys.argv[1]).resolve()
    if out.exists() and any(out.iterdir()):
        fail(f"output directory is not fresh: {out}")
    out.mkdir(parents=True, exist_ok=True)

    selftest = subprocess.run([sys.executable, str(HERE / "stage6_software_selftest.py")],
                              cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    print(selftest.stdout, end="")
    if selftest.returncode or "STAGE6_SOFTWARE_SELFTEST PASS" not in selftest.stdout:
        fail("independent Stage 6 software selftest did not pass")

    legacy = subprocess.run([sys.executable, str(HERE / "prepare_stage4_4.py"), str(out), "--enable-a"],
                            cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    (out / "stage5_preparation.log").write_text(legacy.stdout, encoding="utf-8", newline="\n")
    if legacy.returncode or "STAGE4_4_SOFTWARE_PREFLIGHT PASS legacy=209 c_cases=21 total=230 images=230 references=230 errors=0" not in legacy.stdout:
        fail("Stage 5 software preflight failed; full expected inventory is 248 (230 legacy/C + 18 A)")
    inventories = {key: list(csv.DictReader((out / key).open(newline="")))
                   for key in ("manifest_all.csv", "c_manifest.csv", "a_manifest.csv")}
    if tuple(len(inventories[k]) for k in ("manifest_all.csv", "c_manifest.csv", "a_manifest.csv")) != (209, 21, 18):
        fail("Stage 5 inventory mismatch; expected 209 legacy + 21 C + 18 A cases")
    base_names = {r["name"] for rows0 in inventories.values() for r in rows0}

    suite = ROOT / "tests" / "directed" / "rv32imac_stage6"
    manifest = suite / "manifest.csv"
    if not manifest.is_file():
        fail(f"missing Stage 6 manifest: {manifest}")
    rows = list(csv.DictReader(manifest.open(newline="")))
    if len(rows) != 11 or len({r.get("name") for r in rows}) != len(rows):
        fail(f"Stage 6 manifest must contain eleven unique cases, found {len(rows)}")
    if base_names & {r["name"] for r in rows}:
        fail("Stage 6 case names overlap the Stage 5 manifest")

    hex_dir, ref_dir = out / "z_hex", out / "z_iss"
    hex_dir.mkdir(); ref_dir.mkdir()
    prepared = []
    errors = []
    for row in rows:
        name = row["name"]
        source = suite / (name + ".s")
        if not source.is_file():
            errors.append(f"missing source: {source}")
            continue
        try:
            byte_mem = rv32c_asm.assemble_bytes(source.read_text(encoding="utf-8"), c_enabled=True, a_enabled=True)
            words = rv32c_asm.to_words(byte_mem)
            atom_events, z_events = [], []
            cause, regs, trace, footer, oob, retired = rv32imc_iss.run(
                words, c_enabled=True, a_enabled=True, z_enabled=True,
                a_events=atom_events, z_events=z_events)
            if cause != int(row["expect_cause"]) or oob:
                errors.append(f"{name}: cause={cause} expected={row['expect_cause']} oob={oob}")
            if row["check_gp"] == "1" and cause == rv32imc_iss.CAUSE_ECALL and regs[3] != 1:
                errors.append(f"{name}: expected gp=1, got {regs[3]:08x}")
            (hex_dir / (name + ".hex")).write_text(rv32c_asm.to_hex(byte_mem), encoding="ascii", newline="\n")
            trace_header = "TRACE_V3 RV32IMAC pc raw_insn ilen_bytes expanded_insn rd rdval st_size st_addr st_data atomic_sidecar\n"
            (ref_dir / (name + ".trace")).write_text(trace_header + "\n".join(trace + footer) + "\n", encoding="ascii", newline="\n")
            with (ref_dir / (name + ".a.tsv")).open("w", newline="") as f:
                w = csv.writer(f, delimiter="\t", lineterminator="\n")
                w.writerow(["pc", "raw", "op", "aq", "rl", "rd", "rs1", "rs2", "address", "old", "source", "new", "sc_status", "reservation_before", "reservation_after"])
                w.writerows((f"{e[0]:08x}", f"{e[1]:08x}", *e[2:8], f"{e[8]:08x}",
                             "-" if e[9] is None else f"{e[9]:08x}", f"{e[10]:08x}",
                             "-" if e[11] is None else f"{e[11]:08x}", *e[12:]) for e in atom_events)
            with (ref_dir / (name + ".z.tsv")).open("w", newline="") as f:
                w = csv.writer(f, delimiter="\t", lineterminator="\n")
                w.writerow(["kind", "pc", "raw", "ilen", "csr_or_pcnext", "funct3", "source_index", "source", "old", "new", "write_intent"])
                for event in z_events:
                    if event[0] == "FENCEI":
                        w.writerow([event[0], f"{event[1]:08x}", f"{event[2]:08x}", event[3], f"{event[4]:08x}", "-", "-", "-", "-", "-", "-"])
                    else:
                        w.writerow([event[0], f"{event[1]:08x}", f"{event[2]:08x}", event[3], f"{event[4]:03x}", event[5], event[6], f"{event[7]:08x}", f"{event[8]:08x}", f"{event[9]:08x}", event[10]])
            prepared.append({"name": name, "expect_cause": row["expect_cause"], "check_gp": row["check_gp"],
                             "hexpath": (hex_dir / (name + ".hex")).relative_to(ROOT).as_posix(),
                             "atomics": len(atom_events), "z_events": len(z_events), "retired": retired})
        except Exception as exc:
            errors.append(f"{name}: {type(exc).__name__}: {exc}")
    with (out / "z_manifest.csv").open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["name", "expect_cause", "check_gp", "hexpath", "atomics", "z_events", "retired"], lineterminator="\n")
        w.writeheader(); w.writerows(prepared)
    for row in prepared:
        name = row["name"]
        for path in (hex_dir / (name + ".hex"), ref_dir / (name + ".trace"), ref_dir / (name + ".a.tsv"), ref_dir / (name + ".z.tsv")):
            if not path.is_file() or path.stat().st_size == 0:
                errors.append(f"missing/empty artifact: {path}")
    if errors:
        for error in errors: print("ERROR: " + error)
        fail(f"{len(errors)} software or artifact check(s) failed")
    digest = hashlib.sha256(manifest.read_bytes()).hexdigest()
    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    provenance = [f"git_head={head.stdout.strip() if head.returncode == 0 else 'unavailable'}",
                  f"python={sys.version.split()[0]}", f"z_manifest_sha256={digest}"]
    for path in (HERE / "prepare_stage6.py", HERE / "stage6_software_selftest.py",
                 HERE / "rv32_asm.py", HERE / "rv32c_asm.py", HERE / "rv32c_model.py",
                 HERE / "rv32a_model.py", HERE / "rv32imc_iss.py",
                 ROOT / "rtl/packages/rv32_pkg.sv", ROOT / "rtl/packages/rv_pipe_pkg.sv",
                 ROOT / "rtl/decoder/rv_decoder.sv", ROOT / "rtl/core/rv_core_single.sv",
                 ROOT / "rtl/core/rv_core_pipe.sv", ROOT / "rtl/pipeline/rv_ex_stage.sv",
                 ROOT / "tests/directed/rv32imac_stage6/manifest.csv", *suite.glob("*.s")):
        provenance.append(f"sha256 {path.relative_to(ROOT).as_posix()}={hashlib.sha256(path.read_bytes()).hexdigest()}")
    marker = "STAGE6_PREPARATION PASS stage5=248 stage6=11 total=259 images=259 references=259 errors=0"
    (out / "stage6_preparation.txt").write_text(
        marker + "\nbase_stage5_cases=248\nstage6_cases=11\ncombined_cases=259\n" + "\n".join(provenance) + "\n",
        encoding="ascii", newline="\n")
    print(marker)


if __name__ == "__main__":
    main()
