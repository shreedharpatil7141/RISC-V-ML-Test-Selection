#!/usr/bin/env python3
"""Index the source-matched Stage 5, 6, and 8 saved runs for Stage 9 consolidation."""
import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
sys.path.insert(0,str(HERE))
import stage9_coverage as cov

def verify_stage8_preparation(manifest: Path) -> tuple[Path,int]:
    prep=manifest.parent/"stage8_preparation.txt"
    cov.require(prep.is_file(),f"missing final Stage 8 preparation provenance: {prep}")
    text=prep.read_text(encoding="utf-8",errors="replace")
    cov.require("STAGE8_PREPARATION READY" in text,"final Stage 8 preparation is not PASS")
    stage7_prep=manifest.parent/"stage7_preparation.txt"
    cov.require(stage7_prep.is_file(),f"missing Stage 7 preparation provenance: {stage7_prep}")
    for note in (stage7_prep,prep):
        note_text=note.read_text(encoding="utf-8",errors="replace")
        source_hashes=re.findall(r"^sha256 ([^=]+)=([0-9a-f]{64})$",note_text,re.M)
        cov.require(source_hashes,f"preparation has no source hashes: {note}")
        for rel,digest in source_hashes:
            source=cov.resolve_workspace_path(rel).resolve()
            cov.require(source.is_file() and cov.provenance_hash_matches(source,digest),
                        f"preparation source hash is stale/missing: {source}")
    want=hashlib.sha256(manifest.read_bytes()).hexdigest()
    match=re.search(r"^artifact_sha256 @PREPARED@/m_manifest\.csv=([0-9a-f]{64})$",text,re.M)
    cov.require(match and match.group(1)==want,"Stage 8 manifest does not match final preparation provenance")
    artifacts=re.findall(r"^artifact_sha256 ([^=]+)=([0-9a-f]{64})$",text,re.M)
    cov.require(artifacts,"Stage 8 preparation has no artifact hashes")
    for rel,digest in artifacts:
        p=(manifest.parent/rel[len("@PREPARED@/"):]) if rel.startswith("@PREPARED@/") else cov.resolve_workspace_path(rel)
        p=p.resolve()
        cov.require(p.is_file() and cov.provenance_hash_matches(p,digest),
                    f"Stage 8 prepared artifact hash mismatch: {p}")
    return prep,len(artifacts)

