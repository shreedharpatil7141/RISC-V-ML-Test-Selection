#!/usr/bin/env python3
"""Preflight the Stage 6 compatibility inventory and M-mode reference cases."""
import csv, hashlib, subprocess, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
import rv32c_asm, rv32imc_iss


def fail(message):
    raise SystemExit("STAGE7_PREPARE FAIL: " + message)


def main():
    if len(sys.argv) != 2:
        fail(f"usage: {Path(sys.argv[0]).name} <fresh-output-directory>")
    out = Path(sys.argv[1]).resolve()
    if out.exists() and any(out.iterdir()): fail(f"output directory not fresh: {out}")
    out.mkdir(parents=True, exist_ok=True)
    compat = out / "stage6_compat"
    prep = subprocess.run([sys.executable, str(HERE / "prepare_stage6.py"), str(compat)],
                          cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    (out / "stage6_compat.log").write_text(prep.stdout, encoding="utf-8", newline="\n")
    marker = "STAGE6_PREPARATION PASS stage5=248 stage6=11 total=259 images=259 references=259 errors=0"
    if prep.returncode or marker not in prep.stdout: fail("Stage 6 compatibility preflight failed")
    test = subprocess.run([sys.executable, str(HERE / "stage7_software_selftest.py")],
                          cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    (out / "software_selftest.log").write_text(test.stdout, encoding="utf-8", newline="\n")
    if test.returncode or "STAGE7_SOFTWARE_SELFTEST PASS" not in test.stdout:
        fail("independent M-mode software selftest failed")

    suite = ROOT / "tests/directed/rv32imac_stage7"
    rows = list(csv.DictReader((suite / "manifest.csv").open(newline="")))
    if len(rows) != 13 or len({r["name"] for r in rows}) != len(rows):
        fail(f"expected thirteen unique Stage 7 cases; found {len(rows)}")
    image_dir, ref_dir = out / "m_hex", out / "m_iss"
    image_dir.mkdir(); ref_dir.mkdir()
    inventory, errors = [], []
    for row in rows:
        name, source_path = row["name"], suite / row["source"]
        if not source_path.is_file(): errors.append(f"missing {source_path}"); continue
        try:
            byte_mem = rv32c_asm.assemble_bytes(source_path.read_text(encoding="ascii"), c_enabled=True, a_enabled=True)
            words = rv32c_asm.to_words(byte_mem)
            irq_pc = int(row["irq_pc"], 16) if row["irq_pc"] else None
            schedule = []
            if irq_pc is not None:
                base_traps = []
                base_run = rv32imc_iss.run(words, c_enabled=True, a_enabled=True,
                                           z_enabled=True, machine_enabled=True,
                                           machine_events=base_traps)
                base_pcs = [int(line.split()[1], 16) for line in base_run[2]]
                base_boundaries = base_pcs + [event[0] for event in base_traps]
                if irq_pc not in base_boundaries:
                    errors.append(f"{name}: scheduled IRQ PC {irq_pc:08x} is not executed; "
                                  f"retired={[line.split()[1:4] for line in base_run[2]]} traps={base_traps}")
                irq_ordinal = sum(1 for address in base_pcs if address < irq_pc)
                schedule = [(irq_ordinal, int(row["irq_levels"]))]
            trap_events, z_events = [], []
            cause, regs, trace, footer, oob, retired = rv32imc_iss.run(
                words, c_enabled=True, a_enabled=True, z_enabled=True, machine_enabled=True,
                irq_schedule=schedule, machine_events=trap_events, z_events=z_events)
            retired_insns=[f"{int(line.split()[1],16):08x}/{int(line.split()[3])}:{line.split()[2]}" for line in trace]
            trapped_insns=[f"{e[0]:08x}/{(0 if e[1] == 0 and (e[2]&0x7fffffff)==1 else (2 if e[1]&3 != 3 else 4))}:{e[1]:08x}"
                           for e in trap_events]
            diag = (f"retired_pc_len_raw={retired_insns} trap_pc_len_raw={trapped_insns} "
                    f"csr={[line for line in footer if line.startswith('CSR ')]} "
                    f"schedule={schedule} traps={trap_events}")
            if cause != 0 or oob: errors.append(f"{name}: expected completion cause=0/oob=0 actual cause={cause}/oob={oob}; {diag}")
            if name == "irq_vectored_priority" and (not trap_events or trap_events[0][4] != 0xAC or
                                                       (trap_events[0][2] & 0x7fffffff) != 11):
                errors.append(f"{name}: expected external vectored target 000000ac/cause11; {diag}")
            if name == "machine_trap_return" and [(e[0],e[2]&0x7fffffff,e[3]) for e in trap_events] != [
                    (28,2,0xCC1021F3),(32,11,0),(36,3,0)]:
                errors.append(f"{name}: expected illegal/ECALL/EBREAK trap sequence; {diag}")
            if name == "irq_mask_pending" and (regs[3] != 0x800 or len(trap_events) != 1 or
                                                trap_events[0][0] != 0x20 or trap_events[0][4] != 0x80 or
                                                regs[5] != 1):
                errors.append(f"{name}: expected regs3=00000800, one external trap at PC 00000020/vector 00000080, and resumed x5=1; actual regs3={regs[3]:08x} x5={regs[5]:08x}; {diag}")
            if name in ("irq_software","irq_timer") and (len(trap_events) != 1 or
                    (trap_events[0][2] & 0x7fffffff) != (3 if name == "irq_software" else 7)):
                errors.append(f"{name}: expected its enabled machine interrupt cause; {diag}")
            if name == "irq_div_restart" and (not trap_events or trap_events[0][0] != 0x20 or
                                               (regs[4] & 0xffffffff) != 12):
                errors.append(f"{name}: interrupted DIV did not restart at PC 00000020; {diag}")
            if name == "fencei_store_replace" and (regs[10] != 2 or
                    sum(1 for event in z_events if event[0] == "FENCEI") != 1):
                errors.append(f"{name}: replacement instruction/FENCE.I expectation failed x10={regs[10]}; {diag}")
            if name == "fault_before_irq" and (len(trap_events) != 2 or
                    trap_events[0][0] != 0x1c or trap_events[0][2] != 2 or
                    trap_events[1][0] != 0x20 or trap_events[1][2] != 0x8000000b):
                errors.append(f"{name}: expected illegal trap at 0000001c before external interrupt at 00000020; {diag}")
            if name == "store_fault_precision" and (len(trap_events) != 3 or
                    [(e[0],e[2],e[3]) for e in trap_events] !=
                    [(0x10,6,0x4001),(0x18,5,0x10000),(0x20,7,0x10000)]):
                errors.append(f"{name}: precise misaligned/store/load/AMO fault sequence mismatch; {diag}")
            if name == "fetch_access_trap" and (len(trap_events) != 1 or
                    (trap_events[0][0],trap_events[0][2],trap_events[0][3]) != (0x10000,1,0x10000)):
                errors.append(f"{name}: expected instruction access fault PC/mtval 00010000 (JALR base 00010000, handler mepc=00000010); {diag}")
            (image_dir / f"{name}.hex").write_text(rv32c_asm.to_hex(byte_mem), encoding="ascii", newline="\n")
            header = "TRACE_V3 RV32IMAC pc raw_insn ilen_bytes expanded_insn rd rdval st_size st_addr st_data atomic_sidecar\n"
            (ref_dir / f"{name}.trace").write_text(header + "\n".join(trace + footer) + "\n", encoding="ascii", newline="\n")
            with (ref_dir / f"{name}.trap.tsv").open("w", newline="") as f:
                w = csv.writer(f, delimiter="\t", lineterminator="\n")
                w.writerow(["fault_pc", "raw", "mcause", "mtval", "target"])
                w.writerows((f"{e[0]:08x}", f"{e[1]:08x}", f"{e[2]:08x}", f"{e[3]:08x}", f"{e[4]:08x}") for e in trap_events)
            with (ref_dir / f"{name}.z.tsv").open("w", newline="") as f:
                w = csv.writer(f, delimiter="\t", lineterminator="\n")
                w.writerow(["kind", "pc", "raw", "ilen", "csr_or_pcnext", "funct3", "source_index", "source", "old", "new", "write_intent"])
                for e in z_events:
                    if e[0] == "CSR": w.writerow([e[0], f"{e[1]:08x}", f"{e[2]:08x}", e[3], f"{e[4]:03x}", e[5], e[6], f"{e[7]:08x}", f"{e[8]:08x}", f"{e[9]:08x}", e[10]])
                    else: w.writerow([e[0], f"{e[1]:08x}", f"{e[2]:08x}", e[3], f"{e[4]:08x}", "-", "-", "-", "-", "-", "-"])
            inventory.append({"name": name, "hexpath": (image_dir / f"{name}.hex").relative_to(ROOT).as_posix(),
                              "irq_pc": row["irq_pc"], "irq_levels": row["irq_levels"], "irq_wait_div": row["irq_wait_div"],
                              "traps": len(trap_events), "retired": retired})
        except Exception as exc:
            errors.append(f"{name}: {type(exc).__name__}: {exc}")
    with (out / "m_manifest.csv").open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["name", "hexpath", "irq_pc", "irq_levels", "irq_wait_div", "traps", "retired"], lineterminator="\n")
        w.writeheader(); w.writerows(inventory)
    for row in inventory:
        for path in (ROOT / row["hexpath"], ref_dir / f"{row['name']}.trace", ref_dir / f"{row['name']}.trap.tsv", ref_dir / f"{row['name']}.z.tsv"):
            if not path.is_file() or path.stat().st_size == 0: errors.append(f"missing/empty artifact {path}")
    if errors: fail("; ".join(errors))
    sources = [HERE / "prepare_stage7.py", HERE / "prepare_stage6.py", HERE / "stage7_software_selftest.py",
               HERE / "rv32imc_iss.py", HERE / "rv32_asm.py", HERE / "rv32c_asm.py", HERE / "rv32c_model.py",
               HERE / "rv32a_model.py", HERE / "rv32i_iss.py", HERE / "stage4_4_rtl.f",
               ROOT / "rtl/packages/rv32_pkg.sv", ROOT / "rtl/packages/rv_pipe_pkg.sv",
               ROOT / "rtl/core/rv_machine_state.sv", ROOT / "rtl/core/rv_core_single.sv", ROOT / "rtl/core/rv_core_pipe.sv",
               ROOT / "rtl/pipeline/rv_if_stage.sv", ROOT / "rtl/pipeline/rv_id_stage.sv", ROOT / "rtl/pipeline/rv_ex_stage.sv",
               ROOT / "rtl/pipeline/rv_mem_stage.sv", ROOT / "rtl/decoder/rv_decoder.sv",
               ROOT / "verification/environment/tb_rv_decoder_m.sv",
               ROOT / "verification/environment/tb_rv_decoder_machine.sv", suite / "manifest.csv", *suite.glob("*.s")]
    hashes = [f"sha256 {p.relative_to(ROOT).as_posix()}={hashlib.sha256(p.read_bytes()).hexdigest()}" for p in sources]
    artifacts = [ROOT / row["hexpath"] for row in inventory]
    artifacts += [ref_dir / f"{row['name']}.{suffix}" for row in inventory for suffix in ("trace", "trap.tsv", "z.tsv")]
    artifacts += [out / "m_manifest.csv"]
    hashes += [f"artifact_sha256 {p.relative_to(ROOT).as_posix()}={hashlib.sha256(p.read_bytes()).hexdigest()}" for p in artifacts]
    (out / "stage7_preparation.txt").write_text(
        f"STAGE7_PREPARATION READY stage6_compat=259 stage7_cases={len(inventory)} images={len(inventory)} references={len(inventory)} errors=0\n" + "\n".join(hashes) + "\n",
        encoding="ascii", newline="\n")
    print((out / "stage7_preparation.txt").read_text(encoding="ascii"), end="")


if __name__ == "__main__": main()
