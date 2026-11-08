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
for interface, commands, dependencies, outputs, and historical evidence.

## Stage 4.4: C-enabled pipeline regression

The canonical full coverage commands from Windows CMD are:

```cmd
scripts\simulation\run_stage4_coverage_xsim.bat
wsl.exe --distribution Ubuntu --cd /mnt/c/RISC-V-ML-Test-Selection --exec bash scripts/simulation/run_stage4_coverage_verilator.sh
```

Each runner uses fresh output, preflights all 209 legacy plus 21 C-enabled
images/references, runs seven unit suites including 65,536 decompressor
patterns/16 anchors, compares golden and pipeline traces against the
independent ISS, compares pipeline to golden, and checks timing, divider
protocol, coverage sidecars, and all 16 pipeline events. Expected terminal
markers are `STAGE4_C_COVERAGE_XSIM PASS cases=230 c_cases=21 patterns=65536
pipeline_events=16` and its Verilator equivalent. Separate reports are under
`reports/stage4_c_coverage_<sim>_<UTC>.txt`; raw run data is under
`sim_out_stage4_4_<sim>_<UTC>/`.

The separate Verilator mutation command runs a full baseline followed by ten
isolated mutants; use `--mutants C07,C09` for focused parser validation without
rerunning the other eight:

```cmd
wsl.exe --distribution Ubuntu --cd /mnt/c/RISC-V-ML-Test-Selection --exec python3 scripts/simulation/run_stage4_mutation.py
wsl.exe --distribution Ubuntu --cd /mnt/c/RISC-V-ML-Test-Selection --exec python3 scripts/simulation/run_stage4_mutation.py --mutants C07,C09
```

The approved evidence and exact dependencies are recorded in
[`../architecture/stage4_4_pipeline.md`](../architecture/stage4_4_pipeline.md).
The C coverage dictionary, independent evidence sources, mutation results and
limitations are in
[`../architecture/stage4_c_coverage_mutation.md`](../architecture/stage4_c_coverage_mutation.md).
The new and modified file manifest is in `stage4_coverage_manifest.md`.
