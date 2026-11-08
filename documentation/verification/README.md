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
