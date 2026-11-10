#!/usr/bin/env python3
"""Build and run the Stage 7 machine-mode suite against ISS, golden, and pipeline."""
import argparse, csv, hashlib, json, os, re, shutil, subprocess, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0,str(HERE))
from stage9_run_provenance import capture_snapshot, verify_snapshot
sys.path.insert(0, str(HERE))
import run_stage6_enabled as launch

STAGE7_MANIFEST_FIELDS=("name","hexpath","irq_pc","irq_levels","irq_wait_div","traps","retired")
STAGE8_MANIFEST_FIELDS=STAGE7_MANIFEST_FIELDS+("suite","seed","source")


def read_prepared_manifest(path, stage8=False):
    fields=STAGE8_MANIFEST_FIELDS if stage8 else STAGE7_MANIFEST_FIELDS
    with Path(path).open(newline="",encoding="utf-8") as source:
        reader=csv.DictReader(source)
        if tuple(reader.fieldnames or ())!=fields:
            raise ValueError(f"{'Stage 8' if stage8 else 'Stage 7'} manifest schema mismatch: expected={fields} actual={reader.fieldnames}")
        rows=list(reader)
    seen=set()
    for line,row in enumerate(rows,2):
        if None in row or any(value is None for value in row.values()):
            raise ValueError(f"prepared manifest malformed row {line}: {row!r}")
        if set(row)!=set(fields):
            raise ValueError(f"prepared manifest row {line} has unexpected fields: {tuple(row)}")
        if not row["name"] or row["name"] in seen:
            raise ValueError(f"prepared manifest empty or duplicate identity at row {line}: {row['name']!r}")
        seen.add(row["name"])
        if not row["hexpath"] or not row["traps"].isdigit() or not row["retired"].isdigit():
            raise ValueError(f"prepared manifest invalid required values at row {line}: {row!r}")
        if stage8 and (row["suite"] not in ("stage7_enabled","stage8_seeded") or
                       (row["suite"]=="stage8_seeded" and (not row["seed"] or not row["source"]))):
            raise ValueError(f"Stage 8 manifest invalid scenario metadata at row {line}: {row!r}")
    return rows


def write_selection_manifest(path,rows,stage8=False):
    fields=STAGE8_MANIFEST_FIELDS if stage8 else STAGE7_MANIFEST_FIELDS
    for line,row in enumerate(rows,2):
        if set(row)!=set(fields):
            raise ValueError(f"selection row {line} schema mismatch: expected={fields} actual={tuple(row)}")
    with Path(path).open("w",newline="",encoding="utf-8") as target:
        writer=csv.DictWriter(target,fieldnames=fields,extrasaction="raise",lineterminator="\n")
        writer.writeheader();writer.writerows(rows)
    round_trip=read_prepared_manifest(path,stage8)
    if round_trip!=rows:
        raise ValueError(f"selection manifest round-trip mismatch: {path}")


def require(ok, message):
    if not ok: raise RuntimeError(message)


def read_tsv_records(path, expected_fields, label):
    with path.open(newline="", encoding="ascii") as src:
        reader=csv.DictReader(src,delimiter="\t")
        require(reader.fieldnames == expected_fields,
                f"{label}: malformed header expected={expected_fields} actual={reader.fieldnames} path={path}")
        records=list(reader)
    for number, record in enumerate(records,2):
        if None in record or any(value is None for value in record.values()):
            raise RuntimeError(f"{label}: malformed record line={number} fields={record!r}")
    return records


def sidecar_records(lines, tag, field_count, label):
    records=[]
    for number, line in enumerate(lines,1):
        fields=line.split()
        if fields[:len(tag)] != tag: continue
        if len(fields) != field_count:
            raise RuntimeError(f"{label}: malformed sidecar record line={number} expected_fields={field_count} "
                               f"actual_fields={len(fields)} record={line!r}")
        records.append(fields)
    return records


