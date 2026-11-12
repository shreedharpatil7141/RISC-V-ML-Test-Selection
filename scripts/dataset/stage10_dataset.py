#!/usr/bin/env python3
"""Build and validate the deterministic Stage 10 dataset from closed Stage 9 exports."""
import argparse, csv, hashlib, json, re, sys
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "reports" / "stage9_coverage"
OUT = Path(os.environ.get("STAGE10_DATASET_OUT", ROOT / "reports" / "stage10_dataset"))
SIMS = ("xsim", "verilator")
SCHEMA = "stage10-dataset-1.0.0"
FORBIDDEN = re.compile(r"coverage|observed|actual|runtime|cycles|outcome|status|hit|retir|fault|evidence|validation|cost", re.I)
PROGRAM_IMAGE_BY_TEST = None

def sha(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda: f.read(1024 * 1024), b""): h.update(b)
    return h.hexdigest()

def sha_lf(path):
    """Hash canonical LF text, independent of Git's Windows checkout conversion."""
    data = path.read_bytes().replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    return hashlib.sha256(data).hexdigest()

def read_csv(path):
    with path.open(newline="", encoding="utf-8-sig") as f: return list(csv.DictReader(f))

def write_csv(path, rows, fields):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore", lineterminator="\n")
        w.writeheader(); w.writerows(rows)

def family(s):
    # Related numbered variants remain grouped; exact scenario is the fallback.
    return re.sub(r"(?:[_-](?:seed)?\d+|[_-]0x[0-9a-f]+)$", "", s, flags=re.I)

def template_family(s):
    m=re.match(r"^(stage\d+_(?:csr|fencei)|rr|ri|imm|branch|upper|load|store|pipe|amo|atomic|m|c)_",s,re.I)
    return m.group(1).lower() if m else family(s)

def image_for(run):
    global PROGRAM_IMAGE_BY_TEST
    if PROGRAM_IMAGE_BY_TEST is None:
        map_path = ROOT / "reports" / "stage15_evidence" / "program_image_map.csv"
        if not map_path.is_file(): raise ValueError("Stage 15 program-image map is required for deterministic dataset validation.")
        rows = read_csv(map_path)
        PROGRAM_IMAGE_BY_TEST = {}
        mapped_payload_hashes = {}
        for row in rows:
            if row["test_id"] in PROGRAM_IMAGE_BY_TEST: raise ValueError(f"Duplicate mapped program image for {row['test_id']}.")
            dest = Path(row["destination"])
            if dest.is_absolute() or ".." in dest.parts: raise ValueError(f"Unsafe mapped program-image destination: {dest}")
            path = ROOT / dest
            if not path.is_file(): raise ValueError(f"Missing mapped program image: {dest}")
            actual = sha(path)
            if actual != row["sha256"]: raise ValueError(f"Mapped program-image hash mismatch: {dest}")
            payload = image_bytes(path)
            mapped_payload_hashes[row["test_id"]] = hashlib.sha256(payload).hexdigest() if payload is not None else ""
            PROGRAM_IMAGE_BY_TEST[row["test_id"]] = row
        if len(PROGRAM_IMAGE_BY_TEST) != 282: raise ValueError(f"Expected 282 mapped program images; found {len(PROGRAM_IMAGE_BY_TEST)}.")
        frozen_features = {row["test_id"]: row["image_sha256"] for row in read_csv(OUT / "features.csv")}
        if set(frozen_features) != set(mapped_payload_hashes) or any(frozen_features[k] != mapped_payload_hashes[k] for k in frozen_features):
            raise ValueError("Program-image map/test IDs do not reproduce frozen Stage 10 image hashes.")
    row = PROGRAM_IMAGE_BY_TEST.get(run["test_id"])
    if row is None: raise ValueError(f"No mapped program image for {run['test_id']}.")
    return ROOT / row["destination"]

def image_bytes(path):
    if path is None: return None
    raw = path.read_bytes()
    try:
        tokens = []
        for line in raw.decode("ascii").splitlines():
            line = line.split("#", 1)[0].split("//", 1)[0].strip()
            if line: tokens.append(line)
        return bytes.fromhex("".join(tokens)) if tokens else raw
    except (UnicodeDecodeError, ValueError): return raw

