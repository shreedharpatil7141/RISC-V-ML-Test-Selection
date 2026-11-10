#!/usr/bin/env python3
"""Prepare a Stage 9 index from fresh 39+11+23 runs and saved 209 legacy evidence."""
import argparse
import csv
import datetime
import hashlib
import json
import re
import sys
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
sys.path.insert(0,str(HERE))
import stage9_coverage as cov
import run_stage6_enabled as stage6
import run_stage7_enabled as stage7
import replay_stage9_iss_operands as iss_replay
from prepare_stage9 import relative, verify_stage8_preparation


def report_fields(path: Path, sim: str, marker: str, output_label: str="output_dir",
                  saved_legacy: bool=False) -> tuple[dict,str]:
    cov.require(path.is_file(),f"missing run report: {path}")
    text=path.read_text(encoding="utf-8",errors="replace")
    cov.require(marker in text,f"run report lacks PASS marker: {path}: {marker}")
    provenance=(cov.validate_report_provenance(path,text,sim)
                if not saved_legacy or "producer_snapshot=" in text
                else cov.validate_saved_legacy_supplemental(path,text,sim))
    if output_label=="evidence_dir":
        match=re.search(r"\bevidence_dir=(.*?)\s+selection_manifest=",text,re.S)
    else:
        match=re.search(rf"^{re.escape(output_label)}=(.+)$",text,re.M)
    cov.require(match is not None,f"run report missing {output_label}: {path}")
    out=cov.resolve_workspace_path(match.group(1),path.parent).resolve()
    cov.require(out.is_dir(),f"run output directory missing: {out}")
    return {"outdir":relative(out),"report":relative(path.resolve()),"pass_marker":marker,
            "report_sha256":hashlib.sha256(path.read_bytes()).hexdigest(),
            "source_hashes_checked":provenance["source_hashes_checked"],
            "provenance":relative(Path(provenance["provenance_path"])),
            "provenance_sha256":provenance["provenance_sha256"],
            "source_provenance_status":provenance["source_provenance_status"],
            "unresolved_source_hashes":provenance["unresolved_source_hashes"]},text


def validate_stage5_ca_reuse(report: Path, sim: str) -> dict:
    marker=f"STAGE9_STAGE5_CA_{sim.upper()} PASS c_cases=21 a_cases=18 selected_cases=39 full_trace_comparisons=78"
    details,_=report_fields(report,sim,marker)
    out=ROOT/details["outdir"]
    manifest=cov.read_stage5_manifests(out)
    cov.require(len(manifest)==248 and len({r["name"] for r in manifest})==248,
                "saved Stage 5 manifests must retain all 248 identities")
    selection_path=out/"selection_manifest.csv"
    with selection_path.open(newline="",encoding="utf-8") as source:
        reader=csv.DictReader(source); selection_fields=tuple(reader.fieldnames or ()); selection=list(reader)
    selected_rows=[r for r in manifest if r["suite"]!="rv32im"]
    expected={r["name"] for r in selected_rows}
    full_selection=[{"configuration":"rv32imc" if r["suite"].startswith("rv32imc") else "rv32imac",**r}
                    for r in selected_rows]
    legacy_selection=[{"suite":"rv32imc" if r["suite"].startswith("rv32imc") else "rv32imac",
                       "name":r["name"],"source_hex":r["hexpath"],
                       "configuration":"rv32imc" if r["suite"].startswith("rv32imc") else "rv32imac"}
                      for r in selected_rows]
    cov.require((selection_fields==("configuration","name","expect_cause","check_gp","suite","hexpath") and selection==full_selection) or
                (selection_fields==("suite","name","source_hex","configuration") and selection==legacy_selection),
                "Stage 5 selection must match its full producer schema or the validated historical selection schema")
    cov.require(len(selection)==39 and {r["name"] for r in selection}==expected,
                "saved Stage 5 selection must exactly match its 39 C/A identities")
    for suffix in (".pipe.trace",".golden.trace"):
        cov.require({p.name[:-len(suffix)] for p in out.glob("*"+suffix)}==expected,
                    f"saved Stage 5 C/A {suffix} evidence does not match selection")
    for row in manifest:
        if row["suite"]!="rv32im":
            cov.require(not cov.check_required_sidecars(out,row["name"],cov.stage5_sidecar_policy(row["suite"])),
                        f"saved Stage 5 C/A sidecar missing for {row['name']}")
    return details


