# Stage 14 comparative experiments

The preregistration is `reports/stage14_experiments/configuration.json`; the MATLAB runner saves dataset/model input hashes and runtime there before replay. Run `scripts/machine_learning/run_stage14_matlab.bat`, then `scripts/machine_learning/validate_stage14_matlab.bat`.

The replay keeps the frozen grouped 196/46/40 split. New paired comparisons use only training-pool candidates and identical seed-specific initial sets. The actual-label greedy baseline is an oracle comparison, not a mathematical upper bound. Stage 13 active-learning curves and previously inspected Stage 12 held-out curves are separate conditions; held-out reuse is exploratory, never a new blind evaluation. MATLAB outputs include prefix curves, paired seed differences, AUC, target reachability, summaries, and plots. Simulated cycles are not translated into wall-clock savings.

Review found that the first replay’s Stage 11 prediction export contained validation/test rows only. Its training-candidate lookup therefore produced no probabilities, tying predicted-coverage and cost-aware scores at zero and making both orders equal the full-suite order. Keep that replay as historical evidence; use `run_stage14_matlab.bat` for the corrected, separate output directory. The corrected replay applies the frozen selected Stage 11 models to their training candidates in-sample, without refitting, and records that inference time separately. These predictions are exploratory and do not support generalization claims.

If the owner workstation cannot find/launch MATLAB, use Windows CMD:

```cmd
cd /d C:\RISC-V-ML-Test-Selection
scripts\machine_learning\run_stage14_matlab.bat
scripts\machine_learning\validate_stage14_matlab.bat
```

No simulator reruns are part of this stage.
