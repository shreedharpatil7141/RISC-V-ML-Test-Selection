# Verification Architecture (modular SystemVerilog, no UVM)

## Component responsibilities
| Component | Dir | Responsibility |
|---|---|---|
| `verif_pkg` | verification/packages | Shared types, retirement transaction struct, constants |
| Interfaces | verification/interfaces | Memory and retirement interfaces for DUT binding |
| Generator | verification/generator | Directed + constrained-random program generation (seeded); writes hex image plus a static "feature manifest" |
| Driver | verification/driver | Loads program to memory model, applies reset, drives interrupts, controls run to end-of-test |
| Monitor | verification/monitor | Samples retirement interface into transactions (PC, insn, rd, mem, CSR, trap) |
| Reference model | verification/reference_model | Independent behavioural ISS (own package, own decode/execute); consumes the same memory image |
| Scoreboard | verification/scoreboard | Per-retirement comparison: PC, rd write, memory write, CSR, trap cause/tval, branch target, atomic results; end-of-test memory signature check |
| Coverage | verification/coverage | Functional coverage (instruction, format, operand, register, dependency, branch, memory, M/A/C, CSR, exception, interrupt, crosses, sequences); per-bin hit export |
| Assertions | verification/assertions | SVA on interfaces/pipeline invariants (x0 always 0, valid-handshake, no-retire-after-trap, etc.) |
| Environment | verification/environment | Top-level test bench wiring, test sequencing, regression loop, fault-injection hooks, CSV export |

## Reference model independence
The model lives in its own package, shares only the architectural spec (and the ISA opcode *constants* where unavoidable - these are re-declared, not imported from RTL). It does not instantiate or call any RTL module/function.

## Test types
Directed (per extension), constrained-random profiles (arith-heavy, branch-heavy, memory-heavy, M-heavy, A-heavy, C-mixed, CSR/priv, mixed), corner-case (operand extremes, div by zero, misalignment), integration (long mixed programs, interrupt injection), fault injection (mutated DUT / forced errors to prove scoreboard sensitivity).

## XSim compatibility gate
Before relying on any of these in Stage 8, a small probe project checks XSim support for: classes, `randomize() with {}`, constraints, covergroups/cross/`get_inst_coverage`, SVA, `$fwrite`/`$fscanf`, `$value$plusargs`, queues/assoc arrays, DPI-C. Fallback for anything unsupported is documented.

## Compile order (verification, after RTL)
1. `verification/packages`
2. `verification/interfaces`
3. `verification/reference_model`
4. `verification/generator`, `driver`, `monitor`
5. `verification/coverage`, `assertions`, `scoreboard`
6. `verification/environment` (top testbench; simulation top)

## Simulation flow (to be scripted in scripts/simulation)
`xvlog -sv <files in order>` -> `xelab -debug typical <top> -s sim` -> `xsim sim -runall` with `-testplusarg SEED=<n> -testplusarg TEST=<name>`. Scripts will be verified when XSim is actually run.