def seed_numeric(seed):
    if not seed: return ""
    try: return int(seed, 10)
    except ValueError:
        try: return int(seed, 16)
        except ValueError: return ""

def check_inputs():
    sources = {}
    for sim in SIMS:
        runp, covp = BASE / sim / "runs.csv", BASE / sim / "coverage.csv"
        report = BASE / sim / "report.txt"
        for p in (runp, covp, report):
            if not p.is_file(): raise ValueError(f"missing Stage 9 input: {p.relative_to(ROOT)}")
        rr, cc = read_csv(runp), read_csv(covp)
        if len(rr) != 282 or len(cc) != 282: raise ValueError(f"{sim}: expected 282 closed observations; got runs={len(rr)} coverage={len(cc)}")
        report_text=report.read_text(encoding="utf-8")
        if "observations=282" not in report_text or "coverage_closure=CLOSED" not in report_text or "strict_provenance_closure=PASS" not in report_text:
            raise ValueError(f"{sim}: Stage 9 report does not prove closure")
        if len({r["test_id"] for r in rr}) != 282 or len({r["test_id"] for r in cc}) != 282: raise ValueError(f"{sim}: duplicate IDs")
        if set(r["test_id"] for r in rr) != set(r["test_id"] for r in cc): raise ValueError(f"{sim}: run/coverage identity mismatch")
        for r in rr:
            if r["simulator"] != sim or r["status"] != "PASS" or r["validation_status"] != "PASS" or r["source_provenance_status"] != "PASS" or r["reference_evidence_status"] not in ("PRODUCER_REFERENCE", "RECONSTRUCTED_REFERENCE_TRACE_MATCHED"):
                raise ValueError(f"{sim}/{r['test_id']}: failed status/provenance/identity validation")
            for field in ("evidence_sha256", "validation_report_sha256", "validated_source_provenance_sha256"):
                if not re.fullmatch(r"[0-9a-f]{64}", r[field]): raise ValueError(f"{sim}/{r['test_id']}: invalid {field}")
        run_index={r["test_id"]:r for r in rr}
        for row in cc:
            run=run_index[row["test_id"]]
            for field in ("simulator","configuration","scenario","seed","dictionary_version","schema_version","validation_status","evidence_sha256"):
                if row.get(field) != run.get(field): raise ValueError(f"{sim}/{row['test_id']}: coverage/run {field} mismatch")
            for k,v in row.items():
                if k.startswith("bin_") and v not in ("", "0", "1"): raise ValueError(f"{sim}/{row['test_id']}: invalid label {k}={v}")
        sources[f"{sim}/runs.csv"] = sha(runp); sources[f"{sim}/coverage.csv"] = sha(covp); sources[f"{sim}/report.txt"] = sha(report)
    if set(r["test_id"] for r in read_csv(BASE/"xsim"/"runs.csv")) != set(r["test_id"] for r in read_csv(BASE/"verilator"/"runs.csv")):
        raise ValueError("simulator logical test identities differ")
    allruns=[r for sim in SIMS for r in read_csv(BASE/sim/"runs.csv")]
    versions={(r["schema_version"],r["dictionary_version"]) for r in allruns}
    dictversions={r["dictionary_version"] for r in read_csv(BASE/"xsim"/"coverage.csv")}
    if len(versions)!=1 or len(dictversions)!=1 or next(iter(versions))[1] not in dictversions:
        raise ValueError("Stage 9 schema/dictionary version mismatch")
    d = ROOT / "documentation" / "verification" / "stage9_bin_dictionary.csv"
    if not d.is_file(): raise ValueError("Stage 9 bin dictionary missing")
    dictionary=read_csv(d)
    if not dictionary or len({r.get("bin_id","") for r in dictionary})!=len(dictionary): raise ValueError("invalid/duplicate Stage 9 dictionary identities")
    if {r.get("dictionary_version","") for r in dictionary}!={r["dictionary_version"] for r in read_csv(BASE/"xsim"/"runs.csv")}:
        raise ValueError("Stage 9 dictionary version mismatch")
    sources["documentation/verification/stage9_bin_dictionary.csv"] = sha(d)
    for r in read_csv(BASE/"verilator"/"runs.csv"):
        ip=image_for(r)
        if ip is not None:
            mapping=PROGRAM_IMAGE_BY_TEST[r["test_id"]]
            sources[mapping["manifest_path"]]=sha(ip)
    return sources, read_csv(d)