def validate_stage6_reuse(report: Path, sim: str, expected_manifest: Path) -> dict:
    marker=f"STAGE6_ENABLED_{sim.upper()} PASS cases=11 full_trace_comparisons=22 pipeline_golden=11 atomic_sidecars=22"
    details,text=report_fields(report,sim,marker)
    manifest=stage6.read_stage6_manifest(expected_manifest)
    names={row["name"] for row in manifest}
    recorded=re.search(r"^prepared_manifest_sha256=([0-9a-f]{64})$",text,re.M)
    cov.require(recorded is not None,f"saved Stage 6 report lacks its prepared manifest hash: {report}")
    snapshot_ref=re.search(r"^producer_snapshot=(.+)$",text,re.M)
    cov.require(snapshot_ref is not None,f"saved Stage 6 report lacks its producer snapshot: {report}")
    snapshot_path=cov.resolve_workspace_path(snapshot_ref.group(1),report.parent).resolve()
    snapshot_doc=json.loads(snapshot_path.read_text(encoding="utf-8"))
    manifest_inputs=[entry for entry in snapshot_doc.get("files",[])
                     if entry.get("kind")=="input" and entry.get("path","").replace("\\","/").rsplit("/",1)[-1].lower()=="z_manifest.csv"]
    cov.require(len(manifest_inputs)==1,f"saved Stage 6 snapshot must identify one z_manifest.csv: {report}")
    input_entry=manifest_inputs[0]
    original_manifest_path=cov.resolve_workspace_path(input_entry["path"],report.parent).resolve()
    original_manifest_snapshot=cov.resolve_workspace_path(input_entry["snapshot"],report.parent).resolve()
    original_digest=hashlib.sha256(original_manifest_snapshot.read_bytes()).hexdigest()
    cov.require(recorded.group(1)==original_digest==input_entry["sha256"],
                "Stage 6 report and producer snapshot disagree on the original manifest hash")
    original_rows=stage6.read_stage6_manifest(original_manifest_snapshot)
    comparison=compare_stage6_manifest_inputs(original_manifest_snapshot,original_manifest_path,
                                               expected_manifest,snapshot_doc)
    comparison["original_manifest_sha256"]=original_digest
    comparison["refreshed_manifest_sha256"]=hashlib.sha256(expected_manifest.read_bytes()).hexdigest()
    comparison["original_manifest_path"]=str(original_manifest_path)
    comparison["original_manifest_snapshot"]=str(original_manifest_snapshot)
    comparison["refreshed_manifest_path"]=relative(expected_manifest)
    details["prepared_manifest_comparison"]=comparison
    out=ROOT/details["outdir"]
    selection=stage6.read_stage6_manifest(out/"selection_manifest.csv")
    cov.require(selection==original_rows,
                "saved Stage 6 selection metadata differs from its snapshot manifest")
    for suffix in (".pipe.trace",".golden.trace",".pipe.mcov"):
        cov.require({p.name[:-len(suffix)] for p in out.glob("*"+suffix)}==names,
                    f"saved Stage 6 {suffix} evidence does not match selection")
    return details


