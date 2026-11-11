# Stage 14 comparative experiments

The preregistration is `reports/stage14_experiments/configuration.json`; the MATLAB runner saves dataset/model input hashes and runtime there before replay. Run `scripts/machine_learning/run_stage14_matlab.bat`, then `scripts/machine_learning/validate_stage14_matlab.bat`.

The replay keeps the frozen grouped 196/46/40 split. New paired comparisons use only training-pool candidates and identical seed-specific initial sets; actual-label oracle is an explicitly labeled upper bound. Stage 13 active-learning curves and the previously inspected saturated Stage 12 held-out curves are copied as separate conditions. Held-out reuse is exploratory, never a new blind evaluation. MATLAB outputs include machine-readable prefix curves, paired seed differences, count/cycle AUC, target reachability markers, summaries, and 300-dpi figures. Model fitting and inference are not repeated because frozen Stage 11 predictions are reused; their overhead is recorded as not measured. Simulated cycles are not translated into wall-clock savings.

If the owner workstation cannot find/launch MATLAB, use Windows CMD:

```cmd
cd /d C:\RISC-V-ML-Test-Selection
scripts\machine_learning\run_stage14_matlab.bat
scripts\machine_learning\validate_stage14_matlab.bat
```

No simulator reruns are part of this stage.
