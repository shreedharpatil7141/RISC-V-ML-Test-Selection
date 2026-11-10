#!/usr/bin/env python3
"""Consolidate validated Stage 5-8 DUT coverage evidence without rerunning simulators."""
from __future__ import annotations

import argparse
import collections
import csv
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
DICT_PATH = ROOT / "documentation/verification/stage9_bin_dictionary.csv"
sys.path.insert(0,str(HERE))
import stage2_lib as legacy_coverage
import stage5_coverage as legacy_m_coverage
import stage4_c_coverage as legacy_c_coverage
SCHEMA_VERSION = "stage9-observation-1.0.0"
DICTIONARY_VERSION = "stage9-bin-1.1.0"
SOURCE_PROVENANCE_STATUSES = frozenset(("PASS", "DOCUMENTED_LIMITATION_RUNNER_SNAPSHOT_UNAVAILABLE"))
CONFIGS = {
    "rv32im": "rv32im",
    "rv32imc": "rv32imc",
    "rv32ima": "rv32ima",
    "rv32imac": "rv32imac",
    "stage6": "rv32imac+zicsr+zifencei",
    "stage8": "rv32imac+zicsr+zifencei+priv-m",
}
ISSUES = {
    0x33: ("add", "sll", "slt", "sltu", "xor", "srl", "or", "and"),
    0x13: ("addi", "slli", "slti", "sltiu", "xori", "srli", "ori", "andi"),
    0x03: ("lb", "lh", "lw", None, "lbu", "lhu", None, None),
    0x23: ("sb", "sh", "sw", None, None, None, None, None),
    0x63: ("beq", "bne", None, None, "blt", "bge", "bltu", "bgeu"),
}
M_OPS = ("mul", "mulh", "mulhsu", "mulhu", "div", "divu", "rem", "remu")
A_OPS = {0b00010: "lr.w", 0b00011: "sc.w", 0b00001: "amoswap.w", 0b00000: "amoadd.w",
         0b00100: "amoxor.w", 0b01100: "amoand.w", 0b01000: "amoor.w", 0b10000: "amomin.w",
         0b10100: "amomax.w", 0b11000: "amominu.w", 0b11100: "amomaxu.w"}
APP_STAGE5 = "|".join((CONFIGS["rv32im"],CONFIGS["rv32imc"],CONFIGS["rv32ima"],CONFIGS["rv32imac"]))
APP_C = "|".join((CONFIGS["rv32imc"],CONFIGS["rv32imac"],CONFIGS["stage6"],CONFIGS["stage8"]))
APP_A = "|".join((CONFIGS["rv32ima"],CONFIGS["rv32imac"],CONFIGS["stage6"],CONFIGS["stage8"]))
APP_ALL = "|".join((CONFIGS["rv32im"],CONFIGS["rv32imc"],CONFIGS["rv32ima"],CONFIGS["rv32imac"],CONFIGS["stage6"],CONFIGS["stage8"]))
APP_Z = "|".join((CONFIGS["stage6"],CONFIGS["stage8"]))
APP_PRIV = CONFIGS["stage8"]


def dictionary_rows() -> list[dict[str,str]]:
    rows=[]
    def add(bin_id: str, cls: str, definition: str, configs: str = APP_ALL, evidence: str = "DUT retirement trace matched to independent golden trace",
            reach: str = "reachable", reason: str = "Included ISA/configuration scope; zero aggregate hit remains an explicit reachable gap.") -> None:
        # Historical Stage 3.5/4 identifiers can overlap; preserve the first,
        # more specific stable definition rather than emitting duplicate IDs.
        if any(r["bin_id"]==bin_id for r in rows): return
        rows.append({"bin_id":bin_id,"dictionary_version":DICTIONARY_VERSION,"coverage_class":cls,"definition":definition,
                     "applicable_configurations":configs,"evidence_source":evidence,"reachability":reach,"reachability_reason":reason})
    ops="LUI AUIPC JAL JALR BEQ BNE BLT BGE BLTU BGEU LB LH LW LBU LHU SB SH SW ADDI SLTI SLTIU XORI ORI ANDI SLLI SRLI SRAI ADD SUB SLL SLT SLTU XOR SRL SRA OR AND FENCE FENCEI ECALL EBREAK CSRRW CSRRS CSRRC CSRRWI CSRRSI CSRRCI MRET WFI MUL MULH MULHSU MULHU DIV DIVU REM REMU LR.W SC.W AMOSWAP.W AMOADD.W AMOXOR.W AMOAND.W AMOOR.W AMOMIN.W AMOMAX.W AMOMINU.W AMOMAXU.W".split()
    for op in ops:
        configs=APP_Z if op.startswith("CSR") or op=="FENCEI" else APP_PRIV if op in ("MRET","WFI") else APP_A if op in ("LR.W","SC.W") or op.startswith("AMO") else APP_ALL
        cls="architectural_privileged" if op in ("MRET","WFI","ECALL","EBREAK") else "architectural"
        if op in ("ECALL","EBREAK"):
            cause=11 if op=="ECALL" else 3
            add(f"ARCH.OP.{op}",cls,f"Synchronous M-mode {op} trap observed with mcause={cause} from validated trap records; never inferred from retirement.",
                configs,evidence="DUT fault/trap event checked against passing run and independent golden trap record")
        elif op=="WFI":
            add("ARCH.OP.WFI",cls,"WFI execution behavior; excluded because Stage 7 explicitly leaves WFI out of scope.",
                configs,"Stage 7 decoder trap/illegal-instruction evidence; no WFI implementation claim",
                "unsupported","Released Stage 7 scope marks WFI out of scope in tb_rv_decoder_machine.sv; no ISA feature is added to satisfy coverage.")
        else:
            add(f"ARCH.OP.{op}",cls,f"One retired {op} instruction, counted from a DUT trace equal to the independent golden trace.",configs)
    for ext in ("I","M","C","A","Z","PRIV"):
        configs=APP_Z if ext=="Z" else APP_PRIV if ext=="PRIV" else APP_C if ext=="C" else APP_A if ext=="A" else APP_ALL
        add(f"ARCH.EXT.{ext}","architectural",f"At least one retired instruction from extension/configuration class {ext}.",configs)
    for width in ("COMPRESSED","WORD32"):
        add(f"ARCH.FORMAT.{width}","architectural",f"Retired instruction with {'16-bit' if width=='COMPRESSED' else '32-bit'} encoding.",APP_C if width=="COMPRESSED" else APP_ALL)
    for name,desc in (("CSR_ACCESS","Observed CSR access"),("CSR_WRITE","Observed CSR write commit"),("FENCEI","Observed FENCE.I operation")):
        add(f"ARCH.Z.{name}","architectural",desc,APP_Z,"DUT Z sidecar (Z event) checked by passing Stage 6/8 runner")
    add("ARCH.Z.CSR_ILLEGAL_FAULT","architectural_fault","A CSR instruction faults access/permission checks.",APP_Z,"DUT Z CSR_FAULT event and matched machine trap evidence")
    add("ARCH.A.ATOMIC","architectural_atomic","At least one retired RV32A atomic operation.",APP_A,evidence="DUT and golden atomic sidecars agree")
    for op in sorted(set(A_OPS.values())):
        add("ARCH.A."+op.upper().replace(".","_"),"architectural_atomic",f"At least one retired atomic operation {op}.",APP_A,evidence="DUT and golden atomic sidecars agree")
    for event,definition in (("ATTEMPTED","Dynamic IF/ID entries counted from ordered DUT lifecycle records; repeated held-cycle samples are deduplicated"),("RETIRED","Retirement occurrences in the validated DUT architectural trace, including repeated PCs"),
                            ("FAULTING","Precise fault records emitted by the DUT"),("SQUASHED","DUT squash event records, counted per event including repeated static identities")):
        add("PIPE."+event,"microarchitectural",definition,APP_ALL,"DUT pipeline sidecar plus retirement trace")
    for event,definition in (("ATTEMPTED","Unique pipeline attempts from the Stage 4 C dictionary"),("RETIRED","Retired instructions from the Stage 4 C dictionary"),
                            ("FAULTING","Fault sources from the Stage 4 C dictionary"),("SQUASH.REDIRECT","Redirect squashes from the Stage 4 C dictionary"),
                            ("SQUASH.FAULT","Precise-fault squashes from the Stage 4 C dictionary")):
        add("P."+event,"microarchitectural",definition,APP_ALL,"DUT C sidecar; Stage 4 stable ID preserved")
    for family in legacy_c_coverage.FAMILIES:
        add(f"A.C.FAMILY.{family}","architectural_compressed",f"Observed RV32C {family} halfword family using the Stage 4 raw encoding classifier.",APP_C,"DUT raw retirement/fault event checked against golden trace")
    for name,definition in (("HINT.RETIRED","Compressed HINT retired"),("NOP.RETIRED","Canonical C.NOP retired")):
        add(f"A.C.{name}","architectural_compressed",definition,APP_C,"DUT raw retirement record checked against golden trace")
    for name,definition in (("HALFWORD","DIV/REM issue at a halfword-aligned PC"),("METADATA_HOLD_CYCLES","Observed divider hold cycles")):
        add(f"P.DIV.{name}","microarchitectural",definition,APP_ALL,"DUT M event/pipeline sidecar; Stage 4 stable ID preserved")
    for event,definition in (("REDIRECT","Instruction squashed by a redirect"),("FAULT","Instruction squashed by an older precise fault"),
                            ("DIV_HOLD","Pipeline divider hold event")):
        add("PIPE.SQUASH."+event if event in ("REDIRECT","FAULT") else "PIPE.HAZARD.DIV_HOLD","microarchitectural",definition,APP_ALL,"DUT pipeline event sidecar")
    for op in M_OPS:
        for event in ("ISSUE","COMPLETE","RETIRE"):
            add(f"PIPE.M.{event}.{op.upper()}","microarchitectural",f"{op.upper()} observed at {event.lower()}.",APP_ALL,"DUT M sidecar event")
    for event,definition in (("ISSUE","DIV/REM operation accepted"),("COMPLETE","DIV/REM operation completed"),("RETIRE","DIV/REM result retired"),
                            ("ABORT","Iterative divider operation aborted by interrupt"),("RESTART","Aborted instruction later retired after trap return"),
                            ("CONSECUTIVE","DIV/REM starts in adjacent operations")):
        add("PIPE.DIV."+event,"microarchitectural",definition,APP_ALL,"DUT divider/pipeline sidecar")
    for event,definition in (("RS1","M-extension load-use on rs1"),("RS2","M-extension load-use on rs2")):
        add(f"PIPE.M.LOAD_USE.{event}","microarchitectural",definition,APP_ALL,"DUT M event sidecar")
    add("PIPE.M.FAULT.DIV_START_SUPPRESSED","microarchitectural","Older fault suppresses younger DIV/REM start.",APP_ALL,"DUT M event sidecar")
    add("PIPE.M.SQUASH.REDIRECT","microarchitectural","M-extension instruction squashed by redirect.",APP_ALL,"DUT M event sidecar")
    add("PIPE.M.SQUASH.FAULT","microarchitectural","M-extension instruction squashed by older fault.",APP_ALL,"DUT M event sidecar")
    add("PIPE.M.DIV.WRONG_PATH_SUPPRESSED","microarchitectural","Wrong-path DIV/REM is squashed before issue.",APP_ALL,"DUT M event sidecar")
    for src in ("RS1","RS2"):
        for fwd in ("EXMEM","MEMWB"):
            add(f"PIPE.M.FWD.{src}.{fwd}","microarchitectural",f"M-extension {src} operand forwarded from {fwd}.",APP_ALL,"DUT M issue sidecar")
    for bin_id in legacy_m_coverage._bins():
        if bin_id.startswith("B.ABORT."):
            add(bin_id,"historical_block_protocol",f"Stable Stage 3.5 unit-level bin {bin_id}; not a per-test system observation.","","Legacy divider unit markers","not_targeted","The saved Stage 5-8 per-test runs do not carry independent per-offset wrapper markers; retained historical reports remain authoritative.")
        else:
            cls="architectural" if bin_id.startswith("A.") else "microarchitectural"
            add(bin_id,cls,f"Stable Stage 3.5 M-extension bin {bin_id}; exact prior definition remains in stage3_5_m_coverage_dictionary.md.",
                APP_STAGE5,"Stage 5 ISS M sidecar plus DUT M issue/event sidecar")
    for i,name in enumerate(legacy_coverage.EVENTS):
        add(f"P.PIPE_EVENT.{i:02d}","microarchitectural",f"Legacy RTL event counter {i:02d}: {name}.",APP_ALL,"DUT COV record from passing simulator log; Stage 2 event ID preserved")
    for event,definition in (("MACHINE_MODE","Machine-mode trap or interrupt event"),("MRET","Machine trap return retired")):
        add("PRIV."+event,"architectural_privileged",definition,APP_PRIV,"DUT machine sidecar checked against ISS trace")
    for cause in (1,2,3,4,5,6,7,11):
        add(f"PRIV.TRAP.CAUSE.{cause}","architectural_privileged",f"Synchronous machine trap with mcause={cause}.",APP_PRIV,"DUT trap sidecar compared with golden trap sidecar")
    for cause in (3,7,11):
        add(f"PRIV.IRQ.CAUSE.{cause}","architectural_privileged",f"Machine interrupt with mcause code={cause}.",APP_PRIV,"DUT IRQ event and trap sidecar compared with golden")
    add("CROSS.MACHINE.FAULT_IRQ_OVERLAP","cross","Fault and asynchronous IRQ overlap in one selected scenario.",APP_PRIV,"No current focused sidecar defines this cross","not_targeted","Stage 8 bounded fault/restart and IRQ/DIV scenarios separately; overlap was excluded.")
    add("EXCLUDED.RVV","scope_exclusion","RISC-V Vector extension is outside the implemented design.","","none","unsupported","No RVV RTL or tests are in project scope.")
    add("EXCLUDED.FP","scope_exclusion","Floating-point extensions are outside the implemented design.","","none","unsupported","No floating-point RTL or tests are in project scope.")
    add("EXCLUDED.RVWMO","scope_exclusion","Multi-hart/RVWMO behavior is outside the single-hart model.","","none","unsupported","The memory model assumes one hart and no concurrent writer.")
    return rows


