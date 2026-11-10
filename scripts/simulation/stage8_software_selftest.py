#!/usr/bin/env python3
"""Determinism, scenario inventory, and independent scoreboard fault checks."""
import csv, re, sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
sys.path.insert(0,str(HERE))
import stage8_scenarios
from run_stage7_enabled import compare

def require(ok,msg):
    if not ok: raise AssertionError(msg)

def main():
    require(set(stage8_scenarios.PROFILES)==set(stage8_scenarios.SUPPORTED_COMBINATIONS),"scenario support matrix mismatch")
    seeds=[]
    for profile in stage8_scenarios.PROFILES:
        for offset in stage8_scenarios.SEED_OFFSETS:
            seed=(stage8_scenarios.MASTER_SEED+offset*0x100+stage8_scenarios.PROFILES.index(profile)*0x10000)&0xffffffff
            first=stage8_scenarios.program(profile,seed)
            second=stage8_scenarios.program(profile,seed)
            require(first==second,f"nondeterministic program profile={profile} seed={seed:08x}")
            seeds.append(seed)
    require(len(seeds)==len(set(seeds)) and len(seeds)==10,"seed list collision/count")
    if len(sys.argv)>1:
        prep=Path(sys.argv[1])
        manifest=list(csv.DictReader((prep/"m_manifest.csv").open(newline="")))
        generated=[r for r in manifest if r.get("suite")=="stage8_seeded"]
        require(len(generated)==10 and len({r["seed"] for r in generated})==10,"generated seed manifest mismatch")
        ref=(prep/"m_iss"/(generated[0]["name"]+".trace")).read_text(encoding="ascii")
        m=re.search(r"(?m)^I ([0-9a-f]{8}) ",ref)
        require(m is not None,"seeded ISS reference has no retirement rows")
        bad_pc=f"{(int(m.group(1),16)^2):08x}"
        mutated=ref[:m.start(1)]+bad_pc+ref[m.end(1):]
        try: compare(mutated,ref,"Stage 8 injected retirement PC fault")
        except RuntimeError: pass
        else: raise AssertionError("ISS scoreboard accepted a changed retirement PC")
    print("STAGE8_SOFTWARE_SELFTEST PASS profiles=5 seeds=10 deterministic=1 scoreboard_negative=1")

if __name__=="__main__": main()
