#!/usr/bin/env python3
"""Run the prepared Stage 6 cases against golden and pipeline RTL."""
import argparse
import csv
import hashlib
import json
import os
import shutil
import subprocess
import sys
import traceback
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0,str(HERE))
from stage9_run_provenance import capture_snapshot, verify_snapshot
TOOLS = {}
COMSPEC = None
COMMAND_LOG = []
STAGE6_MANIFEST_FIELDS = ("name", "expect_cause", "check_gp", "hexpath", "atomics", "z_events", "retired")


def read_stage6_manifest(path):
    """Read the prepared Stage 6 schema without dropping or padding columns."""
    with Path(path).open(newline="", encoding="utf-8") as source:
        reader = csv.DictReader(source)
        if tuple(reader.fieldnames or ()) != STAGE6_MANIFEST_FIELDS:
            raise ValueError(f"Stage 6 manifest schema mismatch: expected={STAGE6_MANIFEST_FIELDS} actual={reader.fieldnames}")
        rows = list(reader)
    names = set()
    for line, row in enumerate(rows, 2):
        if None in row or any(value is None for value in row.values()):
            raise ValueError(f"Stage 6 manifest malformed row {line}: {row!r}")
        if set(row) != set(STAGE6_MANIFEST_FIELDS):
            raise ValueError(f"Stage 6 manifest row {line} has unexpected fields: {sorted(row)}")
        if not row["name"] or row["name"] in names:
            raise ValueError(f"Stage 6 manifest empty or duplicate identity at row {line}: {row['name']!r}")
        names.add(row["name"])
        if not row["hexpath"] or row["check_gp"] not in ("0", "1"):
            raise ValueError(f"Stage 6 manifest invalid required values at row {line}: {row!r}")
        for field in ("expect_cause", "atomics", "z_events", "retired"):
            if not row[field].isdigit():
                raise ValueError(f"Stage 6 manifest invalid integer {field} at row {line}: {row[field]!r}")
    return rows


