# Stage 6 CSR and instruction-fetch fence

Specification pins: Zicsr 2.0 and Zifencei 2.0, ratified in the RISC-V Unprivileged ISA manual release 20250508. Sources: https://docs.riscv.org/reference/isa/v20250508/unpriv/zicsr.html and https://docs.riscv.org/reference/isa/v20250508/unpriv/zifencei.html. The release index is https://docs.riscv.org/reference/isa/v20250508/unpriv/colophon.html.

## Implemented CSR map

Stage 6 provides custom user-level RW scratch CSRs `0x800` and `0x801`; both reset to zero with implemented/write mask `0xFFFFFFFF`. It also implements custom user-level RO identification CSR `0xCC0`, fixed at `0x53544736` (`STG6`), with read mask `0xFFFFFFFF` and write mask zero. Every other address, including `0xCC1`, standard counters, and privileged machine CSRs, is unimplemented and faults as illegal. A write attempt to `0xCC0` is illegal. For CSRRS/CSRRC forms, the attempt is determined by the encoded source index, so nonzero `rs1` containing zero still attempts a write; immediate set/clear with `zimm=0` suppresses it. CSRRW forms always attempt a write, including with `rd=x0` or a zero source.

The address encoding gives both registers user-level access and custom read/write allocation. The core has no privilege-state transitions in Stage 6; traps, interrupts, MRET, and machine mode remain Stage 7 work.

## CSR instruction rules

All six Zicsr encodings are decoded. Register forms use `x[rs1]`; immediate forms use zero-extended `zimm=insn[19:15]`. The old CSR value is returned to `rd`. CSRRW always writes; it suppresses the CSR read when `rd=x0`. CSRRS/CSRRC write only when `rs1!=x0`; immediate set/clear forms write only when `zimm!=0`. Suppressing a write does not suppress the read. A nonzero register whose value happens to be zero still requests a write for CSRRS/CSRRC. Illegal/unimplemented access has no register or CSR side effect. CSR state changes only for a nonfaulting instruction at architectural commit.

## FENCE.I and compatibility

FENCE.I synchronizes prior stores to subsequent instruction fetches and restarts fetch at the sequential PC computed using the instruction's actual length. The pipeline drains older memory effects, invalidates younger fetched/decode work, and refetches from that PC. Stage 6 is disabled by default so existing Stage 5 cases retain their prior instruction legality and trace behavior; enabled suites opt in explicitly.

## Validation status

Validation gate: PASS; Stage 6 release approved on 2026-11-09. Scope is the six CSR instructions, the implemented custom CSR map above, and FENCE.I. Full machine-mode behavior, traps, interrupts, and MRET remain Stage 7.

Stage 5 compatibility: 248 cases passed. Stage 6 enabled: 11 cases and 22 ISS trace comparisons passed on each of Verilator and XSim. Focused mutation result: `caught=2 missed=0 invalid=0`.

Evidence: `reports/stage5_a_pipeline_verilator_20261109T084302Z.txt`, `reports/stage5_a_pipeline_xsim_20261109T093653Z.txt`, `reports/stage6_verilator_20261109T101414Z.txt`, `reports/stage6_xsim_20261109T100312Z.txt`, and `reports/stage6_z_mutation_verilator_20261109T101511Z.txt`.

Commands: prepare with `scripts\simulation\prepare_stage6.bat <fresh-output-dir>`; run the full Verilator suite with `C:\Windows\System32\wsl.exe --distribution Ubuntu --cd /mnt/c/RISC-V-ML-Test-Selection --exec bash scripts/simulation/run_stage6_verilator.sh <prepared-dir>`; run the full XSim suite with `scripts\simulation\run_stage6_xsim.bat <prepared-dir>`; run focused mutations with `C:\Windows\System32\wsl.exe --distribution Ubuntu --cd /mnt/c/RISC-V-ML-Test-Selection --exec bash scripts/simulation/run_stage6_z_mutation.sh`.
