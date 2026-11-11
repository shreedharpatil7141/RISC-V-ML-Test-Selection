# Stage 10 dataset

Build from the closed, separate Stage 9 exports with
`scripts\dataset\prepare_stage10_dataset.bat`; validate with
`scripts\dataset\validate_stage10_dataset.bat`. Outputs are in
`reports/stage10_dataset`. There are 282 logical tests and 564 simulator
observations. Simulator observations remain separate in costs, labels, and
provenance, so the paired rows are not independent examples. Features contain only pre-execution identity
metadata. No preprocessing is fitted by this pipeline.

Splits are deterministic and grouped by normalized scenario family, exact
program image, and images within two percent byte difference; both simulator
counterparts share the logical test split. All 282 program images resolved
from the saved Stage 9/preparation artifacts, with 12 near-duplicate pairs
recorded. The manifest records actual split counts and hashes for exports,
dictionary, reports, and resolved images. This small corpus supports no
generalization claim.