def write_stage6_selection_manifest(path, rows):
    """Serialize and round-trip the full prepared Stage 6 metadata schema."""
    for line, row in enumerate(rows, 2):
        if set(row) != set(STAGE6_MANIFEST_FIELDS):
            raise ValueError(f"Stage 6 selection row {line} schema mismatch: expected={STAGE6_MANIFEST_FIELDS} actual={tuple(row)}")
    with Path(path).open("w", newline="", encoding="utf-8") as target:
        writer = csv.DictWriter(target, fieldnames=STAGE6_MANIFEST_FIELDS,
                                extrasaction="raise", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    reread = read_stage6_manifest(path)
    if reread != rows:
        raise ValueError(f"Stage 6 selection manifest round-trip mismatch: {path}")


def resolve(name):
    return TOOLS.get(name) or shutil.which(name) or name


def command_for(argv):
    """Use the Stage 4.4 Windows batch launcher and argument quoting contract."""
    executable = resolve(argv[0])
    if Path(executable).suffix.lower() in (".bat", ".cmd"):
        shell = COMSPEC or os.environ.get("COMSPEC") or shutil.which("cmd.exe")
        if not shell:
            raise RuntimeError("batch launcher requires COMSPEC/cmd.exe")
        pieces = []
        quote_next = False
        for arg in [executable, *argv[1:]]:
            if quote_next:
                pieces.append('"' + arg + '"')
                quote_next = False
            else:
                pieces.append(subprocess.list2cmdline([arg]))
                quote_next = arg in ("--testplusarg", "-generic_top")
        return '"' + shell + '" /d /s /c "' + " ".join(pieces) + '"', executable
    return [executable, *argv[1:]], executable


def simulator_path(path):
    """Pass absolute simulator paths with forward slashes on every host."""
    return str(Path(path).resolve()).replace("\\", "/")


def run(args, cwd, log):
    COMMAND_LOG.append({"argv":[str(x) for x in args],"cwd":str(Path(cwd).resolve()),"log":str(Path(log).resolve())})
    actual, executable = command_for(list(map(str, args)))
    try:
        result = subprocess.run(actual, cwd=cwd, text=True,
                                stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    except OSError as exc:
        diagnostic = (f"LAUNCH_FAILURE executable={args[0]!r} args={list(args[1:])!r} "
                      f"resolved={executable!r} cwd={str(Path(cwd).resolve())!r} "
                      f"error={exc!r}\nCOMMAND={actual!r}\n{traceback.format_exc()}")
        print(diagnostic, file=sys.stderr, flush=True)
        Path(log).write_text(diagnostic + "\n", encoding="utf-8", newline="\n")
        raise RuntimeError(diagnostic) from exc
    Path(log).write_text(result.stdout, encoding="utf-8", newline="\n")
    if result.returncode:
        excerpt = "\n".join(line for line in result.stdout.splitlines() if line.strip())[:1800]
        print(f"FIRST_TOOL_ERROR exit={result.returncode} log={log}\n{excerpt}",
              file=sys.stderr, flush=True)
        raise RuntimeError(f"command failed exit={result.returncode} executable={args[0]!r} "
                           f"resolved={executable!r} cwd={Path(cwd).resolve()} "
                           f"args={list(args[1:])!r} log={log}")
    if Path(executable).stem.lower() in ("verilator", "xvlog", "xelab"):
        errors = [line for line in result.stdout.splitlines()
                  if line.lstrip().startswith(("ERROR:", "FATAL:", "%Error"))]
        if errors:
            for line in errors[:20]:
                print(f"COMPILER_DIAGNOSTIC {line}", file=sys.stderr, flush=True)
            raise RuntimeError(f"compiler emitted {len(errors)} error/fatal diagnostic(s); first={errors[0]!r}; log={log}")
    return result.stdout


def compare(actual, expected, label):
    if actual != expected:
        a, e = actual.splitlines(), expected.splitlines()
        index = next((i for i, (x, y) in enumerate(zip(a, e)) if x != y), min(len(a), len(e)))
        av = a[index] if index < len(a) else "<EOF>"
        ev = e[index] if index < len(e) else "<EOF>"
        raise RuntimeError(f"{label}: trace mismatch line={index+1} actual={av!r} expected={ev!r}")


def plusarg(name, value):
    return f"+{name}={simulator_path(value)}"


def terminal(log):
    text = Path(log).read_text(encoding="utf-8", errors="replace")
    if text.count("TEST_RESULT: PASS") != 1 or "FAIL" in text or "FATAL_ERROR" in text:
        raise RuntimeError(f"invalid simulator terminal record: {log}")
    return text


def main():
    global COMSPEC
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sim", required=True, choices=("verilator", "xsim"))
    parser.add_argument("--prepared", required=True)
    args = parser.parse_args()
    prep = Path(args.prepared).resolve()
    if "STAGE6_PREPARATION PASS stage5=248 stage6=11 total=259 images=259 references=259 errors=0" not in (prep / "stage6_preparation.txt").read_text(encoding="ascii"):
        raise RuntimeError("prepared inventory/provenance marker missing")
    rows = read_stage6_manifest(prep / "z_manifest.csv")
    if len(rows) != 11 or len({r["name"] for r in rows}) != 11:
        raise RuntimeError(f"expected eleven unique Stage 6 prepared rows, found {len(rows)}")
    required = []
    for row in rows:
        name = row["name"]
        required += [ROOT / row["hexpath"], prep / "z_iss" / (name + ".trace"),
                     prep / "z_iss" / (name + ".a.tsv"), prep / "z_iss" / (name + ".z.tsv")]
    missing = [str(p) for p in required if not p.is_file() or p.stat().st_size == 0]
    if missing:
        raise RuntimeError("missing prepared artifact(s): " + ", ".join(missing))
    tools = ("verilator", "make") if args.sim == "verilator" else ("xvlog", "xelab", "xsim")
    unavailable = []
    for tool in tools:
        located = shutil.which(tool)
        if located is None or not Path(located).is_file():
            unavailable.append(tool)
        else:
            TOOLS[tool] = str(Path(located).resolve())
    if unavailable:
        raise RuntimeError("tool preflight missing: " + ", ".join(unavailable))
    if args.sim == "xsim" and any(Path(TOOLS[tool]).suffix.lower() in (".bat", ".cmd")
                                  for tool in tools):
        COMSPEC = os.environ.get("COMSPEC") or shutil.which("cmd.exe")
        if not COMSPEC or not Path(COMSPEC).is_file():
            raise RuntimeError("Vivado batch wrapper requires COMSPEC/cmd.exe")
    cpp = next((shutil.which(x) for x in ("g++", "clang++", "c++") if shutil.which(x)), None)
    if args.sim == "verilator" and not cpp:
        raise RuntimeError("tool preflight missing C++ compiler")

    stamp = __import__("datetime").datetime.now(__import__("datetime").timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out = ROOT / f"sim_out_stage6_{args.sim}_{stamp}"
    if out.exists():
        raise RuntimeError(f"output path exists: {out}")
    out.mkdir()
    stage6_suite = ROOT / "tests/directed/rv32imac_stage6"
    source_paths = [ROOT / "rtl/packages/rv32_pkg.sv", ROOT / "rtl/packages/rv_pipe_pkg.sv",
                    ROOT / "rtl/decoder/rv_decoder.sv", ROOT / "rtl/core/rv_core_single.sv",
                    ROOT / "rtl/core/rv_core_pipe.sv", ROOT / "rtl/pipeline/rv_id_stage.sv",
                    ROOT / "rtl/pipeline/rv_ex_stage.sv", ROOT / "rtl/pipeline/rv_mem_stage.sv",
                    HERE / "rv32_asm.py", HERE / "rv32c_asm.py", HERE / "rv32c_model.py",
                    HERE / "rv32a_model.py", HERE / "rv32imc_iss.py", HERE / "prepare_stage6.py",
                    HERE / "stage6_software_selftest.py", HERE / "run_stage6_enabled.py", HERE / "stage9_run_provenance.py",
                    ROOT / "verification/environment/tb_rv_core.sv",
                    ROOT / "verification/environment/tb_rv_pipe_stage4.sv",
                    ROOT / "verification/environment/tb_rv_stage6.sv",
                    ROOT / "verification/environment/tb_rv_decoder_z.sv",
                    stage6_suite / "manifest.csv", *sorted(stage6_suite.glob("*.s"))]
    rtl_filelist=ROOT/"scripts/simulation/stage4_4_rtl.f"
    source_paths += [rtl_filelist,*[ROOT/line.strip() for line in rtl_filelist.read_text(encoding="utf-8").splitlines() if line.strip()]]
    write_stage6_selection_manifest(out/"selection_manifest.csv", rows)
    snapshot_inputs=[prep/"z_manifest.csv",prep/"stage6_preparation.txt",out/"selection_manifest.csv"]
    for row in rows:
        n=row["name"]
        snapshot_inputs += [ROOT/row["hexpath"],prep/"z_iss"/(n+".trace"),
                            prep/"z_iss"/(n+".a.tsv"),prep/"z_iss"/(n+".z.tsv")]
    snapshot_file=capture_snapshot(out/"producer_snapshot",source_paths,snapshot_inputs,
                                   [sys.executable,str(HERE/"run_stage6_enabled.py"),*sys.argv[1:]])
    rtl = ROOT / "scripts" / "simulation" / "stage4_4_rtl.f"
    env = ROOT / "verification" / "environment"
    if args.sim == "verilator":
        unit_obj = out / "obj_decoder_z"; unit_obj.mkdir()
        unit = unit_obj / "decoder_z"
        unit_log = out / "decoder_z.unit.log"
        run(["verilator", "-sv", "--binary", "--timing", "-Wno-fatal", "-Wno-lint", "-Wno-style",
             "-f", rtl, env / "tb_rv_decoder_z.sv", "--top-module", "tb_rv_decoder_z",
             "-Mdir", unit_obj, "-o", "decoder_z"], ROOT, out / "decoder_z.build.log")
        run([unit], ROOT, unit_log)
        if "STAGE6_DECODER_UNIT PASS checks=18 errors=0" not in unit_log.read_text(encoding="utf-8"):
            raise RuntimeError("Verilator CSR/FENCE.I decoder unit did not pass")
        snapshots = {}
        for name, top in (("golden", "tb_rv_core_stage6"), ("pipe", "tb_rv_pipe_stage6")):
            obj = out / ("obj_" + name); obj.mkdir()
            binary = obj / name
            run(["verilator", "-sv", "--binary", "--timing", "-Wno-fatal", "-Wno-lint", "-Wno-style",
                 "-f", rtl, env / "tb_rv_core.sv", env / "tb_rv_pipe_stage4.sv", env / "tb_rv_stage6.sv",
                 "--top-module", top, "-Mdir", obj, "-o", name], ROOT, out / (name + ".build.log"))
            if not binary.is_file():
                raise RuntimeError(f"successful build marker but missing binary: {binary}")
            snapshots[name] = ("verilator", binary)
    else:
        xdir = out / "xsim"; xdir.mkdir()
        absfl = out / "stage6_rtl_abs.f"
        absfl.write_text("".join(str((ROOT / line.strip()).resolve()).replace("\\", "/") + "\n"
                                   for line in rtl.read_text(encoding="utf-8").splitlines() if line.strip()),
                         encoding="utf-8", newline="\n")
        run(["xvlog", "-sv", "-f", simulator_path(absfl)], xdir, out / "xvlog_rtl.log")
        for source in ("tb_rv_core.sv", "tb_rv_pipe_stage4.sv", "tb_rv_stage6.sv"):
            run(["xvlog", "-sv", simulator_path(env / source)], xdir, out / (source + ".compile.log"))
        run(["xvlog", "-sv", simulator_path(env / "tb_rv_decoder_z.sv")], xdir, out / "tb_rv_decoder_z.compile.log")
        run(["xelab", "-debug", "off", "tb_rv_decoder_z", "-s", "decoder_z"], xdir, out / "decoder_z.elab.log")
        run(["xsim", "decoder_z", "--runall", "--log", simulator_path(out / "decoder_z.unit.log")], xdir, out / "decoder_z.launch.log")
        if "STAGE6_DECODER_UNIT PASS checks=18 errors=0" not in (out / "decoder_z.unit.log").read_text(encoding="utf-8"):
            raise RuntimeError("XSim CSR/FENCE.I decoder unit did not pass")
        snapshots = {}
        for name, top in (("golden", "tb_rv_core_stage6"), ("pipe", "tb_rv_pipe_stage6")):
            run(["xelab", "-debug", "off", top, "-s", name], xdir, out / (name + ".elab.log"))
            snapshots[name] = ("xsim", name)

    full_count = pipeline_count = atomic_compares = z_compares = 0
    for index, row in enumerate(rows, 1):
        name = row["name"]
        image = ROOT / row["hexpath"]
        expected = (prep / "z_iss" / (name + ".trace")).read_text(encoding="ascii")
        expected_a = (prep / "z_iss" / (name + ".a.tsv")).read_text(encoding="ascii")
        expected_z = list(csv.DictReader((prep / "z_iss" / (name + ".z.tsv")).open(newline=""), delimiter="\t"))
        traces = {}
        for kind in ("golden", "pipe"):
            engine, exe = snapshots[kind]
            trace, log = out / f"{name}.{kind}.trace", out / f"{name}.{kind}.log"
            acov = out / f"{name}.{kind}.a.tsv"
            mcov = out / f"{name}.{kind}.mcov"
            args0 = [exe, plusarg("HEX", image), plusarg("TRACE", trace),
                     f"+EXPECT_CAUSE={row['expect_cause']}", f"+CHECK_GP={row['check_gp']}",
                     plusarg("ACOV", acov)]
            if kind == "pipe": args0.append(plusarg("MCOV", mcov))
            if engine == "xsim":
                args0 = ["xsim", exe, "--runall", "--log", simulator_path(log)] + sum((["--testplusarg", x[1:]] for x in args0[1:]), [])
                run(args0, out / "xsim", out / (f"{name}.{kind}.launch.log"))
            else:
                run(args0, ROOT, log)
            terminal(log)
            if not trace.is_file() or not acov.is_file():
                raise RuntimeError(f"{name}/{kind}: trace or atomic sidecar missing")
            actual = trace.read_text(encoding="ascii")
            compare(actual, expected, f"{name}/{kind} vs independent ISS")
            compare(acov.read_text(encoding="ascii"), expected_a, f"{name}/{kind} atomic sidecar vs independent ISS")
            traces[kind] = actual
            full_count += 1
        compare(traces["pipe"], traces["golden"], f"{name} pipeline vs golden")
        pipeline_count += 1
        mcov_lines = (out / f"{name}.pipe.mcov").read_text(encoding="ascii").splitlines()
        actual_writes = [line.split() for line in mcov_lines if line.startswith("Z CSR_WRITE ")]
        expected_writes = [["Z", "CSR_WRITE", event["pc"], event["raw"], event["csr_or_pcnext"], event["old"], event["new"]]
                           for event in expected_z if event["kind"] == "CSR" and event["write_intent"] == "1"]
        if actual_writes != expected_writes:
            raise RuntimeError(f"{name}: CSR commit sidecar differs from independent ISS; actual={actual_writes} expected={expected_writes}")
        actual_fences = [line.split() for line in mcov_lines if line.startswith("Z FENCEI ")]
        expected_fences = [["Z", "FENCEI", event["pc"], event["raw"], event["ilen"], event["csr_or_pcnext"]]
                           for event in expected_z if event["kind"] == "FENCEI"]
        if actual_fences != expected_fences:
            raise RuntimeError(f"{name}: FENCE.I redirect sidecar differs from independent ISS; actual={actual_fences} expected={expected_fences}")
        z_compares += len(actual_writes) + len(actual_fences)
        if name == "stage6_csr_wrongpath":
            if "Z SQUASH_REDIRECT 00000004" not in "\n".join(mcov_lines):
                raise RuntimeError("wrong-path illegal CSR was not observed as redirect-squashed")
            if any(line.startswith("Z RETIRE ") for line in mcov_lines):
                raise RuntimeError("wrong-path CSR instruction retired")
        if name == "stage6_csr_ro_reads":
            ro_retire = [line for line in mcov_lines if line.startswith("Z RETIRE ")]
            if len(ro_retire) != 5 or any(line.startswith("Z CSR_WRITE ") for line in mcov_lines):
                raise RuntimeError("RO CSR legal read retirements/write suppression coverage mismatch")
        if name in {"stage6_csr_ro_write_rd0", "stage6_csr_ro_zero_source", "stage6_csr_ro_immediate_write"}:
            if not any(line.startswith("Z CSR_FAULT ") for line in mcov_lines):
                raise RuntimeError(f"{name}: illegal RO write attempt missing CSR fault sidecar")
            if any(line.startswith("Z CSR_WRITE ") for line in mcov_lines):
                raise RuntimeError(f"{name}: illegal RO write attempt changed CSR state")
        atomic_compares += 2
        print(f"[{index}/{len(rows)}] {name} PASS", flush=True)

    report = ROOT / "reports" / f"stage6_{args.sim}_{stamp}.txt"
    report.parent.mkdir(exist_ok=True)
    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    verify_snapshot(snapshot_file)
    (out/"commands.json").write_text(json.dumps({"owner_command":[sys.executable,str(HERE/"run_stage6_enabled.py"),*sys.argv[1:]],"commands":COMMAND_LOG},indent=2)+"\n",encoding="utf-8",newline="\n")
    hashes = [f"sha256 {p.relative_to(ROOT).as_posix()}={hashlib.sha256(p.read_bytes()).hexdigest()}"
              for p in source_paths]
    report.write_text(f"Stage 6 enabled functional validation simulator={args.sim}\n"
                      f"git_head={head.stdout.strip() if head.returncode == 0 else 'unavailable'}\n"
                      f"output_dir={out.resolve()}\nproducer_snapshot={snapshot_file.resolve()}\n"
                      f"producer_snapshot_sha256={hashlib.sha256(snapshot_file.read_bytes()).hexdigest()}\n"
                      f"prepared_manifest_sha256={hashlib.sha256((prep / 'z_manifest.csv').read_bytes()).hexdigest()}\n"
                      + "\n".join(hashes) + "\n"
                      f"STAGE6_ENABLED_{args.sim.upper()} PASS cases=11 full_trace_comparisons={full_count} "
                      f"pipeline_golden={pipeline_count} atomic_sidecars={atomic_compares} z_sidecar_events={z_compares}\n",
                      encoding="utf-8", newline="\n")
    print(report.read_text(encoding="utf-8"), end="")
    print(f"RUN_OUTPUT={out}\nREPORT={report}")
    print(f"RUN_REPORT={report.resolve()}")


if __name__ == "__main__":
    main()
