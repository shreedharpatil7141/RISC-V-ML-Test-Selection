Verification docs: `verification_architecture.md`. The listed Stage 3.7
results are owner-supplied simulator evidence, retained separately by tool.

Stage 3 regression procedures and current evidence: see
[`architecture/stage3_rv32m_status.md`](../architecture/stage3_rv32m_status.md).
The manifest of Stage 3 sources, tests, scripts, reports, dependencies,
commands, and markers is in `stage3_artifact_manifest.md`.

Stage 4.3 golden-core C integration uses the separately named
`run_stage4_3_xsim.bat` and `run_stage4_3_verilator.sh` entry points. They
preserve Stage 3 runners, execute the exhaustive Stage 4.2 decompressor vectors,
replay the 209 C-disabled cases, and compare the explicit RV32IMC manifest
against `rv32imc_iss.py`. See
[`../architecture/stage4_3_golden_fetch.md`](../architecture/stage4_3_golden_fetch.md)
for interface, commands, dependencies, outputs, expected markers, and pending
validation status.

## Stage 4.4: C-enabled pipeline regression

Use `scripts/simulation/run_stage4_4_xsim.bat` from initialized Windows CMD or
`wsl.exe --distribution Ubuntu --cd /mnt/c/RISC-V-ML-Test-Selection --exec bash scripts/simulation/run_stage4_4_verilator.sh`.
The runner requires fresh output, preflights all 209 legacy plus 20 C-enabled
images and references before compilation, runs seven existing unit suites
including 65,536 decompressor patterns/16 anchors, then compares each golden
and pipeline trace against the independent ISS. It also compares the RTL
traces to each other and checks the derived cycle equation, all 16 pipeline
event counters, and divider starts/completions/33-cycle costs independently.
Expected final markers are `STAGE4_4_PIPELINE_XSIM PASS legacy=209
rv32imc=20 full_trace_comparisons=458 units=7` or the corresponding
`STAGE4_4_PIPELINE_VERILATOR` marker. Reports are separate timestamped files
under `reports/stage4_4_pipeline_<sim>_<UTC>.txt`; full logs and traces are in
`sim_out_stage4_4_<sim>_<UTC>/`. Local validation is pending because Python,
Vivado XSim, and Verilator are unavailable in this execution environment.
Details and the fetch/metadata contract are in
[`../architecture/stage4_4_pipeline.md`](../architecture/stage4_4_pipeline.md).