def write_dictionary(path: Path = DICT_PATH) -> None:
    path.parent.mkdir(parents=True,exist_ok=True)
    fields=["bin_id","dictionary_version","coverage_class","definition","applicable_configurations","evidence_source","reachability","reachability_reason"]
    with path.open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=fields,lineterminator="\n"); w.writeheader(); w.writerows(dictionary_rows())


def write_migration(path: Path = ROOT/"documentation/verification/stage9_bin_migration.csv") -> None:
    rows=[]
    def add(old: str,target: str,status: str,reason: str) -> None:
        rows.append({"legacy_bin_id":old,"target_bin_ids":target,"migration_status":status,"reason":reason})
    for old in legacy_m_coverage._bins():
        if old.startswith("B.ABORT."):
            add(old,"","historical_only","Block-level abort-offset markers lack per-test identifiers; retained Stage 3.5 reports remain authoritative.")
        else: add(old,old,"retained","Stage 9 preserves the stable Stage 3.5 identifier and its exact evidence rule.")
    add("E.C.HALFWORD.65536","","historical_only","Exhaustive unit code coverage is run-level, not attributable to an individual system test.")
    families=legacy_c_coverage.FAMILIES
    for family in families: add(f"A.C.FAMILY.{family}",f"A.C.FAMILY.{family}","retained","Raw compressed family IDs and classifier are preserved.")
    for old in ("A.C.HINT.RETIRED","A.C.NOP.RETIRED","P.ATTEMPTED","P.RETIRED","P.FAULTING","P.SQUASH.REDIRECT","P.SQUASH.FAULT",
                "P.DIV.HALFWORD","P.DIV.METADATA_HOLD_CYCLES"):
        add(old,old,"retained","Stage 4 stable ID and event definition are preserved.")
    for i,name in enumerate(legacy_coverage.EVENTS):
        old=f"P.PIPE_EVENT.{i:02d}"
        add(old,old,"retained",f"Stage 2 event counter preserved: {name}.")
    for old,target,reason in (
        ("A.C.ILLEGAL.FAULT","PIPE.FAULTING","Stage 9 keeps generic precise fault coverage; detailed C legality is preserved in historical Stage 4 reports."),
        ("A.C.UNSUPPORTED_LENGTH.FAULT","PIPE.FAULTING","Stage 9 keeps generic precise fault coverage; raw-length detail is historical-only."),
        ("A.FAULT.NO_RETIRE","PIPE.FAULTING","Mapped to generic precise fault coverage."),
        ("A.FAULT.PRECISE","PIPE.FAULTING","Mapped to generic precise fault coverage."),
        ("A.C.IMM.MEM.MAX","ARCH.FORMAT.COMPRESSED","Coarsened to compressed retired encoding; immediate detail remains in Stage 4 reports."),
        ("A.C.IMM.SHIFT.MAX","ARCH.FORMAT.COMPRESSED","Coarsened to compressed retired encoding; immediate detail remains in Stage 4 reports."),
        ("A.C.IMM.SIGNED6.MAX","ARCH.FORMAT.COMPRESSED","Coarsened to compressed retired encoding; immediate detail remains in Stage 4 reports."),
        ("A.C.IMM.SIGNED6.MIN","ARCH.FORMAT.COMPRESSED","Coarsened to compressed retired encoding; immediate detail remains in Stage 4 reports."),
        ("A.C.IMM.STACK.MAX","ARCH.FORMAT.COMPRESSED","Coarsened to compressed retired encoding; immediate detail remains in Stage 4 reports."),
        ("A.C.REG.PRIME.HIGH","ARCH.FORMAT.COMPRESSED","Coarsened to compressed retired encoding; register detail remains in Stage 4 reports."),
        ("A.C.REG.PRIME.LOW","ARCH.FORMAT.COMPRESSED","Coarsened to compressed retired encoding; register detail remains in Stage 4 reports."),
        ("A.C.REG.SP","ARCH.FORMAT.COMPRESSED","Coarsened to compressed retired encoding; register detail remains in Stage 4 reports."),
        ("A.C.REG.X0.HINT","ARCH.FORMAT.COMPRESSED","Coarsened to compressed retired encoding; register detail remains in Stage 4 reports."),
        ("A.FETCH.CROSS_WORD","ARCH.FORMAT.COMPRESSED","Fetch-crossing detail is not a Stage 9 per-test bin; historic report is retained."),
        ("A.LINK.COMPRESSED_PC_PLUS_2","ARCH.OP.JALR","Mapped to the retired link operation; increment detail remains historical."),
        ("A.LINK.STANDARD_PC_PLUS_4","ARCH.OP.JALR","Mapped to the retired link operation; increment detail remains historical."),
        ("A.PC.OFFSET.0","ARCH.FORMAT.WORD32","Coarsened PC-alignment detail remains in historical Stage 4 reports."),
        ("A.PC.OFFSET.2","ARCH.FORMAT.COMPRESSED","Coarsened PC-alignment detail remains in historical Stage 4 reports."),
        ("A.WIDTH.16_TO_32","ARCH.FORMAT.COMPRESSED|ARCH.FORMAT.WORD32","Mixed-width transition detail remains in historical Stage 4 reports."),
        ("A.WIDTH.32_TO_16","ARCH.FORMAT.COMPRESSED|ARCH.FORMAT.WORD32","Mixed-width transition detail remains in historical Stage 4 reports."),):
        add(old,target,"mapped_coarse",reason)
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=["legacy_bin_id","target_bin_ids","migration_status","reason"],lineterminator="\n")
        w.writeheader(); w.writerows(rows)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def provenance_hash_matches(path: Path, want: str) -> bool:
    """Accept exact provenance bytes or its CRLF/LF text representation."""
    data=path.read_bytes()
    return (hashlib.sha256(data).hexdigest()==want or
            hashlib.sha256(data.replace(b"\r\n",b"\n")).hexdigest()==want)


def resolve_workspace_path(value: str, base: Path = ROOT) -> Path:
    """Resolve repo-relative, Windows-drive, and WSL-mounted repo paths."""
    value=value.strip().replace("\\","/")
    win=re.match(r"^[A-Za-z]:/(.*)$",value)
    if win:
        parts=win.group(1).split("/",1)
        if parts[0].lower()==ROOT.name.lower(): return ROOT/(parts[1] if len(parts)>1 else "")
    wsl=re.match(r"^/mnt/[A-Za-z]/(.*)$",value,re.I)
    if wsl:
        parts=wsl.group(1).split("/",1)
        if parts[0].lower()==ROOT.name.lower(): return ROOT/(parts[1] if len(parts)>1 else "")
    path=Path(value)
    return path if path.is_absolute() else base/path


def validate_provenance_record(record: dict, context: str) -> None:
    """Enforce the serialized provenance status contract at index boundaries."""
    require(isinstance(record,dict) and record.get("source_provenance_status") in SOURCE_PROVENANCE_STATUSES,
            f"{context} has missing or unsupported source_provenance_status")
    unresolved=record.get("unresolved_source_hashes")
    require(isinstance(unresolved,list),f"{context} unresolved_source_hashes must be a list")
    if record["source_provenance_status"]=="PASS":
        require(not unresolved,f"{context} PASS status conflicts with unresolved source hashes")
    else:
        require(bool(unresolved),f"{context} limitation status requires unresolved source hashes")


def validate_report_provenance(report: Path, report_text: str | None = None,
                               expected_sim: str | None = None) -> dict[str,str|int]:
    """Validate source hashes inline or through a report's provenance_file link."""
    require(report.is_file(),f"missing validation report: {report}")
    text=report_text if report_text is not None else report.read_text(encoding="utf-8",errors="replace")
    inline=re.findall(r"^sha256 ([^=]+)=([0-9a-f]{64})$",text,re.M)
    ref=re.search(r"^provenance_file=(.+)$",text,re.M)
    provenance_path=report
    external_text=""
    if ref:
        provenance_path=resolve_workspace_path(ref.group(1),report.parent).resolve()
        require(provenance_path.is_file(),f"missing referenced provenance file: {provenance_path}")
        external_text=provenance_path.read_text(encoding="utf-8",errors="replace")
        ext_sim=re.search(r"^simulator=(\w+)$",external_text,re.M)
        if expected_sim:
            require(ext_sim is not None,f"referenced provenance lacks simulator identity: {provenance_path}")
            require(ext_sim.group(1).lower()==expected_sim.lower(),
                    f"provenance simulator mismatch: {provenance_path}")
    hashes=inline+re.findall(r"^sha256 ([^=]+)=([0-9a-f]{64})$",external_text,re.M)
    require(hashes,f"validation report lacks source provenance: {report}")
    snapshot_ref=re.search(r"^producer_snapshot=(.+)$",text+"\n"+external_text,re.M)
    snapshot_digest=re.search(r"^producer_snapshot_sha256=([0-9a-f]{64})$",text+"\n"+external_text,re.M)
    snapshot_sources={}
    if snapshot_ref:
        snapshot_path=resolve_workspace_path(snapshot_ref.group(1),report.parent).resolve()
        require(snapshot_path.is_file() and snapshot_digest is not None and
                hashlib.sha256(snapshot_path.read_bytes()).hexdigest()==snapshot_digest.group(1),
                f"producer source snapshot missing or hash mismatch: {snapshot_path}")
        snapshot_doc=json.loads(snapshot_path.read_text(encoding="utf-8"))
        require(snapshot_doc.get("schema")=="stage9-producer-snapshot-1",f"unsupported producer snapshot schema: {snapshot_path}")
        for entry in snapshot_doc.get("files",[]):
            # Producer snapshots are commonly captured under WSL and retain
            # /mnt/<drive>/... paths. Resolve both sides through the same
            # cross-platform mapping used for report references so Windows
            # validation can locate the archived bytes and match their source.
            saved=resolve_workspace_path(entry["snapshot"],snapshot_path.parent).resolve()
            require(saved.is_file() and hashlib.sha256(saved.read_bytes()).hexdigest()==entry["sha256"],
                    f"producer snapshot content hash mismatch: {saved}")
            source_path=resolve_workspace_path(entry["path"]).resolve()
            snapshot_sources[str(source_path)]=entry["sha256"]
    head_match=re.search(r"^git_head=([0-9a-f]{40})$",text+"\n"+external_text,re.M)
    for rel,want in hashes:
        source=resolve_workspace_path(rel).resolve()
        current_matches=source.is_file() and provenance_hash_matches(source,want)
        historical_matches=False
        if not current_matches and head_match:
            repo_path=Path(rel.replace("\\","/"))
            if not repo_path.is_absolute():
                snapshot=subprocess.run(["git","show",f"{head_match.group(1)}:{repo_path.as_posix()}"],cwd=ROOT,
                                        stdout=subprocess.PIPE,stderr=subprocess.DEVNULL)
                historical_matches=snapshot.returncode==0 and hashlib.sha256(snapshot.stdout).hexdigest()==want
        archived_matches=snapshot_sources.get(str(source))==want
        require(current_matches or historical_matches or archived_matches,
                f"{'missing provenance source file' if not source.is_file() else 'source provenance hash mismatch'}: {source}")
    if expected_sim:
        report_sim=re.search(r"^Simulator:\s*(\w+)$",text,re.M)
        if not report_sim: report_sim=re.search(r"^.*simulator=(\w+)$",text,re.M)
        if not report_sim:
            report_sim=re.search(rf"^STAGE8_ENABLED_{re.escape(expected_sim.upper())} PASS",text,re.M)
        require(report_sim is not None,f"validation report lacks simulator identity: {report}")
        if report_sim.lastindex:
            require(report_sim.group(1).lower()==expected_sim.lower(),f"report simulator mismatch: {report}")
    # A fully validated report has PASS provenance. Keep this explicit at the
    # producer/consumer boundary; callers must never infer PASS from omission.
    return {"source_hashes_checked":len(hashes),"source_provenance_status":"PASS",
            "unresolved_source_hashes":[],"provenance_path":str(provenance_path),
            "provenance_sha256":hashlib.sha256(provenance_path.read_bytes()).hexdigest()}