def compare_stage6_manifest_inputs(original_snapshot: Path, original_path: Path,
                                   refreshed_path: Path, snapshot_doc: dict | None = None) -> dict:
    """Allow only Stage 6 hexpath relocation, backed by identical input bytes."""
    old_rows=stage6.read_stage6_manifest(original_snapshot)
    new_rows=stage6.read_stage6_manifest(refreshed_path)
    cov.require([row["name"] for row in old_rows]==[row["name"] for row in new_rows],
                "Stage 6 manifest case identities/order changed")
    old_inputs={}
    if snapshot_doc is not None:
        for entry in snapshot_doc.get("files",[]):
            if entry.get("kind")=="input":
                original=cov.resolve_workspace_path(entry["path"]).resolve()
                saved=cov.resolve_workspace_path(entry["snapshot"]).resolve()
                old_inputs[str(original)]=(saved,entry["sha256"])

    def contents(path: Path, label: str) -> bytes:
        resolved=path.resolve()
        item=old_inputs.get(str(resolved))
        if item is None:
            cov.require(snapshot_doc is None,f"Stage 6 producer snapshot lacks required input: {resolved}")
            cov.require(resolved.is_file(),f"missing Stage 6 comparison input: {resolved}")
            return resolved.read_bytes()
        saved,digest=item
        cov.require(saved.is_file() and hashlib.sha256(saved.read_bytes()).hexdigest()==digest,
                    f"Stage 6 producer input snapshot corrupt: {resolved}")
        return saved.read_bytes()

    relocated=0
    artifact_hashes=0
    for old_row,new_row in zip(old_rows,new_rows):
        name=old_row["name"]
        semantic_old={key:value for key,value in old_row.items() if key!="hexpath"}
        semantic_new={key:value for key,value in new_row.items() if key!="hexpath"}
        cov.require(semantic_old==semantic_new,
                    f"Stage 6 manifest semantic fields changed for {name}: {semantic_old} != {semantic_new}")
        old_image=cov.resolve_workspace_path(old_row["hexpath"]).resolve()
        new_image=cov.resolve_workspace_path(new_row["hexpath"]).resolve()
        cov.require(old_image.name==new_image.name==name+".hex",
                    f"Stage 6 image identity changed for {name}: {old_image} / {new_image}")
        old_bytes=contents(old_image,f"{name}.hex")
        cov.require(new_image.is_file(),f"refreshed Stage 6 image missing: {new_image}")
        new_bytes=new_image.read_bytes()
        cov.require(hashlib.sha256(old_bytes).digest()==hashlib.sha256(new_bytes).digest(),
                    f"Stage 6 image content changed for {name}")
        artifact_hashes+=1
        for suffix in ("trace","a.tsv","z.tsv"):
            old_ref=original_path.parent/"z_iss"/f"{name}.{suffix}"
            new_ref=refreshed_path.parent/"z_iss"/f"{name}.{suffix}"
            old_bytes=contents(old_ref,f"{name}.{suffix}")
            cov.require(new_ref.is_file(),f"refreshed Stage 6 reference missing: {new_ref}")
            new_bytes=new_ref.read_bytes()
            cov.require(hashlib.sha256(old_bytes).digest()==hashlib.sha256(new_bytes).digest(),
                        f"Stage 6 reference content changed for {name}.{suffix}")
            artifact_hashes+=1
        relocated += old_row["hexpath"]!=new_row["hexpath"]
    return {"status":"SEMANTICALLY_IDENTICAL_INPUTS","rows_compared":len(old_rows),
            "allowed_path_field":"hexpath","hexpath_relocations":relocated,
            "image_and_reference_hashes_compared":artifact_hashes,
            "meaningful_manifest_fields":"exact_match"}


