# Stage 4.4: RV32IMC pipeline integration

**Gate: validated in both simulators; coverage/mutation gate approved.** This batch extends the existing five-stage pipeline behind the default-off `ENABLE_C` parameter. Final Stage 4 documentation is for owner release review; no completion tag or merge is claimed.

## Fetch and metadata contract

`imem_addr` is the aligned 32-bit word address `PC & ~3`; `imem_addr_next` is the following word address. `imem_rdata`/`imem_valid` describe the first word and `imem_rdata_next`/`imem_next_valid` describe the next. With C enabled, IF selects the halfword at `PC[1]`, expands a compressed instruction, and assembles an ordinary 32-bit instruction at offset two as `{next_word[15:0], current_word[31:16]}`. A missing current word faults at fetch. A missing second parcel faults only for a 32-bit prefix that crosses the word boundary. A legal 16-bit instruction in the final memory parcel remains valid.

IF/ID stores original PC, zero-extended raw instruction bits, canonical expansion, byte length, and any fetch cause. ID decodes the canonical word. The same identity and fault metadata travel through ID/EX, EX/MEM, and MEM/WB. Retirement returns raw bits, canonical expansion, original length, and original PC. Faulting metadata is captured at the oldest MEM-stage fault; a fault does not retire or update architectural state. Redirect flushes discard the younger IF/ID fetch result, including a speculative fetch-boundary fault. C-disabled mode remains the default, retains PC+4, four-byte target alignment, and the released legacy trace format.

Taken C branch/JAL targets use the decompressed immediate and original PC. JAL/JALR link writes use `PC + ilen_bytes`; forwarding observes that value through the normal EX/MEM or MEM/WB path. DIV/REM retain their iterative 34 occupied EX-cycle protocol (33 added hold cycles); divider holds preserve the complete ID/EX metadata. Compressed fetch still supplies one instruction per active cycle, so width changes the sequential PC and trace, not the base pipeline throughput. The independent timing model is `instret + 5 + load_use_stalls + 2*redirects + 33*completed_divisions`; redirect detection uses `PC + ilen_bytes` for fall-through. Protocol counters are checked separately for exact starts, completions, busy cycles, and aborts.

## Scope and tests

The earlier Stage 4.4 checkpoint covered 209 released C-disabled programs plus 12 existing RV32IMC golden-core programs and 8 pipeline-specific programs (229 configurations). The coverage batch adds `coverage_boundaries` for x15 and immediate/stack-offset limits, bringing the current regression to 209 legacy + 21 C-enabled (230 configurations). Every current program runs on golden single-cycle RTL and pipeline RTL; traces are compared to the independent ISS and to each other. Historical 229-case reports remain preserved separately.

The original eight pipeline C programs target mixed-width forwarding, a pair of DIV instructions at halfword PCs including offset-two cross-word fetch, load-use and compressed consumers, stack accesses and JALR link forwarding, compressed JAL links, wrong-path illegal instruction squashing, older EBREAK suppression of a younger store, and a fetch-access fault beyond the final memory word created on the wrong path and squashed by a taken compressed branch. The follow-on coverage case adds x15/high-prime use, signed immediate endpoints, maximum shifts, and maximum memory/stack offsets. Existing C programs cover all implemented compressed families, HINT/x0, memory, links, malformed instructions, and direct fetch-boundary cases. Coverage counters must exercise all 16 existing pipeline event bins across the full regression.

Seven unit suites run in both simulator modes: arithmetic, RV32M arithmetic, M decoder, pipeline units, iterative divider, M wrapper protocol, and the exhaustive RV32C decompressor (65,536 vectors and 16 anchors). The runner requires process success, fresh logs and traces, one PASS terminal record, no FAIL record, all full trace comparisons, the independent timing equation, all 16 pipeline events, and exact divider protocol counters. The separate coverage checker derives architectural bins from ISS records and microarchitectural events from RTL sidecars/COV records; current XSim and Verilator coverage reports both record zero errors.

## Commands and artifacts

Dependencies: Windows uses Python 3 and Vivado 2026.1 XSim (`xvlog`, `xelab`, `xsim`) from initialized CMD. WSL uses Python 3, Verilator 5.x, GNU make, and a C++ compiler. The runner uses the active `sys.executable`, resolves Vivado paths, launches batch tools through COMSPEC, quotes XSim `NAME=value` payloads, and converts simulator file plusarg paths to forward slashes.

From Windows CMD:

```cmd
cd /d C:\RISC-V-ML-Test-Selection
scripts\simulation\run_stage4_4_xsim.bat
```

From Windows CMD using Ubuntu WSL:

```cmd
wsl.exe --distribution Ubuntu --cd /mnt/c/RISC-V-ML-Test-Selection --exec bash scripts/simulation/run_stage4_4_verilator.sh
```

Each run creates a fresh `sim_out_stage4_4_<sim>_<UTC>/` directory and a separate `reports/stage4_4_pipeline_<sim>_<UTC>.txt`. The historical owner-validated marker reports 209+20 and 458 comparisons. Current follow-on full runs expect `STAGE4_4_PIPELINE_XSIM PASS legacy=209 rv32imc=21 full_trace_comparisons=460 units=7` and the corresponding Verilator marker. Reports include actual 16-bin hit totals and summed divider protocol counters. Intermediate markers include software/artifact preflight PASS, unit PASS records, and visible per-test progress.

`stage4_4_rtl.f` is the Stage 4.4 compile list. The historical Stage 2 list gains only the decompressor dependency because `rv_if_stage` now instantiates it even with `ENABLE_C=0`; the default-disabled behavior remains fixed-width. Historical Stage 1/2/3 runners and reports keep their names and output paths. In particular `run_stage4.py`/`run_stage5.py` remain historical RV32M implementation-step names, not ISA extension selectors.

## Validation evidence and limits

Expanded regression reports are `reports/stage4_4_pipeline_xsim_20261108T154108Z.txt` and `reports/stage4_4_pipeline_verilator_20261108T161512Z.txt`. Each records 230 cases, 460 golden/pipeline-to-ISS comparisons, 230 pipeline-to-golden traces, and seven unit suites. Separate coverage reports are `reports/stage4_c_coverage_xsim_20261108T161413Z.txt` and `reports/stage4_c_coverage_verilator_20261108T161707Z.txt`; each records 65,536 decompressor patterns, all 16 event bins hit, and zero coverage errors. Both report divider totals of 2,027 starts, 2,027 dones, 66,891 busy cycles, and zero aborts. Older 229-case reports are preserved as historical evidence.

Coverage is finite and directed, not full ISA/architectural compliance. C is limited to the implemented RV32C integer subset. Floating-point/Zc, A, CSR, privileged traps/interrupts, and Zifencei are not implemented. There is no synthesis or timing-closure evidence and no ML result. Mutation evidence is documented in `stage4_c_coverage_mutation.md`: Verilator only, with eight detections in the original campaign and two focused C07/C09 detections after parser correction, not one fresh ten-mutant run. Original INVALID records and their reanalysis are retained.