def validate_saved_legacy_supplemental(report: Path, report_text: str, expected_sim: str) -> dict:
    """Verify saved supplemental evidence while explicitly retaining its one unavailable producer source.

    The previously validated 209-case supplemental reports record the exact
    pre-selection runner hash, but that source file was not snapshotted. All
    other recorded source hashes must still validate. The unresolved hash is
    surfaced in the resulting collection metadata; it is never silently
    treated as today's runner.
    """
    ref=re.search(r"^provenance_file=(.+)$",report_text,re.M)
    require(ref is not None,f"supplemental report lacks provenance reference: {report}")
    provenance=resolve_workspace_path(ref.group(1),report.parent).resolve()
    require(provenance.is_file(),f"missing supplemental provenance file: {provenance}")
    ptext=provenance.read_text(encoding="utf-8",errors="replace")
    sim=re.search(r"^simulator=(\w+)$",ptext,re.M)
    require(sim and sim.group(1).lower()==expected_sim.lower(),f"supplemental simulator provenance mismatch: {provenance}")
    hashes=re.findall(r"^sha256 ([^=]+)=([0-9a-f]{64})$",ptext,re.M)
    require(hashes,f"supplemental provenance has no source hashes: {provenance}")
    head=re.search(r"^git_head=([0-9a-f]{40})$",ptext,re.M)
    unresolved=[]; checked=0
    for rel,want in hashes:
        src=resolve_workspace_path(rel).resolve()
        ok=src.is_file() and provenance_hash_matches(src,want)
        if not ok and head and not Path(rel.replace("\\","/")).is_absolute():
            snap=subprocess.run(["git","show",f"{head.group(1)}:{Path(rel.replace(chr(92),'/')).as_posix()}"],cwd=ROOT,
                                stdout=subprocess.PIPE,stderr=subprocess.DEVNULL)
            ok=snap.returncode==0 and hashlib.sha256(snap.stdout).hexdigest()==want
        if ok:
            checked+=1
        elif rel=="scripts/simulation/run_stage4_4.py" and want=="443850e1bac59743145307e38e16302417341e0c701ded81612d707b045098e0":
            unresolved.append({"path":rel,"recorded_sha256":want,"status":"SOURCE_SNAPSHOT_UNAVAILABLE"})
        else:
            raise ValueError(f"supplemental source provenance mismatch outside reviewed runner hash: {src} recorded={want}")
    require(len(unresolved)==1 and checked==len(hashes)-1,
            f"supplemental provenance mismatch inventory unexpected: checked={checked} unresolved={unresolved}")
    return {"provenance_path":str(provenance),"provenance_sha256":hashlib.sha256(provenance.read_bytes()).hexdigest(),
            "source_hashes_checked":checked,"unresolved_source_hashes":unresolved,
            "source_provenance_status":"DOCUMENTED_LIMITATION_RUNNER_SNAPSHOT_UNAVAILABLE"}


def instruction_name(raw: int, length: int, expanded: int) -> str:
    insn = expanded if length == 2 else raw
    opcode = insn & 0x7f
    funct3 = (insn >> 12) & 7
    funct7 = (insn >> 25) & 0x7f
    if opcode in ISSUES:
        if opcode == 0x33 and funct7 == 1:
            return M_OPS[funct3]
        name = ISSUES[opcode][funct3]
        if name is None:
            raise ValueError(f"unsupported retired encoding raw={raw:08x} expanded={insn:08x}")
        if opcode == 0x33 and funct7 == 0x20 and funct3 == 5:
            return "sub" if funct3 == 0 else "sra"
        if opcode == 0x33 and funct7 == 0x20 and funct3 == 0:
            return "sub"
        if opcode == 0x13 and funct3 == 5 and funct7 == 0x20:
            return "srai"
        return name
    if opcode == 0x37: return "lui"
    if opcode == 0x17: return "auipc"
    if opcode == 0x6f: return "jal"
    if opcode == 0x67 and funct3 == 0: return "jalr"
    if opcode == 0x0f: return "fencei" if funct3 == 1 else "fence"
    if opcode == 0x2f:
        op = A_OPS.get((insn >> 27) & 0x1f)
        if op and (op != "lr.w" or ((insn >> 20) & 31) == 0): return op
    if opcode == 0x73:
        if insn == 0x00000073: return "ecall"
        if insn == 0x00100073: return "ebreak"
        if insn == 0x30200073: return "mret"
        if insn == 0x10500073: return "wfi"
        if funct3 in (1, 2, 3, 5, 6, 7):
            return ("csrrw", "csrrs", "csrrc", "csrrwi", "csrrsi", "csrrci")[(funct3 - 1) if funct3 <= 3 else (funct3 - 2)]
    raise ValueError(f"unclassified retired encoding raw={raw:08x} expanded={insn:08x}")


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f,delimiter="\t" if path.suffix.lower()==".tsv" else ",")
        require(bool(reader.fieldnames), f"missing CSV header: {path}")
        rows = list(reader)
        require(all(None not in row and all(v is not None for v in row.values()) for row in rows), f"malformed CSV row: {path}")
        return rows


def read_manifest(path: Path, required_headers: set[str]) -> list[dict[str,str]]:
    """Read a manifest and report schema/row errors with file and line."""
    with path.open(newline="",encoding="utf-8-sig") as stream:
        reader=csv.reader(stream)
        try: headers=next(reader)
        except StopIteration: raise ValueError(f"manifest is empty: {path}")
        require(bool(headers) and all(h.strip() for h in headers),f"manifest has empty header: {path}")
        require(len(headers)==len(set(headers)),f"manifest has duplicate headers: {path}")
        missing=required_headers-set(headers)
        require(not missing,f"manifest missing required header(s) {sorted(missing)}: {path}")
        rows=[]
        try:
            for line_no,values in enumerate(reader,2):
                require(len(values)==len(headers),
                        f"manifest malformed row at {path}:{line_no}: expected {len(headers)} columns, found {len(values)}")
                row=dict(zip(headers,values))
                require(bool(row.get("name","")),f"manifest empty test name at {path}:{line_no}")
                rows.append(row)
        except csv.Error as ex:
            raise ValueError(f"manifest malformed CSV at {path}:{reader.line_num}: {ex}") from ex
        return rows


def read_stage5_manifests(outdir: Path) -> list[dict[str,str]]:
    """Combine the producer's disjoint legacy, C, and A manifests."""
    legacy=read_manifest(outdir/"manifest_all.csv",{"name","expect_cause","check_gp","hexpath"})
    c_rows=read_manifest(outdir/"c_manifest.csv",{"name","expect_cause","check_gp","suite","hexpath"})
    a_rows=read_manifest(outdir/"a_manifest.csv",{"name","expect_cause","check_gp","suite","hexpath"})
    require(len(legacy)==209,f"Stage 5 legacy manifest must contain 209 cases, found {len(legacy)}")
    require(len(c_rows)==21,f"Stage 5 C manifest must contain 21 cases, found {len(c_rows)}")
    require(len(a_rows)==18,f"Stage 5 A/C+A manifest must contain 18 cases, found {len(a_rows)}")
    require(len({r["name"] for r in legacy})==len(legacy),"duplicate test identity in Stage 5 legacy manifest")
    require(len({r["name"] for r in c_rows})==len(c_rows),"duplicate test identity in Stage 5 C manifest")
    require(len({r["name"] for r in a_rows})==len(a_rows),"duplicate test identity in Stage 5 A/C+A manifest")
    require({r["suite"] for r in c_rows}<={"rv32imc","rv32imc_pipeline"},"unknown Stage 5 C suite label")
    require({r["suite"] for r in a_rows}<={"rv32ima_software","rv32imac_software","rv32imac_pipeline_a"},
            "unknown Stage 5 A/C+A suite label")
    combined=[{**r,"suite":"rv32im"} for r in legacy]+c_rows+a_rows
    names=[r["name"] for r in combined]
    require(len(combined)==248 and len(set(names))==248,
            "Stage 5 combined manifest must contain 248 unique tests (legacy+C+A/C+A)")
    return combined


def stage5_evidence_selection(manifest: list[dict[str,str]], historical_dir: Path,
                              supplemental_dir: Path | None = None) -> dict[str,Path]:
    """Choose exactly one evidence producer per Stage 5 identity.

    A supplemental legacy run replaces those 209 identities; it never appends
    duplicate observations beside historical versions. C/A identities retain
    the historical producer.
    """
    names=[row["name"] for row in manifest]
    require(len(names)==len(set(names)),"Stage 5 manifest has duplicate identities")
    selected={name:historical_dir for name in names}
    if supplemental_dir is None: return selected
    legacy={row["name"] for row in manifest if row["suite"]=="rv32im"}
    supplemental={p.name[:-len(".pipe.trace")] for p in supplemental_dir.glob("*.pipe.trace")}
    require(supplemental==legacy,
            f"supplemental legacy identity set mismatch: missing={sorted(legacy-supplemental)} extra={sorted(supplemental-legacy)}")
    for name in legacy: selected[name]=supplemental_dir
    require(len(selected)==len(names),"Stage 5 supplemental selection duplicated or omitted identities")
    return selected