def validate_stage8_reuse(report: Path, sim: str, expected_manifest: Path) -> dict:
    marker=f"STAGE8_ENABLED_{sim.upper()} PASS"
    details,text=report_fields(report,sim,marker,output_label="evidence_dir")
    cov.require("cases=23 traces=46 golden_pipeline=23" in text,
                f"saved Stage 8 report does not validate all 23 cases: {report}")
    prep_note,artifact_count=verify_stage8_preparation(expected_manifest)
    expected_rows=stage7.read_prepared_manifest(expected_manifest,stage8=True)
    selection_ref=re.search(r"\bselection_manifest=(.*?)\s+producer_snapshot=",text,re.S)
    cov.require(selection_ref is not None,f"saved Stage 8 report lacks selection manifest: {report}")
    selection_path=cov.resolve_workspace_path(selection_ref.group(1),report.parent).resolve()
    selection=stage7.read_prepared_manifest(selection_path,stage8=True)
    cov.require(selection==expected_rows,"saved Stage 8 selection differs from the complete prepared producer rows")
    out=ROOT/details["outdir"]
    names={row["name"] for row in expected_rows}
    for suffix in (".pipe.trace",".golden.trace",".pipe.mcov"):
        cov.require({p.name[:-len(suffix)] for p in out.glob("*"+suffix)}==names,
                    f"saved Stage 8 {suffix} evidence does not match all 23 selected identities")
    details["selection_manifest"]=relative(selection_path)
    details["prepared_manifest"]=relative(expected_manifest)
    details["prepared_manifest_sha256"]=hashlib.sha256(expected_manifest.read_bytes()).hexdigest()
    details["preparation_provenance"]=relative(prep_note)
    details["preparation_artifacts_checked"]=artifact_count
    return details