def validate_z_records(records, label):
    for number, event in enumerate(records,2):
        malformed=[]
        if event["kind"] not in ("CSR","FENCEI"):
            malformed.append(f"unknown kind={event['kind']!r}")
        for field in ("pc","raw"):
            if not re.fullmatch(r"[0-9a-f]{8}",event[field]): malformed.append(f"bad {field}={event[field]!r}")
        if not event["ilen"].isdigit() or int(event["ilen"]) <= 0:
            malformed.append(f"bad ilen={event['ilen']!r}")
        if event["kind"] == "FENCEI":
            if not re.fullmatch(r"[0-9a-f]{8}",event["csr_or_pcnext"]):
                malformed.append(f"bad next_pc={event['csr_or_pcnext']!r}")
            for field in ("funct3","source_index","source","old","new","write_intent"):
                if event[field] != "-": malformed.append(f"unexpected FENCEI {field}={event[field]!r}")
        elif event["kind"] == "CSR":
            if not re.fullmatch(r"[0-9a-f]{3}",event["csr_or_pcnext"]):
                malformed.append(f"bad csr={event['csr_or_pcnext']!r}")
            for field in ("funct3","source_index"):
                if not event[field].isdigit(): malformed.append(f"bad {field}={event[field]!r}")
            for field in ("source","old","new"):
                if not re.fullmatch(r"[0-9a-f]{8}",event[field]): malformed.append(f"bad {field}={event[field]!r}")
            if event["write_intent"] not in ("0","1"):
                malformed.append(f"bad write_intent={event['write_intent']!r}")
        if malformed:
            raise RuntimeError(f"{label}: malformed event line={number} record={event!r} errors={malformed}")


def require_records_equal(actual, expected, label):
    if actual != expected:
        index=next((n for n,(a,e) in enumerate(zip(actual,expected)) if a != e),min(len(actual),len(expected)))
        raise RuntimeError(f"{label}: record mismatch index={index} actual="
                           f"{actual[index] if index<len(actual) else '<EOF>'!r} expected="
                           f"{expected[index] if index<len(expected) else '<EOF>'!r} "
                           f"actual_count={len(actual)} expected_count={len(expected)}")


def compare(actual, expected, label):
    def filtered(text):
        timing_counters = {0xB00, 0xB80}
        kept = []
        for line in text.splitlines():
            fields = line.split()
            if len(fields) >= 2 and fields[0] == "CSR" and int(fields[1], 16) in timing_counters:
                continue
            kept.append(line)
        return "\n".join(kept)
    a, e = filtered(actual), filtered(expected)
    if a != e:
        aa, ee = a.splitlines(), e.splitlines()
        i = next((n for n,(x,y) in enumerate(zip(aa,ee)) if x!=y), min(len(aa),len(ee)))
        raise RuntimeError(f"{label}: line={i+1} actual={aa[i] if i<len(aa) else '<EOF>'!r} expected={ee[i] if i<len(ee) else '<EOF>'!r}")


