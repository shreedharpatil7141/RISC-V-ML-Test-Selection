#!/usr/bin/env python3
"""Run two focused Stage 6 pipeline mutants after matching dual-simulator baselines."""
import datetime
import difflib
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
REPORTS = ROOT / "reports"
MUTANTS = [
    ("Z01", "Immediate CSR source incorrectly reads the register file", "rtl/pipeline/rv_ex_stage.sv",
     "assign csr_source = id_ex.insn[14] ? {27'b0,id_ex.rs1} : rs1_f;",
     "assign csr_source = rs1_f;", "stage6_csr_ops"),
    ("Z02", "FENCE.I fails to redirect and refetch", "rtl/pipeline/rv_ex_stage.sv",
     "|| id_ex.is_fencei;", ";", "stage6_fencei_store_replace"),
]
SOURCE_SET = ["rtl/packages/rv32_pkg.sv", "rtl/packages/rv_pipe_pkg.sv", "rtl/decoder/rv_decoder.sv", "rtl/core/rv_core_single.sv", "rtl/core/rv_core_pipe.sv",
              "rtl/pipeline/rv_id_stage.sv", "rtl/pipeline/rv_ex_stage.sv", "rtl/pipeline/rv_mem_stage.sv",
              "scripts/simulation/rv32_asm.py", "scripts/simulation/rv32c_asm.py",
              "scripts/simulation/rv32c_model.py", "scripts/simulation/rv32a_model.py",
              "scripts/simulation/rv32imc_iss.py",
              "scripts/simulation/prepare_stage6.py", "scripts/simulation/stage6_software_selftest.py",
              "scripts/simulation/run_stage6_enabled.py",
              "verification/environment/tb_rv_core.sv", "verification/environment/tb_rv_pipe_stage4.sv",
              "verification/environment/tb_rv_stage6.sv", "verification/environment/tb_rv_decoder_z.sv"]
SOURCE_SET += [p.relative_to(ROOT).as_posix() for p in sorted((ROOT / "tests/directed/rv32imac_stage6").glob("*.csv"))]
SOURCE_SET += [p.relative_to(ROOT).as_posix() for p in sorted((ROOT / "tests/directed/rv32imac_stage6").glob("*.s"))]
BASELINE_SOURCE_SET = ["rtl/packages/rv32_pkg.sv", "rtl/packages/rv_pipe_pkg.sv", "rtl/decoder/rv_decoder.sv", "rtl/core/rv_core_single.sv", "rtl/core/rv_core_pipe.sv",
                       "rtl/pipeline/rv_id_stage.sv", "rtl/pipeline/rv_ex_stage.sv", "rtl/pipeline/rv_mem_stage.sv",
                       "scripts/simulation/rv32_asm.py", "scripts/simulation/rv32c_asm.py",
                       "scripts/simulation/rv32a_model.py",
                       "scripts/simulation/rv32imc_iss.py",
                       "verification/environment/tb_rv_core.sv", "verification/environment/tb_rv_pipe_stage4.sv"]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def matching_report(pattern, marker, required_hashes):
    for path in sorted(REPORTS.glob(pattern), key=lambda p: p.stat().st_mtime, reverse=True):
        text = path.read_text(encoding="utf-8", errors="replace")
        if marker not in text:
            continue
        provenance = {}
        if pattern.startswith("stage5_a_"):
            for line in text.splitlines():
                if line.startswith("provenance_file="):
                    raw = line.split("=", 1)[1].replace("\\", "/")
                    if len(raw) > 2 and raw[1:3] == ":/": raw = "/mnt/" + raw[0].lower() + raw[2:]
                    p = Path(raw)
                    if not p.is_absolute(): p = ROOT / p
                    if p.is_file():
                        for item in p.read_text(encoding="utf-8", errors="replace").splitlines():
                            if item.startswith("sha256 ") and "=" in item:
                                rel, value = item[7:].rsplit("=", 1); provenance[rel] = value
        else:
            for line in text.splitlines():
                if line.startswith("sha256 ") and "=" in line:
                    rel, value = line[7:].rsplit("=", 1); provenance[rel] = value
        if all(provenance.get(rel) == sha(ROOT / rel) for rel in required_hashes):
            return path
    return None


