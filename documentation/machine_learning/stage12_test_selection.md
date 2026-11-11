# Stage 12 MATLAB selection

Run `scripts\machine_learning\run_stage12_matlab.bat` and then
`scripts\machine_learning\validate_stage12_matlab.bat`. The selector reuses
the frozen Stage 10 data and Stage 11 models; it does not retrain models.

Validation chooses the cost exponent, predicted-cycle budget fraction, and
count cap. Held-out selection uses calibrated per-bin probabilities and
Stage 11 predicted cycles. Actual test labels and cycles are exported and
scored only after selection; actual-label greedy is an oracle-only upper
bound. Full-corpus replay is separate and includes in-sample train predictions.

Random selection uses 20 fixed seeds. Outputs separate candidate scores and
masks from realized observations and costs. Results are exploratory for this
small corpus and make no savings, superiority, or generalization claim.

Zero added bins reflects the already-saturated initial coverage: train plus
validation covered all 277 reachable bins per simulator. The validation-
selected test budget was about 2,082 predicted cycles; 25 selected tests used
3,451 observed cycles per simulator. Predicted-cost budgets are estimates, not
hard guarantees on actual cost. These results do not demonstrate effective
prioritization or savings; held-out outcomes were not used for tuning.
