# Stage 15 final integration and delivery

## Scope and validation

This checkpoint integrates the released Stages 10–14 artifacts. It does not
change RTL, retrain Stage 11 models, retune selection policies, or execute a
simulator. Run the saved-evidence gate from Windows CMD at the repository root:

```cmd
scripts\machine_learning\validate_stage15.cmd
```

The fail-fast entry point verifies the Stage 10–14 release tags and ancestry,
runs Git LFS object integrity verification, audits current hashes portably,
and validates the Stage 10 dataset in a temporary copy. It then creates a
disposable checkout at `stage14-complete` (with Git for Windows long paths enabled), restores the exact manifest-recorded
Stage 11–14 producer source and artifact byte forms there, and invokes the
existing Stage 11, Stage 12, Stage 13, and corrected-retry Stage 14 validators
in MATLAB R2025a. If MATLAB is installed elsewhere, set `STAGE15_MATLAB_EXE` to
the full path of `matlab.exe` before running the command. The hash audit accepts
either exact raw bytes or only CRLF/CR-to-LF normalization for text; binary
artifacts remain raw-hashed. It does not update expected manifest hashes.
The Stage 14 retry is the current experiment; the initial replay remains
historical, and `stage14_experiments_corrected` remains marked invalid. Those
directories and run-status markings must be retained.

This command validates saved evidence. It is not a fresh simulation or a
reproduction of the simulator observations. XSim and Verilator observations
remain separate. Fresh simulator execution, MATLAB model fitting, and replay
generation are separate operations and are intentionally not part of this
gate. Do not interpret offline replay as live simulation savings.

## Current findings and limitations

Stage 10 contains 282 logical tests, 564 per-simulator cost observations, and
the frozen grouped split of 196/46/40. Stage 11 contains the frozen models and
separate XSim/Verilator predictions. Stage 12 selection and Stage 13 active
learning are offline analyses over saved observations. Stage 14 findings use
only `reports/stage14_experiments_corrected_retry/`; its predictions are
in-sample applications of the frozen Stage 11 models to training candidates.
The actual-label greedy policy is an oracle baseline, not an upper bound.
Predicted cycle budgets can be exceeded. No generalization, statistical
significance, guaranteed-budget, policy-superiority, or wall-clock-savings
claim is supported. Results are exploratory and limited to this corpus.

The Stage 11 configuration records the producing installation's MATLAB root
(`C:\Program Files\MATLAB\R2025a`). This is machine-specific provenance, not a
required checkout location; the validation command allows an explicit local
MATLAB path. MATLAB R2025a Update 1 with Statistics and Machine Learning
Toolbox was used for the recorded ML validation.

## Reproduction guide

1. Check out the Stage 15 branch or a descendant of `stage14-complete` with
   Git LFS installed and retrieve the tracked Stage 14 replay object.
2. Install MATLAB R2025a and Statistics and Machine Learning Toolbox, and make
   Python 3 available to the `py -3` launcher for the Stage 10 validator.
3. In Windows CMD, run `scripts\machine_learning\validate_stage15.cmd`.
   Require the terminal marker `STAGE15_SAVED_EVIDENCE_VALIDATION PASS`.
4. Treat that result as validation of committed/saved evidence only. Fresh
   XSim/Verilator runs and new model/selection/experiment generation require
   their stage-specific commands, produce new evidence, and are not implied by
   this command.

This gate validates saved evidence; it does not freshly generate all simulator
observations, fit models, or generate new selection/experiment outputs. XSim
and Verilator are not rerun. The CMD entry point returns failure if a required
tool, producer input, source hash, or validator is unavailable.

## Checkpoint execution record

- The three tracked Stage 14 replay MAT objects were retrieved in a disposable
  worktree at `stage14-complete`; all materialized at their expected sizes and
  `git lfs fsck --objects` returned `Git LFS fsck OK`. The worktree was removed
  after the check. The owner checkout was not switched or modified by this
  retrieval check.
- The local LFS inventory contains exactly the original Stage 14 replay, the
  superseded corrected run, and the corrected retry. All three remain
  available; only the retry supports current Stage 14 findings.
- Isolated checkout inventory: `reports/stage14_experiments/stage14_replay.mat`
  (1,868,041,876 bytes; LFS SHA-256
  `5fac2f28961b2960f1d8ec070a750ef3389914ec14da1a494390510ea1210d66`),
  `reports/stage14_experiments_corrected/stage14_replay.mat`
  (1,778,040,742 bytes; `f4d74a6c25b0a63e1a37c3f51160ddfc9046f7060b8bb61423fc0dbf6e2a82a9`),
  and `reports/stage14_experiments_corrected_retry/stage14_replay.mat`
  (1,778,040,742 bytes; `8c60a1a2a8059eb67179695ee739a57a069b0fd1ebf6e64d8f5daa865b0230a4`).
- The standalone `py -3` launcher reports no installed Python, but the existing
  Stage 10 batch validator found the per-user Python 3.11 installation and
  passed in the isolated copy: 282 logical tests, 564 observations, 178,224
  coverage rows, split 196/46/40.
