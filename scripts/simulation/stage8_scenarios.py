"""Deterministic Stage 8 integration scenarios with independent ISS references."""
import csv
import random
from pathlib import Path
import rv32c_asm
import rv32imc_iss

MASTER_SEED = 0x8A710008
SEED_OFFSETS = (0, 1)
PROFILES = ("dependency_redirect", "csr_fencei", "irq_divider", "atomic_divider", "fault_restart")
SUPPORTED_COMBINATIONS = {
    "dependency_redirect": "seeded integer/load-store dependencies and taken control redirects",
    "csr_fencei": "seeded custom RW CSR accesses and FENCE.I after an ordinary store",
    "irq_divider": "external IRQ after iterative DIV acceptance; handler returns to the DIV",
    "atomic_divider": "LR/SC effects followed by dependent DIV; no concurrent IRQ or fault",
    "fault_restart": "one precise misaligned load trap and MRET; no asynchronous IRQ overlap",
}

def program(profile, seed):
    rng = random.Random(seed)
    a, b = rng.randrange(5, 90), rng.randrange(2, 13)
    prefix = "li x1, 0x180\ncsrrw x0, 0x305, x1\n"
    irq_pc = irq_levels = ""
    wait_div = "0"
    if profile == "dependency_redirect":
        body = f"li x2, 0x4000\nli x8, {a}\naddi x9, x8, {b}\nslli x10, x9, 1\nsw x10, 0(x2)\nlw x11, 0(x2)\nsub x12, x11, x10\nbeq x12, x0, dep_taken\naddi x13, x0, 99\ndep_taken:\naddi x14, x11, -{b}\njal x0, test_done\n"
    elif profile == "csr_fencei":
        body = f"li x2, {a}\ncsrrw x10, 0x800, x2\ncsrrs x11, 0x800, x0\ncsrrwi x12, 0x801, {a & 31}\ncsrrci x13, 0x801, {b & 31}\nli x3, 0x4000\nsw x11, 0(x3)\nfence.i\nlw x14, 0(x3)\njal x0, test_done\n"
    elif profile == "irq_divider":
        prefix += "li x2, 0x800\ncsrrw x0, 0x304, x2\ncsrrsi x0, 0x300, 8\n"
        body = f"li x5, {a * b}\nli x6, {b}\njal x0, div_start\n.org 0x100\ndiv_start:\ndiv x7, x5, x6\naddi x8, x7, 1\njal x0, test_done\n"
        irq_pc, irq_levels, wait_div = "00000100", "4", "1"
    elif profile == "atomic_divider":
        body = f"li x2, 0x4000\naddi x3, x0, {a}\nlr.w x4, (x2)\nadd x5, x4, x3\nsc.w x6, x5, (x2)\naddi x7, x6, 1\ndiv x8, x5, x7\nsw x8, 4(x2)\njal x0, test_done\n"
    elif profile == "fault_restart":
        body = f"li x2, 0x4000\nlw x4, 1(x2)\naddi x5, x0, {a}\njal x0, test_done\n"
    else:
        raise ValueError(f"unsupported profile: {profile}")
    if profile == "irq_divider":
        handler = ".org 0x180\nmret\n"
    elif profile == "fault_restart":
        handler = ".org 0x180\ncsrrs x20, 0x341, x0\naddi x20, x20, 4\ncsrrw x0, 0x341, x20\nmret\n"
    else:
        handler = ".org 0x180\nmret\n"
    done = ".org 0x200\ntest_done:\nlui x30, 0x10\nli x31, 0x53544737\nsw x31, -4(x30)\njal x0, 0\n"
    return prefix + body + handler + done, irq_pc, irq_levels, wait_div