def parse_trace(path: Path) -> tuple[list[dict[str, int | str]], dict[int, int]]:
    require(path.is_file(), f"missing required trace: {path}")
    text = path.read_text(encoding="ascii")
    rows: list[dict[str, int | str]] = []
    state: dict[int, int] = {}
    header = False
    legacy_format = False
    registers=set()
    for no, line in enumerate(text.splitlines(), 1):
        p = line.split()
        if not p: continue
        if p[0] in ("TRACE_V2","TRACE_V3"):
            header = len(p) >= 2
        elif p[0] == "I":
            require(len(p) == 10, f"{path}:{no}: malformed instruction trace row")
            try:
                rows.append({"pc": int(p[1],16), "raw": int(p[2],16), "length": int(p[3]),
                             "expanded": int(p[4],16), "rd": int(p[5]), "rdval": int(p[6],16), "line": line})
            except ValueError as ex: raise ValueError(f"{path}:{no}: malformed numeric trace field") from ex
            require(rows[-1]["length"] in (2,4), f"{path}:{no}: invalid retired instruction length")
        elif len(p)==7 and re.fullmatch(r"[0-9a-fA-F]{8}",p[0]) and re.fullmatch(r"[0-9a-fA-F]{8}",p[1]):
            # Stage 5 legacy traces predate TRACE_V3 and encode fixed-width
            # instructions as: pc raw rd rdval store_size store_addr store_data.
            legacy_format=True
            try:
                raw=int(p[1],16)
                rows.append({"pc":int(p[0],16),"raw":raw,"length":4,"expanded":raw,
                             "rd":int(p[2],16),"rdval":int(p[3],16),"line":line})
            except ValueError as ex: raise ValueError(f"{path}:{no}: malformed legacy trace row") from ex
        elif p[0] == "REG":
            require(len(p)==3,f"{path}:{no}: malformed REG record")
            reg=int(p[1]); state[0x20000+reg]=int(p[2],16); registers.add(reg)
        elif p[0] == "MEM":
            require(len(p) == 3, f"{path}:{no}: malformed MEM record")
            state[int(p[1],16)] = int(p[2],16)
        elif p[0] == "CSR":
            require(len(p) == 3, f"{path}:{no}: malformed CSR record")
            address = int(p[1],16)
            if address not in (0xb00,0xb80): state[0x10000+address] = int(p[2],16)
        elif p[0] in ("HALT", "STOP"):
            state[-1]=int(hashlib.sha256(line.encode()).hexdigest()[:8],16)
    require((header or legacy_format) and registers==set(range(1,32)), f"incomplete architectural trace footer: {path}")
    return rows, state


def parse_sidecar(path: Path, ordered: list[tuple[str,list[str]]] | None = None) -> dict[str, list[list[str]]]:
    require(path.is_file(), f"missing required DUT sidecar: {path}")
    records: dict[str, list[list[str]]] = collections.defaultdict(list)
    for no, line in enumerate(path.read_text(encoding="ascii").splitlines(), 1):
        p = line.split()
        if not p: continue
        require(len(p) >= 2, f"{path}:{no}: malformed event record")
        event = (" ".join(p[:2]) if p[0] in ("C", "Z", "A", "EV") else
                 ("M " + p[1] if p[0] == "M" and p[1] in ("TRAP", "IRQ", "MRET", "DIV_ABORT") else "M") if p[0] == "M" else p[0])
        if p[:2] == ["MCOV_VERSION", "2"]:
            event="MCOV_VERSION"
        elif p[:2] == ["C", "ENTER"]:
            event="C ENTER"
        records[event].append(p)
        if ordered is not None: ordered.append((event,p))
    allowed = {"MCOV_VERSION", "C ENTER", "C ATTEMPT", "C RETIRE", "C FAULT", "C SQUASH_REDIRECT", "C SQUASH_FAULT", "C SQUASH_FAULT_IFID", "C DIV_HOLD",
               "Z ATTEMPT", "Z RETIRE", "Z CSR_WRITE", "Z CSR_ACCESS", "Z CSR_FAULT", "Z FENCEI", "Z SQUASH_REDIRECT",
               "A ATTEMPT", "A RETIRE", "A FAULT", "A SQUASH_FAULT", "A SQUASH_FAULT_IFID", "A SQUASH_REDIRECT",
               "M", "M TRAP", "M IRQ", "M MRET", "M DIV_ABORT", "EV ISSUE", "EV COMPLETE", "EV RETIRE", "EV DIV_CONSECUTIVE",
               "EV SQUASH_REDIRECT", "EV SQUASH_FAULT_IDEX", "EV SQUASH_FAULT_IFID", "EV FAULT_DIV_SUPPRESS", "EV LOAD_USE_RS1", "EV LOAD_USE_RS2"}
    unknown = sorted(set(records) - allowed)
    require(not unknown, f"{path}: unknown evidence event(s): {unknown}")
    for event, rows in records.items():
        expected = {"MCOV_VERSION":3,"C ENTER":6,"C ATTEMPT":5,"C RETIRE":5,"C FAULT":6,"C SQUASH_REDIRECT":5,"C SQUASH_FAULT":5,"C SQUASH_FAULT_IFID":5,
                    "C DIV_HOLD":5,"Z ATTEMPT":5,"Z RETIRE":5,"Z CSR_WRITE":7,"Z CSR_ACCESS":9,"Z CSR_FAULT":5,
                    "Z SQUASH_REDIRECT":5,"Z FENCEI":6,"A ATTEMPT":4,"A RETIRE":4,"A FAULT":5,"A SQUASH_FAULT":4,
                    "A SQUASH_FAULT_IFID":4,"A SQUASH_REDIRECT":4,"M":7,"M TRAP":5,"M IRQ":4,
                    "M MRET":4,"M DIV_ABORT":4,"EV ISSUE":4,"EV COMPLETE":4,"EV RETIRE":4,"EV DIV_CONSECUTIVE":4,
                    "EV SQUASH_REDIRECT":4,"EV SQUASH_FAULT_IDEX":4,"EV SQUASH_FAULT_IFID":4,"EV FAULT_DIV_SUPPRESS":4,
                    "EV LOAD_USE_RS1":4,"EV LOAD_USE_RS2":4}.get(event)
        for row in rows:
            require(len(row) == expected, f"{path}: malformed {event} record: {' '.join(row)}")
            if event == "C ENTER":
                require(row[2].isdigit() and int(row[2]) > 0, f"{path}: malformed C ENTER dynamic ID")
            if event == "MCOV_VERSION":
                require(row == ["MCOV_VERSION","2","DYNAMIC_IFID_ENTRY"], f"{path}: unsupported MCOV version")
            pc_index=3 if event=="C ENTER" else 2
            require(re.fullmatch(r"[0-9a-fA-F]{8}", row[pc_index]) if event.startswith(("C ","Z ","A ","EV ")) else True,
                    f"{path}: malformed PC in {event}")
    if "C ENTER" in records:
        dyn_ids=[int(row[2]) for row in records["C ENTER"]]
        require(dyn_ids==list(range(1,len(dyn_ids)+1)),f"{path}: duplicate or nonsequential dynamic IF/ID entry IDs")
    return records


def analyze_ordered_lifecycle(ordered: list[tuple[str,list[str]]]) -> dict[str,object]:
    """Count lifecycle occurrences from ordered producer records without static-ID exclusivity.

    ATTEMPT is sampled every cycle while IF/ID is valid. Consecutive repeats of
    one PC/raw/length are retries. A repeated key after another ATTEMPT can be a
    second in-flight occurrence; without a producer dynamic ID its attempt
    count is ambiguous. Terminal events still retain their independent counts.
    """
    active: dict[tuple[int,int,int],int]={}
    ambiguous:set[tuple[int,int,int]]=set()
    last_attempt:tuple[int,int,int]|None=None
    attempts=0; terminals=0
    terminal_events={"C RETIRE","C FAULT","C SQUASH_REDIRECT","C SQUASH_FAULT","C SQUASH_FAULT_IFID","M DIV_ABORT"}
    for event,row in ordered:
        if event=="C ATTEMPT":
            key=(int(row[2],16),int(row[3],16),int(row[4]))
            if key not in active:
                active[key]=1; attempts+=1
            elif key!=last_attempt:
                active[key]+=1; attempts+=1; ambiguous.add(key)
            last_attempt=key
        elif event in terminal_events:
            key=(int(row[2],16),int(row[3],16),4) if event=="M DIV_ABORT" else (int(row[2],16),int(row[3],16),int(row[4]))
            count=active.get(key,0)
            if count==0 and event.startswith("C SQUASH_"):
                # A flush may report the same fetch-fault identity from more
                # than one pipeline stage. The sidecar lacks stage-instance
                # links, so keep event totals but do not infer its lifecycle.
                ambiguous.add(key)
                continue
            require(count>0,f"lifecycle terminal {event} has no prior ordered attempt for {key}")
            terminals+=1
            if count==1: del active[key]
            else: active[key]=count-1
    return {"attempt_count":None if ambiguous else attempts,
            "ambiguous_attempt_keys":ambiguous,"terminal_count":terminals}


def trap_instruction_bins(trap_rows: list[dict[str,str]]) -> collections.Counter[str]:
    """Classify ECALL/EBREAK from synchronous trap rows, never retirement rows."""
    counts:collections.Counter[str]=collections.Counter()
    for row in trap_rows:
        raw=int(row["raw"],16); mcause=int(row["mcause"],16)
        if mcause&0x80000000: continue
        cause=mcause&0x7fffffff
        if raw==0x00000073 and cause==11: counts["ARCH.OP.ECALL"]+=1
        elif raw==0x00100073 and cause==3: counts["ARCH.OP.EBREAK"]+=1
    return counts


def pass_log(path: Path) -> tuple[int, float | None]:
    require(path.is_file(), f"missing simulator log: {path}")
    text = path.read_text(encoding="utf-8", errors="replace")
    matches = re.findall(r"TEST_RESULT:\s*(PASS|FAIL|TIMEOUT).*?cycles=(\d+)", text)
    require(len(matches) == 1 and matches[0][0] == "PASS", f"failed or incomplete simulation record: {path}")
    causes=re.findall(r"\bcause=(\d+)\s+expect=(\d+)\b",text)
    require(len(causes)==1 and causes[0][0]==causes[0][1],f"validated trap cause is missing or differs from expected cause: {path}")
    runtimes = re.findall(r"walltime\s+([0-9.]+)\s*s", text)
    return int(matches[0][1]), (float(runtimes[-1]) if runtimes else None)


def verify_trace_pair(pipe: Path, golden: Path) -> list[dict[str, int | str]]:
    p_rows, p_state = parse_trace(pipe)
    g_rows, g_state = parse_trace(golden)
    def norm(rows: list[dict[str, int | str]], state: dict[int,int]) -> tuple[list[tuple[int,...]],dict[int,int]]:
        return [(int(r["pc"]),int(r["raw"]),int(r["length"]),int(r["expanded"]),int(r["rd"]),int(r["rdval"])) for r in rows], state
    require(norm(p_rows,p_state) == norm(g_rows,g_state), f"DUT trace differs from independent golden trace: {pipe}")
    return p_rows


def canonical_config(stage: str, suite: str) -> str:
    if stage=="stage5":
        aliases={"rv32imc_pipeline":"rv32imc","rv32ima_software":"rv32ima",
                 "rv32imac_software":"rv32imac","rv32imac_pipeline_a":"rv32imac"}
        key=aliases.get(suite,suite)
    else: key=stage
    require(key in CONFIGS, f"unknown evidence stage/configuration {stage}/{suite}")
    return CONFIGS[key]


def evidence_path(outdir: Path, name: str, stage: str, suffix: str) -> Path:
    """Resolve a sidecar using the naming contract of its evidence producer."""
    if suffix==".pipe.mcov" and stage=="stage5":
        # Stage 5 producers (including the supplemental legacy-gap runner)
        # emit the C-format pipeline sidecar. Stage 6/8 emit MCOV instead.
        suffix=".pipe.ccov"
    return outdir/f"{name}{suffix}"


