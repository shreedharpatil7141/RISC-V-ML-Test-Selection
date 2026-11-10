#!/usr/bin/env python3
"""Preflight released suites and generate seeded Stage 8 ISS-backed scenarios."""
import csv, hashlib, re, subprocess, sys
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
sys.path.insert(0,str(HERE))
import stage8_scenarios

def fail(message): raise SystemExit("STAGE8_PREPARE FAIL: "+message)

def audit_sources():
    filelist=ROOT/"scripts/simulation/stage4_4_rtl.f"
    entries=[line.strip() for line in filelist.read_text(encoding="utf-8").splitlines() if line.strip() and not line.lstrip().startswith("#")]
    if any("\\" in path for path in entries): fail("RTL file list must use forward slashes")
    if len(entries)!=len(set(entries)): fail("duplicate source in Stage 8 RTL file list")
    sources=[ROOT/path for path in entries]
    benches=[ROOT/"verification/environment"/name for name in (
        "tb_rv_core.sv","tb_rv_pipe_stage4.sv","tb_rv_stage7.sv","tb_rv_stage8.sv",
        "tb_rv_stage8_components.sv","tb_rv_decoder_machine.sv")]
    missing=[str(path) for path in sources+benches if not path.is_file()]
    if missing: fail("missing source(s): "+", ".join(missing))
    names={}
    for path in sources+benches:
        text=path.read_text(encoding="utf-8")
        text=re.sub(r"/\*.*?\*/","",text,flags=re.S)
        text=re.sub(r"//[^\n]*","",text)
        for name in re.findall(r"\bmodule\s+(?:automatic\s+)?([A-Za-z_][A-Za-z0-9_$]*)",text):
            names.setdefault(name,[]).append(path.relative_to(ROOT).as_posix())
    duplicates={name:paths for name,paths in names.items() if len(paths)>1}
    if duplicates: fail("module-name collision(s): "+repr(duplicates))

def main():
    if len(sys.argv)!=2: fail(f"usage: {Path(sys.argv[0]).name} <fresh-output-directory>")
    out=Path(sys.argv[1]).resolve()
    if out.exists() and any(out.iterdir()): fail(f"output directory is not fresh: {out}")
    out.mkdir(parents=True,exist_ok=True)
    audit_sources()
    stage7=out/"stage7"
    result=subprocess.run([sys.executable,str(HERE/"prepare_stage7.py"),str(stage7)],cwd=ROOT,
                          text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    (out/"stage7_prepare.log").write_text(result.stdout,encoding="utf-8",newline="\n")
    required="STAGE7_PREPARATION READY stage6_compat=259 stage7_cases=13 images=13 references=13 errors=0"
    if result.returncode or required not in result.stdout: fail("released Stage 7 preparation failed; see stage7_prepare.log")
    try:
        rows,coverage=stage8_scenarios.generate(stage7)
        (stage7/"stage8_component.hex").write_text("00000013\n",encoding="ascii",newline="\n")
        manifest=stage7/"m_manifest.csv"
        base=list(csv.DictReader(manifest.open(newline="")))
        names=[row["name"] for row in base+rows]
        if len(base)!=13 or len(names)!=len(set(names)): fail("base/generated case naming collision")
        fields=["name","hexpath","irq_pc","irq_levels","irq_wait_div","traps","retired","suite","seed","source"]
        with manifest.open("w",newline="") as f:
            writer=csv.DictWriter(f,fieldnames=fields,lineterminator="\n")
            writer.writeheader()
            for row in base: writer.writerow({**row,"suite":"stage7_enabled","seed":"","source":""})
            writer.writerows(rows)
        selftest=subprocess.run([sys.executable,str(HERE/"stage8_software_selftest.py"),str(stage7)],cwd=ROOT,
                                text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
        (out/"software_selftest.log").write_text(selftest.stdout,encoding="utf-8",newline="\n")
        if selftest.returncode or "STAGE8_SOFTWARE_SELFTEST PASS" not in selftest.stdout:
            fail("Stage 8 deterministic software/scoreboard selftest failed; see software_selftest.log")
        # The base preparation provenance includes a digest of the manifest;
        # refresh only that artifact entry after the controlled extension.
        prep_text=stage7/"stage7_preparation.txt"
        ptext=prep_text.read_text(encoding="ascii")
        digest=hashlib.sha256(manifest.read_bytes()).hexdigest()
        ptext=re.sub(r"^artifact_sha256 .*m_manifest\.csv=[0-9a-f]{64}$",
                     f"artifact_sha256 {manifest.relative_to(ROOT).as_posix()}={digest}",ptext,flags=re.M)
        prep_text.write_text(ptext,encoding="ascii",newline="\n")
        entries=[]
        sources=[HERE/"prepare_stage8.py",HERE/"run_stage8_enabled.py",HERE/"stage8_scenarios.py",HERE/"stage8_software_selftest.py",
                 HERE/"run_stage7_enabled.py",ROOT/"verification/stage8/rv_stage8_components.sv",
                 ROOT/"verification/environment/tb_rv_stage8.sv",ROOT/"verification/environment/tb_rv_stage8_components.sv",
                 ROOT/"verification/environment/tb_rv_core.sv",ROOT/"verification/environment/tb_rv_pipe_stage4.sv",
                 ROOT/"scripts/simulation/stage4_4_rtl.f"]
        entries += [f"sha256 {p.relative_to(ROOT).as_posix()}={hashlib.sha256(p.read_bytes()).hexdigest()}" for p in sources]
        artifacts=[manifest]
        artifacts += sorted((stage7/"stage8_hex").glob("*.hex"))
        artifacts += sorted((stage7/"stage8_src").glob("*.s"))
        artifacts += [stage7/"stage8_component.hex"]
        artifacts += [stage7/"m_iss"/f"{r['name']}.{suffix}" for r in rows for suffix in ("trace","trap.tsv","z.tsv")]
        for p in artifacts:
            rel="@PREPARED@/"+p.relative_to(stage7).as_posix()
            entries.append(f"artifact_sha256 {rel}={hashlib.sha256(p.read_bytes()).hexdigest()}")
        counts=" ".join(f"{key}={coverage[key]}" for key in stage8_scenarios.PROFILES)
        summary=f"STAGE8_PREPARATION READY base_cases=13 generated_cases={len(rows)} total_cases={13+len(rows)} errors=0\nmaster_seed={stage8_scenarios.MASTER_SEED:08x}\nseed_offsets={','.join(map(str,stage8_scenarios.SEED_OFFSETS))}\nscenario_counts={counts}\nsupported={'; '.join(f'{k}:{v}' for k,v in stage8_scenarios.SUPPORTED_COMBINATIONS.items())}\n"+"\n".join(entries)+"\n"
        (stage7/"stage8_preparation.txt").write_text(summary,encoding="ascii",newline="\n")
        # Include the completed Stage 8 note in the Stage 7 inventory file, whose
        # digest was intentionally updated above; this is temporary prep output.
        print(summary,end="")
        print(f"STAGE8_PREPARATION PASS base=13 generated={len(rows)} total={13+len(rows)} output={stage7}")
    except Exception as exc:
        fail(f"{type(exc).__name__}: {exc}")

if __name__=="__main__": main()