def artifacts(name, source, out_dir, irq_pc, irq_levels):
    byte_mem = rv32c_asm.assemble_bytes(source, c_enabled=True, a_enabled=True)
    words = rv32c_asm.to_words(byte_mem)
    schedule = []
    if irq_pc:
        scheduled_pc = int(irq_pc, 16)
        _, _, base_trace, _, _, _ = rv32imc_iss.run(words, c_enabled=True, a_enabled=True, z_enabled=True, machine_enabled=True)
        pcs = [int(row.split()[1], 16) for row in base_trace]
        if scheduled_pc not in pcs:
            raise ValueError(f"{name}: scheduled IRQ pc {scheduled_pc:08x} is not executed; {pcs}")
        schedule = [(sum(1 for pc in pcs if pc < scheduled_pc), int(irq_levels))]
    traps, z_events = [], []
    cause, regs, trace, footer, oob, retired = rv32imc_iss.run(words, c_enabled=True, a_enabled=True,
        z_enabled=True, machine_enabled=True, irq_schedule=schedule, machine_events=traps, z_events=z_events)
    if cause != 0 or oob:
        raise ValueError(f"{name}: completion cause={cause} oob={oob} traps={traps}")
    if name.startswith("seed_irq_divider") and (not traps or traps[0][0] != 0x100):
        raise ValueError(f"{name}: IRQ/DIV return expectation failed; traps={traps}")
    if name.startswith("seed_fault_restart") and (len(traps) != 1 or traps[0][2] != 4 or traps[0][3] != 0x4001):
        raise ValueError(f"{name}: fault/MRET expectation failed; traps={traps}")
    if name.startswith("seed_atomic_divider"):
        # The ISS retirement schema carries raw and expanded instructions; it
        # does not append a separate atomic_sidecar column. Check the executed
        # AMO encodings independently instead of searching a nonexistent field.
        atomics = [int(row.split()[4], 16) for row in trace
                   if row.startswith("I ") and (int(row.split()[4], 16) & 0x7f) == 0x2f]
        funct5 = [(insn >> 27) & 0x1f for insn in atomics]
        if funct5 != [0b00010, 0b00011]:
            raise ValueError(f"{name}: expected executed LR.W then SC.W; instructions={atomics} funct5={funct5}")
    if name.startswith("seed_csr_fencei") and not any(row[0] == "FENCEI" for row in z_events):
        raise ValueError(f"{name}: expected FENCE.I absent from ISS events")
    hex_path = out_dir / "stage8_hex" / f"{name}.hex"
    ref_dir = out_dir / "m_iss"
    hex_path.parent.mkdir(parents=True, exist_ok=True)
    hex_path.write_text(rv32c_asm.to_hex(byte_mem), encoding="ascii", newline="\n")
    (out_dir / "stage8_src").mkdir(parents=True, exist_ok=True)
    (out_dir / "stage8_src" / f"{name}.s").write_text(source, encoding="ascii", newline="\n")
    header = "TRACE_V3 RV32IMAC pc raw_insn ilen_bytes expanded_insn rd rdval st_size st_addr st_data atomic_sidecar\n"
    (ref_dir / f"{name}.trace").write_text(header + "\n".join(trace + footer) + "\n", encoding="ascii", newline="\n")
    with (ref_dir / f"{name}.trap.tsv").open("w", newline="") as f:
        w = csv.writer(f, delimiter="\t", lineterminator="\n")
        w.writerow(["fault_pc", "raw", "mcause", "mtval", "target"])
        w.writerows((f"{e[0]:08x}",f"{e[1]:08x}",f"{e[2]:08x}",f"{e[3]:08x}",f"{e[4]:08x}") for e in traps)
    with (ref_dir / f"{name}.z.tsv").open("w", newline="") as f:
        w = csv.writer(f, delimiter="\t", lineterminator="\n")
        w.writerow(["kind","pc","raw","ilen","csr_or_pcnext","funct3","source_index","source","old","new","write_intent"])
        for e in z_events:
            if e[0] == "CSR":
                w.writerow([e[0],f"{e[1]:08x}",f"{e[2]:08x}",e[3],f"{e[4]:03x}",e[5],e[6],f"{e[7]:08x}",f"{e[8]:08x}",f"{e[9]:08x}",e[10]])
            else:
                w.writerow([e[0],f"{e[1]:08x}",f"{e[2]:08x}",e[3],f"{e[4]:08x}","-","-","-","-","-","-"])
    return {"name":name,"hexpath":f"@PREPARED@/stage8_hex/{name}.hex","irq_pc":irq_pc,
            "irq_levels":irq_levels,"irq_wait_div":"1" if irq_pc else "0","traps":len(traps),"retired":retired}

def generate(out_dir):
    out_dir = Path(out_dir)
    rows, coverage = [], {}
    for profile in PROFILES:
        for offset in SEED_OFFSETS:
            seed = (MASTER_SEED + offset * 0x100 + PROFILES.index(profile) * 0x10000) & 0xFFFFFFFF
            name = f"seed_{profile}_{seed:08x}"
            source, irq_pc, irq_levels, wait_div = program(profile, seed)
            row = artifacts(name, source, out_dir, irq_pc, irq_levels)
            row.update({"suite":"stage8_seeded","seed":f"{seed:08x}","source":f"stage8_src/{name}.s"})
            rows.append(row)
            coverage[profile] = coverage.get(profile, 0) + 1
    return rows, coverage
