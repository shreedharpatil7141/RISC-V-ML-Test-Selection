# MATLAB ML Architecture

MATLAB is the primary ML environment (Statistics and Machine Learning Toolbox assumed; confirm availability in Stage 11).

## Modules
| Folder | Contents |
|---|---|
| matlab/preprocessing | CSV loaders, alignment checks, scaling, rare/constant bin handling, grouped split builders |
| matlab/models | Binary-relevance training: Random Forest (`TreeBagger`, primary), Decision Tree (`fitctree`), Naive Bayes (`fitcnb`); probability calibration (Platt / isotonic-style reliability) |
| matlab/evaluation | Precision, recall, F1, micro/macro-F1, Hamming loss, AUPRC, per-bin quality, calibration curves, grouped k-fold |
| matlab/selection | Cost-aware selector, baselines (random, greedy historical, greedy oracle) |
| matlab/active_learning | Exploit-only, uncertainty-only, combined, random exploration |
| matlab/visualization | Coverage-vs-tests/cost curves, reliability diagrams, importance plots |

## Selection algorithm
For candidate t, with uncovered set U: `E[new](t) = sum_{b in U} p_b(t)`; `Score(t) = E[new](t) / cost_est(t)`. Pick argmax, execute (or replay), reveal true coverage, update U, repeat until target coverage or budget. Covered bins contribute zero.

## Baselines
Random; greedy historical (ranked by past hit totals from the training set); greedy oracle (uses true coverage of the whole candidate pool: **upper bound, not achievable**); ML-based.

## Evaluation integrity
- Grouped splits (by profile / seed family); the test pool is never used to train the model used on it.
- Offline replay (labels pre-recorded) is reported as "replay", not as real simulation savings; real closed-loop runs reported separately when performed.
- Active learning: only revealed labels may update the model; cold-start and exploration tests count toward cost.
- Metrics reported with multiple random seeds and spread.

## Reproducibility
`rng(seed)` set in every script; scripts take a config struct; results saved under `reports/` with the git commit hash.