def prepare(args) -> None:
    manifest=Path(args.stage8_manifest).resolve()
    cov.require(manifest.is_file(),f"missing Stage 8 manifest: {manifest}")
    stage8_prep,artifact_count=verify_stage8_preparation(manifest)
    mrows=cov.read_manifest(manifest,{"name","hexpath","source","seed","suite"})
    cov.require(len(mrows)==23 and len({r["name"] for r in mrows})==23,"Stage 8 manifest must have 23 unique cases")
    simulators={}
    replay_stamp=datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    old_path=ROOT/"reports/stage9_coverage/prepared.json"
    old=json.loads(old_path.read_text(encoding="utf-8")) if old_path.is_file() else {"simulators":{}}
    superseded={sim:{stage:{"report":old.get("simulators",{}).get(sim,{}).get(stage,{}).get("report"),
                                  "report_sha256":old.get("simulators",{}).get(sim,{}).get(stage,{}).get("report_sha256")}
                          for stage in ("stage5","stage6","stage8")} for sim in ("verilator","xsim")}
    for sim in ("verilator","xsim"):
        ca_report=Path(getattr(args,f"{sim}_stage5_ca")).resolve()
        ca=validate_stage5_ca_reuse(ca_report,sim)
        caout=ROOT/ca["outdir"]
        replay_output=ROOT/f"sim_out_stage9_iss_replay_{sim}_{replay_stamp}"
        ca["reconstructed_m_reference"]=iss_replay.replay(sim,caout,replay_output)
        manifests=cov.read_stage5_manifests(caout)
        gap_report=Path(getattr(args,f"{sim}_legacy_report")).resolve()
        gap_marker=f"STAGE9_LEGACY_GAP_{sim.upper()} PASS legacy=209 full_trace_comparisons=418 dynamic_mcov=209"
        gap_out,text=report_fields(gap_report,sim,gap_marker,saved_legacy=True)
        gapdir=ROOT/gap_out["outdir"]
        legacy_names={r["name"] for r in manifests if r["suite"]=="rv32im"}
        gap_names={p.name[:-len(".pipe.trace")] for p in gapdir.glob("*.pipe.trace")}
        cov.require(len(legacy_names)==209 and gap_names==legacy_names,"saved supplemental run must match the 209 legacy identities exactly")
        for name in legacy_names:
            for suffix in (".pipe.trace",".golden.trace",".pipe.log",".pipe.ccov"):
                cov.require((gapdir/f"{name}{suffix}").is_file(),f"supplemental legacy evidence missing: {name}{suffix}")
        ca.update({"legacy_outdir":relative(gapdir),"legacy_report":relative(gap_report),
                   "legacy_pass_marker":gap_marker,"legacy_report_sha256":hashlib.sha256(gap_report.read_bytes()).hexdigest(),
                   "legacy_provenance":gap_out["provenance"],
                   "legacy_provenance_sha256":gap_out["provenance_sha256"],
                   "legacy_source_hashes_checked":gap_out["source_hashes_checked"],
                   "legacy_source_provenance_status":gap_out["source_provenance_status"],
                   "legacy_unresolved_source_hashes":gap_out["unresolved_source_hashes"]})

        s6_report=Path(getattr(args,f"{sim}_stage6")).resolve()
        s6=validate_stage6_reuse(s6_report,sim,manifest.parent/"stage6_compat"/"z_manifest.csv")
        s6dir=ROOT/s6["outdir"]
        s6_manifest=cov.read_csv(s6dir/"selection_manifest.csv")
        s6_traces={p.name[:-len(".pipe.trace")] for p in s6dir.glob("*.pipe.trace")}
        s6_mcov={p.name[:-len(".pipe.mcov")] for p in s6dir.glob("*.pipe.mcov")}
        s6_names={r["name"] for r in s6_manifest}
        cov.require(len(s6_names)==11 and s6_traces==s6_names and s6_mcov==s6_names,
                    "fresh Stage 6 selection, trace, and MCOV identities must match exactly (11)")

        s8_report=Path(getattr(args,f"{sim}_stage8")).resolve()
        s8_marker=f"STAGE8_ENABLED_{sim.upper()} PASS"
        s8=validate_stage8_reuse(s8_report,sim,manifest)
        s8["pass_marker"]=s8_marker
        s8["manifest"]=relative(manifest)
        s8["manifest_sha256"]=hashlib.sha256(manifest.read_bytes()).hexdigest()
        simulators[sim]={"stage5":ca,"stage6":s6,"stage8":s8}
    statuses=[simulators[s][stage]["source_provenance_status"]
              for s in ("verilator","xsim") for stage in ("stage5","stage6","stage8")]
    statuses += [simulators[s]["stage5"]["legacy_source_provenance_status"] for s in ("verilator","xsim")]
    unresolved=[entry for s in ("verilator","xsim") for stage in ("stage5","stage6","stage8")
                for entry in simulators[s][stage]["unresolved_source_hashes"]]
    unresolved += [entry for s in ("verilator","xsim")
                   for entry in simulators[s]["stage5"]["legacy_unresolved_source_hashes"]]
    strict_closure="PASS" if all(status=="PASS" for status in statuses) and not unresolved else "BLOCKED"
    payload={"schema_version":cov.SCHEMA_VERSION,"dictionary_version":cov.DICTIONARY_VERSION,
             "base_commit":"fcc151dccc4e8e98b4b70ba52871c8a0594a4967","collection":"stage9-recovery-73+209",
             "provenance_policy":{"saved_legacy_accepted_for_coverage_reuse":True,
                                  "status":"PASS" if strict_closure=="PASS" else "DOCUMENTED_LIMITATION",
                                  "strict_source_provenance_closure":strict_closure,
                                  "unresolved_source_hashes":unresolved},
             "superseded_historical_reports":superseded,"simulators":simulators}
    out=Path(args.output).resolve(); out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(payload,indent=2)+"\n",encoding="utf-8",newline="\n")
    print(f"STAGE9_RECOVERY_PREPARATION PREPARED strict_provenance_closure={strict_closure} "
          "fresh=73 supplemental_legacy=209 unique_per_simulator=282 "
          f"unresolved_source_hashes={len(unresolved)}")
    print(out)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage8-manifest",required=True)
    for sim in ("verilator","xsim"):
        parser.add_argument(f"--{sim}-stage5-ca",required=True)
        parser.add_argument(f"--{sim}-legacy-report",required=True)
        parser.add_argument(f"--{sim}-stage6",required=True)
        parser.add_argument(f"--{sim}-stage8",required=True)
    parser.add_argument("--output",default=ROOT/"reports/stage9_coverage/recovery_prepared.json")
    prepare(parser.parse_args())


if __name__=="__main__":
    try: main()
    except (ValueError,OSError,KeyError,TypeError) as exc:
        print(f"STAGE9_RECOVERY_PREPARATION INVALID {type(exc).__name__}: {exc}",file=sys.stderr)
        raise SystemExit(1)
