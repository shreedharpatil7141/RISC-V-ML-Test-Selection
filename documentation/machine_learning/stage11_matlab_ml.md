# Stage 11 MATLAB baselines

Run `scripts\machine_learning\run_stage11_matlab.bat`, then
`scripts\machine_learning\validate_stage11_matlab.bat`. The batch files find
an installed R2025 MATLAB executable under `%ProgramFiles%\MATLAB` instead of
using PATH. R2025a Update 1 and the licensed Statistics and Machine Learning
Toolbox were detected on the owner laptop.

Targets are per simulator and coverage bin. XSim/Verilator rows are never
pooled. Predictors are static program byte length/diversity and configuration
indicators learned from training IDs; test/scenario names, seeds, image hashes,
coverage, costs, outcomes, and provenance are excluded. Models are majority,
decision tree, Gaussian Naive Bayes, 10-tree bagged forest, and deterministic
ridge logistic. Validation chooses by Brier score, fits calibration when class
support permits, and selects the threshold. Test metrics are computed only
after those choices are locked.

Observed cycles have one valid cost row per logical test/simulator, so a
separate cycle cost task compares median, ridge, and regression-tree models.
Wall time is not modeled. Results are exploratory for this small corpus and
do not establish generalization or superiority. Artifacts are written to
`reports/stage11_matlab_ml`.