def check_report(path: Path, marker: str, sim: str, stage: str, outdir: Path,
                 stage8_manifest: Path | None = None) -> dict:
    cov.require(path.is_file(),f"missing validation report: {path}")
    text=path.read_text(encoding="utf-8",errors="replace")
    cov.require(marker in text,f"validation marker missing: {path}: {marker}")
    if stage=="stage5":
        found=re.search(r"^Simulator:\s*(\w+)$",text,re.M)
        cov.require(found and found.group(1).lower()==sim,f"wrong Stage 5 simulator identity: {path}")
        od=re.search(r"^output_dir=(.+)$",text,re.M)
        cov.require(od and cov.resolve_workspace_path(od.group(1)).resolve()==outdir.resolve(),f"Stage 5 report/output directory mismatch: {path}")
        prov=re.search(r"^provenance_file=(.+)$",text,re.M)
        cov.require(prov,"Stage 5 report lacks provenance file reference")
        prov_path=cov.resolve_workspace_path(prov.group(1),path.parent).resolve()
        cov.require(prov_path==outdir/"provenance.txt" and prov_path.is_file(),f"Stage 5 provenance/output mismatch: {prov_path}")
        provenance_check=cov.validate_report_provenance(path,text,sim)
        checked=provenance_check["source_hashes_checked"]
        provenance=relative(prov_path)
        provenance_sha256=hashlib.sha256(prov_path.read_bytes()).hexdigest()
    else:
        provenance_check=cov.validate_report_provenance(path,text,sim)
        checked=provenance_check["source_hashes_checked"]
        provenance=relative(path)
        provenance_sha256=hashlib.sha256(path.read_bytes()).hexdigest()
    if stage=="stage6":
        cov.require(stage8_manifest is not None,"Stage 6 manifest linkage unavailable")
        prep=stage8_manifest.parent/"stage6_compat"/"z_manifest.csv"
        want=re.search(r"^prepared_manifest_sha256=([0-9a-f]{64})$",text,re.M)
        cov.require(prep.is_file() and want and hashlib.sha256(prep.read_bytes()).hexdigest()==want.group(1),
                    f"Stage 6 prepared manifest does not match saved run: {path}")
        names={p.name[:-len(".pipe.trace")] for p in outdir.glob("stage6_*.pipe.trace")}
        cov.require(len(names)==11 and len({p.name[:-len(".golden.trace")] for p in outdir.glob("stage6_*.golden.trace")})==11,
                    f"Stage 6 {sim} run inventory must contain 11 DUT/golden traces")
    if stage=="stage5":
        manifest=cov.read_stage5_manifests(outdir)
        names={r["name"] for r in manifest}
        for suffix,count in ((".pipe.trace",248),(".golden.trace",248),(".pipe.log",248)):
            cov.require(len(list(outdir.glob("*"+suffix)))==count,f"Stage 5 {sim} missing {suffix} evidence")
        for suffix in (".pipe.trace",".golden.trace",".pipe.log"):
            actual={p.name[:-len(suffix)] for p in outdir.glob("*"+suffix)}
            cov.require(actual==names,f"Stage 5 {sim} {suffix} identities do not match combined manifests")
        for row in manifest:
            name=row["name"]
            hex_path=cov.resolve_workspace_path(row["hexpath"]).resolve()
            suite=row["suite"]
            iss_dir=outdir/"iss" if suite=="rv32im" else outdir/"c_iss" if suite in ("rv32imc","rv32imc_pipeline") else outdir/"a_iss"
            cov.require(hex_path.is_file(),f"Stage 5 {sim} manifest image missing: {hex_path}")
            cov.require((iss_dir/(name+".iss.trace" if suite=="rv32im" else name+".trace")).is_file(),
                        f"Stage 5 {sim} independent reference trace missing for {name}")
            if suite=="rv32im":
                cov.require((outdir/"iss"/(name+".iss.m.tsv")).is_file(),f"Stage 5 ISS M sidecar missing for {name}")
            elif suite.startswith("rv32ima") or suite.startswith("rv32imac"):
                cov.require((outdir/"a_iss"/(name+".a.tsv")).is_file(),f"Stage 5 atomic reference sidecar missing for {name}")
    if stage=="stage8":
        cov.require(stage8_manifest is not None,"Stage 8 manifest linkage unavailable")
        prep,artifact_count=verify_stage8_preparation(stage8_manifest)
        prep_rel=relative(prep)
        prep_hash=hashlib.sha256(prep.read_bytes()).hexdigest()
        linked=re.search(rf"^sha256 {re.escape(prep_rel)}=([0-9a-f]{{64}})$",text,re.M)
        cov.require(linked and linked.group(1)==prep_hash,
                    f"Stage 8 report is not linked to the final owner preparation: {path}")
        checked+=artifact_count
    return {"pass_marker":marker,"report_sha256":hashlib.sha256(path.read_bytes()).hexdigest(),
            "source_hashes_checked":checked,"provenance":provenance,"provenance_sha256":provenance_sha256}

def relative(path: Path) -> str:
    try: return path.resolve().relative_to(ROOT).as_posix()
    except ValueError as ex: raise ValueError(f"artifact must be inside the workspace: {path}") from ex