def build():
    sources, dictionary = check_inputs()
    bysim = {s: {r["test_id"]: r for r in read_csv(BASE/s/"runs.csv")} for s in SIMS}
    cov = {s: {r["test_id"]: r for r in read_csv(BASE/s/"coverage.csv")} for s in SIMS}
    ids = sorted(bysim["xsim"])
    bins = sorted(k for k in cov["xsim"][ids[0]] if k.startswith("bin_"))
    dictids = {"bin_"+r["bin_id"] for r in dictionary}
    dictbycol = {"bin_"+r["bin_id"]: r for r in dictionary}
    if set(bins) != dictids: raise ValueError(f"dictionary mismatch: table={len(bins)} dictionary={len(dictids)}")
    meta, features, labels, costs, provenance = [], [], [], [], []
    images={tid:image_bytes(image_for(bysim["verilator"][tid])) for tid in ids}
    image_hash={tid:(hashlib.sha256(x).hexdigest() if x is not None else "") for tid,x in images.items()}
    for tid in ids:
        a, b = bysim["xsim"][tid], bysim["verilator"][tid]
        if (a["configuration"], a["scenario"], a["seed"], a["suite"], a["schema_version"], a["dictionary_version"]) != (b["configuration"], b["scenario"], b["seed"], b["suite"], b["schema_version"], b["dictionary_version"]): raise ValueError(f"cross-simulator identity mismatch: {tid}")
        suite = a["suite"]
        test_name=tid.split(":",1)[-1]
        seed_family=re.sub(r"_[0-9a-f]{8}$","",test_name,flags=re.I) if test_name.startswith("seed_") else (family(a["scenario"]) if a["seed"] else "")
        meta.append(dict(test_id=tid, configuration=a["configuration"], scenario=a["scenario"], seed=a["seed"], seed_numeric=seed_numeric(a["seed"]), family=family(a["scenario"]), template_family=template_family(a["scenario"]), seed_family=seed_family, suite=suite, logical_test_id=tid))
        # Only design-time identity fields enter the feature table. No observed run fields.
        program=images[tid]
        features.append(dict(test_id=tid, configuration=a["configuration"], scenario=a["scenario"], seed=a["seed"], seed_numeric=seed_numeric(a["seed"]), family=family(a["scenario"]), template_family=template_family(a["scenario"]), seed_family=seed_family, suite=suite, image_sha256=image_hash[tid], program_bytes=(len(program) if program is not None else ""), unique_byte_values=(len(set(program)) if program is not None else "")))
        for sim in SIMS:
            cr = cov[sim][tid]
            for col in bins:
                v = cr[col]
                # Stage 9 blank means unavailable. Dictionary config scope distinguishes inapplicable.
                drow = dictbycol.get(col)
                applicable_cfg = set((drow or {}).get("applicable_configurations", "").split("|"))
                unsupported = (drow or {}).get("reachability", "").lower()=="unsupported"
                applicable = int(not unsupported and (not applicable_cfg or a["configuration"] in applicable_cfg))
                availability = int(v in ("0", "1"))
                state = "unsupported" if unsupported else ("inapplicable" if not applicable else ("unavailable" if not availability else ("observed_zero" if v=="0" else "observed_hit")))
                if state in ("unsupported", "inapplicable"): availability=0; v=""
                labels.append(dict(observation_id=f"{tid}:{sim}", test_id=tid, simulator=sim, bin_id=col[4:], value=v, applicable=applicable, available=availability, state=state))
            r = bysim[sim][tid]
            costs.append(dict(observation_id=f"{tid}:{sim}", test_id=tid, simulator=sim, observed_cycles=r["observed_cycles"], cycles_unit="cycle", cycles_source="Stage9 validated DUT observation", runtime_seconds=r["runtime_seconds"], runtime_unit="second", runtime_source="Stage9 measured only when present", status=r["status"]))
            provenance.append(dict(observation_id=f"{tid}:{sim}", test_id=tid, simulator=sim, schema_version=r["schema_version"], dictionary_version=r["dictionary_version"], evidence_sha256=r["evidence_sha256"], validation_report=r["validation_report"], validation_report_sha256=r["validation_report_sha256"], validated_source_provenance_sha256=r["validated_source_provenance_sha256"], evidence_sources=r["evidence_sources"], source_provenance_status=r["source_provenance_status"], reference_evidence_status=r["reference_evidence_status"]))
    # Group deterministic splits at logical-test level by related scenario family and counterpart.
    parent={t:t for t in ids}
    def root(t):
        while parent[t]!=t: parent[t]=parent[parent[t]]; t=parent[t]
        return t
    def union(x,y): parent[root(x)]=root(y)
    related={}
    for m in meta: related.setdefault(m["family"], []).append(m["test_id"])
    for members in related.values():
        for t in members[1:]: union(members[0],t)
    templates={}
    for m in meta: templates.setdefault(m["template_family"],[]).append(m["test_id"])
    for members in templates.values():
        for t in members[1:]: union(members[0],t)
    related_seed={}
    for m in meta:
        if m["seed_family"]: related_seed.setdefault(m["seed_family"],[]).append(m["test_id"])
    for members in related_seed.values():
        for t in members[1:]: union(members[0],t)
    # Exact duplicate and near-identical equal-length images are held in one split.
    near_pairs=[]
    valid=[t for t in ids if images[t] is not None]
    packed={t:int.from_bytes(images[t],"big") for t in valid}
    for i,t in enumerate(valid):
        x=images[t]
        for u in valid[i+1:]:
            y=images[u]
            if len(x)!=len(y) or not x: continue
            # A byte mismatch contributes at most eight differing bits; this native
            # big-integer filter avoids Python-level per-byte scans for all pairs.
            if (packed[t]^packed[u]).bit_count() > len(x)*0.16: continue
            delta=sum(a!=b for a,b in zip(x,y))
            if delta==0 or delta/len(x)<=0.02:
                union(t,u)
                if delta: near_pairs.append((t,u,delta/len(x)))
    groups = {}
    for t in ids: groups.setdefault(root(t), []).append(t)
    assign = {}
    ordered = sorted(groups, key=lambda g: hashlib.sha256((SCHEMA+g).encode()).hexdigest())
    targets=(.70,.15,.15); counts={"train":0,"validation":0,"test":0}; names=list(counts)
    for g in ordered:
        n=len(groups[g]); ix=min(range(3), key=lambda i: (counts[names[i]]/max(1,len(ids))-targets[i], i))
        for tid in groups[g]: assign[tid]=names[ix]
        counts[names[ix]] += n
    splits=[dict(test_id=t, group_id=root(t), split=assign[t]) for t in ids]
    # Static image duplicate audit is reported when a source image can be resolved unambiguously.
    # Stage 9 exports do not carry a canonical image path, so scenario/config identities are conservatively hashed.
    nearmap={t:[] for t in ids}
    for x,y,ratio in near_pairs: nearmap[x].append(y); nearmap[y].append(x)
    dup=[]
    for t in ids:
        relatives=set(nearmap[t])
        if image_hash[t]: relatives.update(u for u in ids if u!=t and image_hash[u]==image_hash[t])
        dup.append(dict(test_id=t, image_sha256=image_hash[t], near_duplicate_group=(root(t) if relatives else ""), near_duplicate_ids="|".join(sorted(relatives)), detection=("exact_or_near_image_checked" if images[t] is not None else "image_path_not_resolved")))
    OUT.mkdir(parents=True, exist_ok=True)
    tables={"test_metadata.csv":(meta,list(meta[0])),"features.csv":(features,list(features[0])),"coverage_labels.csv":(labels,list(labels[0])),"execution_costs.csv":(costs,list(costs[0])),"provenance.csv":(provenance,list(provenance[0])),"split_assignments.csv":(splits,list(splits[0])),"duplicate_audit.csv":(dup,list(dup[0]))}
    for fn,(rows,fields) in tables.items(): write_csv(OUT/fn,rows,fields)
    write_csv(OUT/"bin_dictionary.csv",dictionary,list(dictionary[0]))
    write_csv(OUT/"feature_dictionary.csv",[dict(feature=f,role="pre_execution_static",description="Pre-execution identity or static program-image feature; no simulator observation") for f in features[0] if f!="test_id"],["feature","role","description"])
    schema=[]
    for fn,(rows,fields) in tables.items():
        for field in fields:
            sample=next((r.get(field) for r in rows if r.get(field) not in (None,"")),"")
            typ="numeric" if field in ("seed_numeric","program_bytes","unique_byte_values","value","applicable","available","observed_cycles","runtime_seconds") else "text"
            schema.append(dict(table=fn,field=field,type=typ,missing_values="allowed" if field in ("seed","seed_numeric","seed_family","runtime_seconds","value","program_bytes","unique_byte_values","image_sha256") else "not_allowed",row_count=len(rows)))
    write_csv(OUT/"schema_dictionary.csv",schema,["table","field","type","missing_values","row_count"])
    csv_outputs={p.name:{"sha256":sha(p),"rows":len(read_csv(p))} for p in sorted(OUT.glob("*.csv"))}
    manifest={"schema_version":SCHEMA,"base_commit":"73fb3948627c79a0b26f0179e106adf2ec6e624d","input_hashes":sources,"source_closure_status":{"xsim":"CLOSED","verilator":"CLOSED","provenance":"PASS"},"simulators":list(SIMS),"simulator_observations_per_simulator":282,"simulator_observations_total":564,"logical_tests":282,"cross_simulator_rows_are_repeated_observations":True,"split_counts":counts,"split_method":"scenario-family, template-family, seed-family, exact-image, and <=2% equal-length byte-difference image groups assigned by deterministic SHA256; simulator counterparts share logical test ID","preprocessing":"none fitted; downstream preprocessing must fit training rows only","image_paths_resolved":sum(x is not None for x in images.values()),"near_duplicate_pairs_detected":len(near_pairs),"csv_outputs":csv_outputs}
    (OUT/"manifest.json").write_text(json.dumps(manifest,indent=2,sort_keys=True)+"\n",encoding="utf-8")

