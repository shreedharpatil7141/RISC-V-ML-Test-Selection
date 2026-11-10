#!/usr/bin/env python3
"""Run compatibility, modular component checks, and seeded ISS-backed integration."""
import argparse, datetime, hashlib, json, os, re, shutil, subprocess, sys
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
sys.path.insert(0,str(HERE))
import run_stage6_enabled as launch
from run_stage7_enabled import compare
COMMANDS=[]

def require(ok,message):
    if not ok: raise RuntimeError(message)

def capture(args,cwd,log,expected_failure=False,marker=None):
    actual,exe=launch.command_for(list(map(str,args)))
    COMMANDS.append({"argv":list(map(str,args)),"cwd":str(Path(cwd).resolve()),
                     "log":str(Path(log).resolve()),"expected_failure":expected_failure})
    try:
        result=subprocess.run(actual,cwd=cwd,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    except OSError as exc:
        Path(log).write_text(f"LAUNCH_FAILURE executable={exe!r} cwd={str(cwd)!r} args={args!r} error={exc!r}\n",encoding="utf-8",newline="\n")
        raise
    Path(log).write_text(result.stdout,encoding="utf-8",newline="\n")
    if expected_failure:
        require(result.returncode!=0 and marker and marker in result.stdout,
                f"negative protocol run did not reject expected defect rc={result.returncode} marker={marker!r} log={log}")
    else:
        require(result.returncode==0,
                f"command failed rc={result.returncode} exe={exe!r} cwd={str(cwd)!r} argv={list(map(str,args))!r} log={log}")
        if marker: require(marker in result.stdout,f"missing terminal marker {marker!r}; log={log}")
    return result.stdout

def source_inventory(prep):
    path=prep/"stage8_preparation.txt"
    note=path.read_text(encoding="ascii")
    match=re.search(r"STAGE8_PREPARATION READY base_cases=13 generated_cases=(\d+) total_cases=(\d+) errors=0",note)
    require(match is not None,"Stage 8 preparation marker missing")
    for line in note.splitlines():
        m=re.fullmatch(r"(artifact_sha256|sha256) (.+)=([0-9a-f]{64})",line)
        if not m: continue
        kind,rel,want=m.groups()
        p=(prep/rel[len("@PREPARED@/"):] if rel.startswith("@PREPARED@/") else ROOT/rel)
        require(p.is_file() and hashlib.sha256(p.read_bytes()).hexdigest()==want,
                f"preparation provenance mismatch: {p}")
    return int(match.group(1)),int(match.group(2))

def run_units(sim,prep,out):
    component=ROOT/"verification/stage8/rv_stage8_components.sv"
    tb=ROOT/"verification/environment/tb_rv_stage8_components.sv"
    hexfile=prep/"stage8_component.hex"
    if sim=="verilator":
        build=out/"stage8_units"; build.mkdir()
        capture(["verilator","-sv","--binary","--timing","-Wno-fatal","-Wno-lint","-Wno-style",
                 component,tb,"--top-module","tb_rv_stage8_components","-Mdir",build,"-o","s8_units"],
                ROOT,out/"stage8_units.build.log")
        capture([build/"s8_units",f"+HEX={launch.simulator_path(hexfile)}"],ROOT,out/"stage8_units.run.log",
                marker="STAGE8_COMPONENT_UNIT PASS")
        bad=out/"stage8_bad_csr"; bad.mkdir()
        capture(["verilator","-sv","--binary","--timing","-Wno-fatal","-Wno-lint","-Wno-style",
                 component,tb,"--top-module","tb_rv_stage8_bad_csr","-Mdir",bad,"-o","s8_bad_csr"],
                ROOT,out/"stage8_bad_csr.build.log")
        capture([bad/"s8_bad_csr"],ROOT,out/"stage8_bad_csr.run.log",True,"STAGE8_CSR unauthorized/misaligned commit")
        bad_retire=out/"stage8_bad_retire"; bad_retire.mkdir()
        capture(["verilator","-sv","--binary","--timing","-Wno-fatal","-Wno-lint","-Wno-style",
                 component,tb,"--top-module","tb_rv_stage8_bad_retire","-Mdir",bad_retire,"-o","s8_bad_retire"],
                ROOT,out/"stage8_bad_retire.build.log")
        for kind,marker in ((1,"STAGE8_RETIRE invalid length"),
                            (2,"STAGE8_RETIRE malformed 16-bit record"),
                            (3,"STAGE8_RETIRE malformed 16-bit record"),
                            (4,"STAGE8_RETIRE malformed 32-bit record")):
            capture([bad_retire/"s8_bad_retire",f"+BAD_RETIRE_KIND={kind}"],ROOT,
                    out/f"stage8_bad_retire_{kind}.run.log",True,marker)
    else:
        xdir=out/"xsim_units"; xdir.mkdir()
        capture(["xvlog","-sv",launch.simulator_path(component),launch.simulator_path(tb)],xdir,out/"stage8_units.compile.log")
        capture(["xelab","-debug","off","tb_rv_stage8_components","-s","s8_units"],xdir,out/"stage8_units.elab.log")
        capture(["xsim","s8_units","--runall","--log",launch.simulator_path(out/"stage8_units.sim.log"),
                 "--testplusarg",f"HEX={launch.simulator_path(hexfile)}"],xdir,out/"stage8_units.run.log")
        unit_text=(out/"stage8_units.run.log").read_text(encoding="utf-8",errors="replace")+(out/"stage8_units.sim.log").read_text(encoding="utf-8",errors="replace")
        require("STAGE8_COMPONENT_UNIT PASS" in unit_text,"XSim component unit did not pass")
        capture(["xelab","-debug","off","tb_rv_stage8_bad_csr","-s","s8_bad_csr"],xdir,out/"stage8_bad_csr.elab.log")
        negative_argv=["xsim","s8_bad_csr","--runall","--log",launch.simulator_path(out/"stage8_bad_csr.sim.log")]
        actual,exe=launch.command_for(negative_argv)
        COMMANDS.append({"argv":negative_argv,"cwd":str(xdir.resolve()),
                         "log":str((out/"stage8_bad_csr.run.log").resolve()),"expected_failure":True})
        result=subprocess.run(actual,cwd=xdir,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
        (out/"stage8_bad_csr.run.log").write_text(result.stdout,encoding="utf-8",newline="\n")
        neg=result.stdout+(out/"stage8_bad_csr.sim.log").read_text(encoding="utf-8",errors="replace")
        require("STAGE8_CSR unauthorized/misaligned commit" in neg,
                f"XSim negative protocol check failed to report CSR defect rc={result.returncode}")
        capture(["xelab","-debug","off","tb_rv_stage8_bad_retire","-s","s8_bad_retire"],
                xdir,out/"stage8_bad_retire.elab.log")
        for kind,marker in ((1,"STAGE8_RETIRE invalid length"),
                            (2,"STAGE8_RETIRE malformed 16-bit record"),
                            (3,"STAGE8_RETIRE malformed 16-bit record"),
                            (4,"STAGE8_RETIRE malformed 32-bit record")):
            simlog=out/f"stage8_bad_retire_{kind}.sim.log"
            negative_argv=["xsim","s8_bad_retire","--runall","--log",launch.simulator_path(simlog),
                           "--testplusarg",f"BAD_RETIRE_KIND={kind}"]
            actual,exe=launch.command_for(negative_argv)
            runlog=out/f"stage8_bad_retire_{kind}.run.log"
            COMMANDS.append({"argv":negative_argv,"cwd":str(xdir.resolve()),
                             "log":str(runlog.resolve()),"expected_failure":True})
            result=subprocess.run(actual,cwd=xdir,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
            runlog.write_text(result.stdout,encoding="utf-8",newline="\n")
            sim_text=simlog.read_text(encoding="utf-8",errors="replace") if simlog.is_file() else ""
            require(marker in result.stdout+sim_text,
                    f"XSim retirement monitor kind={kind} failed to reject malformed record rc={result.returncode}; logs={runlog},{simlog}")
    # Exercise the actual architectural trace comparator with a one-bit retirement-PC fault.
    trace=(prep/"m_iss"/next((prep/"stage8_src").glob("seed_*.s")).stem).with_suffix(".trace")
    expected=trace.read_text(encoding="ascii")
    match=re.search(r"(?m)^I ([0-9a-f]{8}) ",expected)
    require(match is not None,"negative scoreboard check needs an instruction reference")
    bad_pc=f"{(int(match.group(1),16)^2):08x}"
    mutated=expected[:match.start(1)]+bad_pc+expected[match.end(1):]
    try: compare(mutated,expected,"Stage 8 injected retirement-PC error")
    except RuntimeError: pass
    else: raise RuntimeError("independent trace scoreboard accepted an injected retirement-PC error")

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sim",required=True,choices=("verilator","xsim"))
    parser.add_argument("--prepared",required=True)
    args=parser.parse_args()
    prep=Path(args.prepared).resolve()/"stage7"
    generated,total=source_inventory(prep)
    rows=list(__import__("csv").DictReader((prep/"m_manifest.csv").open(newline="")))
    require(len(rows)==total==13+generated and len({r["name"] for r in rows})==len(rows),"Stage 8 manifest count/name mismatch")
    tools=("verilator","make") if args.sim=="verilator" else ("xvlog","xelab","xsim")
    missing=[name for name in tools if shutil.which(name) is None]
    cpp=next((shutil.which(x) for x in ("g++","clang++","c++") if shutil.which(x)),None)
    if args.sim=="verilator" and cpp is None: missing.append("C++ compiler (g++, clang++, or c++)")
    if missing: raise RuntimeError("tool preflight missing: "+", ".join(missing))
    if args.sim=="xsim":
        launch.COMSPEC=os.environ.get("COMSPEC") or shutil.which("cmd.exe")
    stamp=datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out=ROOT/"reports"/"stage8_runs"/f"run_{stamp}_{args.sim}"
    out.mkdir(parents=True,exist_ok=False)
    def run_python(name,script,extra,marker):
        command=[sys.executable,str(HERE/script),*map(str,extra)]
        return capture(command,ROOT,out/(name+".log"),marker=marker)
    try:
        run_units(args.sim,prep,out)
        compat=run_python("compat_stage5", "run_stage4_4.py", ["--sim",args.sim,"--enable-a"],
                          f"STAGE5_A_PIPELINE_{args.sim.upper()} PASS legacy=209 c_cases=21 a_cases=18")
        stage6=run_python("compat_stage6", "run_stage6_enabled.py", ["--sim",args.sim,"--prepared",prep/"stage6_compat"],
                          f"STAGE6_ENABLED_{args.sim.upper()} PASS cases=11")
        enabled=run_python("stage7_and_seeded", "run_stage7_enabled.py", ["--sim",args.sim,"--prepared",prep,"--stage8"],
                           f"STAGE8_ENABLED_{args.sim.upper()} PASS cases={total}")
        require("full_trace_comparisons=496" in compat,"Stage 5 compatibility trace count mismatch")
        require("full_trace_comparisons=22" in stage6,"Stage 6 compatibility trace count mismatch")
        match=re.search(r"traces=(\d+) golden_pipeline=(\d+)",enabled)
        require(match and int(match.group(1))==2*total and int(match.group(2))==total,
                "Stage 7/8 integration comparison counts mismatch")
        summary=(f"STAGE8_{args.sim.upper()} PASS compatibility=259 stage5=248 stage6=11 "
                 f"stage7_existing=13 seeded={generated} enabled_total={total} "
                 f"iss_comparisons={2*total} golden_pipeline={total} scoreboard_negative=1 "
                 f"protocol_negative=1 retirement_negative=4\n")
        (out/"stage8_summary.txt").write_text(summary,encoding="ascii",newline="\n")
        (out/"commands.json").write_text(json.dumps(COMMANDS,indent=2)+"\n",encoding="utf-8",newline="\n")
        report=ROOT/"reports"/f"stage8_{args.sim}_{stamp}.txt"
        srcs=[HERE/"prepare_stage8.py",HERE/"run_stage8_enabled.py",HERE/"stage8_scenarios.py",HERE/"stage8_software_selftest.py",
              HERE/"run_stage7_enabled.py",ROOT/"verification/stage8/rv_stage8_components.sv",
              ROOT/"verification/environment/tb_rv_stage8.sv",ROOT/"verification/environment/tb_rv_stage8_components.sv",
              ROOT/"verification/environment/tb_rv_core.sv",
              ROOT/"verification/environment/tb_rv_pipe_stage4.sv",ROOT/"tests/directed/rv32imac_stage7/manifest.csv"]
        hashes="\n".join(f"sha256 {p.relative_to(ROOT).as_posix()}={hashlib.sha256(p.read_bytes()).hexdigest()}" for p in srcs)
        report.write_text(summary+f"evidence=reports/stage8_runs/run_{stamp}_{args.sim}\n"+hashes+"\n",encoding="utf-8",newline="\n")
        print(report.read_text(encoding="utf-8"),end="")
    except Exception as exc:
        (out/"commands.json").write_text(json.dumps(COMMANDS,indent=2)+"\n",encoding="utf-8",newline="\n")
        (out/"failure.txt").write_text(f"STAGE8_{args.sim.upper()} INVALID {type(exc).__name__}: {exc}\n",encoding="utf-8",newline="\n")
        raise

if __name__=="__main__": main()