def validate_stage5_iss_replay(item: dict, sim: str, stage5_out: Path) -> Path:
    """Validate reconstructed ISS operands against the captured inputs and DUT traces."""
    replay_out=ROOT/item["outdir"]
    report=ROOT/item["report"]
    manifest=ROOT/item["manifest"]
    require(hashlib.sha256(report.read_bytes()).hexdigest()==item["report_sha256"],
            f"Stage 5 ISS replay report changed: {report}")
    report_text=report.read_text(encoding="utf-8",errors="replace")
    marker=f"STAGE9_ISS_REPLAY_{sim.upper()} PASS cases=39 c_cases=21 a_cases=18 trace_comparisons=117 evidence=RECONSTRUCTED_REFERENCE_TRACE_MATCHED"
    require(marker in report_text,"Stage 5 ISS replay did not pass its reference/DUT trace checks")
    require(hashlib.sha256(manifest.read_bytes()).hexdigest()==item["manifest_sha256"],
            f"Stage 5 ISS replay manifest changed: {manifest}")
    snapshot=resolve_workspace_path(item["source_snapshot"]).resolve()
    require(snapshot.is_file() and hashlib.sha256(snapshot.read_bytes()).hexdigest()==item["source_snapshot_sha256"],
            f"Stage 5 ISS replay source snapshot missing or changed: {snapshot}")
    snapshot_doc=json.loads(snapshot.read_text(encoding="utf-8"))
    require(snapshot_doc.get("schema")=="stage9-producer-snapshot-1","unsupported Stage 5 ISS replay snapshot schema")
    for entry in snapshot_doc.get("files",[]):
        saved=resolve_workspace_path(entry["snapshot"],snapshot.parent).resolve()
        source=resolve_workspace_path(entry["path"]).resolve()
        require(saved.is_file() and hashlib.sha256(saved.read_bytes()).hexdigest()==entry["sha256"],
                f"Stage 5 ISS replay snapshot file missing or corrupt: {saved}")
        require(source.is_file() and hashlib.sha256(source.read_bytes()).hexdigest()==entry["sha256"],
                f"Stage 5 ISS replay source/input changed after capture: {source}")
    rows=read_csv(manifest)
    require(len(rows)==39 and len({r["name"] for r in rows})==39,
            "Stage 5 ISS replay manifest must contain 39 unique cases")
    expected={r["name"]:r["suite"] for r in read_stage5_manifests(stage5_out)
              if r["suite"]!="rv32im"}
    require({r["name"] for r in rows}==set(expected),"Stage 5 ISS replay identities differ from validated C/A selection")
    for row in rows:
        name=row["name"]; a_case=row["configuration"]=="rv32imac"
        require(row["configuration"]==("rv32imac" if expected[name].startswith("rv32ima") or expected[name].startswith("rv32imac") else "rv32imc"),
                f"Stage 5 ISS replay configuration mismatch for {name}")
        image=stage5_out/("a_hex" if a_case else "c_hex")/(name+".hex")
        ref=stage5_out/("a_iss" if a_case else "c_iss")/(name+".trace")
        pipe=stage5_out/(name+".pipe.trace"); golden=stage5_out/(name+".golden.trace")
        side=replay_out/row["m_operand_sidecar"]
        trace=replay_out/"replayed_trace"/(name+".trace")
        for key,path in (("image_sha256",image),("reference_trace_sha256",ref),
                         ("dut_pipe_trace_sha256",pipe),("dut_golden_trace_sha256",golden),
                         ("m_operand_sha256",side),("replayed_trace_sha256",trace)):
            require(path.is_file() and hashlib.sha256(path.read_bytes()).hexdigest()==row[key],
                    f"Stage 5 ISS replay evidence changed for {name}: {key}")
        actual=trace.read_text(encoding="ascii").splitlines()
        require(actual==ref.read_text(encoding="ascii").splitlines()==pipe.read_text(encoding="ascii").splitlines()==golden.read_text(encoding="ascii").splitlines(),
                f"Stage 5 ISS replay trace no longer matches validated DUT evidence for {name}")
        require(row["evidence_status"]=="RECONSTRUCTED_REFERENCE_TRACE_MATCHED",
                f"Stage 5 ISS replay evidence lacks reconstructed label: {name}")
    return replay_out/"iss"