def ignore_copy(directory, names):
    ignored = []
    for name in names:
        path = Path(directory) / name
        if name in (".git", "reports", "__pycache__", ".venv", "venv") or name.startswith(("sim_out", "obj_dir", "xsim.dir")):
            ignored.append(name)
        elif path.is_file() and path.suffix == ".hex":
            ignored.append(name)
    return ignored


def apply_mutant(root, rel, old, new):
    path = root / rel
    source = path.read_text(encoding="utf-8")
    if source.count(old) != 1:
        raise ValueError(f"exact mutation anchor count is {source.count(old)} for {rel}: {old!r}")
    changed = source.replace(old, new, 1)
    path.write_text(changed, encoding="utf-8", newline="\n")
    return "".join(difflib.unified_diff(source.splitlines(True), changed.splitlines(True),
                                       fromfile="baseline/" + rel, tofile="mutant/" + rel))


def run(cmd, cwd):
    return subprocess.run([str(x) for x in cmd], cwd=cwd, text=True,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def main():
    for sim, pattern, marker in (
        ("verilator", "stage5_a_pipeline_verilator_*.txt", "STAGE5_A_PIPELINE_VERILATOR PASS legacy=209 c_cases=21 a_cases=18"),
        ("xsim", "stage5_a_pipeline_xsim_*.txt", "STAGE5_A_PIPELINE_XSIM PASS legacy=209 c_cases=21 a_cases=18"),
        ("verilator", "stage6_verilator_*.txt", "STAGE6_ENABLED_VERILATOR PASS cases=11"),
        ("xsim", "stage6_xsim_*.txt", "STAGE6_ENABLED_XSIM PASS cases=11"),
    ):
        required = BASELINE_SOURCE_SET if pattern.startswith("stage5_a_") else SOURCE_SET
        if matching_report(pattern, marker, required) is None:
            print(f"STAGE6_MUTATION INVALID: no source-matched {sim} baseline report for {pattern}")
            return 2
    if not sys.platform.startswith("linux") or not shutil.which("verilator"):
        print("STAGE6_MUTATION INVALID: campaign requires Verilator in Ubuntu WSL")
        return 2

    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out = REPORTS / "stage6_z_mutation_runs" / ("run_" + stamp)
    out.mkdir(parents=True, exist_ok=False)
    results = []
    for ident, description, rel, old, new, expected_case in MUTANTS:
        evidence = out / "mutants" / ident
        evidence.mkdir(parents=True)
        with tempfile.TemporaryDirectory(prefix=f"stage6_{ident}_") as temp:
            workspace = Path(temp) / "workspace"
            shutil.copytree(ROOT, workspace, ignore=ignore_copy)
            commands = []
            try:
                diff = apply_mutant(workspace, rel, old, new)
            except Exception as exc:
                results.append({"id": ident, "status": "INVALID", "reason": str(exc)})
                (evidence / "result.json").write_text(json.dumps(results[-1], indent=2) + "\n", encoding="utf-8")
                continue
            (evidence / "source.diff").write_text(diff, encoding="utf-8", newline="\n")
            prep_dir = workspace / "sim_out_stage6_mutation_prep"
            prep_args = [sys.executable, workspace / "scripts/simulation/prepare_stage6.py", prep_dir]
            commands.append({"argv": list(map(str, prep_args)), "cwd": str(workspace)})
            prep = run(prep_args, workspace)
            (evidence / "prepare.stdout.log").write_text(prep.stdout, encoding="utf-8", newline="\n")
            (evidence / "prepare.stderr.log").write_text(prep.stderr, encoding="utf-8", newline="\n")
            if prep.returncode:
                record = {"id": ident, "status": "INVALID", "reason": "preparation failed", "exit": prep.returncode}
            else:
                runner_args = [sys.executable, workspace / "scripts/simulation/run_stage6_enabled.py",
                               "--sim", "verilator", "--prepared", prep_dir]
                commands.append({"argv": list(map(str, runner_args)), "cwd": str(workspace)})
                result = run(runner_args, workspace)
                (evidence / "runner.stdout.log").write_text(result.stdout, encoding="utf-8", newline="\n")
                (evidence / "runner.stderr.log").write_text(result.stderr, encoding="utf-8", newline="\n")
                outputs = sorted(workspace.glob("sim_out_stage6_verilator_*"))
                run_out = outputs[-1] if outputs else None
                built = bool(run_out and (run_out / "obj_golden/golden").is_file() and
                             (run_out / "obj_pipe/pipe").is_file() and
                             "STAGE6_DECODER_UNIT PASS checks=18 errors=0" in
                             (run_out / "decoder_z.unit.log").read_text(encoding="utf-8", errors="replace"))
                detected = False
                if built and run_out:
                    expected = (prep_dir / "z_iss" / (expected_case + ".trace")).read_text(encoding="ascii")
                    glog = run_out / f"{expected_case}.golden.log"
                    plog = run_out / f"{expected_case}.pipe.log"
                    gtrace = run_out / f"{expected_case}.golden.trace"
                    ptrace = run_out / f"{expected_case}.pipe.trace"
                    if glog.is_file() and plog.is_file() and gtrace.is_file() and ptrace.is_file():
                        gtext = glog.read_text(encoding="utf-8", errors="replace")
                        ptext = plog.read_text(encoding="utf-8", errors="replace")
                        detected = gtext.count("TEST_RESULT: PASS") == 1 and gtrace.read_text(encoding="ascii") == expected
                        if ident == "Z01":
                            detected = detected and ptext.count("TEST_RESULT: PASS") == 1 and ptrace.read_text(encoding="ascii") != expected
                        else:
                            detected = detected and "TEST_RESULT: FAIL" in ptext and "cause=2 expect=1" in ptext
                status = "CAUGHT" if detected else ("MISSED" if result.returncode == 0 else "INVALID")
                record = {"id": ident, "description": description, "status": status,
                          "expected_case": expected_case, "build_success": built,
                          "runner_exit": result.returncode, "detector": "independent ISS trace or expected halt-cause difference" if detected else "none"}
                if run_out:
                    shutil.copytree(run_out, evidence / "simulator_output", dirs_exist_ok=True)
                shutil.copytree(prep_dir / "z_iss", evidence / "prepared_iss", dirs_exist_ok=True)
                shutil.copytree(prep_dir / "z_hex", evidence / "prepared_hex", dirs_exist_ok=True)
            results.append(record)
            (evidence / "commands.json").write_text(json.dumps(commands, indent=2) + "\n", encoding="utf-8")
            (evidence / "result.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")

    summary = {"simulator": "Verilator", "mutants": results,
               "caught": sum(x.get("status") == "CAUGHT" for x in results),
               "missed": sum(x.get("status") == "MISSED" for x in results),
               "invalid": sum(x.get("status") == "INVALID" for x in results)}
    (out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    text = "\n".join(f"{r['id']} {r.get('status')}: {r.get('description', r.get('reason', ''))}" for r in results)
    text += f"\nSTAGE6_Z_MUTATION_VERILATOR {'PASS' if summary['caught'] == len(MUTANTS) and not summary['invalid'] else 'FAIL'} caught={summary['caught']} missed={summary['missed']} invalid={summary['invalid']}\nRUN_EVIDENCE={out}\n"
    (out / "audit.txt").write_text(text, encoding="utf-8", newline="\n")
    (REPORTS / f"stage6_z_mutation_verilator_{stamp}.txt").write_text(text, encoding="utf-8", newline="\n")
    print(text, end="")
    return 0 if summary["caught"] == len(MUTANTS) and not summary["invalid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
