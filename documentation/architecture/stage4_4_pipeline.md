# Stage 4.4: RV32IMC pipeline integration

**Gate: implementation complete, simulation validation pending.** This batch extends the existing five-stage pipeline behind the default-off `ENABLE_C` parameter. It does not claim Stage 4 completion.

## Fetch and metadata contract

`imem_addr` is the aligned 32-bit word address `PC & ~3`; `imem_addr_next` is the following word address. `imem_rdata`/`imem_valid` describe the first word and `imem_rdata_next`/`imem_next_valid` describe the next. With C enabled, IF selects the halfword at `PC[1]`, expands a compressed instruction, and assembles an ordinary 32-bit instruction at offset two as `{next_word[15:0], current_word[31:16]}`. A missing current word faults at fetch. A missing second parcel faults only for a 32-bit prefix that crosses the word boundary. A legal 16-bit instruction in the final memory parcel remains valid.

IF/ID stores original PC, zero-extended raw instruction bits, canonical expansion, byte length, and any fetch cause. ID decodes the canonical word. The same identity and fault metadata travel through ID/EX, EX/MEM, and MEM/WB. Retirement returns raw bits, canonical expansion, original length, and original PC. Faulting metadata is captured at the oldest MEM-stage fault; a fault does not retire or update architectural state. Redirect flushes discard the younger IF/ID fetch result, including a speculative fetch-boundary fault. C-disabled mode remains the default, retains PC+4, four-byte target alignment, and the released legacy trace format.

Taken C branch/JAL targets use the decompressed immediate and original PC. JAL/JALR link writes use `PC + ilen_bytes`; forwarding observes that value through the normal EX/MEM or MEM/WB path. DIV/REM retain their iterative 34 occupied EX-cycle protocol (33 added hold cycles); divider holds preserve the complete ID/EX metadata. Compressed fetch still supplies one instruction per active cycle, so width changes the sequential PC and trace, not the base pipeline throughput. The independent timing model is `instret + 5 + load_use_stalls + 2*redirects + 33*completed_divisions`; redirect detection uses `PC + ilen_bytes` for fall-through. Protocol counters are checked separately for exact starts, completions, busy cycles, and aborts.

## Scope and tests

The regression contains all 209 released C-disabled programs plus the 12 existing RV32IMC golden-core programs and 8 new pipeline-specific programs (229 program configurations). Every program runs on the independent golden single-cycle RTL and the pipeline RTL; both complete traces must match the independent ISS, and the two RTL traces must match each other. Reports distinguish 209 legacy and 20 C-enabled cases.

The eight new C programs target mixed-width forwarding, a pair of DIV instructions at halfword PCs including offset-two cross-word fetch, load-use and compressed consumers, stack accesses and JALR link forwarding, compressed JAL links, wrong-path illegal instruction squashing, older EBREAK suppression of a younger store, and a fetch-access fault beyond the final memory word created on the wrong path and squashed by a taken compressed branch. Existing C programs cover all implemented compressed families, HINT/x0, memory, links, malformed instructions, and direct fetch-boundary cases. Coverage counters must exercise all 16 existing pipeline event bins across the regression.

Seven unit suites run in both simulator modes: arithmetic, RV32M arithmetic, M decoder, pipeline units, iterative divider, M wrapper protocol, and the exhaustive RV32C decompressor (65,536 vectors and 16 anchors). The runner requires process success, fresh logs and traces, one PASS terminal record, no FAIL record, all full trace comparisons, the independent timing equation, all 16 pipeline events, and exact divider protocol counters.

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

Each run creates a fresh `sim_out_stage4_4_<sim>_<UTC>/` directory and a separate `reports/stage4_4_pipeline_<sim>_<UTC>.txt`. Expected final markers are `STAGE4_4_PIPELINE_XSIM PASS legacy=209 rv32imc=20 full_trace_comparisons=458 units=7` and the corresponding `STAGE4_4_PIPELINE_VERILATOR` marker. Reports include actual 16-bin hit totals and summed divider protocol counters. Intermediate markers include software/artifact preflight PASS, unit PASS records, and visible per-test progress.

`stage4_4_rtl.f` is the Stage 4.4 compile list. The historical Stage 2 list gains only the decompressor dependency because `rv_if_stage` now instantiates it even with `ENABLE_C=0`; the default-disabled behavior remains fixed-width. Historical Stage 1/2/3 runners and reports keep their names and output paths. In particular `run_stage4.py`/`run_stage5.py` remain historical RV32M implementation-step names, not ISA extension selectors.

## Validation status and limits

Local static review and `git diff --check` are available. The current environment has no installed Python interpreter, Vivado XSim tools, or native Verilator. WSL was not retried because the earlier access failure is unchanged. Therefore no Stage 4.4 software-preparation, unit, system simulation, timing, protocol, or compliance PASS is claimed. Run the Windows CMD or WSL command above in its tool environment. Any RTL or testbench changes after those runs require rerunning this batch.

This is a directed finite regression, not full ISA/architectural compliance. It does not implement C floating-point/Zc extensions, A, CSR, privileged traps, interrupts, or ML-based test selection, and it contains no synthesis or physical timing evidence. No mutation campaign is included in Stage 4.4.