def collect_test(stage: str, sim: str, outdir: Path, name: str, meta: dict[str,str], suite: str,
                 scenario: str, seed: str | None, report: Path,
                 reconstructed_m_dir: Path | None = None) -> dict:
    test_id = f"{stage}:{name}"
    config = canonical_config(stage,suite)
    pipe = outdir / f"{name}.pipe.trace"
    golden = outdir / f"{name}.golden.trace"
    rows = verify_trace_pair(pipe, golden)
    side_path = evidence_path(outdir,name,stage,".pipe.mcov")
    legacy_c_disabled = stage=="stage5" and suite=="rv32im" and not side_path.is_file()
    ordered_side=[]
    side = parse_sidecar(side_path,ordered_side) if side_path.is_file() else {}
    require(side_path.is_file() or legacy_c_disabled,
            f"{test_id}: required DUT coverage sidecar missing: {side_path}")
    cycles, runtime = pass_log(outdir / f"{name}.pipe.log")
    log_text=(outdir/f"{name}.pipe.log").read_text(encoding="utf-8",errors="replace")
    cov_lines=re.findall(r"(?m)^COV\s+(.+)$",log_text)
    require(len(cov_lines)==1,f"{test_id}: required DUT pipeline COV record missing or duplicated")
    try: legacy_counts=[int(x) for x in cov_lines[0].split()]
    except ValueError as ex: raise ValueError(f"{test_id}: malformed pipeline COV record") from ex
    require(len(legacy_counts)==len(legacy_coverage.EVENTS) and all(x>=0 for x in legacy_counts),f"{test_id}: malformed legacy COV width/count")
    retired_seq = [(int(r["pc"]),int(r["raw"]),int(r["length"])) for r in rows]
    if "C ENTER" in side:
        require("MCOV_VERSION" in side, f"{test_id}: dynamic IF/ID entries require MCOV_VERSION 2")
        entries=side["C ENTER"]
        dyn_ids=[int(r[2]) for r in entries]
        require(dyn_ids==list(range(1,len(dyn_ids)+1)),f"{test_id}: duplicate or nonsequential dynamic IF/ID entry IDs")
        lifecycle={"attempt_count":len(entries),"ambiguous_attempt_keys":set(),"terminal_count":0}
    else:
        lifecycle=analyze_ordered_lifecycle(ordered_side) if ordered_side else {"attempt_count":None,"ambiguous_attempt_keys":set(),"terminal_count":0}
    side_retired_seq = [(int(x[2],16),int(x[3],16),int(x[4])) for x in side.get("C RETIRE",[])]
    if not legacy_c_disabled:
        require(retired_seq == side_retired_seq, f"{test_id}: pipeline retire events disagree with architectural trace")
    identity = {"test_id":test_id,"simulator":sim,"configuration":config,"scenario":scenario,"seed":seed or "",
        "suite":suite,"dictionary_version":DICTIONARY_VERSION,"schema_version":SCHEMA_VERSION,
                "observed_cycles":cycles,"runtime_seconds":"" if runtime is None else f"{runtime:.6f}",
                "status":"PASS","validation_status":"PASS"}
    identity["source_provenance_status"]="PASS"
    identity["reference_evidence_status"]=("RECONSTRUCTED_REFERENCE_TRACE_MATCHED"
        if stage=="stage5" and suite!="rv32im" and reconstructed_m_dir is not None else "PRODUCER_REFERENCE")
    counts: collections.Counter[str] = collections.Counter()
    unavailable_reasons={}
    def bump(bin_id: str, amount: int = 1) -> None:
        if amount > 0: counts[bin_id] += amount
    # Architectural operation counts come from DUT retirements whose full states match the independent ISS trace.
    for pc, raw, length in retired_seq:
        rec = next(r for r in rows if int(r["pc"]) == pc and int(r["raw"]) == raw)
        op = instruction_name(raw,length,int(rec["expanded"]))
        if op not in ("ecall","ebreak"):
            bump(f"ARCH.OP.{op.upper()}")
        bump("ARCH.FORMAT.COMPRESSED" if length == 2 else "ARCH.FORMAT.WORD32")
        if op in A_OPS.values():
            bump("ARCH.A.ATOMIC")
            bump("ARCH.A."+op.upper().replace(".","_"))
        ext = "C" if length == 2 else ("M" if op in M_OPS else "A" if op in A_OPS.values() else "Z" if op.startswith("csr") or op == "fencei" else "PRIV" if op in ("mret","wfi","ecall","ebreak") else "I")
        bump(f"ARCH.EXT.{ext}")
    if lifecycle["attempt_count"] is not None:
        bump("PIPE.ATTEMPTED",lifecycle["attempt_count"])
        bump("P.ATTEMPTED",lifecycle["attempt_count"])
    else:
        for bin_id in ("PIPE.ATTEMPTED","P.ATTEMPTED"):
            unavailable_reasons[bin_id]="Ordered MCOV records contain overlapping repeats of the same static identity; producer emits no dynamic ID, so unique attempt count is ambiguous"
    bump("PIPE.RETIRED",len(retired_seq))
    bump("PIPE.FAULTING",len(side.get("C FAULT",[])))
    squashed_count=sum(len(side.get(k,[])) for k in ("C SQUASH_REDIRECT","C SQUASH_FAULT","C SQUASH_FAULT_IFID"))
    bump("PIPE.SQUASHED",squashed_count)
    for bin_id,amount in (("P.RETIRED",len(retired_seq)),("P.FAULTING",len(side.get("C FAULT",[]))),
                          ("P.SQUASH.REDIRECT",len(side.get("C SQUASH_REDIRECT",[]))),
                          ("P.SQUASH.FAULT",len(side.get("C SQUASH_FAULT",[]))+len(side.get("C SQUASH_FAULT_IFID",[])))):
        bump(bin_id,amount)
    compressed_records=[(int(r["raw"]),int(r["length"])) for r in rows if int(r["length"])==2]
    compressed_records += [(int(e[3],16),int(e[4])) for e in side.get("C FAULT",[]) if int(e[4])==2]
    for raw,length in compressed_records:
        family=legacy_c_coverage.c_family(raw)
        if family: bump(f"A.C.FAMILY.{family}")
    for r in rows:
        if int(r["length"])==2:
            raw=int(r["raw"])
            if legacy_c_coverage.is_hint(raw): bump("A.C.HINT.RETIRED")
            if legacy_c_coverage.c_family(raw)=="NOP": bump("A.C.NOP.RETIRED")
    for bin_id, events in (("PIPE.SQUASH.REDIRECT",("C SQUASH_REDIRECT",)),("PIPE.SQUASH.FAULT",("C SQUASH_FAULT","C SQUASH_FAULT_IFID")),
                           ("PIPE.HAZARD.DIV_HOLD",("C DIV_HOLD",))):
        bump(bin_id,sum(len(side.get(event,[])) for event in events))
    bump("P.DIV.METADATA_HOLD_CYCLES",len(side.get("C DIV_HOLD",[])))
    for ev in side.get("EV ISSUE",[]):
        if int(ev[2],16)%4==2 and legacy_m_coverage._op(int(ev[3],16)) in ("DIV","DIVU","REM","REMU"):
            bump("P.DIV.HALFWORD")
    for i,value in enumerate(legacy_counts):
        if value: bump(f"P.PIPE_EVENT.{i:02d}",value)
    if "A RETIRE" in side:
        a_path = outdir / f"{name}.pipe.a.tsv"
        golden_a = outdir / f"{name}.golden.a.tsv"
        atomic_trace=[(int(r["pc"]),int(r["raw"])) for r in rows
                      if instruction_name(int(r["raw"]),int(r["length"]),int(r["expanded"])) in A_OPS.values()]
        a_retire=[(int(r[2],16),int(r[3],16)) for r in side["A RETIRE"]]
        require(a_retire==atomic_trace,f"{test_id}: DUT atomic lifecycle events disagree with matched architectural trace")
        if a_path.is_file() and golden_a.is_file():
            a_rows=read_csv(a_path); g_rows=read_csv(golden_a)
            require(a_rows == g_rows and len(a_rows)==len(side["A RETIRE"]),f"{test_id}: DUT/ISS atomic sidecars or DUT atomic events differ")
        else:
            require(stage=="stage8",f"{test_id}: atomic reference sidecars are required for {stage}")
    z_types={"Z CSR_ACCESS":"ARCH.Z.CSR_ACCESS","Z CSR_WRITE":"ARCH.Z.CSR_WRITE","Z FENCEI":"ARCH.Z.FENCEI"}
    for event,bin_id in z_types.items(): bump(bin_id,len(side.get(event,[])))
    bump("ARCH.Z.CSR_ILLEGAL_FAULT",len(side.get("Z CSR_FAULT",[])))
    if "M TRAP" in side or "M IRQ" in side or "M MRET" in side:
        bump("PRIV.MRET",len(side.get("M MRET",[])))
        trap_path=outdir/f"{name}.pipe.trap.tsv"; golden_trap=outdir/f"{name}.golden.trap.tsv"
        require(trap_path.is_file() and golden_trap.is_file(),f"{test_id}: machine trap evidence missing")
        trap_rows=read_csv(trap_path); golden_trap_rows=read_csv(golden_trap)
        require(trap_rows==golden_trap_rows,f"{test_id}: DUT and golden trap sidecars differ")
        op_traps=trap_instruction_bins(trap_rows)
        fault_rows={(int(ev[2],16),int(ev[3],16),int(ev[5])) for ev in side.get("C FAULT",[])}
        for ev in trap_rows:
            raw=int(ev["raw"],16); mcause=int(ev["mcause"],16); cause=mcause&0x7fffffff
            if mcause&0x80000000: continue
            if raw==0x73 and cause==11:
                require((int(ev["fault_pc"],16),raw,1) in fault_rows,f"{test_id}: ECALL trap lacks matching DUT fault event")
            if raw==0x00100073 and cause==3:
                require((int(ev["fault_pc"],16),raw,2) in fault_rows,f"{test_id}: EBREAK trap lacks matching DUT fault event")
        for bin_id,count in op_traps.items(): bump(bin_id,count)
        for ev in trap_rows:
            mcause=int(ev["mcause"],16); cause=mcause&0x7fffffff
            if mcause&0x80000000: bump(f"PRIV.IRQ.CAUSE.{cause}")
            else: bump(f"PRIV.TRAP.CAUSE.{cause}")
        if trap_rows: bump("PRIV.MACHINE_MODE")
        for ev in side.get("M DIV_ABORT",[]):
            bump("PIPE.DIV.ABORT")
            pc,raw=int(ev[2],16),int(ev[3],16)
            key=(pc,raw,4)
            if key in lifecycle["ambiguous_attempt_keys"]:
                unavailable_reasons["PIPE.DIV.RESTART"]="Abort and restart records share a static identity with overlapping ordered occurrences; producer has no dynamic lifecycle ID"
            else:
                abort_at=next(i for i,(_,row) in enumerate(ordered_side) if row is ev)
                attempted_after=[i for i,(event,row) in enumerate(ordered_side) if i>abort_at and event=="C ATTEMPT" and (int(row[2],16),int(row[3],16),int(row[4]))==key]
                if any(event=="C RETIRE" and (int(row[2],16),int(row[3],16),int(row[4]))==key
                       for attempt_at in attempted_after for event,row in ordered_side[attempt_at+1:]):
                    bump("PIPE.DIV.RESTART")
    elif stage!="stage8":
        # Stage 5/6 do not emit machine trap TSVs; their enabled DUT fault
        # records plus a passing cause==expect log establish synchronous ends.
        for ev in side.get("C FAULT",[]):
            raw=int(ev[3],16); cause=int(ev[5])
            if raw==0x00000073 and cause==1: bump("ARCH.OP.ECALL")
            elif raw==0x00100073 and cause==2: bump("ARCH.OP.EBREAK")
    iss_path=None
    if stage=="stage5" and (suite=="rv32im" or reconstructed_m_dir is not None):
        iss_path=((outdir/"iss") if suite=="rv32im" else reconstructed_m_dir)/f"{name}.iss.m.tsv"
        require(iss_path.is_file(),f"{test_id}: independent ISS M operand evidence missing")
        iss_m=read_csv(iss_path)
        rtl_m=side.get("M",[])
        if not legacy_c_disabled:
            require(len(iss_m)==len(rtl_m),f"{test_id}: ISS/DUT M issue row counts differ")
        trace_m=[r for r in rows if legacy_m_coverage._op(int(r["expanded"])) is not None]
        require(len(trace_m)==len(iss_m),f"{test_id}: ISS M operand rows do not match retired trace")
        for i,(ir,tr) in enumerate(zip(iss_m,trace_m)):
            pc,insn=int(ir["pc"],16),int(ir["insn"],16)
            op=legacy_m_coverage._op(insn)
            require(op is not None and int(ir["op"])==(insn>>12)&7,f"{test_id}: invalid ISS M operation record")
            if not legacy_c_disabled:
                rr=rtl_m[i]
                require((int(rr[1],16),int(rr[2],16),int(rr[3],16),int(rr[4],16))==(pc,insn,int(ir["a"],16),int(ir["b"],16)),
                        f"{test_id}: DUT and ISS M issue operands differ at pc={pc:08x}")
            require((int(tr["pc"]),int(tr["raw"]))==(pc,insn),f"{test_id}: ISS M issue does not align to DUT/golden retirement")
            result=int(ir["result"],16); trace_value=int(tr["rdval"])
            require(trace_value==(result if int(ir["rd"]) else 0),f"{test_id}: ISS M result differs from matched golden trace")
            for legacy_id in legacy_m_coverage._arch_operand_bins(insn,int(ir["a"],16),int(ir["b"],16)):
                bump(legacy_id)
            for legacy_id in legacy_m_coverage._arch_corner_bins(insn,int(ir["a"],16),int(ir["b"],16),result):
                bump(legacy_id)
            if not legacy_c_disabled:
                for src,col in (("RS1",5),("RS2",6)):
                    forward=int(rr[col])
                    if forward==1:
                        bump(f"P.FWD.{src}.EXMEM"); bump(f"PIPE.M.FWD.{src}.EXMEM")
                    elif forward==2:
                        bump(f"P.FWD.{src}.MEMWB"); bump(f"PIPE.M.FWD.{src}.MEMWB")
                    else: require(forward==0,f"{test_id}: invalid M forwarding selection {forward}")
    for event in ("ISSUE","COMPLETE","RETIRE","SQUASH_REDIRECT","SQUASH_FAULT_IDEX","SQUASH_FAULT_IFID","FAULT_DIV_SUPPRESS","LOAD_USE_RS1","LOAD_USE_RS2","DIV_CONSECUTIVE"):
        for ev in side.get("EV "+event,[]):
            pc,raw=int(ev[2],16),int(ev[3],16); op=legacy_m_coverage._op(raw)
            if event in ("ISSUE","COMPLETE","RETIRE"):
                require(op is not None,f"{test_id}: {event} does not reference an M instruction")
                bump(f"PIPE.M.{event}.{op}")
                if stage=="stage5": bump(f"P.{event}.{op}")
                if event in ("ISSUE","RETIRE") and ((raw>>7)&31)==0 and stage=="stage5": bump("P.RD.X0")
            elif event=="SQUASH_REDIRECT":
                if op is not None:
                    bump("PIPE.M.SQUASH.REDIRECT")
                    if stage=="stage5": bump("P.SQUASH.REDIRECT.M")
                    if op in ("DIV","DIVU","REM","REMU"):
                        bump("PIPE.M.DIV.WRONG_PATH_SUPPRESSED")
                        if stage=="stage5": bump("P.DIV.WRONG_PATH_SUPPRESSED")
            elif event in ("SQUASH_FAULT_IDEX","SQUASH_FAULT_IFID"):
                if op is not None:
                    bump("PIPE.M.SQUASH.FAULT")
                    if stage=="stage5": bump("P.SQUASH.FAULT.M")
            elif event=="FAULT_DIV_SUPPRESS":
                require(op in ("DIV","DIVU","REM","REMU"),f"{test_id}: DIV suppression event names non-DIV instruction")
                bump("PIPE.M.FAULT.DIV_START_SUPPRESSED")
                if stage=="stage5": bump("P.FAULT.DIV_START_SUPPRESSED")
            elif event=="LOAD_USE_RS1":
                require(op is not None,f"{test_id}: load-use RS1 event names non-M instruction")
                bump("PIPE.M.LOAD_USE.RS1")
                if stage=="stage5": bump("P.LOAD_USE.RS1")
            elif event=="LOAD_USE_RS2":
                require(op is not None,f"{test_id}: load-use RS2 event names non-M instruction")
                bump("PIPE.M.LOAD_USE.RS2")
                if stage=="stage5": bump("P.LOAD_USE.RS2")
            elif event=="DIV_CONSECUTIVE":
                require(op in ("DIV","DIVU","REM","REMU"),f"{test_id}: consecutive-divider event names non-DIV instruction")
                bump("PIPE.DIV.CONSECUTIVE")
                if stage=="stage5": bump("P.DIV.CONSECUTIVE")
    for event in ("ISSUE","COMPLETE","RETIRE"):
        for ev in side.get("EV "+event,[]):
            raw=int(ev[3],16); op=legacy_m_coverage._op(raw)
            if op in ("DIV","DIVU","REM","REMU"): bump(f"PIPE.DIV.{event}")
    # Keep the proof source concise and content-addressed for downstream ingest.
    srcs=[pipe,golden,outdir/f"{name}.pipe.log"]
    if side_path.is_file(): srcs.append(side_path)
    if iss_path is not None: srcs.append(iss_path)
    for suffix in (".pipe.trap.tsv",".pipe.a.tsv",".pipe.z.tsv"):
        p=outdir/f"{name}{suffix}"
        if p.is_file(): srcs.append(p)
    identity["evidence_sha256"] = hashlib.sha256("\n".join(hashlib.sha256(p.read_bytes()).hexdigest() for p in srcs).encode()).hexdigest()
    identity["evidence_sources"] = ";".join(p.name for p in srcs)
    identity["validation_report"] = report.name
    identity["validation_report_sha256"] = hashlib.sha256(report.read_bytes()).hexdigest()
    identity["validated_source_provenance_sha256"] = hashlib.sha256(report.read_bytes()).hexdigest()
    unavailable=[]
    if stage=="stage5":
        # Legacy Stage 5's runner did not pass MCOV for rv32im. Architectural
        # retirement and the 16 RTL COV counters remain evidenced; detailed
        # attempt/fault/squash/forward/divider events were not recorded.
        for b in load_dictionary():
            state,reason=bin_evidence_policy(b,config,stage,detailed_pipeline=not legacy_c_disabled,
                                               m_operand_reference=(reconstructed_m_dir is not None or suite=="rv32im"))
            if state=="unavailable": unavailable_reasons[b["bin_id"]]=reason
        if legacy_c_disabled and not side_path.is_file():
            for bin_id in ("ARCH.OP.ECALL","ARCH.OP.EBREAK"):
                unavailable_reasons[bin_id]="Saved legacy producer has no DUT fault sidecar identifying the trapping instruction; terminal cause alone cannot distinguish ECALL from EBREAK"
    return {"identity":identity,"counts":counts,"unavailable_bins":list(unavailable_reasons),"unavailable_reasons":unavailable_reasons}


def audit_saved_evidence(index: dict) -> None:
    """Audit required and configuration-inapplicable sidecars before parsing any test."""
    totals=collections.Counter(); missing=[]; case_count=0
    def demand(outdir: Path, name: str, stage: str, suffix: str, required: bool, label: str) -> None:
        path=evidence_path(outdir,name,stage,suffix)
        key=(label,"required" if required else "inapplicable")
        totals[key]+=1
        if required and not path.is_file(): missing.append(str(path))
    for sim in ("verilator","xsim"):
        items=index["simulators"][sim]
        out=ROOT/items["stage5"]["outdir"]
        legacy_out=ROOT/items["stage5"].get("legacy_outdir",items["stage5"]["outdir"])
        for row in read_stage5_manifests(out):
            case_count+=1; name=row["name"]; suite=row["suite"]
            producer_out=legacy_out if suite=="rv32im" else out
            policy=stage5_sidecar_policy(suite)
            if suite=="rv32im" and producer_out!=out: policy[".pipe.ccov"]=True
            for suffix,required in policy.items():
                totals[(f"Stage5 {suffix[1:]}","required" if required else "inapplicable")]+=1
                missing.extend(check_required_sidecars(producer_out,name,policy))
        out=ROOT/items["stage6"]["outdir"]
        names=sorted(p.name[:-len(".pipe.trace")] for p in out.glob("stage6_*.pipe.trace"))
        require(len(names)==11 and len(set(names))==11,"Stage 6 inventory must contain 11 cases before evidence audit")
        for name in names:
            case_count+=1
            for suffix in (".pipe.mcov",".pipe.a.tsv",".golden.a.tsv"):
                demand(out,name,"stage6",suffix,True,f"Stage6 {suffix[1:]}")
            demand(out,name,"stage6",".pipe.ccov",False,"Stage6 pipe.ccov")
        out=ROOT/items["stage8"]["outdir"]
        names=sorted(p.name[:-len(".pipe.trace")] for p in out.glob("*.pipe.trace"))
        require(len(names)==23 and len(set(names))==23,"Stage 8 inventory must contain 23 cases before evidence audit")
        for name in names:
            case_count+=1
            for suffix in (".pipe.mcov",".pipe.trap.tsv",".golden.trap.tsv"):
                demand(out,name,"stage8",suffix,True,f"Stage8 {suffix[1:]}")
            for suffix in (".pipe.ccov",".pipe.a.tsv",".golden.a.tsv"):
                demand(out,name,"stage8",suffix,False,f"Stage8 {suffix[1:]}")
    print(f"STAGE9_EVIDENCE_AUDIT cases_per_sim=282 simulator_case_observations={case_count}")
    for (label,state),count in sorted(totals.items()): print(f"  {label} {state}={count}")
    if missing:
        print(f"  missing_required={len(missing)}")
        for path in missing: print(f"  MISSING {path}")
        raise ValueError(f"saved evidence audit found {len(missing)} missing required files")
    print("  missing_required=0")


