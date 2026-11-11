# Stage 10 Dataset Exports

Build and validation commands are `scripts\dataset\prepare_stage10_dataset.bat`
and `scripts\dataset\validate_stage10_dataset.bat`. Outputs and the hashed
lineage manifest are in `reports/stage10_dataset`.

| File | Row key and content |
|---|---|
| `test_metadata.csv` | One row per logical test: configuration, scenario, seed (raw text and numeric form where parseable), family, suite |
| `features.csv` | One row per logical test. Pre-execution configuration/scenario/seed metadata and static program image hash, byte length, and byte-value diversity |
| `coverage_labels.csv` | Long table keyed by observation ID, logical test ID, simulator, and bin ID. State explicitly distinguishes observed zero, observed hit, inapplicable, unavailable, and unsupported |
| `execution_costs.csv` | Separate simulator rows with observed cycles and measured runtime when available, units, measurement source, and status |
| `provenance.csv` | Separate simulator rows with Stage 9 schema/dictionary versions and evidence, validation, and source-provenance hashes |
| `split_assignments.csv` | One assignment per logical test; simulator counterparts share it |
| `duplicate_audit.csv` | Canonical program image hashes and exact/near-duplicate relationships |
| `schema_dictionary.csv`, `feature_dictionary.csv`, `bin_dictionary.csv` | Field types, feature roles, and Stage 9 bin definitions |
| `manifest.json` | Input/output hashes, lineage, closure lineage, split sizes, and duplicate-detection method |

There are 282 logical tests and 564 simulator observations. The simulator
rows are repeated observations of each logical test, not independent training
examples. Features do not contain coverage, runtime, cycles, outcomes, or
other post-execution values. The pipeline fits no preprocessing. Any later
preprocessing must be fit on training rows only. Splits keep normalized
scenario and template families, seed families, identical images, near-identical equal-length images
(two percent byte threshold), and simulator counterparts together. The small
corpus does not support a generalization claim.