def main():
    global_args = argparse.ArgumentParser(description=__doc__)
    global_args.add_argument("--sim", required=True, choices=("verilator", "xsim"))
    global_args.add_argument("--prepared", required=True)
    global_args.add_argument("--case")
    global_args.add_argument("--case-list",type=Path)
    global_args.add_argument("--stage8", action="store_true", help="run the Stage 8 extended prepared inventory")
    global_args.add_argument("--cases-only",action="store_true",help="skip decoder unit; execute only the explicitly selected prepared cases")
    args = global_args.parse_args()
    prep = Path(args.prepared).resolve()
    prep_text=(prep / "stage7_preparation.txt").read_text(encoding="ascii")
    marker = "STAGE7_PREPARATION READY stage6_compat=259 stage7_cases=13 images=13 references=13 errors=0"
    require(marker in prep_text, "prepared Stage 7 inventory missing")
    for line in prep_text.splitlines():
        m=re.fullmatch(r"(artifact_)?sha256 ([^=]+)=([0-9a-f]{64})",line)
        if not m: continue
        path=(ROOT/m.group(2)).resolve()
        require(path.is_file() and hashlib.sha256(path.read_bytes()).hexdigest()==m.group(3),
                f"prepared provenance mismatch/missing file: {path}")
    rows = read_prepared_manifest(prep / "m_manifest.csv",stage8=args.stage8)
    require(len({r["name"] for r in rows}) == len(rows), "duplicate case names in prepared inventory")
    if args.stage8:
        stage8_note=(prep / "stage8_preparation.txt").read_text(encoding="ascii")
        match=re.search(r"STAGE8_PREPARATION READY base_cases=13 generated_cases=(\d+) total_cases=(\d+) errors=0",stage8_note)
        require(match is not None and int(match.group(2)) == len(rows), "Stage 8 prepared inventory mismatch")
        for line in stage8_note.splitlines():
            source_item=re.fullmatch(r"sha256 (.+)=([0-9a-f]{64})",line)
            if source_item:
                rel,digest=source_item.groups(); path=ROOT/rel
                require(path.is_file() and hashlib.sha256(path.read_bytes()).hexdigest()==digest,
                        f"Stage 8 source provenance mismatch: {path}")
            item=re.fullmatch(r"artifact_sha256 (.+)=([0-9a-f]{64})",line)
            if item:
                rel,digest=item.groups()
                path=prep/rel[len("@PREPARED@/"):] if rel.startswith("@PREPARED@/") else ROOT/rel
                require(path.is_file() and hashlib.sha256(path.read_bytes()).hexdigest()==digest,
                        f"Stage 8 prepared artifact provenance mismatch: {path}")
    else:
        require(len(rows) == 13, "Stage 7 case inventory mismatch")
    require(not (args.case and args.case_list),"use either --case or --case-list")
    require(not args.cases_only or args.stage8,"--cases-only requires --stage8")
    selected_names=([x.strip() for x in args.case_list.read_text(encoding="utf-8").splitlines() if x.strip()]
                    if args.case_list else ([args.case] if args.case else None))
    require(selected_names is None or len(selected_names)==len(set(selected_names)),"duplicate selected case identity")
    run_rows=[row for row in rows if selected_names is None or row["name"] in set(selected_names)]
    require(len(run_rows)==(len(rows) if selected_names is None else len(selected_names)),
            f"selected case missing from manifest: {selected_names}")
    if args.stage8 and args.cases_only:
        require(len(run_rows)==23 and {r["name"] for r in run_rows}=={r["name"] for r in rows},
                "Stage 8 cases-only selection must be the complete 23-case Stage 8 manifest")
    def resolve_image(row):
        rel=row["hexpath"]
        return prep / rel[len("@PREPARED@/"):] if rel.startswith("@PREPARED@/") else ROOT / rel
    for row in run_rows:
        for p in (resolve_image(row), prep / "m_iss" / f"{row['name']}.trace",
                  prep / "m_iss" / f"{row['name']}.trap.tsv", prep / "m_iss" / f"{row['name']}.z.tsv"):
            require(p.is_file() and p.stat().st_size, f"missing prepared artifact: {p}")

    tools = ("verilator", "make") if args.sim == "verilator" else ("xvlog", "xelab", "xsim")
    for tool in tools:
        path = shutil.which(tool)
        require(path is not None and Path(path).is_file(), f"simulator preflight missing {tool}")
        launch.TOOLS[tool] = str(Path(path).resolve())
    if args.sim == "verilator":
        require(any(shutil.which(c) for c in ("g++", "clang++", "c++")), "C++ compiler missing")
    else:
        launch.COMSPEC = os.environ.get("COMSPEC") or shutil.which("cmd.exe")
        require(launch.COMSPEC is not None, "COMSPEC/cmd.exe missing for XSim batch executables")
    stamp = __import__("datetime").datetime.now(__import__("datetime").timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_kind = ("selected_stage8" if args.stage8 and (args.case_list or args.cases_only) else (f"focused_{args.case}" if args.case else "full"))
    out = ROOT / f"sim_out_{'stage8' if args.stage8 else 'stage7'}_{args.sim}_{run_kind}_{stamp}"
    require(not out.exists(), f"output directory exists: {out}")
    out.mkdir()
    selection_path=out/"selection_manifest.csv"
    write_selection_manifest(selection_path,run_rows,stage8=args.stage8)
    command_records={"owner_command": [sys.executable, *sys.argv], "commands": {}}
    commands_file=out/"commands.json"
    def record_command(label, argv, cwd):
        command_records["commands"][label]={"argv":[str(x) for x in argv],"cwd":str(Path(cwd).resolve())}
        commands_file.write_text(json.dumps(command_records,indent=2)+"\n",encoding="utf-8",newline="\n")
    commands_file.write_text(json.dumps(command_records,indent=2)+"\n",encoding="utf-8",newline="\n")
    rtl = ROOT / "scripts/simulation/stage4_4_rtl.f"
    env = ROOT / "verification/environment"
    rtl_sources=[ROOT/line.strip() for line in rtl.read_text(encoding="utf-8").splitlines() if line.strip()]
    require(all(source.is_file() for source in rtl_sources),
            "RTL file list has missing source(s): " + ", ".join(str(p) for p in rtl_sources if not p.is_file()))
    stage6_source=ROOT/"tests/directed/rv32imac_stage6"
    source_paths=[ROOT/"rtl/core/rv_machine_state.sv",ROOT/"rtl/core/rv_core_single.sv",ROOT/"rtl/core/rv_core_pipe.sv",
           ROOT/"rtl/pipeline/rv_id_stage.sv",ROOT/"rtl/pipeline/rv_ex_stage.sv",ROOT/"rtl/pipeline/rv_mem_stage.sv",
           ROOT/"rtl/decoder/rv_decoder.sv",HERE/"rv32imc_iss.py",HERE/"prepare_stage7.py",HERE/"run_stage7_enabled.py",
           HERE/"run_stage6_enabled.py",HERE/"run_stage4_4.py",HERE/"prepare_stage6.py",HERE/"stage7_software_selftest.py",HERE/"stage9_run_provenance.py",
           HERE/"rv32_asm.py",HERE/"rv32c_asm.py",HERE/"rv32c_model.py",HERE/"rv32a_model.py",HERE/"rv32i_iss.py",
           ROOT/"rtl/packages/rv32_pkg.sv",ROOT/"rtl/packages/rv_pipe_pkg.sv",rtl,
           ROOT/"verification/environment/tb_rv_core.sv",ROOT/"verification/environment/tb_rv_pipe_stage4.sv",
           ROOT/"verification/environment/tb_rv_stage7.sv",ROOT/"verification/environment/tb_rv_decoder_machine.sv",
           ROOT/"tests/directed/rv32imac_stage7/manifest.csv",*sorted((ROOT/"tests/directed/rv32imac_stage7").glob("*.s"))]
    if args.stage8:
        source_paths += [ROOT/"verification/stage8/rv_stage8_components.sv",ROOT/"verification/environment/tb_rv_stage8.sv",
                         ROOT/"verification/environment/tb_rv_stage8_components.sv",HERE/"stage8_scenarios.py",
                         HERE/"run_stage8_enabled.py",prep/"stage8_preparation.txt"]
    source_paths += sorted(rtl_sources)
    input_paths=[prep/"stage7_preparation.txt",prep/"m_manifest.csv",selection_path]
    if args.stage8: input_paths.append(prep/"stage8_preparation.txt")
    for row in run_rows:
        input_paths += [resolve_image(row),prep/"m_iss"/f"{row['name']}.trace",
                        prep/"m_iss"/f"{row['name']}.trap.tsv",prep/"m_iss"/f"{row['name']}.z.tsv"]
    snapshot_file=capture_snapshot(out/"producer_snapshot",source_paths,input_paths,
                                   [sys.executable,str(HERE/"run_stage7_enabled.py"),*sys.argv[1:]])
    tops = (("golden", "tb_rv_core_stage8"), ("pipe", "tb_rv_pipe_stage8")) if args.stage8 else \
           (("golden", "tb_rv_core_stage7"), ("pipe", "tb_rv_pipe_stage7"))
    snapshots = {}
    if args.sim == "verilator":
        if not args.cases_only:
            unit_obj=out/"obj_decoder_machine"; unit_obj.mkdir()
            unit_build=["verilator","-sv","--binary","--timing","-Wno-fatal","-Wno-lint","-Wno-style",
                        "-f",rtl,env/"tb_rv_decoder_machine.sv","--top-module","tb_rv_decoder_machine",
                        "-Mdir",unit_obj,"-o","decoder_machine"]
            record_command("build_decoder_machine",unit_build,ROOT)
            launch.run(unit_build,ROOT,out/"decoder_machine.build.log")
            record_command("run_decoder_machine",[unit_obj/"decoder_machine"],ROOT)
            launch.run([unit_obj/"decoder_machine"],ROOT,out/"decoder_machine.unit.log")
            require("STAGE7_DECODER_UNIT PASS checks=15 errors=0" in (out/"decoder_machine.unit.log").read_text(encoding="utf-8"),
                    "Verilator M-mode decoder unit did not pass")
        build_errors={}
        for name, top in tops:
            obj=out/f"obj_{name}"; obj.mkdir()
            top_sources=[env/"tb_rv_core.sv",env/"tb_rv_pipe_stage4.sv",env/"tb_rv_stage7.sv"]
            if args.stage8: top_sources.append(env/"tb_rv_stage8.sv")
            build_args=["verilator","-sv","--binary","--timing","-Wno-fatal","-Wno-lint","-Wno-style",
                        "-f",rtl,*top_sources,"--top-module",top,"-Mdir",obj,"-o",name]
            record_command(f"build_{name}",build_args,ROOT)
            try:
                launch.run(build_args, ROOT, out/f"{name}.build.log")
                binary=obj/name
                require(binary.is_file(), f"missing successful build output: {binary}")
                snapshots[name]=("verilator",binary)
            except Exception as exc:
                build_errors[name]=f"{type(exc).__name__}: {exc}"
        require(not build_errors, f"one or more core builds failed after both were attempted; {build_errors}; evidence={out}")
    elif args.sim == "xsim":
        xdir=out/"xsim"; xdir.mkdir()
        absfl=out/"stage7_rtl_abs.f"
        absfl.write_text("".join(str((ROOT/ln.strip()).resolve()).replace("\\","/")+"\n" for ln in rtl.read_text(encoding="utf-8").splitlines() if ln.strip()),encoding="utf-8",newline="\n")
        launch.run(["xvlog","-sv","-f",launch.simulator_path(absfl)],xdir,out/"xvlog_rtl.log")
        compile_sources=["tb_rv_core.sv","tb_rv_pipe_stage4.sv","tb_rv_stage7.sv"]
        if args.stage8: compile_sources.append("tb_rv_stage8.sv")
        for source in compile_sources:
            args0=["xvlog","-sv",launch.simulator_path(env/source)]
            record_command(f"compile_{source}",args0,xdir)
            launch.run(args0,xdir,out/(source+".compile.log"))
        if not args.cases_only:
            args0=["xvlog","-sv",launch.simulator_path(env/"tb_rv_decoder_machine.sv")]
            record_command("compile_decoder_machine",args0,xdir); launch.run(args0,xdir,out/"decoder_machine.compile.log")
            args0=["xelab","-debug","off","tb_rv_decoder_machine","-s","decoder_machine"]
            record_command("elab_decoder_machine",args0,xdir); launch.run(args0,xdir,out/"decoder_machine.elab.log")
            args0=["xsim","decoder_machine","--runall","--log",launch.simulator_path(out/"decoder_machine.unit.log")]
            record_command("run_decoder_machine",args0,xdir); launch.run(args0,xdir,out/"decoder_machine.launch.log")
            require("STAGE7_DECODER_UNIT PASS checks=15 errors=0" in (out/"decoder_machine.unit.log").read_text(encoding="utf-8"),
                    "XSim M-mode decoder unit did not pass")
        for name,top in tops:
            args0=["xelab","-debug","off",top,"-s",name]
            record_command(f"elab_{name}",args0,xdir); launch.run(args0,xdir,out/(name+".elab.log"))
            snapshots[name]=("xsim",name)

    full=gold_pipe=trap_count=csr_commits=mret_count=fencei_count=div_irq_aborts=0
    sync_causes=set(); irq_causes=set(); csr_addresses=set()
    for row in run_rows:
        name=row["name"]
        expected=(prep/"m_iss"/f"{name}.trace").read_text(encoding="ascii")
        expected_trap_rows=read_tsv_records(prep/"m_iss"/f"{name}.trap.tsv",
                                            ["fault_pc","raw","mcause","mtval","target"],
                                            f"{name}/ISS trap reference")
        zrows=read_tsv_records(prep/"m_iss"/f"{name}.z.tsv",
                              ["kind","pc","raw","ilen","csr_or_pcnext","funct3",
                               "source_index","source","old","new","write_intent"],
                              f"{name}/ISS CSR/FENCE.I reference")
        validate_z_records(zrows,f"{name}/ISS CSR/FENCE.I reference")
        traces={}
        launch_errors={}
        # Always capture both implementations before architectural comparisons,
        # so a golden failure does not discard pipeline diagnostics (or vice versa).
        for kind in ("golden","pipe"):
            engine,exe=snapshots[kind]
            trace,log,trap=out/f"{name}.{kind}.trace",out/f"{name}.{kind}.log",out/f"{name}.{kind}.trap.tsv"
            mcov=out/f"{name}.{kind}.mcov"
            plus=[f"+HEX={launch.simulator_path(resolve_image(row))}",f"+TRACE={launch.simulator_path(trace)}",
                  f"+TRAP={launch.simulator_path(trap)}","+EXPECT_CAUSE=0","+CHECK_GP=0"]
            if row["irq_pc"]:
                plus += [f"+IRQ_PC={row['irq_pc']}",f"+IRQ_LEVELS={row['irq_levels']}",
                         f"+IRQ_WAIT_DIV={row['irq_wait_div']}"]
            plus += [f"+MCOV={launch.simulator_path(mcov)}"]
            try:
                if engine=="xsim":
                    args0=["xsim",exe,"--runall","--log",launch.simulator_path(log)]
                    for p in plus: args0 += ["--testplusarg",p[1:]]
                    record_command(f"run_{name}_{kind}",args0,out/"xsim")
                    launch.run(args0,out/"xsim",out/f"{name}.{kind}.launch.log")
                else:
                    args0=[exe,*plus]
                    record_command(f"run_{name}_{kind}",args0,ROOT)
                    launch.run(args0,ROOT,log)
            except Exception as exc:
                launch_errors[kind]=f"{type(exc).__name__}: {exc}"
        for kind in ("golden","pipe"):
            engine,exe=snapshots[kind]
            trace,log,trap=out/f"{name}.{kind}.trace",out/f"{name}.{kind}.log",out/f"{name}.{kind}.trap.tsv"
            mcov=out/f"{name}.{kind}.mcov"
            require(kind not in launch_errors,
                    f"{name}/{kind}: launch failed after both cores were attempted; {launch_errors}; evidence={out}")
            text=launch.terminal(log)
            require("TIMEOUT" not in text and "cause=0 expect=0" in text,f"{name}/{kind}: terminal check mismatch")
            compare(trace.read_text(encoding="ascii"),expected,f"{name}/{kind} vs independent ISS")
            actual_trap_rows=read_tsv_records(trap,["fault_pc","raw","mcause","mtval","target"],
                                              f"{name}/{kind} trap sidecar")
            require_records_equal(actual_trap_rows,expected_trap_rows,
                                  f"{name}/{kind} trap events vs independent ISS")
            mcov_lines=mcov.read_text(encoding="ascii").splitlines()
            access_rows=sidecar_records(mcov_lines,["Z","CSR_ACCESS"],9,f"{name}/{kind} CSR_ACCESS")
            actual_accesses=[record[2:] for record in access_rows]
            expected_accesses=[[e["pc"],e["raw"],e["csr_or_pcnext"],e["source"],e["old"],e["new"],e["write_intent"]]
                               for e in zrows if e["kind"]=="CSR"]
            require_records_equal(actual_accesses,expected_accesses,f"{name}/{kind} CSR access/intent sidecar")
            actual_writes=sidecar_records(mcov_lines,["Z","CSR_WRITE"],7,f"{name}/{kind} CSR_WRITE")
            expected_writes=[["Z","CSR_WRITE",e["pc"],e["raw"],e["csr_or_pcnext"],e["old"],e["new"]]
                             for e in zrows if e["kind"]=="CSR" and e["write_intent"]=="1"]
            require_records_equal(actual_writes,expected_writes,f"{name}/{kind} CSR write commit sidecar")
            mret_rows=sidecar_records(mcov_lines,["M","MRET"],4,f"{name}/{kind} MRET")
            actual_mret=[record[2] for record in mret_rows]
            expected_mret=[f"{int(line.split()[1],16):08x}" for line in expected.splitlines()
                           if line.startswith("I ") and int(line.split()[2],16)==0x30200073]
            require(actual_mret==expected_mret,f"{name}/{kind}: MRET commit records mismatch")
            fencei_rows=sidecar_records(mcov_lines,["Z","FENCEI"],6,f"{name}/{kind} FENCEI")
            actual_fencei=[record[2:] for record in fencei_rows]
            expected_fencei=[[e["pc"],e["raw"],str(int(e["ilen"])),e["csr_or_pcnext"]]
                             for e in zrows if e["kind"]=="FENCEI"]
            require_records_equal(actual_fencei,expected_fencei,
                                  f"{name}/{kind} FENCE.I PC/raw/length/next-PC/count/order")
            if name == "irq_div_restart" and kind == "pipe":
                aborts=[line.split()[2] for line in mcov_lines if line.startswith("M DIV_ABORT ")]
                require(aborts == ["00000020"], f"{name}/{kind}: expected one interrupted DIV abort, got {aborts}")
                div_insn="0262c233"
                issues=[line.split()[2:] for line in mcov_lines if line.startswith("EV ISSUE 00000020 ")]
                completes=[line.split()[2:] for line in mcov_lines if line.startswith("EV COMPLETE 00000020 ")]
                retires=[line.split()[2:] for line in mcov_lines if line.startswith("EV RETIRE 00000020 ")]
                expected_div=["00000020",div_insn]
                require(issues == [expected_div,expected_div] and completes == [expected_div] and retires == [expected_div],
                        f"{name}/{kind}: DIV must start, abort, restart, complete, and retire once; "
                        f"issues={issues} completes={completes} retires={retires}")
                div_irq_aborts += len(aborts)
            fencei_count += len(expected_fencei) if kind == "golden" else 0
            csr_commits += len(actual_writes); mret_count += len(actual_mret)
            csr_addresses.update(int(e["csr_or_pcnext"],16) for e in zrows if e["kind"]=="CSR")
            # Hardware counters have independent timing: minstret must equal the
            # retired trace count; mcycle must equal the local simulator cycle count.
            trace_text=trace.read_text(encoding="ascii")
            stop=next(line.split() for line in trace_text.splitlines() if line.startswith("STOP "))
            instret=trace_text.count("\nI ")
            require(int(stop[-1])==0,f"{name}/{kind}: completion STOP cause is not zero")
            result=re.search(r"instret=(\d+) cycles=(\d+)",text)
            require(result is not None,f"{name}/{kind}: missing cycle/retirement terminal counters")
            csr={line.split()[1]:int(line.split()[2],16) for line in trace_text.splitlines() if line.startswith("CSR ")}
            terminal_instret,terminal_cycles=map(int,result.groups())
            require(terminal_instret==instret,f"{name}/{kind}: terminal instret differs from retirement trace")
            require(csr.get("b02")== (terminal_instret & 0xffffffff),f"{name}/{kind}: minstret low half differs from retired count")
            require(csr.get("b82")== ((terminal_instret >> 32) & 0xffffffff),f"{name}/{kind}: minstret high half differs from retired count")
            require(csr.get("b00")== (terminal_cycles & 0xffffffff),f"{name}/{kind}: mcycle low half differs from local cycle count")
            require(csr.get("b80")== ((terminal_cycles >> 32) & 0xffffffff),f"{name}/{kind}: mcycle high half differs from local cycle count")
            traces[kind]=trace_text; full+=1
        compare(traces["pipe"],traces["golden"],f"{name} pipeline/golden trace")
        gold_pipe+=1
        trap_count += len(expected_trap_rows)
        for event in expected_trap_rows:
            cause=int(event["mcause"],16)
            (irq_causes if cause & 0x80000000 else sync_causes).add(cause & 0x7fffffff)
    report_prefix="stage8" if args.stage8 else "stage7"
    report=ROOT/"reports"/f"{report_prefix}_{args.sim}_{run_kind}_{stamp}.txt"; report.parent.mkdir(exist_ok=True)
    files=source_paths
    verify_snapshot(snapshot_file)
    digest="\n".join(f"sha256 {p.relative_to(ROOT).as_posix()}={hashlib.sha256(p.read_bytes()).hexdigest()}" for p in files)
    coverage=(f"cases={len(run_rows)} traces={full} golden_pipeline={gold_pipe} " +
              (f"stage7_existing={sum(1 for r in run_rows if r.get('suite') == 'stage7_enabled')} "
               f"stage8_seeded={sum(1 for r in run_rows if r.get('suite') == 'stage8_seeded')} " if args.stage8 else "") +
              f"traps={trap_count} "
              f"sync_causes={','.join(str(x) for x in sorted(sync_causes))} "
              f"irq_causes={','.join(str(x) for x in sorted(irq_causes))} "
              f"csr_commits_both_cores={csr_commits} csr_addresses={','.join(f'{x:03x}' for x in sorted(csr_addresses))} "
              f"mret={mret_count} fencei={fencei_count} interrupted_div_aborts={div_irq_aborts}\n")
    (out/"stage7_coverage.txt").write_text(coverage,encoding="utf-8",newline="\n")
    marker="STAGE8_ENABLED" if args.stage8 else "STAGE7_ENABLED"
    report.write_text(f"{marker}_{args.sim.upper()} PASS evidence_dir={out.resolve()} selection_manifest={selection_path.resolve()} "
                      f"producer_snapshot={snapshot_file.resolve()} producer_snapshot_sha256={hashlib.sha256(snapshot_file.read_bytes()).hexdigest()} "
                      f"{coverage}{digest}\n",encoding="utf-8",newline="\n")
    print(report.read_text(encoding="utf-8"),end="")
    print(f"RUN_REPORT={report.resolve()}",flush=True)


if __name__ == "__main__": main()
