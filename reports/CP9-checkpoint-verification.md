# CP9 checkpoint verification

F1 completed all 28 seed-17 runs: four centralized references, twelve five-model local systems and twelve global federated systems. All 36 tests pass; the targeted F1 tests were rerun after final helper additions.

- Parent artifacts, C1 row identity, training/validation ownership and source hashes are verified.
- Each method/scenario has 2,000,000 example presentations; per-client steps and full-coverage order hashes reproduce.
- All 240 federated rounds reconstruct with independent NumPy weighted sums; uploaded shapes/dtypes/finite values, shared starts and global chaining pass.
- Final models reproduce all saved global or owner-routed validation probabilities and metrics.
- Centralized ownership views reuse the same saved probabilities; no duplicate fit is counted.
- Initializer, objective coefficient, selected learning rates, optimizer reset policy and paired local/FL order streams match F1.
- Resource, dense tensor-payload and cumulative four-hour model-worker accounting pass.
- Single seed; no final winner, DP, secure aggregation, CL or final/external score.

The machine-readable verification and comparison bind all run reports. CP10 remains required for registered challengers and seed sensitivity.