- Stage 11 source hash root cause: the manifest records
  `5e6ab3d114ac190c3d4b1d5e22705dfdfd57ef8fbab7a28e6a39574acf722051`. The
  current raw file hash is
  `a706e1766706a2844fb60068cffb2644e23d4cc43a0d1e843952ddd61b00e1cf`
  (36,129 bytes, 602 CRLF pairs); its LF-normalized hash is exactly the
  manifest value (35,527 bytes). The exact source at `stage11-complete` and
  approved producer checkpoint `2700393049e1ff029cb97c4b021568d3b3cbaf98`
  both hash to the manifest value. This was checkout line endings only; the
  current Stage 11 source has no semantic difference from the producer source.
- Joint Stage 11–14 audit found only raw-equal or LF-equivalent hashes: Stage 11
  raw=297/LF-only=15; Stage 12 raw=2/LF-only=38; Stage 13 raw=3/LF-only=34;
  corrected Stage 14 inputs raw=1/LF-only=15, source hashes raw=0/LF-only=3,
  and exported outputs raw=0/LF-only=9. No unexpected or
  missing hashes remained. All 15 current MATLAB/batch producer source files
  matched their stage release source blobs after LF normalization.
- The history validator ran against exact producer sources in a disposable
  Stage 14 checkout and passed: Stage 11 validation (54,352 prediction rows,
  632 per-bin metrics, two cost models), Stage 12 validation (2,000 orders,
  1,204 curves, two policies), Stage 13 standalone validation, and Stage 14
  standalone corrected-retry validation. The final marker was
  `STAGE15_SAVED_EVIDENCE_VALIDATION PASS`.
- All 34 previously owner-local Stage 11 program images are packaged byte-for-byte
  under `reports/stage15_evidence/program_images/`. The 282-row
  `program_image_map.csv` records each frozen manifest path, original path,
  SHA-256, repository-relative destination, and storage class (34 packaged, 248
  already tracked). The gate strictly verifies all 282 destination hashes and has
  no dependency on untracked `sim_out_*` directories. It materializes the mapped
  images only inside its disposable historical validation checkout.
- The Stage 10 validator's canonical-LF hash check and isolated output setting
  keep its deterministic regeneration from rewriting the frozen owner CSVs.
- `reports/stage11_matlab_ml/configuration.json` records
  `C:\Program Files\MATLAB\R2025a` as the producing MATLAB root. It is
  provenance only; use `STAGE15_MATLAB_EXE` for another installation path.
- The Stage 10 batch validator probes
  `%USERPROFILE%\AppData\Local\Programs\Python\Python311\python.exe`, then
  falls back to `py -3`. MATLAB discovery probes Program Files R2025a locations.
  These are local tool-discovery paths, not artifact lineage paths. Git for Windows
  must support long paths; the gate enables `core.longpaths` on its temporary
  worktree add and removal commands.

The full gate was rerun in a clean isolated worktree at `stage14-complete` with
all 34 packaged images and the required LFS objects present; the three owner-local
simulation directories were absent. The full run ended with
`STAGE15_SAVED_EVIDENCE_VALIDATION PASS`. Its earlier first attempt exposed Windows
path-length failures during worktree checkout/removal; the gate now enables Git long
paths for both operations.

An earlier direct MATLAB launch returned service error 5202 before validation.
The subsequent isolated integrated invocation completed all four MATLAB validators
successfully; the earlier startup failure was not counted as validation.

To rerun the integrated gate on a workstation where MATLAB works:

```cmd
set "STAGE15_MATLAB_EXE=C:\Program Files\MATLAB\R2025a\bin\matlab.exe"
scripts\machine_learning\validate_stage15.cmd
```

## Paper outline

1. **Problem and scope:** test prioritization for finite directed functional
   coverage experiments on this RISC-V verification corpus.
2. **Evidence pipeline:** independent simulator observations, static
   pre-execution features, coverage labels, estimated cycle costs, and grouped
   196/46/40 split.
3. **Baselines and methods:** Stage 11 per-simulator/bin models; Stage 12
   selector and baselines; Stage 13 offline active-learning policies; Stage 14
   paired exploratory replay and cost audit.
4. **Results:** report XSim and Verilator separately; label training-pool,
   validation, held-out exploratory reuse, and oracle comparisons explicitly.
5. **Threats and limitations:** small corpus, frozen split, in-sample Stage 14
   predictions, budget overruns, saved-observation replay, finite directed
   verification, and no wall-clock measurement.
6. **Conclusion:** describe workflow feasibility only; make no claims of
   generalization, significance, guaranteed budgets, superiority, or savings.

## Résumé text

Built a reproducible ML-assisted test-selection research pipeline for a
RISC-V processor verification corpus, integrating per-simulator coverage
models, cost-aware selection, offline active-learning replay, hashed artifact
lineage, and validation of a frozen grouped dataset. Evaluated saved XSim and
Verilator evidence separately and documented exploratory limits; no live
simulation-savings or generalization claim.

## Interview preparation

- **Why group the split?** To keep related test profiles/seeds together and
  reduce leakage between train, validation, and test.
- **Why separate simulators?** Their observations and costs are distinct; the
  evidence does not justify pooling them.
- **What does Stage 14 establish?** Corrected exploratory in-sample replay
  behavior for this dataset, with explicit candidate orders and observed-cost
  audits; not generalization or deployment performance.
- **Why can a predicted budget be exceeded?** Estimated cycle costs are
  predictions, not hard constraints; the saved replay includes overruns.
- **Was speedup measured?** No. Simulated instruction cycles are not
  wall-clock measurements, and replay does not execute a live simulator.
- **What is the validation gate?** Hash and schema checks over frozen saved
  evidence; fresh execution is a separate experiment.