def main() -> int:
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--stage5-verilator",required=True,type=Path); ap.add_argument("--stage5-verilator-report",required=True,type=Path)
    ap.add_argument("--stage6-verilator",required=True,type=Path); ap.add_argument("--stage6-verilator-report",required=True,type=Path)
    ap.add_argument("--stage8-verilator",required=True,type=Path); ap.add_argument("--stage8-verilator-report",required=True,type=Path)
    ap.add_argument("--stage5-xsim",required=True,type=Path); ap.add_argument("--stage5-xsim-report",required=True,type=Path)
    ap.add_argument("--stage6-xsim",required=True,type=Path); ap.add_argument("--stage6-xsim-report",required=True,type=Path)
    ap.add_argument("--stage8-xsim",required=True,type=Path); ap.add_argument("--stage8-xsim-report",required=True,type=Path)
    ap.add_argument("--stage8-manifest",required=True,type=Path)
    ap.add_argument("--output",type=Path,default=ROOT/"reports/stage9_coverage/prepared.json")
    a=ap.parse_args()
    simulators={}
    for sim in ("verilator","xsim"):
        simulators[sim]={}
        for stage in ("stage5","stage6","stage8"):
            od=getattr(a,f"{stage}_{sim}").resolve()
            report=getattr(a,f"{stage}_{sim}_report").resolve()
            if stage=="stage5":
                marker=f"STAGE5_A_PIPELINE_{sim.upper()} PASS legacy=209 c_cases=21 a_cases=18 full_trace_comparisons=496 units=8"
            elif stage=="stage6": marker=f"STAGE6_ENABLED_{sim.upper()} PASS cases=11 full_trace_comparisons=22 pipeline_golden=11 atomic_sidecars=22 z_sidecar_events=11"
            else:
                marker=f"STAGE8_ENABLED_{sim.upper()} PASS cases=23 traces=46 golden_pipeline=23 stage7_existing=13 stage8_seeded=10"
            cov.require(od.is_dir(),f"missing simulator output directory: {od}")
            evidence=check_report(report,marker,sim,stage,od,a.stage8_manifest.resolve())
            simulators[sim][stage]={"outdir":relative(od),"report":relative(report),**evidence}
    manifest=a.stage8_manifest.resolve()
    cov.require(manifest.is_file(),f"missing Stage 8 manifest: {manifest}")
    stage8_prep,stage8_artifacts=verify_stage8_preparation(manifest)
    mrows=cov.read_manifest(manifest,{"name","hexpath","source","seed","suite"})
    cov.require(len(mrows)==23 and len({r["name"] for r in mrows})==23,"final Stage 8 manifest must contain 23 unique cases")
    cov.require(stage8_artifacts>0,"final Stage 8 artifact provenance is empty")
    for sim in simulators:
        out=ROOT/simulators[sim]["stage8"]["outdir"]
        names={r["name"] for r in mrows}
        cov.require({p.name[:-len(".pipe.trace")] for p in out.glob("*.pipe.trace")}==names,
                    f"Stage 8 {sim} trace inventory does not match final manifest")
        cov.require({p.name[:-len(".golden.trace")] for p in out.glob("*.golden.trace")}==names,
                    f"Stage 8 {sim} golden inventory does not match final manifest")
    for sim in simulators: simulators[sim]["stage8"]["manifest"]=relative(manifest)
    for sim in simulators:
        simulators[sim]["stage8"]["manifest_sha256"]=hashlib.sha256(manifest.read_bytes()).hexdigest()
        simulators[sim]["stage8"]["preparation_provenance"]=relative(stage8_prep)
    payload={"schema_version":cov.SCHEMA_VERSION,"dictionary_version":cov.DICTIONARY_VERSION,
             "base_commit":"fcc151dccc4e8e98b4b70ba52871c8a0594a4967","simulators":simulators}
    # Emit derived Stage 9 metadata only after every saved evidence input is
    # verified, so a rejected preparation leaves the evidence tree untouched.
    cov.write_dictionary()
    cov.write_migration()
    out=a.output.resolve(); out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(payload,indent=2)+"\n",encoding="utf-8",newline="\n")
    print(f"STAGE9_PREPARATION PASS schema={cov.SCHEMA_VERSION} dictionary={cov.DICTIONARY_VERSION} source_matched=6 reports=6")
    print(out)
    return 0

if __name__=="__main__":
    try: raise SystemExit(main())
    except (ValueError,OSError,KeyError) as ex:
        print(f"STAGE9_PREPARATION INVALID {type(ex).__name__}: {ex}",file=sys.stderr); raise SystemExit(1)
