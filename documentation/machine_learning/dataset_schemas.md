# Dataset Schemas (CSV)

Every file is keyed by `test_id` (string, e.g. `T000123`) with identical row order across features/coverage/runs. Files are produced by real simulations only.

## features.csv - PRE-EXECUTION only
Computed from the generated program image (static analysis); never from simulation outputs.

| Column | Type | Description |
|---|---|---|
| test_id | string | Key |
| profile | categorical | Generator profile |
| seed | int | Generator seed |
| inst_count | int | Static instruction count |
| program_bytes | int | Program length |
| n_arith, n_logic, n_shift, n_branch, n_jump, n_load, n_store, n_upper | int | Class counts |
| n_mul, n_div | int | M-extension counts (finer: per-op counts) |
| n_lr, n_sc, n_amo | int | A-extension counts |
| n_compressed, n_c_branch, n_c_mem | int | C-extension counts |
| n_csr, n_system | int | CSR / ECALL/EBREAK/MRET counts |
| frac_<class> | float | Class distribution |
| reg_diversity_rd, reg_diversity_rs | int | Distinct registers used |
| n_raw_dep_dist1, n_raw_dep_dist2, ... | int | Static register dependency counts by distance |
| imm_zero, imm_max, imm_min, imm_neg_frac, imm_mean_abs | num | Immediate characteristics |
| op_zero, op_allones, op_minint | int | Operand corner-case counts where statically known from LI/LUI setup |
| n_taken_hint, n_backward_branch | int | Static branch characteristics |
| max_loop_depth (optional) | int | If generated |

Caution: counts that depend on run-time values (dynamic branch outcomes) are NOT features.

## coverage.csv
`test_id`, then one 0/1 column per bin, named `bin_<id>`. 1 = the bin was hit by this test run in isolation (fresh coverage state per test).

## runs.csv
| Column | Description |
|---|---|
| test_id, seed, profile | Identity |
| executed_inst_count | Retired instructions (cost proxy, **estimated cost**) |
| status | PASS / FAIL / TIMEOUT / ERROR |
| sim_time_ns | Simulated time (simulation time, not wall-clock) |
| wall_seconds | Real runtime; blank/NaN when not measured (**actual runtime**) |
| cost_type | `proxy_instcount` or `measured_wall` |

Failed tests are retained and flagged; they are excluded from ML training unless explicitly analysed.

## bin_dictionary.csv
`bin_id`, `description`, `category` (instruction, format, operand, register, dependency, branch, memory, mext, aext, cext, csr, exception, interrupt, cross, sequence), `associated` (instruction or condition), `reachability` (reachable / unreachable / unknown), `reachability_note`, `hit_count_total`, `rarity_class`.

## Validation checks (Stage 10)
Row/ID alignment across files; no duplicate IDs; feature columns free of post-execution fields; every bin column in dictionary; seed reproducibility spot-check (rerun and compare coverage vector).