def stage5_sidecar_policy(suite: str) -> dict[str,bool]:
    """Producer-specific required evidence for saved Stage 5 suite modes."""
    c_enabled=suite!="rv32im"
    a_enabled=suite.startswith("rv32ima") or suite.startswith("rv32imac")
    return {".pipe.ccov":c_enabled,".pipe.a.tsv":a_enabled,".golden.a.tsv":a_enabled}


def bin_evidence_policy(bin_row: dict[str,str], config: str, stage: str = "stage5",
                        detailed_pipeline: bool = False,
                        m_operand_reference: bool = False) -> tuple[str,str]:
    """Return required, unavailable, or inapplicable evidence for a bin/config producer."""
    if config not in bin_row["applicable_configurations"].split("|") or bin_row["reachability"]!="reachable":
        return "inapplicable", ""
    if stage=="stage5" and config==CONFIGS["rv32im"] and not detailed_pipeline and bin_row["coverage_class"] in ("microarchitectural","historical_block_protocol") and bin_row["bin_id"] not in ("PIPE.RETIRED","P.RETIRED") and not bin_row["bin_id"].startswith("P.PIPE_EVENT."):
        return "unavailable", "Stage 5 rv32im producer emitted no detailed pipeline sidecar; trace/log do not encode this event"
    if stage=="stage5" and config!=CONFIGS["rv32im"] and not m_operand_reference and bin_row["bin_id"] in legacy_m_coverage._bins() and bin_row["bin_id"].startswith("A."):
        return "unavailable", "Stage 5 C/A producer has no per-test ISS M operand sidecar required for this historical architectural bin"
    return "required", bin_row["evidence_source"]


def check_required_sidecars(outdir: Path, name: str, policy: dict[str,bool]) -> list[str]:
    """Return missing producer-required sidecar paths; inapplicable files are ignored."""
    return [str(path) for suffix,required in policy.items()
            if required and not (path:=evidence_path(outdir,name,"stage5",suffix)).is_file()]


def applicable(bin_row: dict[str,str], config: str) -> bool:
    return bin_row["reachability"]=="reachable" and config in bin_row["applicable_configurations"].split("|")


def config_applicable(bin_row: dict[str,str], config: str) -> bool:
    return config in bin_row["applicable_configurations"].split("|")


def load_dictionary(path: Path = DICT_PATH) -> list[dict[str,str]]:
    if not path.is_file(): write_dictionary(path)
    rows=read_csv(path)
    required={"bin_id","dictionary_version","coverage_class","definition","applicable_configurations","evidence_source","reachability","reachability_reason"}
    require(set(rows[0]) == required if rows else False,f"dictionary schema mismatch: {path}")
    ids=[r["bin_id"] for r in rows]
    require(len(ids)==len(set(ids)),"duplicate dictionary bin IDs")
    require(all(r["dictionary_version"]==DICTIONARY_VERSION for r in rows),"inconsistent dictionary version")
    return rows


def validate_observations(observations: list[dict], bins: list[dict[str,str]]) -> None:
    ids={r["bin_id"]:r for r in bins}
    seen=set()
    for obs in observations:
        require(isinstance(obs,dict) and set(obs) in ({"identity","counts"},{"identity","counts","unavailable_bins"},{"identity","counts","unavailable_bins","unavailable_reasons"}) and isinstance(obs.get("identity"),dict)
                and isinstance(obs.get("counts"),dict),"malformed observation record")
        unavailable=obs.get("unavailable_bins",[])
        require(isinstance(unavailable,list) and len(unavailable)==len(set(unavailable)),"malformed unavailable-bin list")
        reasons=obs.get("unavailable_reasons",{b:"Evidence unavailable" for b in unavailable})
        require(isinstance(reasons,dict) and set(reasons)==set(unavailable) and all(isinstance(v,str) and v for v in reasons.values()),
                "unavailable-bin reasons are missing or malformed")
        ident=obs["identity"]
        required={"test_id","simulator","configuration","scenario","seed","dictionary_version","schema_version",
                  "observed_cycles","runtime_seconds","status","validation_status","evidence_sha256","evidence_sources",
                  "validation_report","validation_report_sha256","validated_source_provenance_sha256"}
        require(required.issubset(ident),"observation missing required identity/provenance fields")
        require(ident.get("test_id") and ident.get("scenario") and ident.get("simulator") in ("xsim","verilator"),"malformed test identity/configuration/scenario")
        require(re.fullmatch(r"[0-9a-f]{64}",ident["evidence_sha256"]) is not None and ident["evidence_sources"],
                "observation missing valid evidence provenance")
        require(re.fullmatch(r"[0-9a-f]{64}",ident["validation_report_sha256"]) is not None and
                ident["validated_source_provenance_sha256"]==ident["validation_report_sha256"],
                "observation validation report provenance is malformed")
        key=(ident["simulator"],ident["test_id"])
        require(key not in seen,f"duplicate test identity: {key}")
        seen.add(key)
        require(ident["schema_version"]==SCHEMA_VERSION and ident["dictionary_version"]==DICTIONARY_VERSION,"inconsistent observation/schema version")
        require(ident["validation_status"]=="PASS" and ident["status"]=="PASS","invalid run cannot contribute coverage")
        require(ident["configuration"] in CONFIGS.values(),f"unknown configuration: {ident['configuration']}")
        require(isinstance(ident["observed_cycles"],int) and ident["observed_cycles"]>0,"invalid observed cycle count")
        for bin_id,count in obs["counts"].items():
            require(bin_id in ids,f"unknown coverage bin: {bin_id}")
            require(applicable(ids[bin_id],ident["configuration"]),f"bin {bin_id} not applicable to {ident['configuration']}")
            require(isinstance(count,int) and count>0,f"malformed bin count for {bin_id}")
            require(bin_id not in unavailable,f"bin {bin_id} is both observed and unavailable")
        for bin_id in unavailable:
            require(bin_id in ids and applicable(ids[bin_id],ident["configuration"]),
                    f"unavailable bin {bin_id} is unknown or inapplicable")


def aggregate_observations(observations: list[dict], bins: list[dict[str,str]]) -> list[dict]:
    """Aggregate once per validated test identity; callers cannot silently double count retries."""
    validate_observations(observations,bins)
    aggregate={b["bin_id"]:{"applicable_tests":0,"evidence_tests":0,"unavailable_tests":0,"hit_tests":0,"event_count":0,"reasons":set()} for b in bins}
    bin_map={b["bin_id"]:b for b in bins}
    for obs in observations:
        config=obs["identity"]["configuration"]
        for bin_id,b in bin_map.items():
            if config_applicable(b,config):
                vals=aggregate[bin_id]
                aggregate[bin_id]["applicable_tests"]+=1
                if b["reachability"]!="reachable": continue
                if bin_id in obs.get("unavailable_bins",[]):
                    vals["unavailable_tests"]+=1
                    vals["reasons"].add(obs.get("unavailable_reasons",{}).get(bin_id,"Evidence unavailable"))
                else:
                    count=obs["counts"].get(bin_id,0)
                    vals["evidence_tests"]+=1
                    vals["hit_tests"]+=int(count>0)
                    vals["event_count"]+=count
    result=[]
    for b in bins:
        vals=aggregate[b["bin_id"]]
        if b["reachability"] in ("unsupported","not_targeted","unreachable"): status=b["reachability"].upper()
        elif vals["applicable_tests"]==0: status="NOT_APPLICABLE"
        elif vals["evidence_tests"]==0: status="UNAVAILABLE_EVIDENCE"
        elif vals["hit_tests"]: status="HIT"
        else: status="GAP_REACHABLE"
        reason_text="; ".join(sorted(vals.pop("reasons")))
        result.append({**{k:b[k] for k in ("bin_id","coverage_class","definition","reachability","reachability_reason")},**vals,
                       "availability_reasons":reason_text,
                       "hit_rate":f"{vals['hit_tests']/vals['evidence_tests']:.6f}" if vals["evidence_tests"] else "","status":status})
    return result


def write_csv(path: Path, fields: list[str], rows: list[dict]) -> None:
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=fields,extrasaction="raise",lineterminator="\n")
        w.writeheader(); w.writerows(rows)


