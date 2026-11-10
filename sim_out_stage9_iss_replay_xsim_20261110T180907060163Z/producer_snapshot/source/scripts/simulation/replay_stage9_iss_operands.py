#!/usr/bin/env python3
"""Replay independent RV32IMC/IMAC ISS operand evidence for saved Stage 5 runs."""
import argparse
import csv
import datetime
import hashlib
import json
import sys
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
sys.path.insert(0,str(HERE))
import rv32imc_iss
from stage9_run_provenance import capture_snapshot,verify_snapshot


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def replay(sim: str, stage5_out: Path, output: Path) -> dict:
    stage5_out=stage5_out.resolve(); output=output.resolve()
    if output.exists(): raise FileExistsError(f"refusing to overwrite ISS replay output: {output}")
    c_rows=list(csv.DictReader((stage5_out/"c_manifest.csv").open(newline="",encoding="utf-8")))
    a_rows=list(csv.DictReader((stage5_out/"a_manifest.csv").open(newline="",encoding="utf-8")))
    if len(c_rows)!=21 or len(a_rows)!=18 or len({r["name"] for r in c_rows+a_rows})!=39:
        raise ValueError("Stage 5 C/A replay input must contain exactly 21 C and 18 A unique cases")
    output.mkdir(parents=True)
    sources=[HERE/n for n in ("replay_stage9_iss_operands.py","rv32imc_iss.py","rv32i_iss.py","rv32a_model.py","rv32c_model.py","stage9_run_provenance.py")]
    inputs=[stage5_out/n for n in ("c_manifest.csv","a_manifest.csv","selection_manifest.csv","provenance.txt")]
    selected=[]
    for mode,rows in (("rv32imc",c_rows),("rv32imac",a_rows)):
        for row in rows:
            name=row["name"]
            image=stage5_out/("c_hex" if mode=="rv32imc" else "a_hex")/(name+".hex")
            ref=stage5_out/("c_iss" if mode=="rv32imc" else "a_iss")/(name+".trace")
            pipe=stage5_out/(name+".pipe.trace"); golden=stage5_out/(name+".golden.trace")
            for path in (image,ref,pipe,golden):
                if not path.is_file(): raise FileNotFoundError(f"replay input missing: {path}")
                inputs.append(path)
            selected.append((mode,row,image,ref,pipe,golden))
    snap=capture_snapshot(output/"producer_snapshot",sources,inputs,
                          [sys.executable,str(HERE/"replay_stage9_iss_operands.py"),"--sim",sim,
                           "--stage5-outdir",str(stage5_out),"--output",str(output)])
    side_dir=output/"iss"; trace_dir=output/"replayed_trace"
    side_dir.mkdir(); trace_dir.mkdir()
    manifest=[]
    for mode,row,image,ref,pipe,golden in selected:
        name=row["name"]; c_on=mode in ("rv32imc","rv32imac"); a_on=mode in ("rv32ima","rv32imac")
        m_events=[]; a_events=[] if a_on else None
        result=rv32imc_iss.run(rv32imc_iss.load_hex(image),c_enabled=c_on,a_enabled=a_on,
                               m_events=m_events,a_events=a_events)
        cause,regs,rows,footer,oob,steps=result
        trace_header=("TRACE_V3 RV32IMAC pc raw_insn ilen_bytes expanded_insn rd rdval st_size st_addr st_data atomic_sidecar"
                      if a_on else "TRACE_V2 RV32IMC pc raw_insn ilen_bytes expanded_insn rd rdval st_size st_addr st_data")
        replay_trace=trace_header+"\n"+"\n".join(rows+footer)+"\n"
        saved_ref=ref.read_text(encoding="ascii"); saved_pipe=pipe.read_text(encoding="ascii"); saved_golden=golden.read_text(encoding="ascii")
        for label,saved in (("independent-reference",saved_ref),("DUT-pipeline",saved_pipe),("DUT-golden",saved_golden)):
            if replay_trace.splitlines()!=saved.splitlines():
                raise ValueError(f"{name}: replayed ISS trace differs from saved {label} trace")
        trace_path=trace_dir/(name+".trace"); trace_path.write_text(replay_trace,encoding="ascii",newline="\n")
        side=side_dir/(name+".iss.m.tsv")
        with side.open("w",encoding="ascii",newline="") as target:
            writer=csv.writer(target,delimiter="\t",lineterminator="\n")
            writer.writerow(("pc","insn","op","rd","rs1","rs2","a","b","result"))
            writer.writerows((f"{pc:08x}",f"{insn:08x}",op,rd,rs1,rs2,f"{a:08x}",f"{b:08x}",f"{value:08x}")
                              for pc,insn,op,rd,rs1,rs2,a,b,value in m_events)
        manifest.append({"name":name,"configuration":mode,"image_sha256":digest(image),
                         "reference_trace_sha256":digest(ref),"dut_pipe_trace_sha256":digest(pipe),
                         "dut_golden_trace_sha256":digest(golden),"replayed_trace_sha256":digest(trace_path),
                         "m_operand_sidecar":side.relative_to(output).as_posix(),"m_operand_sha256":digest(side),
                         "m_events":len(m_events),"trace_comparisons":3,
                         "evidence_status":"RECONSTRUCTED_REFERENCE_TRACE_MATCHED"})
    verify_snapshot(snap)
    manifest_path=output/"replay_manifest.csv"
    with manifest_path.open("w",encoding="utf-8",newline="") as target:
        writer=csv.DictWriter(target,fieldnames=list(manifest[0]),extrasaction="raise",lineterminator="\n")
        writer.writeheader();writer.writerows(manifest)
    report=output/"report.txt"
    report.write_text(f"STAGE9_ISS_REPLAY_{sim.upper()} PASS cases=39 c_cases=21 a_cases=18 "
                      f"trace_comparisons=117 evidence=RECONSTRUCTED_REFERENCE_TRACE_MATCHED\n"
                      f"source_snapshot={snap.resolve()}\nsource_snapshot_sha256={digest(snap)}\n"
                      f"stage5_outdir={stage5_out}\nmanifest={manifest_path.resolve()}\n"
                      f"manifest_sha256={digest(manifest_path)}\n",encoding="utf-8",newline="\n")
    return {"outdir":output.relative_to(ROOT).as_posix(),"report":report.relative_to(ROOT).as_posix(),
            "report_sha256":digest(report),"manifest":manifest_path.relative_to(ROOT).as_posix(),
            "manifest_sha256":digest(manifest_path),"source_snapshot":snap.relative_to(ROOT).as_posix(),
            "source_snapshot_sha256":digest(snap),"cases":len(manifest),
            "evidence_status":"RECONSTRUCTED_REFERENCE_TRACE_MATCHED"}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--sim",required=True,choices=("verilator","xsim"))
    p.add_argument("--stage5-outdir",required=True,type=Path)
    p.add_argument("--output",required=True,type=Path)
    args=p.parse_args()
    info=replay(args.sim,args.stage5_outdir,args.output)
    print(f"STAGE9_ISS_REPLAY_{args.sim.upper()} PASS cases=39 trace_comparisons=117 evidence=RECONSTRUCTED_REFERENCE_TRACE_MATCHED")
    print(info["outdir"])


if __name__=="__main__":
    try: main()
    except (ValueError,OSError,KeyError,TypeError) as exc:
        print(f"STAGE9_ISS_REPLAY INVALID {type(exc).__name__}: {exc}",file=sys.stderr)
        raise SystemExit(1)
