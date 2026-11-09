#!/usr/bin/env python3
"""Run independently detected M-mode mutants after both source-matched baselines."""
import datetime, difflib, hashlib, os, re, shutil, subprocess, sys
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
REPORTS=ROOT/"reports"
SOURCES=["rtl/core/rv_machine_state.sv","rtl/core/rv_core_single.sv","rtl/core/rv_core_pipe.sv",
         "rtl/pipeline/rv_id_stage.sv","rtl/pipeline/rv_ex_stage.sv","rtl/pipeline/rv_mem_stage.sv",
         "rtl/decoder/rv_decoder.sv","rtl/packages/rv32_pkg.sv","rtl/packages/rv_pipe_pkg.sv",
         "scripts/simulation/rv32imc_iss.py","scripts/simulation/prepare_stage7.py",
         "scripts/simulation/run_stage7_enabled.py","verification/environment/tb_rv_core.sv",
         "verification/environment/tb_rv_pipe_stage4.sv","verification/environment/tb_rv_stage7.sv",
         "tests/directed/rv32imac_stage7/manifest.csv"]
MUTANTS=[
    ("M01","MIE is not restored from MPIE","rtl/core/rv_machine_state.sv",
     "mstatus <= (32'h0000_1800 | (mstatus[7] ? 32'h8 : 0) | 32'h80);",
     "mstatus <= 32'h0000_1880;","machine_trap_return"),
    ("M02","vectored mtvec drops the interrupt offset","rtl/core/rv_machine_state.sv",
     "{25'b0,trap_cause,2'b00}","32'b0","irq_vectored_priority"),
    ("M03","trap fails to invalidate LR reservation","rtl/core/rv_core_pipe.sv",
     ".reservation_invalidate(machine_trap || irq_take)",".reservation_invalidate(1'b0)","lr_trap_sc"),
]


def fail(msg): raise SystemExit("STAGE7_MUTATION INVALID: "+msg)


def main():
    baselines={}
    for sim,marker in (("verilator","STAGE7_ENABLED_VERILATOR PASS cases=13"),("xsim","STAGE7_ENABLED_XSIM PASS cases=13")):
        candidates=sorted(REPORTS.glob(f"stage7_{sim}_*.txt"),key=lambda p:p.stat().st_mtime,reverse=True)
        match=None
        for report in candidates:
            data=report.read_text(encoding="utf-8")
            hashes=re.findall(r"^sha256 (.+)=([0-9a-f]{64})$",data,re.M)
            source_matched=bool(hashes) and all((ROOT/name).is_file() and hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==digest for name,digest in hashes)
            if marker in data and source_matched:
                match=report; break
        if match is None: fail(f"no source-matched {sim} baseline report (required {marker})")
        baselines[sim]=match
    prep_candidates=sorted(ROOT.glob("sim_out_stage7_prepare_*/stage7_preparation.txt"),key=lambda p:p.stat().st_mtime,reverse=True)
    if not prep_candidates: fail("prepared Stage 7 inputs not found")
    prep_file=prep_candidates[0]
    if "STAGE7_PREPARATION READY stage6_compat=259 stage7_cases=13 images=13 references=13 errors=0" not in prep_file.read_text(encoding="ascii"):
        fail("latest Stage 7 preparation inventory failed")
    stamp=datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out=REPORTS/"stage7_machine_mutation_runs"/f"run_{stamp}"
    out.mkdir(parents=True)
    (out/"baseline_provenance.txt").write_text("\n".join(f"{k}={v}" for k,v in baselines.items())+"\n",encoding="utf-8",newline="\n")
    prep=prep_file.parent
    caught=missed=invalid=0
    for ident,description,path,old,new,case_name in MUTANTS:
        work=out/"mutants"/ident/"workspace"; work.mkdir(parents=True)
        for directory in ("rtl","verification/environment","tests/directed/rv32imac_stage7"):
            shutil.copytree(ROOT/directory,work/directory)
        (work/"scripts/simulation").mkdir(parents=True,exist_ok=True)
        for file in ("run_stage7_enabled.py","run_stage6_enabled.py","run_stage4_4.py","prepare_stage7.py","prepare_stage6.py","stage7_software_selftest.py",
                     "rv32imc_iss.py","rv32_asm.py","rv32c_asm.py",
                     "rv32c_model.py","rv32a_model.py","rv32i_iss.py","stage4_4_rtl.f"):
            shutil.copy2(HERE/file,work/"scripts/simulation"/file)
        (work/"reports").mkdir(exist_ok=True)
        relprep=prep.relative_to(ROOT)
        shutil.copytree(prep,work/relprep)
        target=work/path; content=target.read_text(encoding="utf-8")
        if content.count(old)!=1: fail(f"{ident}: mutation anchor count is {content.count(old)}")
        mutated=content.replace(old,new,1)
        target.write_text(mutated,encoding="utf-8",newline="\n")
        staged_prep=work/relprep/"stage7_preparation.txt"
        staged_text=staged_prep.read_text(encoding="ascii")
        prefix=f"sha256 {path}="
        if staged_text.count(prefix)!=1: fail(f"{ident}: prepared source hash entry missing/duplicated for {path}")
        staged_text=re.sub(rf"(?m)^sha256 {re.escape(path)}=[0-9a-f]{{64}}$",
                           f"sha256 {path}={hashlib.sha256(mutated.encode('utf-8')).hexdigest()}",staged_text)
        staged_prep.write_text(staged_text,encoding="ascii",newline="\n")
        (evidence_dir:=out/"mutants"/ident/"source.diff").write_text(
            "".join(difflib.unified_diff(content.splitlines(True),mutated.splitlines(True),
                                         fromfile=path,tofile=path+" [mutant]")),
            encoding="utf-8",newline="\n")
        cmd=[sys.executable,str(work/"scripts/simulation/run_stage7_enabled.py"),"--sim","verilator","--prepared",str(work/relprep)]
        result=subprocess.run(cmd,cwd=work,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
        evidence=out/"mutants"/ident
        (evidence/"command.txt").write_text(" ".join(cmd)+"\n",encoding="utf-8",newline="\n")
        (evidence/"output.log").write_text(result.stdout,encoding="utf-8",newline="\n")
        if result.returncode==0:
            missed+=1; verdict="MISSED"
        elif re.search(r"command failed exit=.*(verilator|make)|%Error|Compiler emitted|segmentation fault|SIGSEGV|core dumped|internal error|fatal error",result.stdout,re.I):
            invalid+=1; verdict="INVALID_BUILD"
        else:
            caught+=1; verdict="CAUGHT"
        (evidence/"result.txt").write_text(f"{ident} {verdict} case={case_name} description={description}\n",encoding="utf-8",newline="\n")
    status="PASS" if caught==len(MUTANTS) and missed==0 and invalid==0 else "FAIL"
    report=REPORTS/f"stage7_machine_mutation_verilator_{stamp}.txt"
    mutation_sources=SOURCES+["scripts/simulation/run_stage7_mutation.py"]
    provenance="\n".join(f"sha256 {name}={hashlib.sha256((ROOT/name).read_bytes()).hexdigest()}" for name in mutation_sources)
    report.write_text(f"STAGE7_MACHINE_MUTATION_VERILATOR {status} caught={caught} missed={missed} invalid={invalid} baselines=verilator,xsim\nevidence={out.relative_to(ROOT).as_posix()}\n{provenance}\n",encoding="utf-8",newline="\n")
    print(report.read_text(encoding="utf-8"),end="")
    if status!="PASS": raise SystemExit(1)


if __name__=="__main__": main()