def export(sim: str, prepared: Path, stage5_gap_dir: Path | None = None,
           stage5_gap_report: Path | None = None) -> None:
    idx=json.loads(prepared.read_text(encoding="utf-8"))
    require(idx.get("schema_version")==SCHEMA_VERSION,"prepared index schema mismatch")
    require(idx.get("base_commit")=="fcc151dccc4e8e98b4b70ba52871c8a0594a4967","prepared evidence base is not approved stage8-complete")
    for stage in ("stage5","stage6","stage8"):
        validate_provenance_record(idx["simulators"][sim][stage],f"prepared {sim} {stage}")
    validate_provenance_record(idx["simulators"][sim]["stage5"],f"prepared {sim} stage5")
    legacy_record={"source_provenance_status":idx["simulators"][sim]["stage5"].get("legacy_source_provenance_status"),
                   "unresolved_source_hashes":idx["simulators"][sim]["stage5"].get("legacy_unresolved_source_hashes")}
    validate_provenance_record(legacy_record,f"prepared {sim} legacy supplemental")
    audit_saved_evidence(idx)
    bins=load_dictionary()
    observations=[]
    for stage in ("stage5","stage6","stage8"):
        item=idx["simulators"][sim][stage]
        report=ROOT/item["report"]
        require(hashlib.sha256(report.read_bytes()).hexdigest()==item["report_sha256"],f"prepared validation report changed: {report}")
        report_text=report.read_text(encoding="utf-8",errors="replace")
        require(item["pass_marker"] in report_text,f"validation report is not PASS: {report}")
        provenance=validate_report_provenance(report,report_text,sim)
        require(provenance["source_hashes_checked"]>0,
                f"validation report lacks source provenance: {report}")
        provenance_path=resolve_workspace_path(item["provenance"]).resolve()
        require(provenance_path==Path(provenance["provenance_path"]).resolve(),
                f"prepared provenance reference changed: {report}")
        require(provenance_hash_matches(provenance_path,item["provenance_sha256"]),
                f"prepared provenance file changed: {provenance_path}")
        if stage=="stage5":
            manifest=read_stage5_manifests(ROOT/item["outdir"])
            require(len(manifest)==248 and len({r["name"] for r in manifest})==248,
                    "Stage 5 combined manifest count/identity error")
            reconstructed_item=item.get("reconstructed_m_reference")
            reconstructed_m_dir=(validate_stage5_iss_replay(reconstructed_item,sim,ROOT/item["outdir"])
                                 if reconstructed_item else None)
            require(reconstructed_m_dir is not None,
                    "Stage 5 C/A M-operand observations require validated reconstructed ISS evidence")
            gap_dir=ROOT/item["legacy_outdir"] if item.get("legacy_outdir") else (stage5_gap_dir.resolve() if stage5_gap_dir is not None else None)
            gap_report=ROOT/item["legacy_report"] if item.get("legacy_report") else stage5_gap_report
            evidence_dirs=stage5_evidence_selection(manifest,ROOT/item["outdir"],gap_dir)
            for row in manifest:
                name=row["name"]
                test_out=evidence_dirs[name]; test_report=report
                if test_out==gap_dir and gap_dir is not None:
                    require(gap_report is not None and gap_report.is_file(),"Stage 5 legacy gap report is required with its run directory")
                    gap_report=gap_report.resolve(); gap_text=gap_report.read_text(encoding="utf-8",errors="replace")
                    require(f"STAGE9_LEGACY_GAP_{sim.upper()} PASS legacy=209 full_trace_comparisons=418 dynamic_mcov=209" in gap_text,
                            f"Stage 5 legacy gap run did not pass the 209-case validation gate: {gap_report}")
                    provenance_gap=(validate_report_provenance(gap_report,gap_text,sim)
                                    if "producer_snapshot=" in gap_text
                                    else validate_saved_legacy_supplemental(gap_report,gap_text,sim))
                    require(item.get("legacy_source_provenance_status")==provenance_gap["source_provenance_status"] and
                            item.get("legacy_unresolved_source_hashes")==provenance_gap["unresolved_source_hashes"],
                            "supplemental provenance review metadata changed")
                    gap_out=gap_dir
                    od=re.search(r"^output_dir=(.+)$",gap_text,re.M)
                    require(od and resolve_workspace_path(od.group(1)).resolve()==gap_out,f"legacy gap report/output directory mismatch: {gap_report}")
                    gap_names={p.name[:-len(".pipe.trace")] for p in gap_out.glob("*.pipe.trace")}
                    require(len(gap_names)==209 and len(gap_names)==len({r["name"] for r in manifest if r["suite"]=="rv32im"}),
                            "legacy gap run must contain exactly the 209 unique legacy identities")
                    require(name in gap_names,f"legacy gap evidence is missing test {name}")
                    for suffix in (".pipe.trace",".golden.trace",".pipe.log",".pipe.mcov"):
                        required_path=evidence_path(gap_out,name,"stage5",suffix)
                        require(required_path.is_file(),f"legacy gap run missing required {required_path.suffix} evidence for {name}")
                    test_out=gap_out; test_report=gap_report
                observation=collect_test(stage,sim,test_out,name,row,row["suite"],name,None,test_report,
                                         reconstructed_m_dir)
                if test_out==gap_dir and gap_dir is not None:
                    observation["identity"]["source_provenance_status"]=item["legacy_source_provenance_status"]
                observations.append(observation)
        elif stage=="stage6":
            outdir=ROOT/item["outdir"]
            names=sorted(p.name[:-len(".pipe.trace")] for p in outdir.glob("stage6_*.pipe.trace"))
            require(len(names)==11 and len(set(names))==11,"Stage 6 test inventory incomplete or duplicated")
            for name in names: observations.append(collect_test(stage,sim,outdir,name,{},"stage6_zicsr_zifencei",name,None,report))
        else:
            outdir=ROOT/item["outdir"]
            manifest=read_csv(ROOT/item["manifest"])
            require(len(manifest)==23 and len({r["name"] for r in manifest})==23,"Stage 8 test inventory incomplete or duplicated")
            for row in manifest:
                source=Path(row["source"]).stem if row["source"] else row["name"]
                scenario=source.removeprefix("seed_")
                if row["seed"] and scenario.endswith("_"+row["seed"]): scenario=scenario[:-(len(row["seed"])+1)]
                observations.append(collect_test(stage,sim,outdir,row["name"],row,row["suite"],scenario,row["seed"] or None,report))
    validate_observations(observations,bins)
    dest=ROOT/"reports"/"stage9_coverage"/sim
    dest.mkdir(parents=True,exist_ok=True)
    observations.sort(key=lambda x:x["identity"]["test_id"])
    run_fields=list(observations[0]["identity"].keys())
    write_csv(dest/"runs.csv",run_fields,[o["identity"] for o in observations])
    long=[]; wide=[]
    bin_ids=[b["bin_id"] for b in bins]
    bin_map={b["bin_id"]:b for b in bins}
    for obs in observations:
        ident=obs["identity"]; counts=obs["counts"]; unavailable=set(obs.get("unavailable_bins",[]))
        vector={"test_id":ident["test_id"],"simulator":sim,"configuration":ident["configuration"],
                "scenario":ident["scenario"],"seed":ident["seed"],"dictionary_version":DICTIONARY_VERSION,
                "schema_version":SCHEMA_VERSION,"evidence_sha256":ident["evidence_sha256"],
                "validation_status":ident["validation_status"]}
        for b in bins:
            if not config_applicable(b,ident["configuration"]): continue
            if b["reachability"]!="reachable":
                state=b["reachability"].upper()
                long.append({"test_id":ident["test_id"],"simulator":sim,"configuration":ident["configuration"],
                             "scenario":ident["scenario"],"seed":ident["seed"],"dictionary_version":DICTIONARY_VERSION,
                             "schema_version":SCHEMA_VERSION,"evidence_sha256":ident["evidence_sha256"],"bin_id":b["bin_id"],
                             "bin_hit":"","bin_count":"","validation_status":state,
                             "availability_reason":b["reachability_reason"]})
                vector[f"bin_{b['bin_id']}"]=""
                continue
            if b["bin_id"] in unavailable:
                reasons=obs.get("unavailable_reasons",{})
                long.append({"test_id":ident["test_id"],"simulator":sim,"configuration":ident["configuration"],
                             "scenario":ident["scenario"],"seed":ident["seed"],"dictionary_version":DICTIONARY_VERSION,
                             "schema_version":SCHEMA_VERSION,"evidence_sha256":ident["evidence_sha256"],"bin_id":b["bin_id"],
                             "bin_hit":"","bin_count":"","validation_status":"UNAVAILABLE_EVIDENCE",
                             "availability_reason":reasons.get(b["bin_id"],"")})
                vector[f"bin_{b['bin_id']}"]=""
                continue
            count=counts.get(b["bin_id"],0)
            long.append({"test_id":ident["test_id"],"simulator":sim,"configuration":ident["configuration"],
                         "scenario":ident["scenario"],"seed":ident["seed"],"dictionary_version":DICTIONARY_VERSION,
                         "schema_version":SCHEMA_VERSION,"evidence_sha256":ident["evidence_sha256"],"bin_id":b["bin_id"],
                         "bin_hit":int(count>0),"bin_count":count,"validation_status":ident["validation_status"],"availability_reason":""})
            vector[f"bin_{b['bin_id']}"]=int(count>0)
        wide.append(vector)
    coverage_fields=["test_id","simulator","configuration","scenario","seed","dictionary_version","schema_version","evidence_sha256","bin_id","bin_hit","bin_count","validation_status","availability_reason"]
    write_csv(dest/"coverage_long.csv",coverage_fields,long)
    write_csv(dest/"coverage.csv",["test_id","simulator","configuration","scenario","seed","dictionary_version","schema_version","evidence_sha256","validation_status"]+[f"bin_{b}" for b in bin_ids],wide)
    agg_rows=aggregate_observations(observations,bins)
    write_csv(dest/"aggregate.csv",["bin_id","coverage_class","definition","reachability","reachability_reason","applicable_tests","evidence_tests","unavailable_tests","availability_reasons","hit_tests","event_count","hit_rate","status"],agg_rows)
    classes=collections.defaultdict(lambda:[0,0,0])
    for r in agg_rows:
        if r["reachability"] in ("unsupported","not_targeted","unreachable"): continue
        c=classes[r["coverage_class"]]; c[0]+=1; c[1]+=r["status"]=="HIT"; c[2]+=r["status"]=="GAP_REACHABLE"
    gap_rows=[r for r in agg_rows if r["status"]=="GAP_REACHABLE"]
    unavailable_observation_count=sum(len(o.get("unavailable_bins",[])) for o in observations)
    partial=[o["identity"]["test_id"] for o in observations if o["identity"].get("source_provenance_status")!="PASS"]
    targeted_status=("ALL_REACHABLE_TARGETED_BINS_HIT" if not gap_rows and not unavailable_observation_count
                     else "OPEN_REACHABLE_GAPS_OR_UNAVAILABLE_EVIDENCE")
    per_test_status="COMPLETE" if not unavailable_observation_count else "INCOMPLETE"
    strict_status="BLOCKED" if partial else "PASS"
    privileged_bins=[b for b in bins if b["coverage_class"]=="architectural_privileged"]
    privileged_targeted=sum(b["reachability"]=="reachable" for b in privileged_bins)
    wfi=next((b for b in privileged_bins if b["bin_id"]=="ARCH.OP.WFI"),None)
    lines=[f"STAGE9_COVERAGE_{sim.upper()} PASS schema={SCHEMA_VERSION} dictionary={DICTIONARY_VERSION} observations={len(observations)}",
           "Coverage is DUT-observed, gated by passing per-test logs and complete DUT/ISS golden trace equality.",
           "Architectural and microarchitectural coverage are separate; simulator code coverage was not collected.",
           f"targeted_bin_status={targeted_status} reachable_gaps={len(gap_rows)}",
           f"per_test_evidence_status={per_test_status} observations={len(observations)} unavailable_bin_observations={unavailable_observation_count}",
           f"strict_provenance_closure={strict_status} unresolved_test_identities={len(partial)}",
           f"architectural_privileged_bins_original={len(privileged_bins)} reachable_targeted={privileged_targeted} excluded_wfi={wfi['reachability'] if wfi else 'missing'}",
           f"coverage_closure={'OPEN' if gap_rows or unavailable_observation_count or partial else 'CLOSED'}",
           f"valid_tests={len(observations)} failed_or_incomplete_excluded=0 duplicate_identities=0"]
    if partial:
        lines.append(f"SOURCE_PROVENANCE_REVIEW partial={len(partial)} status=DOCUMENTED_LIMITATION_RUNNER_SNAPSHOT_UNAVAILABLE strict_provenance_closure=BLOCKED")
        lines.append("SOURCE_PROVENANCE_IDS "+",".join(partial))
    for c,(den,hits,gaps) in sorted(classes.items()): lines.append(f"{c} bins_hit={hits}/{den} reachable_gaps={gaps}")
    lines += [f"GAP {r['bin_id']} applicable={r['applicable_tests']}" for r in agg_rows if r["status"]=="GAP_REACHABLE"]
    lines += [f"UNAVAILABLE {r['bin_id']} applicable={r['applicable_tests']} evidence={r['evidence_tests']} unavailable={r['unavailable_tests']} reason={r['availability_reasons']}" for r in agg_rows if r["unavailable_tests"]]
    lines += [f"CLASSIFIED {r['bin_id']} state={r['status']} reason={r['availability_reasons'] or r['reachability_reason']}" for r in agg_rows if r["status"] in ("UNSUPPORTED","NOT_TARGETED","UNREACHABLE","UNAVAILABLE_EVIDENCE")]
    (dest/"report.txt").write_text("\n".join(lines)+"\n",encoding="utf-8",newline="\n")
    print("\n".join(lines))


def main() -> int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sim",required=True,choices=("xsim","verilator"))
    parser.add_argument("--prepared",required=True,type=Path)
    parser.add_argument("--stage5-legacy-gap-dir",type=Path)
    parser.add_argument("--stage5-legacy-gap-report",type=Path)
    args=parser.parse_args()
    require(bool(args.stage5_legacy_gap_dir)==bool(args.stage5_legacy_gap_report),"Stage 5 legacy gap run directory and report must be supplied together")
    export(args.sim,args.prepared.resolve(),args.stage5_legacy_gap_dir,args.stage5_legacy_gap_report)
    return 0


if __name__=="__main__":
    try: raise SystemExit(main())
    except (ValueError,OSError,KeyError,TypeError) as exc:
        print(f"STAGE9_COVERAGE INVALID {type(exc).__name__}: {exc}",file=sys.stderr)
        raise SystemExit(1)