def validate():
    sources,_=check_inputs(); m=json.loads((OUT/"manifest.json").read_text(encoding="utf-8"))
    if sources != m["input_hashes"]: raise ValueError("changed input hashes; rebuild required")
    prior={fn:sha_lf(OUT/fn) for fn in m["csv_outputs"]}
    # Regenerate from the same immutable Stage 9 inputs and compare byte hashes.
    build()
    for fn,old_hash in prior.items():
        if sha_lf(OUT/fn)!=old_hash: raise ValueError(f"deterministic regeneration mismatch: {fn}")
    m=json.loads((OUT/"manifest.json").read_text(encoding="utf-8"))
    for fn,rec in m["csv_outputs"].items():
        p=OUT/fn
        if sha_lf(p)!=rec["sha256"]: raise ValueError(f"output hash/round-trip check failed: {fn}")
        rows=read_csv(p)
        if len(rows)!=rec["rows"]: raise ValueError(f"row count mismatch: {fn}")
        if any(None in r for r in rows): raise ValueError(f"malformed CSV round trip: {fn}")
    for fn in ("features.csv","test_metadata.csv","execution_costs.csv","provenance.csv"):
        for row in read_csv(OUT/fn):
            for key,value in row.items():
                if value=="" and not (key in ("seed","seed_numeric","seed_family","runtime_seconds","program_bytes","unique_byte_values","image_sha256")):
                    raise ValueError(f"unexpected missing value: {fn}/{key}")
    meta=read_csv(OUT/"test_metadata.csv"); feats=read_csv(OUT/"features.csv"); splits=read_csv(OUT/"split_assignments.csv")
    ids=[r["test_id"] for r in meta]
    if len(ids)!=len(set(ids)) or ids != [r["test_id"] for r in feats] or ids != [r["test_id"] for r in splits]: raise ValueError("logical row alignment/duplicate ID failure")
    if any(FORBIDDEN.search(c) for c in feats[0] if c!="test_id"): raise ValueError("feature leakage detected")
    seen={}
    for r in splits:
        if r["group_id"] in seen and seen[r["group_id"]]!=r["split"]: raise ValueError("split group overlap")
        seen[r["group_id"]]=r["split"]
    lab=read_csv(OUT/"coverage_labels.csv")
    if len(lab)!=282*2*len([k for k in read_csv(BASE/"xsim"/"coverage.csv")[0] if k.startswith("bin_")]): raise ValueError("coverage row alignment failure")
    obsids=[r["observation_id"] for r in read_csv(OUT/"execution_costs.csv")]
    if len(obsids)!=564 or len(set(obsids))!=564 or set(obsids)!={f"{t}:{s}" for t in ids for s in SIMS}: raise ValueError("simulator observation alignment/duplicate ID failure")
    provids=[r["observation_id"] for r in read_csv(OUT/"provenance.csv")]
    if set(provids)!=set(obsids): raise ValueError("provenance row alignment failure")
    for r in lab:
        if r["available"] not in ("0","1") or r["applicable"] not in ("0","1"): raise ValueError("invalid mask")
        if r["state"] in ("observed_zero","observed_hit") and r["value"] not in ("0","1"): raise ValueError("invalid observed label")
        if r["state"] in ("observed_zero","observed_hit") and (r["available"]!="1" or r["applicable"]!="1"): raise ValueError("observed label has invalid masks")
        if (r["state"],r["value"]) not in (("observed_zero","0"),("observed_hit","1")) and r["state"] in ("observed_zero","observed_hit"): raise ValueError("observed label state/value mismatch")
        if r["state"] in ("inapplicable","unsupported") and (r["applicable"]!="0" or r["available"]!="0"): raise ValueError(f"{r['state']} label has invalid masks")
        if r["state"]=="unavailable" and (r["applicable"]!="1" or r["available"]!="0"): raise ValueError("unavailable label has invalid masks")
    split_by={r["test_id"]:r["split"] for r in splits}; dup_rows=read_csv(OUT/"duplicate_audit.csv"); dupe_splits={}
    for r in dup_rows:
        if r["near_duplicate_group"]:
            dupe_splits.setdefault(r["near_duplicate_group"],set()).add(split_by[r["test_id"]])
    if any(len(v)>1 for v in dupe_splits.values()): raise ValueError("duplicate-image split overlap")
    actual_counts={s:sum(1 for r in splits if r["split"]==s) for s in ("train","validation","test")}
    if actual_counts!=m["split_counts"]: raise ValueError("manifest split sizes mismatch")
    for r in read_csv(OUT/"execution_costs.csv"):
        for field in ("observed_cycles","runtime_seconds"):
            if r[field] and (not re.fullmatch(r"\d+(?:\.\d+)?",r[field])): raise ValueError(f"non-MATLAB numeric representation: {field}")
    for r in read_csv(OUT/"test_metadata.csv"):
        if r["seed_numeric"] and not re.fullmatch(r"-?\d+",r["seed_numeric"]): raise ValueError("non-MATLAB numeric seed representation")
    if any(not r["image_sha256"] for r in dup_rows): raise ValueError("unresolved program image for duplicate analysis")
    print(f"STAGE10 VALIDATION PASS logical_tests={len(ids)} observations={len(read_csv(OUT/'execution_costs.csv'))} coverage_rows={len(lab)} split_counts={m['split_counts']}")

if __name__=="__main__":
    p=argparse.ArgumentParser(); p.add_argument("command",choices=("build","validate")); a=p.parse_args()
    try: build() if a.command=="build" else validate()
    except Exception as e: print(f"STAGE10 {a.command.upper()} FAIL: {e}",file=sys.stderr); sys.exit(1)
