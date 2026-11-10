#!/usr/bin/env python3
"""Focused encoding and independent M-mode trap/CSR reference checks."""
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import rv32_asm
import rv32imc_iss as iss


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def image(source):
    words = rv32_asm.assemble(source)
    return [words.get(4 * i, 0) for i in range(max(words) // 4 + 1)]


def main():
    require(rv32_asm.assemble("mret\n")[0] == 0x30200073, "MRET encoding")
    require(iss._decode32(0x30200073, machine_enabled=True)[0], "MRET machine legality")
    require(not iss._decode32(0x30200073, machine_enabled=False)[0], "MRET disabled legality")

    # Fixed mtvec handler records the original ECALL PC, advances mepc, then
    # returns. A dedicated test-completion store is the only successful stop.
    src = """
      li x1, 0x40
      csrrw x0, 0x305, x1
      csrrsi x0, 0x300, 8
      csrrs x4, 0xCC0, x0
      lui x6, 0x10
      li x5, 0x53544737
      csrrs x3, 0xCC1, x0
      ecall
      sw x5, -4(x6)
      .org 0x40
      csrrs x2, 0x341, x0
      addi x2, x2, 4
      csrrw x0, 0x341, x2
      mret
    """
    traps = []
    csr_events = []
    cause, regs, rows, footer, oob, n = iss.run(
        image(src), c_enabled=True, a_enabled=True, z_enabled=True,
        machine_enabled=True, machine_events=traps, z_events=csr_events)
    require(cause == 0 and oob == 0, "test-completion store and bounded memory")
    require(traps == [(28, 0xCC1021F3, 2, 0xCC1021F3, 64), (32, 0x00000073, 11, 0, 64)],
            f"illegal CSR then ECALL trap identity/order: {traps}")
    require(regs[2] == 36 and regs[3] == 0 and regs[4] == iss.CSR_STAGE6_ID,
            f"RO read and trap suppression: x2={regs[2]:08x} x3={regs[3]:08x} x4={regs[4]:08x}")
    id_events = [event for event in csr_events if event[0] == "CSR" and event[4] == 0xCC0]
    require(len(id_events) == 1 and id_events[0][8:11] ==
            (iss.CSR_STAGE6_ID, iss.CSR_STAGE6_ID, 0),
            f"custom RO CSR access intent and before/after values: {id_events}")
    retired_pcs = [int(row.split()[1], 16) for row in rows]
    require(28 not in retired_pcs and 32 not in retired_pcs,
            "illegal CSR and ECALL must not retire")
    require(retired_pcs.count(36) == 1, "MRET resumes exactly at mepc")
    require("CSR 342 0000000b" in footer and "CSR 343 00000000" in footer,
            "mcause/mtval architectural values")
    require("CSR 300 00001888" in footer, "MRET restores MIE and sets MPIE")

    # A nonzero source register whose value is zero still requests a write;
    # fixed identification state is read-only and never appears in RW state.
    require(iss._machine_csr_read({}, 0xCC0) == 0x53544736, "fixed Stage 6 RO ID")
    require(not iss._decode32(0xCC029073, z_enabled=True, machine_enabled=True)[0],
            "RO ID CSRRW attempt remains illegal")
    require(not iss._decode32(0xCC102073, z_enabled=True, machine_enabled=True)[0],
            "unimplemented CC1 remains illegal")

    # Machine WARL masks and read-only enforcement are checked in the
    # independent ISS with exact trap PCs and post-trap architectural state.
    mask_src = """
      li x1, 0x80
      csrrw x0, 0x305, x1
      li x3, -1
      csrrw x2, 0x300, x3
      csrrw x4, 0x304, x3
      li x5, 0x83
      csrrw x6, 0x305, x5
      li x7, 0x23
      csrrw x8, 0x341, x7
      csrrs x9, 0x344, x0
      csrrs x12, 0x301, x0
      csrrw x0, 0x344, x0
      csrrw x0, 0x301, x0
      lui x13, 0x10
      li x5, 0x53544737
      sw x5, -4(x13)
      .org 0x80
      csrrs x11, 0x341, x0
      addi x11, x11, 4
      csrrw x0, 0x341, x11
      mret
    """
    mask_traps=[]
    mcause, mregs, mrows, mfooter, moob, mn = iss.run(
        image(mask_src), c_enabled=True, a_enabled=True, z_enabled=True,
        machine_enabled=True, machine_events=mask_traps)
    require(mcause == 0 and moob == 0, "machine WARL test completion")
    require([(e[0],e[2],e[3],e[4]) for e in mask_traps] ==
            [(44,2,0x34401073,0x80),(48,2,0x30101073,0x80)],
            f"MIP/MISA write attempts trap precisely: {mask_traps}")
    mstate={int(line.split()[1],16):int(line.split()[2],16) for line in mfooter if line.startswith("CSR ")}
    require((mregs[2],mregs[4],mregs[6],mregs[8],mregs[9],mregs[12]) ==
            (0x1800,0,0x80,0,0,0x40001105), "CSR old-value reads and MISA/MIP reads")
    require((mstate[0x300],mstate[0x304],mstate[0x305],mstate[0x341]) ==
            (0x1888,0x888,0x80,52), "mstatus/mie/mtvec/mepc WARL masks")
    print("STAGE7_SOFTWARE_SELFTEST PASS mret=1 ecall_trap=1 ro_id=1 completion=explicit")


if __name__ == "__main__":
    main()
